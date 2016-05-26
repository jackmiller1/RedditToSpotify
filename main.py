import re
from collections import namedtuple

from diskmemo import DiskMemoize
import praw
import spotipy
import spotipy.util
import click

Track = namedtuple('Track', ['track', 'artist'])
       
class RedditPlaylist():

    ## Memoize the spotify uri for tracks
    TrackMemoize = DiskMemoize('tracks.pickle', cache_filter=lambda t: t is not None)

    ## Regular expression to parse a reddit post's title)
    ## In the form "artistName -- trackName [genre / genres] (year)"
    title_re = re.compile(r"(?P<artist>.*?) -+ (?P<track>.*?) \[(?P<genre>.*?)\] \((?P<year>\d+)\)")

    def __init__(self, subreddit, time_period, playlist_size, playlist_name, username, replace_playlist):
        self.reddit = praw.Reddit(user_agent="spotify_scraper")

        ## Subreddit to pull from
        self.subreddit = subreddit

        ## Can be 'all', 'year', 'month', 'week', 'day', or 'hour'
        self.time_period = time_period

        ## Desired playlist size
        self.playlist_size = playlist_size

        ## Name of playlist on spotify
        self.playlist_name = playlist_name

        ## Spotify username
        self.username = username

        self.spotify = self.login_to_spotify()

        ## Whether the playlist should be cleared before adding new tracks
        self.replace_playlist = replace_playlist

    ## Attempts to login to spotify
    def login_to_spotify(self):
        token = spotipy.util.prompt_for_user_token(self.username, scope='playlist-modify-public')
        if token:
            return spotipy.Spotify(auth=token)
        else:
            return spotipy.Spotify()

    ## Extracts the artist and track from the title of a post.
    ## Possible to also get genre and year.
    def parse_title(self, title):
        parsed_title = re.match(RedditPlaylist.title_re, title)
        if parsed_title != None:
            return Track(parsed_title.group('track'), parsed_title.group('artist'))


    ## Fetches the posts from the subreddit
    ## param: last_id   The reddit ID of the last post from a previous query
    def get_posts(self, last_id=None):
        sub = self.reddit.get_subreddit(self.subreddit)    
        ## Map a time period to a function
        funcs = {
            'hot': sub.get_hot,
            'new': sub.get_new,
            'top_all': sub.get_top_from_all,
            'top_day': sub.get_top_from_day,
            'top_hour': sub.get_top_from_hour,
            'top_month': sub.get_top_from_month,
            'top_week': sub.get_top_from_week,
            'top_year': sub.get_top_from_year
        }
        if last_id != None:
            return list(funcs.get(self.time_period, sub.get_hot)(limit = self.playlist_size, params={'after': 't3_'+last_id}))
        else:
            return list(funcs.get(self.time_period, sub.get_hot)(limit = self.playlist_size))

    ## Parses the artist and track from every post in 'posts' array
    def parse_posts(self, posts):
        tracks = [self.parse_title(post.title) for post in posts]
        return [track for track in tracks if track is not None]

    ## Searchs for tracks on spotify.  Returns an array of spotify IDs for found tracks
    def get_spotify_tracks(self, tracks):
        found_tracks = [self.get_spotify_track_uri(track) for track in tracks]
        return [track for track in found_tracks if track is not None]

    ## Queries spotify for a track and returns the 
    @TrackMemoize
    def get_spotify_track_uri(self, track):
        uri = None
        query = "artist:'{artist}' track:'{track}'".format(artist=track.artist, track=track.track)
        results = self.spotify.search(query, type="track", limit=1)
        if results['tracks']['total'] > 0:
            uri = results['tracks']['items'][0]['uri']
        return uri

    ## Finds enough tracks on spotify to fill a playlist with the size 'self.playlist_size'
    def find_tracks(self):
        tracks = []
        last_id = None
        while len(tracks) < self.playlist_size:
            posts = self.get_posts(last_id=last_id)
            ## If there are no more posts to look at, return the tracks found so far
            if len(posts) == 0:
                return tracks
            last_id = posts[-1].id
            found_tracks = self.parse_posts(posts)
            tracks.extend(self.get_spotify_tracks(found_tracks))
        return tracks[:self.playlist_size]


    ## Finds the playlist with a specific name or returns None if not found
    def find_playlist(self):
        playlists = self.spotify.user_playlists(self.username)['items']
        for playlist in playlists:
            if playlist['name'] == self.playlist_name and playlist['owner']['id'] == self.username:
                return playlist
        return None

    ## Returns a list of track ids in the playlist
    def playlist_track_ids(self, playlist_id):
        tracks = []
        results = self.spotify.user_playlist(self.username, playlist_id, fields='tracks,next')['tracks']
        tracks.extend([track['track']['uri'] for track in results['items']])
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend([track['track']['uri'] for track in results['items']])
        return tracks

    ## Adds the tracks to a playlist
    ## Returns the number added to the playlist
    def add_to_playlist(self, tracks):
        playlist = self.find_playlist()
        if playlist == None:
            playlist = self.spotify.user_playlist_create(self.username, self.playlist_name)
        
        if playlist and playlist.get('id'):
            if self.replace_playlist:
                self.spotify.user_playlist_replace_tracks(self.username, playlist.get('id'), tracks)
            else:
                ## Get the current tracks in playlist and only add new ones
                current_tracks = self.playlist_track_ids(playlist.get('id'))
                new_tracks = set(tracks).difference(current_tracks)
                if len(new_tracks) > 0:
                    self.spotify.user_playlist_add_tracks(self.username, playlist.get('id'), new_tracks)

    ## Creates a playlist from a subreddit with a desired length
    def make_playlist(self):
        tracks = self.find_tracks()
        
        formatting_dict = {
            'track_count': len(tracks), 
            'playlist_name': self.playlist_name
        }
        if self.replace_playlist:
            print("Replacing {track_count} tracks in '{playlist_name}'".format(**formatting_dict))
        else:
            print("Adding {track_count} tracks to '{playlist_name}'".format(**formatting_dict))

        self.add_to_playlist(tracks)
        RedditPlaylist.TrackMemoize.save_cache()

@click.command()
@click.option('--subreddit', default='listentothis', help="The subreddit to get tracks from")
@click.option('--time', default='hot', help="The sorting method for the tracks", type=click.Choice(['hot', 'new', 'top_all', 'top_year', 'top_month', 'top_week', 'top_day', 'top_hour']))
@click.option('--username', help='Spotify username', prompt='Please enter your Spotify username', type=str)
@click.option('--playlist_size', default=25, help='Size of the playlist to make', type=click.IntRange(1, 100))
@click.option('--playlist_name', default='listentothis', help='The name of the playlist to create.')
@click.option('--replace_playlist', help="Whether the playlist should be cleared before adding new tracks.", is_flag=True)
def main_cli(subreddit, time, username, playlist_size, playlist_name, replace_playlist):
    r = RedditPlaylist(subreddit, time, playlist_size, playlist_name, username, replace_playlist)
    r.make_playlist()

if __name__ == '__main__':
    main_cli()