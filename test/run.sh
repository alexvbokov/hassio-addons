#!/usr/bin/with-contenv bashio

echo "== $(printenv SUPERVISOR_TOKEN) =="
wget -q -O- --header="Authorization: Bearer $(printenv SUPERVISOR_TOKEN)" --header="Content-Type: application/json" http://supervisor/core/api/states/sensor.processor_temperature

hassio_ip=$(ha network info | grep "192.168" | grep "/" | awk '{print $2}' | cut -d/ -f1)
echo "hassio ip is $hassio_ip"