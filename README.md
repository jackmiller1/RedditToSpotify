# RedditToSpotify
Creates a playlist on spotify from songs posted on reddit.  

The diskmemo class memoizes a function and saves the cache to disk.  This was added so the script could be run as a cron job and prevent tracks from having to be looked up on spotify multiple times.  This also allows multiple scripts to share the same cache.

## Getting Started
1. Create an application on https://developer.spotify.com 
1. Create client id, client secrete, and redirect url (ie. http://localhost)
1. Setup your environment:

  ```
  export SPOTIPY_CLIENT_ID='your_client_id'
  export SPOTIPY_CLIENT_SECRET='your_client_secret'
  export SPOTIPY_REDIRECT_URI='your_redirect_url'
  ```
1. Install script dependencies

   ```pip install -r requirements.txt```
1. Run the script

  ```python3 main.py --username USERNAME```
  
1. For help or a list of parameters, run
  
  ```python3 main.py --help```


  ```
Usage: main.py [OPTIONS]

Options:
  --subreddit TEXT                The subreddit to get tracks from
  --time [hot|new|top_all|top_year|top_month|top_week|top_day|top_hour]
                                  The sorting method for the tracks
  --username TEXT                 Spotify username
  --playlist_size INTEGER RANGE   Size of the playlist to make
  --playlist_name TEXT            The name of the playlist to create.
  --replace_playlist              Whether the playlist should be cleared
                                  before adding new tracks.
  --help                          Show this message and exit.

  ```
