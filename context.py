import json
import pandas as pd
from IPython.display import display, HTML
from collections.abc import Iterable
import spotipy
import spotipy.util as util
import requests
import os
import re



class spotifyContext():
    
    def __init__(self, folder = None):
        if folder == None:
            self.folder = os.getcwd()
        else:
            self.folder = folder
        self.playlists = None
        self.username = 'sebsan.619'
        self.client_id ='17b4fe6f10e04bb1871f5eb68362dab8'
        self.client_secret = '9182b7b53b0d4fd584b631160df9dfc6'
        self.redirect_uri = 'http://localhost:7777/callback'
        self.scope = 'user-read-recently-played'
        self.token = util.prompt_for_user_token(username=self.username, 
                                   scope=self.scope, 
                                   client_id=self.client_id,   
                                   client_secret=self.client_secret,     
                                   redirect_uri=self.redirect_uri)

        self.lookUpFails = []

        

        

        #self.data = data['playlists']
                
    
    def lookUp(self, title: str, artist: str, playlist = None):
        #Given string with feature in the title, remove the (feat. " ---- ") 
        # ex. 'Drove you crazy (fasdasdf) (feat. Bryson Tiller)' (#by Gucci Mane) ---> Drove you crazy (fasdasdf) bryson tiller gucci mane
        

        match = re.search(r'\(feat. (.+)\)', title)
        if match != None:
            ft = match.group(1)
            index = title.index('(feat. ')
            title = title[0:index]
            title = title + ft
        
        query = title + " " + artist
        

        success, trackID = self.getTrackID(query, self.token)


        if success:
            info = self.getFeatures(trackID, self.token)
            genres = self.getGenres(trackID, self.token)
        else:
            info = []
            genres = []

        return [info, genres]
    
    #Go back and change later
    def getPlaylists(self):
        '''Prints all playlists associated with user'''
        
        with open("Playlist.json", encoding="utf8") as f:
            rawData = json.load(f)
            self.playlists = rawData['playlists']

        #Account for off by one in playlist info method
        count = 1
        lst = []
        for x in self.playlists:
            lst.append(str(count) + ": "+ x['name'] + ": " + str(x['numberOfFollowers']) + " followers")
            #print(str(count) + ": "+ x['name'] + ": " + str(x['numberOfFollowers']) + " followers")
            count += 1
        return lst

    def loadPlaylistFrame(self, index):
        '''returns dataframe of selected playlist'''
        
        dict = self.getPlaylistInfo(index)
        df = pd.DataFrame(dict, columns = ["Title", "Artist", "Album"])
        #display(df)
        return df
    
    def loadStreamFrame(self):
        '''returns dataframe of Stream History'''
        dict = self.getStreamInfo()
        df = pd.DataFrame(dict, columns = ["Title", "Artist", "Listen Time"])
        #display(df)
        return df
    
    def loadLibraryFrame(self):
        '''returns dataframe of User Library'''
        dict = self.getLibraryInfo()
        df = pd.DataFrame(dict, columns = ["Title", "Artist", "Album"])
        #display(df)
        return df
    

    def getQueries(self):
        '''returns list of query history'''
        with open('SearchQueries.json', encoding="utf8") as f:
            rawData = json.load(f)

        self.queries = []
        for x in rawData:
            if x['typedQuery'] != None:
                self.queries.append(x['typedQuery'])
        return self.queries

    
    

    
    
    
    
    #---------------------------------------------------------------------------------------------------------
    
    
    def getTrackID(self, query: str, token: str) -> str:
        headers = { 'Authorization': 'Bearer ' + token,}

        params = (
            ('q', query),
            ('type', 'track'),
        )

        try:
            response = requests.get('https://api.spotify.com/v1/search', 
                        headers = headers, params = params, timeout = 5)
            json = response.json()
            #Major issue is that the first track returned by spotify is not necessarily the correct one based on the search
            #This is particularly the case for small artists
            first_result = json['tracks']['items'][0]
            track_id = first_result['id']
            return True, track_id
        except:
            print("track id is none here")
            self.lookUpFails.append(query)
            return None, query

    def getGenres(self, id, token):
        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
        }

        params = (
        ('market', 'US'),
        )

        response = requests.get('https://api.spotify.com/v1/tracks/' + id, headers=headers, params=params)
        json = response.json()

        #Use to check that this is the right song in previous method maybe
        reponseArtist = json['album']['artists'][0]['name']
        responseAlbum = json['album']['name']
        responseTrack = json['name']

        artistID = json['artists'][0]['id']


        headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
        }

        response2 = requests.get('https://api.spotify.com/v1/artists/' + artistID, headers=headers)
        json2 = response2.json()
        genres = json2['genres']
        
        
        return genres



    #Gets features from track ID argument and returns as dictionary
    def getFeatures(self, track_id: str, token: str) -> dict:
        sp = spotipy.Spotify(auth=token)
        try:
            features = sp.audio_features([track_id])
            #print(features)
            return features[0]
        except:
            return None
    
    
    def getPlaylistInfo(self, index):
        index -= 1
            
        if self.playlists == None:
            self.getPlaylists()
        
        title = []
        artist = []
        album = []

        for x in self.playlists[index]['items']:
            title.append(x['track']['trackName'])
            artist.append(x['track']['artistName'])
            album.append(x['track']['albumName'])
        info = {
            'Title' : title,
            'Artist' : artist,
            'Album' : album,
        }
        return info
    
    def getStreamInfo(self):
        with open('StreamingHistory.json', encoding="utf8") as f:
            self.streamHistory = json.load(f)

        title = []
        artist = []
        length = []

        for x in self.streamHistory:
            title.append(x['artistName'])
            artist.append(x['trackName'])
            length.append(x['msPlayed'])



        mins = []
        secs = []

        #Convert mins ms to mins and seconds separately
        for ms in length:
            m, s = divmod(ms, (1000*60))
            mins.append(m)
            secs.append(int(s / (1000)))


        #Format mins and seconds as string
        timeSigs = []
        for x in range(0, len(mins)):
            #print(x)
            tempMin = mins[x]
            #print(tempMin)
            tempSec = secs[x]
            if tempSec < 10:
                builder = str(tempMin) + ":" + "0" + str(tempSec)
            else:
                builder = str(tempMin) + ":" + str(tempSec)
            timeSigs.append(builder)

        info = {
            'Title' : title,
            'Artist' : artist,
            'Listen Time' : timeSigs,
        }

        #Extra calcs if needed    
        inSeconds = [ms / (1000) for ms in length]

        totalSeconds = 0
        for time in inSeconds:
            totalSeconds += time
        #End of extras

        return info
    
   
    def getLibraryInfo(self):
        with open('YourLibrary.json', encoding="utf8") as f:
            self.library = json.load(f)
        
        title = []
        artist = []
        album = []

        for x in self.library['tracks']:
            title.append(x['track'])
            artist.append(x['artist'])
            album.append(x['album'])

        info = {
            'Title' : title,
            'Artist' : artist,
            'Album' : album,
        }

        return info

    
