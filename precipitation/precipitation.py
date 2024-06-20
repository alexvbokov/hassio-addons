# rain & precipitations volume for hass.io (с) Alex Bokov 2021-2024

import os
import sys
import math
import time
from datetime import datetime
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


print( "precipitation (c)Alex Bokov 2021-2024", flush=True )
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
weather_codes = ['','','','','','','','']
dates = ['','','','','','','','']
week_day = [ "пн","вт","ср","чт","пт","сб","вс" ]
verbose = config['verbose']
supervisor_token = os.environ["SUPERVISOR_TOKEN"]


def report_to_hassio():


    def report_precipitations( entity_id, friendly_name, value, icon ):
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
            if weather_codes[i] in [ 0 ]:						icon = "mdi:weather-sunny"         	# clear sky
            if weather_codes[i] in [ 1,2,3 ]: 					icon = "mdi:weather-partly-cloudy" 	# few clouds
            if weather_codes[i] in [ 45,48 ]: 					icon = "mdi:weather-cloudy"        	# scattered clouds
            if weather_codes[i] in [ 51,53,55,56,57 ]: 			icon = "mdi:weather-rainy" 			# drizzle
            if weather_codes[i] in [ 61,63,65,66,67,80,81,82 ]: icon = "mdi:weather-rainy"  		# shower rain
            if weather_codes[i] in [ 71,73,75,77,85,86 ]: 		icon = "mdi:weather-snowy"         	# snow
            if weather_codes[i] in [ 95,96,99 ]: 				icon = "mdi:weather-lightning"     	# thunderstorm
            if i == 0 :
                report_precipitations( "precipitations", "precipitations", value, icon )
            report_precipitations( "precipitations"+str(i), dates[i], value, icon )
            print( icon )


def hassio_family_is_home():
    try:
        response = requests.get( "http://supervisor/core/api/states/group.family", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        if verbose is True:
            print( response )
        print( timestamp() + " hassio_family_is_home: ", json.loads(response)["state"] )
    except:
        response = '{ "state":"home" }'
        print( timestamp() + " assuming family is home" )
    return ( not json.loads(response)["state"] == 'not_home' )
def hassio_get_lat_lng():
    try:
        response = requests.get( "http://supervisor/core/api/states/zone.Home", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        if verbose is True:
            print( response )
        lat = json.loads(response)["attributes"]["latitude"]
        lng = json.loads(response)["attributes"]["longitude"]
    except:
        lat = 55.7558
        lng = 37.6173       # moscow center
    print( timestamp() + " latitude, longitude: ", lat, lng )
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
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
			"latitude": lat,
			"longitude": lng,
			"daily": ["weather_code", "precipitation_sum"],
			"timezone": "Europe/Moscow",
			"forecast_days": 8
		}

        try:
            weather = requests.get( url, params ).json()["daily"]
            if family_is_home:
                precipitations_since_home = 0
            else:
            	precipitations_since_home += weather["precipitation_sum"][0]
        except:
            weather = {}
            precipitations_quantity = None


        for i in range(8):
            weather_codes[ i ] = weather["weather_code"][i]
            dates[i] = week_day[ datetime.strptime(weather['time'][i],'%Y-%m-%d').weekday() ]
            precipitations_quantity[ i ] = weather["precipitation_sum"][i]
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
