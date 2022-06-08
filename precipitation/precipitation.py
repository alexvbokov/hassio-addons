# rain & precipitations volume for hass.io (с) Alex Bokov 2021-2022

import os
import sys
import math
import time
import json
import urllib.request
import requests

def timestamp(seconds=None):
    from datetime import datetime
    if seconds is None:
        seconds = time.time()
    return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d,%H:%M:%S")
def str22f(temp):
    return "None" if temp is None else "%2.2f" % temp
def hour():
    return time.localtime()[3]
def minute():
    return time.localtime()[4]
def second():
    return time.localtime()[5]


print( "precipitation (c)Alex Bokov 2021-2022", flush=True )
config = {}
try:
    with open( '/data/options.json', 'r') as config_file:
        config = json.load(config_file)
except IOError:
    print( timestamp() + " no options.json, using defaults", flush=True )
print( timestamp() + " " + str(config), flush=True )


precipitations_quantity = None
precipitations_checked_at = None
precipitations_since_home = 0       # amount since family was home
weather_icons = ['','','','','','','','']
dates = ['','','','','','','','']
week_day = [ "пн","вт","ср","чт","пт","сб","вс" ]


def report_to_hassio():

    supervisor_token = os.environ["SUPERVISOR_TOKEN"]

    def report_precipitations( entity_id, friendly_name, value ):
        try:
            response = requests.post(
                "http://supervisor/core/api/states/sensor."+entity_id,
                headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" },
                data=json.dumps({ "state": value, "attributes": {"friendly_name": friendly_name, "unit_of_measurement": "", "icon": icon } })
            )
        except:
            print( timestamp() + " failed reporting to hassio", flush=True )


    if precipitations_quantity is not None:

        try:
            response = requests.post(
                "http://supervisor/core/api/states/sensor."+"precipitations_since_home",
                headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" },
                data=json.dumps({ "state": round( precipitations_since_home, 1 ), "attributes": {"friendly_name": "precipitations since home", "unit_of_measurement": "mm", "icon": "mdi:weather-snowy" } })
            )
        except:
            print( timestamp() + " failed reporting to hassio", flush=True )

        for i in range(8):
            value = round( precipitations_quantity[i], 1 )
            if "01" in weather_icons[i]: icon = "mdi:weather-sunny"         # clear sky
            if "02" in weather_icons[i]: icon = "mdi:weather-partly-cloudy" # few clouds
            if "03" in weather_icons[i]: icon = "mdi:weather-cloudy"        # scattered clouds
            if "04" in weather_icons[i]: icon = "mdi:weather-partly-cloudy" # broken clouds
            if "09" in weather_icons[i]: icon = "mdi:weather-partly-rainy"  # shower rain
            if "10" in weather_icons[i]: icon = "mdi:weather-rainy"         # rain
            if "11" in weather_icons[i]: icon = "mdi:weather-lightning"     # thunderstorm
            if "13" in weather_icons[i]: icon = "mdi:weather-snowy"         # snow
            if "50" in weather_icons[i]: icon = "mdi:weather-fog"           # mist
            if i == 0 :
                report_precipitations( "precipitations", "precipitations", value )
            report_precipitations( "precipitations"+str(i), dates[i], value )


def hassio_family_is_home():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/group.family", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        print( "hassio_family_is_home: ", response )
    except:
        response = '{ "state":"home" }'
    return ( not json.loads(response)["state"] == 'not_home' )
def hassio_get_lat_lng():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/zone.Home", headers={ "Authorization": "Bearer "+token, "content-type": "application/json" } ).text
        lat = json.loads(response)["attributes"]["latitude"]
        lng = json.loads(response)["attributes"]["longitude"]
    except:
        lat = 55.7558
        lng = 37.6173       # moscow center
    return lat, lng



def check_precipitations():
    global precipitations_quantity
    global precipitations_checked_at
    global precipitations_since_home
    global dates
    if ( precipitations_quantity is None ) or ( hour() == 0 and minute() == 0 ) or ( time.time() - precipitations_checked_at > 24 * 60 * 60 ):
        precipitations_quantity = [ 0,0,0,0,0,0,0,0 ]
        precipitations_checked_at = math.floor(time.time())

        family_is_home = hassio_family_is_home()
        lat, lng = hassio_get_lat_lng()

        try:
            weather = json.loads(urllib.request.urlopen("http://api.openweathermap.org/data/2.5/onecall?exclude=current,minutely,hourly,alerts&units=metric&lat=" + lat + "&lon=" + lng + "&appid=" + config['api_key'] ).read())["daily"]
            if family_is_home:
                precipitations_since_home = 0
            else:
                if "snow" in weather[0]:
                    precipitations_since_home += weather[0]["snow"]
                if "rain" in weather[0]:
                    precipitations_since_home += weather[0]["rain"]
        except:
            weather = {}
            precipitations_quantity = None


        for i in range( len(weather) ):
            weather_icons[ i ] = weather[i]["weather"][0]["icon"]
            dates[i] = week_day[ time.localtime(weather[i]['dt'])[6] ]
            if "snow" in weather[i]:
                precipitations_quantity[ i ] += weather[i]["snow"]
            if "rain" in weather[i]:
                precipitations_quantity[ i ] += weather[i]["rain"]
        print( timestamp() + str( precipitations_quantity ), flush=True )
    return ( precipitations_quantity is not None )


count = 0
while True :
    try:
        hassio_family_is_home()
        break
    except:
        count += 1
        time.sleep(1)
        if count > 100:
            print( timestamp() + " tried connecting to hassio %d times, giving up ..." % count, flush=True )
            sys.exit()

check_precipitations()


progress_bar = "  ··°°ººooooºº°°··  "
while True:
    if check_precipitations():
        report_to_hassio()

    while second() != 0:     # wait until minute start
#       print(progress_bar[second() % 20],flush=True,end="")
        time.sleep(1)
    print()
    time.sleep(1)
