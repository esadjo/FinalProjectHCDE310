import ssl
ssl._create_default_https_context = ssl._create_unverified_context
import requests
import urllib.request, urllib.error, urllib.parse, json, webbrowser
from flask import Flask, render_template, request
import logging


### Utility functions
def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)


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
    print(weather_forecast.lower())

# Reference - https://openweathermap.org/weather-conditions
def weather_to_music_match(weather_forecast):
    music_features = {'energy':[], 'acousticness':[]}
    if 'thunder' or 'hail' in weather_forecast:
        music_features['acousticness'] = [0, 0.0125]
        music_features['energy'] = [0.5, 0.75]
    elif 'rain' or 'drizzle' or 'cloud' in weather_forecast:
        music_features['acousticness'] = [0.5, 0.75]
        music_features['energy'] = [0, 0.25]
    elif 'snow' or 'ice' or 'sleet' in weather_forecast:
        music_features['acousticness'] = [0.05, 0.5]
        music_features['energy'] = [0.25, 0.5]
    elif 'sunny' or 'clear' in weather_forecast:
        music_features['acousticness'] = [0.75, 1]
        music_features['energy'] = [0.75, 1]
    else:
        music_features['acousticness'] = [0, 1]
        music_features['energy'] = [0, 1]
    return(music_features)



app = Flask(__name__)

@app.route("/")
def main_handler():
    app.logger.info("Main_Handler")
    return render_template('location info.html', page_title="Location")


@app.route("/response")
def get_coord():
    city_state = request.args.get('city_state')
    app.logger.info(city_state)
    lat_long = extract_lat_long(city_state)
    music_features = weather_to_music_match(extract_lat_long_weather(city_state))
    if lat_long is not None:
        title = "Coordinates for %s"%city_state + " are: " + str(lat_long[0]) + ", " + str(lat_long[1]) + 'and this is the music_features: ' + music_features
        return render_template('music dictionary.html', title=title)
    else:
        return render_template('music dictionary.html',
                               page_title="Location - Error",
                               prompt="Something went wrong with the API Call :(")
if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)


