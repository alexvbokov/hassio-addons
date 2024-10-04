# valokaari plugin for hass.io. no config, minimum html

import os
import sys
import datetime
import time
import json
import math
import urllib.request
import requests
import threading


def timestamp(seconds=None):
    if seconds is None:
        seconds = time.time()
    return datetime.datetime.fromtimestamp(seconds).strftime("%Y-%m-%d,%H:%M:%S")
def str22f(temp):
    return "None" if temp is None else "%2.2f" % temp
def hour( tm=None ):
    if tm is None:
        return time.localtime()[3]
    else:
        return math.floor( ( ( tm - time.timezone ) // (60*60) ) % 24 )
def minute():
    return time.localtime()[4]
def second():
    return time.localtime()[5]

try:
    with open('/config.json', 'r') as config_file:
        config = json.load(config_file)
        version = config["version"]
        description = config["description"]
except IOError:
    print(timestamp() + " no config.json")
    version = "v.None"
    description = ""

print( "valokaari (c)Alex Bokov 2021/2024 v.newapi / " + version )
print( description )

try:
    with open('/data/options.json', 'r') as options_file:
        config = json.load(options_file)
except IOError:
    print(timestamp() + " no options.json, using defaults")
print( json.dumps( config, indent=4 ), flush=True )


config_house_delta_temp = 8

morning_at = time.localtime()
house_temp = None                           # current temp
house_morning_temp = None                   # at 7.00
just_started = True                         # recalс all values in check_house()
house_delta_temp = config_house_delta_temp  # temperature delta during a day
house_warm_up = 100                         # house warm-up at 7.00 in %, should be -> 100%
house_target_temp = None
average_temp = None                         # outside average 7:00-23:00
house_heater_on = False


def hassio_get_lat_lng():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/zone.Home", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        lat = json.loads(response)["attributes"]["latitude"]
        lng = json.loads(response)["attributes"]["longitude"]
    except:
        lat = 55.7558
        lng = 37.6173       # moscow center
    return lat, lng
def report_to_hassio( entity_id, value, friendly_name, unit, icon ):
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.post( "http://supervisor/core/api/states/"+entity_id, headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "state": value, "attributes": {"friendly_name": friendly_name, "unit_of_measurement": unit, "icon": icon } }) )
    except:
        print( timestamp() + " failed reporting to hassio", flush=True )
def hassio_set_climate( temp_low, temp_high, onoff ):
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["climate"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).json()
        attributes = response["attributes"]
        if ( attributes["target_temp_high"] != temp_high ) or ( attributes["target_temp_low"] != temp_low ) or ( response["state"] != ["heat_cool","heat"][onoff] ):
            response = requests.post( "http://supervisor/core/api/services/climate/set_hvac_mode", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "entity_id":config["climate"], "hvac_mode":["heat_cool","heat"][onoff] }) ).text
            response = requests.post( "http://supervisor/core/api/services/climate/set_temperature", headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "entity_id":config["climate"], "target_temp_high":temp_high, "target_temp_low":temp_low }) ).text
    except:
        print( timestamp() + " hassio_set_climate failed connecting to hassio", flush=True )
