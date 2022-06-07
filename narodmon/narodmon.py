import socket
import os
import sys
import time
import json
import urllib.request
import threading
import math
import requests



config_server = '185.245.187.136'   # narodmon.ru
config_period = 300                 # seconds between reporting
config_mac = 'ESP_E8DB84DE4F30'
config_sensors = [
    { "name": "28B4BE061720060D", "sensor_name": "sensor.house_temp" },
    { "name": "28890DD21620060F", "sensor_name": "sensor.house_temp_upstairs" },
    { "name": "28D640CF162006A5", "sensor_name": "sensor.outside_temp" },
    { "name": "28DE8FC716200655", "sensor_name": "sensor.radiator_water_temp" },
    { "name": "280E43DC1620063E", "sensor_name": "sensor.radiator_water_back_temp" }
]
supervisor_token = os.environ["SUPERVISOR_TOKEN"]



def timestamp(seconds=None):
    from datetime import datetime
    if seconds is None:
        seconds = time.time()
    return datetime.fromtimestamp(seconds).strftime("%Y-%m-%d,%H:%M:%S")
def get_script_path():
    path = os.path.dirname(os.path.realpath(sys.argv[0]))
    return path if path != '/' else ''
def str22f(temp):
    return "None" if temp is None else "%2.2f" % temp
def hour():
    return time.localtime()[3]
def minute():
    return time.localtime()[4]
def second():
    return time.localtime()[5]



def reboot_script():
    print("doing reboot/exit...")
    os._exit( 0 )

def watchdog():
    threading.Timer(60.0, watchdog).start()
    if time.time() - watchdog_timestamp > 30 * 60:      # 30 minutes?
        print(timestamp() + " rebooting (stopping) by internal watchdog...\n\n\n\n\n\n\n\n")
        reboot_script()



program_start = time.time()
watchdog_timestamp = time.time()
watchdog()      # init ones


time_reported = time.time()
time_delta = config_period


print( "report data to narodmon.ru (c)Alex Bokov 2021-2022 v1.1", flush=True )


count = 0
while True:

    watchdog_timestamp = time.time()


    request = "#" + config_mac
    for sensor in config_sensors:
        try:
            response = requests.get( "http://supervisor/core/api/states/"+sensor['sensor_name'], headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" } ).text
        #    print( response )
        #    response = urllib.request.urlopen(sensor['url']).read()
            data = json.loads(response)
        #    print( data )
            value = data['state']   # if data['state'] != -127.00 else None
        #    print( value )
        #    print( config_sensors[i]["name"] + ":" + str22f(value) )
        except:
            value = None
        if value is not None:
            request += "\n#" + sensor["name"] + "#" + value
    request += "\n##"

    if request != "#" + config_mac:
        print(timestamp() + " " + request.replace("\n", " "))
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((config_server, 8283))
            sock.send(request.encode("utf-8"))
            response = str(sock.recv(64))
            print(response)
            sock.close()
        except socket.error:
            print(timestamp() + " error connecting to " + config_server)
    else:
        print(timestamp() + " nothing to report to " + config_server)
    time_reported = time.time()



    progress_bar = "   ···°°°ºººooooooººº°°°···   "
    while time.time() - time_reported < time_delta:
        print(progress_bar[second() % 20],flush=True,end="")
        time.sleep(3)
    print("")


    count += 1
    if count >= 288:        # hour() * 60 + minute() == 7 * 60 :     # morning reboot
        count = 0;
        reboot_script()

