import os
import datetime
import time
import json
import urllib.request
import requests
import numpy as np
import base64
from io import BytesIO
from PIL import Image


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
        return tm[3]
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
    
    
config = { 
    "x_start": 0.1,
    "x_end": 0.9,
    "y_start": 0,
    "y_end": 0.16,
    "scan_interval": 10,
    "sensor": "sensor.cctv_light",
    "dusk": 50,
    "dark": 10,
    "camera_url": "http://192.168.0.96/ISAPI/Streaming/channels/101/picture",
    "userpass": "bokov:bokov1972"
  }

print( "camera light sensor (c)Alex Bokov 2025 " + version )
print( description )

try:
    with open('/data/options.json', 'r') as options_file:
        config = json.load(options_file)
except IOError:
    print(timestamp() + " no options.json, using defaults")
print( json.dumps( config, indent=4 ), flush=True )



def report_to_hassio( entity_id, value, friendly_name, unit, icon ):
    supervisor_token = os.environ["SUPERVISOR_TOKEN"]
#     supervisor_token = "SUPERVISOR_TOKEN"
    try:
        response = requests.post( "http://supervisor/core/api/states/"+entity_id, headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "state": value, "attributes": {"friendly_name": friendly_name, "unit_of_measurement": unit, "icon": icon } }) )
    except:
        print( timestamp() + " failed reporting to hassio", value, flush=True )


def cctv_camera_light_value( camera_url, userpass, x_start, x_end, y_start, y_end ):

    request = urllib.request.Request(camera_url)
    base64_auth = base64.b64encode(userpass.encode('ascii')).decode('ascii')    # Кодирование логина и пароля в формат Base64 для HTTP заголовка 'Authorization'
    request.add_header('Authorization', f'Basic {base64_auth}')
    
    try:
        with urllib.request.urlopen(request) as response:
            image_bytes = response.read()
    except Exception as e:
        print( timestamp() + f"image download error: {e}", flush=True )
        return None

#     # 2. Преобразование байтов изображения в формат массива NumPy, понятный OpenCV
#     # Преобразуем байты в массив numpy
#     np_array = np.frombuffer(image_bytes, np.uint8)
#     # Декодируем массив numpy в изображение OpenCV (BGR формат)
#     img_cv2 = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
# 
#     if img_cv2 is None or img_cv2.size == 0:
#         print("Ошибка: Не удалось декодировать изображение. Проверьте URL или формат изображения.")
#         return None

    try:
        img = Image.open(BytesIO(image_bytes))  # Pillow сам поймёт, что это JPEG
    except Exception as e:
        print( timestamp() + f"can't open JPEG: {e}", flush=True )
        return None
    
    img = img.convert("RGB")	# Приводим к RGB (на случай, если камера отдаёт YUV-JPEG или что-то редкое)
    img_np = np.array(img)		# Сразу получаем numpy-массив [H, W, 3]

    height, width, _ = img_np.shape
    x_start_px = int(width * x_start)    # Преобразование относительных долей в абсолютные пиксели
    x_end_px = int(width * x_end)
    y_start_px = int(height * y_start)
    y_end_px = int(height * y_end)

    cropped_img = img_np[
        min(y_start_px, y_end_px):max(y_start_px, y_end_px), 
        min(x_start_px, x_end_px):max(x_start_px, x_end_px)
    ]

    if cropped_img is None or cropped_img.size == 0:
        print( timestamp() + f"empty image. before crop: {width}x{height}. crop to: X={x_start_px}:{x_end_px}, Y={y_start_px}:{y_end_px}", flush=True)
        return None

    gray_image = cropped_img.mean(axis=2).astype(np.uint8)
#     cv2.imwrite("grey.jpg", gray_image)

    return np.mean(gray_image)


while True:
    time.sleep(1)
    light_value = cctv_camera_light_value( config["camera_url"], config["userpass"], config["x_start"], config["x_end"], config["y_start"], config["y_end"] )
    if light_value is not None:
        report_to_hassio( config["sensor"], round(light_value), "cctv light", "", "mdi:weather-sunset" )
        report_to_hassio( config["sensor"]+"_dusk", ["off","on"][ light_value <= config["dusk"] ], "cctv light dusk", "", "mdi:weather-sunset" )
        report_to_hassio( config["sensor"]+"_dark", ["off","on"][ light_value <= config["dark"] ], "cctv light dark", "", "mdi:weather-sunset" )

        print( timestamp(), "reported", config["sensor"], round(light_value), flush=True )
        

    while second() % config["scan_interval"] != 0:
        time.sleep(1)