def hassio_climate_get_min_temp():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["climate"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        target_temp_low = json.loads(response)["attributes"]["target_temp_low"]
    except:
        target_temp_low = 18            # response = '{ "attributes": { "target_temp_low": 18.0 } }'
    return target_temp_low              # temperature
def hassio_house_temp():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["house_temp"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        temp = float( json.loads(response)["state"] )
    except:
        temp = None
    return temp
def hassio_family_is_home():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["group_family"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        state_home = not ( json.loads(response)["state"] == 'not_home' )
    except Exception as error:
        state_home = False
        print( timestamp() + " hassio_family_is_home exception occurred:", error )
    return state_home
def hassio_will_come_tomorrow():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["will_come_tomorrow"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
    except:
        response = '{ "state":"on" }'
    return ( not json.loads(response)["state"] == 'off' )
def hassio_house_heating_season():
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.get( "http://supervisor/core/api/states/"+config["house_heating_season"], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
    except:
        response = '{ "state":"on" }'
    return ( not json.loads(response)["state"] == 'off' )
def hassio_switch( switch_name, onoff ):
    state = { True:"on", False:"off" }[onoff]
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
    try:
        response = requests.post( "http://supervisor/core/api/services/switch/turn_"+state, headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "entity_id": switch_name }) )
    except:
        print( timestamp() + " failed switching " + switch_name + " to " + onoff, flush=True  )



def is_night(seconds=None):
    if seconds is None:
        seconds = time.time()
    hour = time.localtime(seconds)[3]
    minute = time.localtime(seconds)[4]
    return (hour * 60 + minute >= config["nightstart_minutes"] or hour * 60 + minute < config["daystart_minutes"])
def is_weekend():
    workdays = config['workdays'] if 'workdays' in config else config_workdays
    return ( workdays.find(str(time.localtime()[6])) < 0  )
def is_tomorrow_weekend():
    workdays = config['workdays'] if 'workdays' in config else config_workdays
    return ( workdays.find(str((time.localtime()[6]+1) % 7)) < 0 )
def todays_temp():
    weekend_temp = int(config['weekend_temp']) if 'weekend_temp' in config else config_weekend_temp
    workday_temp = int(config['workday_temp']) if 'workday_temp' in config else config_workday_temp
    return (weekend_temp if is_weekend() or family_is_home else workday_temp)
def tomorrows_temp():
    weekend_temp = int(config['weekend_temp']) if 'weekend_temp' in config else config_weekend_temp
    workday_temp = int(config['workday_temp']) if 'workday_temp' in config else config_workday_temp
    return (weekend_temp if is_tomorrow_weekend() or family_is_home or hassio_will_come_tomorrow() else workday_temp)
def tomorrows_state():
    if is_tomorrow_weekend():
        return "tomorrow is weekend"
    elif family_is_home is True:
        return "family is home"
    elif hassio_will_come_tomorrow():
        return "will come tomorrow"
    else:
        return "tomorrow is workday"



def estimated_delta():
    if house_temp is not None and house_morning_temp is not None:
        delta_time = (hour() * 60 + minute()) - (morning_at[3] * 60 + morning_at[4])
        if delta_time == 0:
            return 0
        else:
            delta_temp = house_morning_temp - house_temp
            day_length = config["nightstart_minutes"] - config["daystart_minutes"]
            return round(delta_temp * (day_length / delta_time) * 100 ) / 100
    else:
        return 8
def average_for_day(tm):
    lat, lon = hassio_get_lat_lng()
#     api_key = config["api_key"]
    if tm <= time.time():
        start_date = datetime.datetime.fromtimestamp(tm).strftime("%Y-%m-%d")
#         weather_hourly = json.loads(urllib.request.urlopen( "https://api.openweathermap.org/data/2.5/onecall/timemachine?units=metric&lat=" + str(lat) + "&lon=" + str(lon) + "&appid=" + api_key + "&dt=" + str(round((tm // 60 // 60 // 24) * 60 * 60 * 24)) ).read())["hourly"]
    else:
        start_date = datetime.datetime.fromtimestamp(tm+60*60*24).strftime("%Y-%m-%d")
#         weather_hourly = json.loads(urllib.request.urlopen( "http://api.openweathermap.org/data/2.5/onecall?exclude=current,minutely,daily,alerts&units=metric&lat=" + str(lat) + "&lon=" + str(lon) + "&appid=" + api_key ).read())["hourly"]

    print( timestamp() + " requesting average values for " + start_date, flush=True )	# datetime.datetime.fromtimestamp(tm).strftime("%d-%b-%Y")
	weather_hourly = requests.get( "https://api.open-meteo.com/v1/forecast", { "latitude": lat, "longitude": lng, "hourly": ["temperature_2m", "cloud_cover"], "start_date": start_date, "end_date": start_date } ).json()["hourly"]

    #print(json.dumps(weather_hourly, indent=4, sort_keys=True))
    temp_sigma = 0
    temp_hours = 0  # за сколько часов
    sunny_sigma = 0
    sunny_hours = 0
    # twelve_oclock_am = (tm // 60 // 60 // 24) * 60 * 60 * 24 + time.timezone
    for i in range(len(weather_hourly['time'])):
#         if weather_hourly[i]["dt"] > twelve_oclock_am and weather_hourly[i]["dt"] - twelve_oclock_am < 60 * 60 * 24:
		temp = weather_hourly['temperature_2m'][i]
		sunny = 100 - weather_hourly['cloud_cover'][i]
		hour = i			# datetime.datetime.fromtimestamp(weather_hourly[i]['dt']).hour
		if hour >= 7 and hour < 23:
			temp_sigma += temp
			temp_hours += 1
			if hour >= 10 and hour <= 14:
				sunny_sigma += sunny
				sunny_hours += 1
    day_average_temp = round((temp_sigma / temp_hours) * 10) / 10
    day_average_sunny = round((sunny_sigma / sunny_hours))/100
    print( timestamp() + " %f, %f -> average_temp %2.1f, average_sunny %2.2f" % ( lat, lon, day_average_temp, day_average_sunny ), flush=True )
    return day_average_temp, day_average_sunny


def house_heating_on_off( onoff ):
    if hassio_house_heating_season():
        hassio_switch( config["house_heating"], onoff )
def check_house():
    global house_temp
    global house_heater_on
    global house_morning_temp
    global house_warm_up
    global morning_at
    global house_delta_temp
    global house_target_temp
    global average_temp
    global just_started

    if house_temp != hassio_house_temp():
        house_temp = hassio_house_temp()
#         print( timestamp() + " house temp: %s °C" % house_temp, flush=True )

    if house_morning_temp is None:
        house_morning_temp = round( house_temp, 1 )
        morning_at = time.localtime()
        try:
            average_temp, average_sunny = average_for_day(time.time()) # today
        except urllib.error.URLError:
            print(timestamp() + " request timeout", flush=True )
            average_temp = None
        except:
            average_temp = None

        house_delta_temp = estimated_delta()
        house_target_temp = round( tomorrows_temp() + house_delta_temp, 1)
        average_temp = round(average_temp, 1) if average_temp is not None else None

    if house_temp is not None:
        if is_night() or just_started is True:      # night
            if hour() * 60 + minute() == config["nightstart_minutes"] or just_started is True:      # night just started
                if just_started is True:
                    print(timestamp() + " just started. calculating values...", flush=True )
                    just_started = False;

                try:
                    average_temp, average_sunny = average_for_day(time.time()) # today
                    print(timestamp() + " morning_temp = %.2f, house_temp = %.2f, hour = %d, morning_at = %d, average_temp = %.2f" % (morning_temp,house_temp,hour(),hour(morning_at),average_temp) )
                    k = ( morning_temp - house_temp ) / ( ( hour() - hour(morning_at) ) * (( morning_temp + house_temp )/2 - average_temp ) )
                    print(timestamp() + " calculated K = " + str(k), flush=True)
                except urllib.error.URLError:
                    print(timestamp() + " request timeout", flush=True )
                except:
                    print(timestamp() + " failed calculating K", flush=True )

                try:
                    average_temp, average_sunny = average_for_day(time.time()+60*60*24) # tomorrow
                    k = float(config["house_k"])
                    a = float(config["house_a"])
                    house_delta_temp = (tomorrows_temp() - average_temp) * k * 16 / (1 - k * 8) - a * average_sunny
                except urllib.error.URLError:
                    print(timestamp() + " request timeout", flush=True )
                    house_delta_temp = config_house_delta_temp
                    average_temp = None
                except:
                    house_delta_temp = config_house_delta_temp
                    average_temp = None
                house_target_temp = round( tomorrows_temp() + house_delta_temp, 1)
                average_temp = round(average_temp, 1) if average_temp is not None else None
                print(timestamp() + " house_target_temp for tomorrow morning: %s + %s = %s" % ( tomorrows_temp(), round(house_delta_temp,1), house_target_temp ) + ", " + tomorrows_state(), flush=True)

            evening_target_temp = tomorrows_temp() if hour() * 60 + minute() >= config["nightstart_minutes"] else todays_temp()
            if house_temp < evening_target_temp + house_delta_temp and ( house_temp < config["max_temp"] or family_is_home is False ):
                if house_heater_on is False:
                    print( timestamp() + " house temp: %s °C" % house_temp, flush=True )
                    print( timestamp() + " switching " + config["house_heating"] + " to on", flush=True )
                house_heater_on = True
            if house_temp > evening_target_temp + house_delta_temp + 0.5 or ( house_temp > config["max_temp"] and family_is_home ):
                if house_heater_on is True:
                    print( timestamp() + " house temp: %s °C" % house_temp, flush=True )
                    print( timestamp() + " switching " + config["house_heating"] + " to off", flush=True )
                house_heater_on = False
            house_heating_on_off( house_heater_on )

            house_min_temp = hassio_climate_get_min_temp()
            hassio_set_climate( house_min_temp, min( house_target_temp, config["max_temp"] ), house_heater_on )
        else:               # day
            if hour() * 60 + minute() == config["daystart_minutes"]:        # day just started
                house_morning_temp = round( house_temp, 1 )

                if ( house_temp - todays_temp() ) > 0:
                    if house_delta_temp != 0:
                        house_warm_up = round( min( abs( float(house_temp - todays_temp() ) / house_delta_temp ) * 100, 100 ) / 5 ) * 5     # <= 100%
                    else:
                        house_warm_up = 100
                else:
                    house_warm_up = 100     # no need to warm up
                morning_at = time.localtime()
                print(timestamp() + " morning temperature: %s °C" % house_temp, flush=True )
                hassio_switch( config["will_come_tomorrow"], False )


            house_delta_temp = estimated_delta()

            house_min_temp = hassio_climate_get_min_temp()      # config["min_temp"] if "min_temp" in config else config_min_temp
            if house_temp < house_min_temp :
                if house_heater_on is False:
                    house_heater_on = True
                    print( timestamp() + " house temp: %s °C" % house_temp, flush=True )
                    print( timestamp() + " switching " + config["house_heating"] + " to on", flush=True )
            if house_temp > house_min_temp + 1:
                if house_heater_on is True:
                    house_heater_on = False
                    print( timestamp() + " house temp: %s °C" % house_temp, flush=True )
                    print( timestamp() + " switching " + config["house_heating"] + " to off", flush=True )
            house_heating_on_off( house_heater_on )
            hassio_set_climate( house_min_temp, house_min_temp+1, house_heater_on )



while True:
    family_is_home = hassio_family_is_home()
    check_house()
    time.sleep(1)
    report_to_hassio( "sensor.valokaari_house_target_temp", house_target_temp, "target temp", "°C", "")
    report_to_hassio( "sensor.valokaari_average_temp", average_temp, "average temp", "°C", "")
    report_to_hassio( "sensor.valokaari_house_morning_temp", house_morning_temp, "morning temp", "°C", "")
    report_to_hassio( "sensor.valokaari_house_warm_up", house_warm_up, "warm up", "%", "mdi:radiator")  # initial

    while second() != 0:     # wait until minute start
        time.sleep(1)
