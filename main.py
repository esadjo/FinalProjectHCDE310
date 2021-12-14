#!/usr/bin/env python

# checking that apis work for PythonAnywhere -- https://www.pythonanywhere.com/whitelist/
##### STARTING FROM HERE
# Reference documentation source: Sean -- https://github.com/hcde310a21/ClassCode/blob/main/s17/spotify-oauth-example-nodatastore/main.py
# Reference from -- https://github.com/hcde310a21/ClassCode/tree/main/s17/spotify-oauth-example-nodatastore

import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests
import urllib.request, urllib.error, urllib.parse, json, webbrowser
from flask import Flask, render_template, request, session, redirect, url_for
import logging



app = Flask(__name__) # Question -- how modify this and main if using google app, etc.


### Utility functions
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

# ---------- OPENWEATHER CODE -----------
from hw7key import key as google_api_key
from weather_api_key import key as openweather_API_key
def extract_lat_long_weather(city_state):
    lat, lng = None, None
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
    city_state_clean = city_state.replace(" ", "")
    endpoint = str(base_url) + "?address=" + str(city_state_clean) + "&key=" + str(google_api_key)
    r = urllib.request.urlopen(endpoint).read()
    r = json.loads(r)
    results = r['results'][0]
    # Reference - https://openweathermap.org/current#geo
    args = {}
    args['lat'] = str(results['geometry']['location']['lat']) #lat
    args['lon'] = str(results['geometry']['location']['lng']) #lng
    args['appid'] = openweather_API_key
    weather_url = 'https://api.openweathermap.org/data/2.5/weather?' + urllib.parse.urlencode(args)
    re = urllib.request.urlopen(weather_url).read()
    request = json.loads(re)
    weather_forecast = request['weather'][0]['description']
    return(weather_forecast.lower())

# Reference - https://openweathermap.org/weather-conditions
def weather_to_music_match(weather_forecast):
    music_features = {'energy':[]}

    if ('thunder' in weather_forecast) or ('hail' in weather_forecast):
        music_features['energy'] = [0.8, 1]
    elif ('rain' in weather_forecast) or ('drizzle' in weather_forecast) or ('cloud' in weather_forecast):
        music_features['energy'] = [0.1, 0.58]
    elif ('snow' in weather_forecast) or ('ice' in weather_forecast) or ('sleet' in weather_forecast):
        music_features['energy'] = [0, 0.1]
    elif ('sunny' in weather_forecast) or ('clear' in weather_forecast):
        music_features['energy'] = [0.58, 0.8] # CHANGE BACK -- 0.75
    else: #Need to catch mist, etc.
        music_features['energy'] = [0, 1]
    return(music_features)





# ------------ SPOTIFY CODE ----------------
from secrets import client_id, client_secret #importing client app related information from secret file
grant_type = 'authorization_code'

# To crypotgraphically secure our sessions. Do this with client secret
app.secret_key = client_secret



# Function to add header w/ user's access_token when requesting data from Spotify about the user and its activities
def spotifyurlfetch(url,access_token,params=None):
    headers = {'Authorization': 'Bearer '+access_token,
               'Content-Type': "application/json",
               "Accept": "application/json"}
    req = urllib.request.Request(
        url = url,
        data = params,
        headers = headers
    )
    try:
        response = urllib.request.urlopen(req)
        return response.read()
    except urllib.error.HTTPError as e:
        return e.read()

def sortKeysByValue(dictionary): # right now, wouldn't sort correctly -- see if need to
    keys = dictionary.keys()
    return sorted(keys, key= lambda k: dictionary[k], reverse= True)

#def getUserPlaylists(accessToken, userId, offest)
   #params = {}
    #params['limit'] = '50'
    #params['offset'] = offsetNum
    #url = "https://api.spotify.com/v1/users/%s/playlists"%userId + urllib.parse.urlencode(params)
    #response = json.loads(spotifyurlfetch(url,accessToken))
    #playlists=response["items"] # list of dictionaries
    #return playlists
    #FINISH --


    # Need a method where pulls tracks features -- tests them # getAudioFeaturesAndSeeIfMatchesWeather
def audioFeatureAnalysis(accessToken, trackId, dictionary): #dictionary with weather acoustic features
    url = 'https://api.spotify.com/v1/audio-features/' + trackId
    response = json.loads(spotifyurlfetch(url, session['access_token']))
    trackEnergy = response['energy']

    # dictionary format -- {energy: [low, high]}
    energyLow = dictionary['energy'][0]
    energyHigh = dictionary['energy'][1]

    #if (trackAcousticness > acousticLow) and (trackAcousticness <= acousticHigh):
    if (trackEnergy > energyLow) and (trackEnergy <= energyHigh):
        return True
    else:
        return False



