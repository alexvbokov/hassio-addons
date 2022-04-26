#!/usr/bin/with-contenv bashio

cat /data/options.json
echo "pre-run..."
while true; do python3 /precipitation.py; done
echo "post-run..."

