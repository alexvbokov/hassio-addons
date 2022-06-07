#!/usr/bin/with-contenv bashio

cat /data/options.json
echo "now running..."
while ((1)); do 
	python3 /precipitation.py && break
done
echo "finishing..."

