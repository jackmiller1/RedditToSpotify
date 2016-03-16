import re
from collections import namedtuple
from enum import Enum 

import praw
import spotipy
import spotipy.util as util
import click

Track = namedtuple('Track', ['track', 'artist'])

class RedditPlaylist():

    ## Regular expression to parse a reddit post's title
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

        self.spotify = self.__login_to_spotify()

        ## Whether the playlist should be cleared before adding new tracks
        self.replace_playlist = replace_playlist


    ## Attempts to login to spotify
    def __login_to_spotify(self):
        token = util.prompt_for_user_token(self.username, scope='playlist-modify-public')
        if token:
            return spotipy.Spotify(auth=token)
        else:
            return spotipy.Spotify()

    ## Extracts the artist and track from the title of a post.
    ## Possible to also get genre and year.
    def __parse_title(self, title):
        a = re.match(RedditPlaylist.title_re, title)
        if a != None:
            return Track(a.group('track'), a.group('artist'))


    ## Fetches the posts from the subreddit
    ## param: last_id   The reddit ID of the last post from a previous query
    def __get_posts(self, last_id=None):
        sub = self.reddit.get_subreddit(self.subreddit)    
        ## Map a time period to a function
        funcs = {
            'all': sub.get_top_from_all,
            'day': sub.get_top_from_day,
            'hour': sub.get_top_from_hour,
            'month': sub.get_top_from_month,
            'week': sub.get_top_from_week,
            'year': sub.get_top_from_year
        }
        if last_id != None:
            return list(funcs.get(self.time_period, sub.get_top_from_all)(limit = self.playlist_size, params={'after': 't3_'+last_id}))
        else:
            return list(funcs.get(self.time_period, sub.get_top_from_all)(limit = self.playlist_size))

    ## Parses the artist and track from every post in 'posts' array
    def __parse_posts(self, posts):
        tracks = []
        for post in posts:
            t = self.__parse_title(post.title)
            if t != None:
                tracks.append(t)
        return tracks

    ## Searchs for tracks on spotify.  Returns an array of spotify IDs for found tracks
    def __get_spotify_tracks(self, tracks):
        found_tracks = []
        for track in tracks:
            query = "artist:'{artist}' track:'{track}'".format(artist=track.artist, track=track.track)
            results = self.spotify.search(query, type="track", limit=1)
            if results['tracks']['total'] > 0:
                found_tracks.append(results['tracks']['items'][0]['uri'])
        return found_tracks

    ## Finds enough tracks on spotify to fill a playlist with the size 'self.playlist_size'
    def __find_tracks(self):
        tracks = []
        last_id = None
        while len(tracks) < self.playlist_size:
            posts = self.__get_posts(last_id=last_id)
            ## If there are no more posts to look at, return the tracks found so far
            if len(posts) == 0:
                return tracks

            last_id = posts[-1].id
            found_tracks = self.__parse_posts(posts)
            tracks.extend(self.__get_spotify_tracks(found_tracks))
        return tracks[:self.playlist_size]


    ## Finds the playlist with a specific name or returns None if not found
    def __find_playlist(self):
        playlists = self.spotify.user_playlists(self.username)['items']
        for playlist in playlists:
            if playlist['name'] == self.playlist_name and playlist['owner']['id'] == self.username:
                return playlist
        return None

    ## Returns a list of track ids in the playlist
    def __playlist_track_ids(self, playlist_id):
        tracks = []
        results = self.spotify.user_playlist(self.username, playlist_id, fields='tracks,next')['tracks']
        tracks.extend([track['track']['uri'] for track in results['items']])
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend([track['track']['uri'] for track in results['items']])
        return tracks

    ## Adds the tracks to a playlist
    ## Returns the number added to the playlist
    def __add_to_playlist(self, tracks):
        playlist = self.__find_playlist()
        if playlist == None:
            playlist = self.spotify.user_playlist_create(self.username, self.playlist_name)
        
        if playlist and playlist.get('id'):
            if self.replace_playlist:
                self.spotify.user_playlist_replace_tracks(self.username, playlist.get('id'), tracks)
            else:
                ## Get the current tracks in playlist and only add new ones
                current_tracks = self.__playlist_track_ids(playlist.get('id'))
                new_tracks = set(tracks).difference(current_tracks)
                if len(new_tracks) > 0:
                    self.spotify.user_playlist_add_tracks(self.username, playlist.get('id'), new_tracks)

    ## Creates a playlist from a subreddit with a desired length
    def make_playlist(self):
        tracks = self.__find_tracks()
        formatting_dict = {
            'track_count': len(tracks), 
            'playlist_name': self.playlist_name
        }
        if self.replace_playlist:
            print("Replacing {track_count} tracks in '{playlist_name}'".format(**formatting_dict))
        else:
            print("Adding {track_count} tracks to '{playlist_name}'".format(**formatting_dict))

        self.__add_to_playlist(tracks)

@click.command()
@click.option('--subreddit', default='listentothis', help="The subreddit to get tracks from")
@click.option('--time', default='all', help="The time period to get the top tracks.", type=click.Choice(['all', 'year', 'month', 'week', 'day', 'hour']))
@click.option('--username', help='Spotify username', prompt='Please enter your Spotify username', type=str)
@click.option('--playlist_size', default=25, help='Size of the playlist to make', type=click.IntRange(1, 1000))
@click.option('--playlist_name', default='listentothis', help='The name of the playlist to create.')
@click.option('--replace_playlist', help="Whether the playlist should be cleared before adding new tracks.", is_flag=True)
def main_cli(subreddit, time, username, playlist_size, playlist_name, replace_playlist):
    r = RedditPlaylist(subreddit, time, playlist_size, playlist_name, username, replace_playlist)
    r.make_playlist()

if __name__ == '__main__':
    main_cli()