def createPlaylist(accessToken, userId, location, weather): #, offsetNum):
    #Getting playlists to be able to see if Spot In the Weather playlists currently exists
    url = "https://api.spotify.com/v1/users/%s/playlists"%userId
    # in the future, should make this more robust so it checks
    # if the access_token is still valid and retrieves a new one
    # using refresh_token if not
    response = json.loads(spotifyurlfetch(url,accessToken))
    playlists=response["items"] # list of dictionaries
    for playlist in playlists:
        if playlist["name"] == "Spot In the Weather":
            return playlist["id"] #QUESTION -- how ensure that seeing all playlists (they might have more than 50 playlists -- probably need to do multiple for loops where
    # if doesn't return id -- meaning it doesn't find the playlist in the list of playlists, then should create a playlist
    # Reference -- https://developer.spotify.com/console/post-playlists/
    #Create playlist if doesn't already exist
    inquiryParams = {}
    inquiryParams['name'] = "Spot in the Weather"
    inquiryParams['description'] = "A personalized playlist for " + weather + " in " + location + "."
    inquiryParams['public'] = False
    #paramsencoded = urllib.parse.urlencode(inquiryParams).encode("ascii")
    paramsencoded = json.dumps(inquiryParams).encode("ascii")
    response = json.loads(spotifyurlfetch(url, accessToken, paramsencoded))
    return response["id"] #playlist id of new, created playlist


### Handlers ###

### handler for handling home page # COME BACK TO -- NEED TO MODIFY THIS PART
@app.route("/")
def index():
    if 'user_id' in session:
        return redirect(url_for('location'))
    else:
        return render_template('oauth.html') # COME BACK TO HERE -- AS WELL #added playlistID



### handler for user authorization requests where have users log in
@app.route("/auth/login")
def login_handler():
    # after  login; redirected here
    # did we get a successful login back?


    inquiryParams = {}
    inquiryParams['client_id'] = client_id

    verification_code = request.args.get("code")
    if verification_code:
        # if so, we will use code to get the access_token from Spotify
        # This corresponds to STEP 4 in https://developer.spotify.com/web-api/authorization-guide/

        inquiryParams["client_secret"] = client_secret
        inquiryParams["grant_type"] = grant_type
        # store the code we got back from Spotify
        inquiryParams["code"] = verification_code
        # the current page
        inquiryParams['redirect_uri'] = request.base_url
        data = urllib.parse.urlencode(inquiryParams).encode("utf-8")

        # We need to make a POST request, according to the documentation
        # headers = {'content-type': 'application/x-www-form-urlencoded'}
        url = "https://accounts.spotify.com/api/token"
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, data=data)
        response_dict = json.loads(response.read())
        access_token = response_dict["access_token"]
        refresh_token = response_dict["refresh_token"]

        # Download the user profile. Save profile and access_token
        # in Datastore; we'll need the access_token later

        ## the user profile is at https://api.spotify.com/v1/me
        profile = json.loads(spotifyurlfetch('https://api.spotify.com/v1/me', access_token))

        ## Put user info in session, but not that risk of all user data being exposed, including access_token
        session['user_id'] = profile["id"]
        session['displayname'] = profile["display_name"]
        session['access_token'] = access_token
        session['profile_url'] = profile["external_urls"]["spotify"]
        session['api_url'] = profile["href"]
        session['refresh_token'] = refresh_token
        if profile.get('images') is not None:
            session['img'] = profile["images"][0]["url"]

        ## Then send them back to the App's home page
        return redirect(url_for('index'))
    else:
        # not logged in yet-- send the user to Spotify to do that
        # Following STEP 1 in https://developer.spotify.com/web-api/authorization-guide/

        inquiryParams['redirect_uri'] = request.base_url
        inquiryParams['response_type'] = "code"
        # ask for the necessary permissions -
        # see details at https://developer.spotify.com/web-api/using-scopes/
        inquiryParams['scope'] = "user-library-modify playlist-modify-private playlist-modify-public playlist-read-collaborative playlist-read-private user-top-read"

        url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(inquiryParams)
        return redirect(url)


@app.route("/location")
def location():
    app.logger.info("Main_Handler")
    return render_template('location info.html', user=session)


