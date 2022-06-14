#!/usr/bin/with-contenv bashio

echo "== $(printenv SUPERVISOR_TOKEN) =="
wget -q -O- --header="Authorization: Bearer $(printenv SUPERVISOR_TOKEN)" --header="Content-Type: application/json" http://supervisor/core/api/states/zone.Home

