# RedditToSpotify
Creates a playlist on spotify from songs posted on reddit

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
  --time [all|year|month|week|day|hour]
                                  The time period to get the top tracks.
  --username TEXT                 Spotify username
  --playlist_size INTEGER RANGE   Size of the playlist to make
  --playlist_name TEXT            The name of the playlist to create.
  --replace_playlist              Whether the playlist should be cleared
                                  before adding new tracks.
  --help                          Show this message and exit.

  ```
