import tidalapi
import spotipy
from spotipy.oauth2 import SpotifyOAuth

#MAJOR BUG: The code can skip over songs where the lengths of the "added" and "not_added" variables don't add up to the length of the playlist.
#It's usually not much, but I don't know how to fix it.

#These logins will open a url in your browser. Then in the terminal, it will ask you to paste the link it redirected you to. Just do what it says.

# Initialize Tidal stuff
session = tidalapi.Session()
session.login_oauth_simple()
user = session.user

#Initialize Spotify stuff
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="***your id***",
    client_secret="***your secret***",
    redirect_uri="https://www.pictureofhotdog.com/",
    scope="user-library-read" #This may need to be changed
))

# Get current user's playlists
playlists = sp.current_user_playlists()
playlists_offset=0
while len(playlists)!=0: #on every iteration, loads playlists again but offsets by a greater amount to load new ones because max spotify can load is 50 i think
    #go through either your playlists or your liked songs
    playlists = sp.current_user_playlists(limimt=50, offset=playlists_offset) #I'm pretty sure 50 is the maximum spotify can load
    liked_songs = sp.current_user_saved_tracks(limit=50) #I'm pretty sure 50 is the maximum spotify can load
    for playlist in playlists['items']:
        
        #make a new playlist or use Tidal's "My Collection"
        new_playlist = user.create_playlist(playlist["name"],description='')
        favorites = tidalapi.Favorites(session, user.id)
        
        total = int(playlist['tracks']['total']) #number of tracks in playlist
        song_offset = 0 
        not_added = []
        added=[]

        while len(not_added) + len(added) < total:  #on every iteration, loads playlists again but offsets by a greater amount to load new ones
            for item in sp.current_user_saved_tracks(limit=50, offset=song_offset)["items"]: #can loop through liked songs or playlists (liked songs as is)
                title = item['track']['name']
                artist = item['track']['artists'][0]['name']
                album = item['track']['album']['name']

                response = session.request.request(
                    'get',
                    'search',
                    params={
                        'query': f'{title} {artist}',
                        'types': 'TRACKS',
                        'limit': 50,
                        'countryCode': session.country_code
                    }
                ).json() #searches for the song in Tidal by title and artist

                found = False #found song match flag
                for track in response['tracks']['items']: #loops through search results
                    if (artist.lower() in track['artists'][0]['name'].lower() or
                        album.lower() in track['album']['title'].lower() or 
                        track['artists'][0]['name'].lower() in artist.lower() or
                        track['album']['title'].lower() in album.lower()): #my super dumb algorithm to see if the songs match. Probably a better way to do this.
                        new_playlist.add(str(track['id']))

                        #favorites.add_track(str(track['id'])) do this if using Tidal favorites
                        if track['title'] not in added:
                            added.append(track['title']) #this might not work. if it doesn't u can just do track['id'] or whatever
                        found = True
                        break
                if not found:
                    print(f'could not add {title}, {artist}, {album} to playlist {playlist['name']}')
                    if title not in not_added:
                        not_added.append(title)

            #sometimes these numbers don't add up to the full 50. Idk why.
            print(f"added: {len(added)}, not added: {len(not_added)}")
            song_offset+=50%total
    playlists_offset+=50
