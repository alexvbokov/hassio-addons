# rain & precipitations volume for hass.io (с) Alex Bokov 2021-2022

import os
import sys
import math
import time
import json
import urllib.request
import requests

print( "begin...." )

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

print( "precipitation (c)Alex Bokov 2021-2022 v1.1")
#config = {'lat':'56.2062', 'lon':'37.7987', 'api_key':'8f093e433c0c2b70df025f186097d63d', "hassio_token":"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJkYTg1Y2QyNTU3YzY0MGU0YmRjZmQ2NzNiYmIzNDFjNSIsImlhdCI6MTYwODI5OTYzMywiZXhwIjoxOTIzNjU5NjMzfQ.dy6asQ0LuDZnm0qgeeZSwKv772hyBZvh4x_Zj3sEokw" }
config = {}
try:
    with open( '/data/options.json', 'r') as config_file:
        config = json.load(config_file)
except IOError:
    print(timestamp() + " no options.json, using defaults")
print(timestamp() + " " + str(config))


hassio_ip = "192.168.0.4"
precipitations_quantity = None
precipitations_checked_at = None
precipitations_since_home = 0       # amount since family was home
weather_icons = ['','','','','','','','']
dates = ['','','','','','','','']
week_day = [ "пн","вт","ср","чт","пт","сб","вс" ]


def report_to_hassio():
    if precipitations_quantity is not None:

        try:
            response = requests.post(
                "http://"+hassio_ip+":8123/api/states/sensor."+"precipitations_since_home",
                headers={ "Authorization": "Bearer "+config['hassio_token'], "content-type": "application/json" },
                data=json.dumps({ "state": round( precipitations_since_home, 1 ), "attributes": {"friendly_name": "precipitations since home", "unit_of_measurement": "mm", "icon": "mdi:weather-snowy" } })
            )
        except:
            print( timestamp() + "failed reporting to hassio" )

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
                entity_id = "precipitations"
            else:
                entity_id = "precipitations"+str(i)
            try:
                response = requests.post(
                    "http://"+hassio_ip+":8123/api/states/sensor."+entity_id,
                    headers={ "Authorization": "Bearer "+config['hassio_token'], "content-type": "application/json" },
                    data=json.dumps({ "state": value, "attributes": {"friendly_name": dates[i], "unit_of_measurement": "", "icon": icon } })
                )
            except:
                print( timestamp() + "failed reporting to hassio" )
            # print( response.text )

def hassio_family_is_home():
    try:
        response = requests.get( "http://"+hassio_ip+":8123/api/states/group.family", headers={ "Authorization": "Bearer "+config['hassio_token'], "content-type": "application/json" } ).text
    except:
        response = '{ "state":"home" }'
    return ( not json.loads(response)["state"] == 'not_home' )




def check_precipitations():
    global precipitations_quantity
    global precipitations_checked_at
    global precipitations_since_home
    global dates
    if ( precipitations_quantity is None ) or ( hour() == 0 and minute() == 0 ) or ( time.time() - precipitations_checked_at > 24 * 60 * 60 ):
        precipitations_quantity = [ 0,0,0,0,0,0,0,0 ]
        precipitations_checked_at = math.floor(time.time())

        family_is_home = hassio_family_is_home()

        try:
            weather = json.loads(urllib.request.urlopen("http://api.openweathermap.org/data/2.5/onecall?exclude=current,minutely,hourly,alerts&units=metric&lat=" + config['lat'] + "&lon=" + config['lon'] + "&appid=" + config['api_key'] ).read())["daily"]
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
        print( precipitations_quantity )
    return ( precipitations_quantity is not None )
        # report_to_hassio()



check_precipitations()


while True:
    if check_precipitations():
        report_to_hassio()

    while second() != 0:
        time.sleep(1)