#-----------------------------------------------------------------------------------------------------------
                                                #Data frame manipulation
    
    def getCache(self, dataframe):
        
        try:
            with open("sebCache.json") as f:
                js = json.load(f)
        except:
            js = self.updateFrames(dataframe)
            js2 = json.dumps(js, indent = 2)
            with open("sebCache.json", "w+") as f:
                f.write(js2)

        return js
            
    
    def updateFrames(self, dataframe):
        
        title = ""
        artist = ""
        album = ""

        genres = []
        danceability = []
        energy = []
        loudness = []
        speechiness = []
        acousticness = []
        instrumentalness = []
        liveness = []
        tempo = []
        timeSig = []


        for x in range(0, dataframe.shape[0] - 1):
            title = dataframe.iat[x, 0]
            artist = dataframe.iat[x, 1]
            album = dataframe.iat[x, 2]

            print(title)

            qInfo = self.lookUp(title, artist)

            features = qInfo[0]
            genre = qInfo[1]

            if len(features) == 0 or len(genre == 0):
                continue


            genres.append(genre)
            danceability.append(features["danceability"])
            energy.append(features["energy"])
            loudness.append(features["loudness"])
            speechiness.append(features["speechiness"])
            acousticness.append(features["acousticness"])
            instrumentalness.append(features["instrumentalness"])
            liveness.append(features["liveness"])
            tempo.append(features["tempo"])
            timeSig.append(features["time_signature"])

        return {"genres": genres,
                "danceability": danceability,
                "energy": energy,
                "loudness" : loudness,
                "speechiness" : speechiness,
                "acousticness" : acousticness,
                "instrumentalness" : instrumentalness,
                "liveness" : liveness,
                "tempo" : tempo,
                "timeSig" : timeSig,
        }




if __name__ == "__main__":
    import os
    print(os.getcwd())

    import sebSpotifyDev.context as ctx

    me = ctx.spotifyContext()

    trip = me.loadPlaylistFrame(3)

    myStreams = me.loadStreamFrame()
    myStreams

    myLibrary = me.loadLibraryFrame()
    myLibrary

    myQueries = me.getQueries()
    myQueries

    me.lookUp("in your arms", "illenium")

    me.updateFrames(myLibrary)


#Where am I:
# -Currently obtaining all of the genre and classification information for every song in an inputted list of songs (library, playlist etc)
# -

#What I need to do:
# -Check each search for correct song - and if song cannot be found, try other options
# -Store all learned information in a cache file that grows over time so I don't have to spend a ton of time everytime waiting for the file to process

#Where I want to go:
# -For each collection of songs, firstly be able to visualize things and provide conclusions based on the data
# -Beyond this, offer recommendations (see Gnoosic)