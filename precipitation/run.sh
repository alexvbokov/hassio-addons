#!/usr/bin/with-contenv bashio

#cat /data/options.json
echo "/data folder contents"
ls -la /data

echo "./ folder contents"
ls -la

echo "find / "
find /

echo "now running..."
while ((1)); do 
	python3 /precipitation.py && break
done
echo "finishing..."