@app.route("/track")
def track():
    city_state = request.args.get('city_state')
    app.logger.info(city_state)
    if city_state == "":
        error = "Location - Error"
        errorMessage = "Something went wrong with the API Call :( Try again!"
        return render_template('location info.html', error=error, errorMessage=errorMessage)
    currentWeather = extract_lat_long_weather(city_state)
    music_features_dict = weather_to_music_match(currentWeather)


    if currentWeather is not None:
        #Need to add call to method to get weather in location (city_state) and call weather_to_music_match <--- TO DO!!!!
            if 'user_id' in session:
                #If logged in
                # Step 1 -- get user's top tracks and retrieve their uris, putting them into a dictionary to later make a call to add those items to playlist (Step 3)
                queryParamsDict = {}
                queryParamsDict['time_range'] = 'medium_term' # conditional if not enough options, refresh and pull other artists -- # or long_term? -- but then years
                queryParamsDict['limit'] = '50' #make sure won't break if a new artists and don't have 50 artists
                url = 'https://api.spotify.com/v1/me/top/tracks?' + urllib.parse.urlencode(queryParamsDict)
                response = json.loads(spotifyurlfetch(url, session['access_token']))
                trackItems = response["items"]
                #return render_template('tracks.html', user=session['user_id'], trackItems=trackItems)
                trackItemsForPlaylist = []

                #return render_template('location info.html', user=session['user_id'], trackItems=trackItems)
                # Step 2 -- Creating a dictionary of track Uris to then be able to add them to the "Spot In the Weather" playlist
                # also pulling Spotify ids to get audio features
                trackUriDict = {'uris': []}
                trackIdDict = {'ids': []}
                tracksDisplayList = []
                for track in trackItems:
                    trackUri = track['uri']
                    #trackUriDict['uris'].append(trackUri)

                    trackId = track['id']
                    meetCriteria = audioFeatureAnalysis(session['access_token'], trackId, music_features_dict)
                    if meetCriteria == True:
                        trackItemsForPlaylist.append(track)
                        #trackIdDict['ids'].append(trackId)
                        trackUriDict['uris'].append(trackUri)

                        #Adding to dictionary for easier html processing on tracks.html page
                        listofArtists = []

                        for artist in track['artists']:
                            listofArtists.append(artist['name'])

                        listingArtists = ""
                        if len(listofArtists) > 1:
                            for artist in listofArtists[:-1]:  # up to and not including last artist
                                listingArtists += artist + ", "
                            listingArtists += "and " + listofArtists[-1]
                        else:
                            listingArtists = listofArtists[0]

                        tracksDisplayList.append(track['name'] + " by " + listingArtists)





                # Step 2 -- Create new playlist if "Spot In the Weather" playlist doesn't exist already
                # Documentation --
                # Retrieve plyalistId
                playlistId = createPlaylist(session['access_token'],session['user_id'], city_state, currentWeather) # NOTE -- MIGHT NEED TO USE THIS IN A DIFFERENT PLACE #QUESTION -- do I need to pass these are parameters or is the scope larger than that that could refer to directly in the methods I created

                # Step 3 - Adding Items to Playlist
                # Documentation -- https://developer.spotify.com/console/post-playlist-tracks/
                # post requestion
                #urlTracks = 'https://api.spotify.com/v1/playlists/%s/tracks?'%playlistId + urllib.parse.urlencode(trackUriDict)
                #urlTracks = 'https://api.spotify.com/v1/playlists/%s/tracks?'%playlistId + urllib.parse.urlencode({'uris': 'spotify:track:0BWBqb5XxraObLopqskk6D'})
                urlTracks = 'https://api.spotify.com/v1/playlists/%s/tracks'%playlistId
                tracksencoded = json.dumps(trackUriDict).encode("ascii")
                #responseTracks = json.loads(spotifyurlfetch(urlTracks, session['access_token']))
                responseTracks = json.loads(spotifyurlfetch(urlTracks, session['access_token'],tracksencoded))

                # We need to make a POST request, according to the documentation
                # headers = {'content-type': 'application/json'} ??
                #response_dict = json.loads(spotifyurlfetch(url, session['access_token']))

            else:
                trackItems = None
                trackItemsForPlaylist = None
                #playlists = None
                tracksDisplayList = None

            return render_template('tracks.html', user=session, trackItemsForPlaylist=trackItemsForPlaylist, currentWeather=currentWeather, music_features_dict=music_features_dict, city_state=city_state, tracksDisplayList=tracksDisplayList, playlistId=playlistId) # COME BACK TO HERE -- AS WELL #added playlistID


    #Something wrong with the way catching errors -- need to fix it so that it won't go through --@Sarah
    #Ask about how to catch error for when someone doesn't input something valid (e.g., a number) -- Not covered with  "is not None"
    else:
        error = "Location - Error"
        errorMessage = "Something went wrong with the API Call :( Try again!"
        return render_template('location info.html', error=error, errorMessage=errorMessage)






## handler to log the user out by making the cookie expire (deletes all the keys have stored for that user from the session)
@app.route("/auth/logout")
def logout_handler():
    ## remove each key from the session!
    for key in list(session.keys()):
        session.pop(key)
    return redirect(url_for('index'))


if __name__ == "__main__":
    # Used when running locally only.
	# When deploying to Google AppEngine, a webserver process
	# will serve your app.
    app.run(host="localhost", port=8080, debug=True)