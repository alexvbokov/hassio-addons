#!/usr/bin/with-contenv bashio

#cat /data/options.json
echo "/data folder contents"
ls -l /data

echo "./ folder contents"
ls -l 

echo "now running..."
while ((1)); do 
	python3 /precipitation.py && break
done
echo "finishing..."

