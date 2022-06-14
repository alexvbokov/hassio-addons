#!/usr/bin/with-contenv bashio

echo "== $(printenv SUPERVISOR_TOKEN) =="
curl -X GET -H "Authorization: Bearer $(printenv SUPERVISOR_TOKEN)" -H "Content-Type: application/json" http://supervisor/network/config
# python3 /test.py

