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
