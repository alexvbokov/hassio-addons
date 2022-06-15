#!/usr/bin/with-contenv bashio

# echo "== $(printenv SUPERVISOR_TOKEN) =="
# wget -q -O- --header="Authorization: Bearer $(printenv SUPERVISOR_TOKEN)" --header="Content-Type: application/json" http://supervisor/core/api/states/sensor.processor_temperature
# hassio_ip=$(ha network info | grep "192.168" | grep "/" | awk '{print $2}' | cut -d/ -f1)
# echo "hassio ip is $hassio_ip"


#!/usr/bin/with-contenv bashio

# Generate key
KEY_PATH=/data/ssh_keys
if [ ! -d "$KEY_PATH" ]; then
    echo "[INFO] Setup private key"
    mkdir -p "$KEY_PATH"

	ssh-keygen -t ed25519 -N "" -f "${KEY_PATH}/autossh_ed25519"
else
    echo "[INFO] Restore private_keys"
fi

echo "[INFO] public key is:"
cat "${KEY_PATH}/autossh_ed25519.pub"

echo "[INFO] json config is:"
cat /data/options.json 


#client_id=$(cat /data/options.json | jq -r ".client_id")
#client_ssh=$(cat /data/options.json | jq -r ".client_ssh")
#hassio_ip=$(/usr/bin/ha network info | grep "192.168" | grep "/" | awk '{print $2}' | cut -d/ -f1)


#hassio_ip=$(cat /data/options.json | jq -r ".hassio_ip")
#hassio_ip=$(/usr/bin/ha network info | grep "192.168" | grep "/" | awk '{print $2}' | cut -d/ -f1)


client_id=23456
hassio_ip="127.0.0.200"

cloud_hostname='cloud.uzvhost.ru'
cloud_username='cloudio'
cloud_ssh_port=722
control_port=$((client_id))
monitor_port=$((control_port+1))


# export AUTOSSH_DEBUG=1

echo "[INFO] testing cloud ssh connection"
ssh -o StrictHostKeyChecking=no -p $cloud_ssh_port $cloud_hostname 2>/dev/null || true

command_args="-M ${monitor_port} -R 0.0.0.0:${control_port}:${hassio_ip}:8123 -N -q -o ServerAliveInterval=25 -o ServerAliveCountMax=3 ${cloud_username}@${cloud_hostname} -p ${cloud_ssh_port} -i ${KEY_PATH}/autossh_ed25519"
echo "[INFO] command args: ${command_args}"
/usr/bin/autossh ${command_args}



