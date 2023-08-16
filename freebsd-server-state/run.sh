#!/usr/bin/with-contenv bashio


echo "[INFO] json config is:"
cat /data/options.json 

server_ip=$(jq -r ".server" /data/options.json)
ssh_login=$(jq -r ".login" /data/options.json)
ssh_pass=$(jq -r ".password" /data/options.json)

command1=$(jq -r ".command1" /data/options.json)
name1=$(jq -r ".name1" /data/options.json)

while true
do

	echo "loop start..."

	if [ ! -z "$name1" ]; then
		command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${command1}"
		echo "[INFO] command: ${command}"
		value=$(${command})
		echo "[INFO] value: ${value}"
		json_data='{"state": "${value}" }'
		echo "[INFO] json_data: ${json_data}"
		url="http://supervisor/core/api/states/${name1}"
		echo "[INFO] url: ${url}"
		curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
	fi
	
	# http://supervisor/core/api/states/"+entity_id, headers={ "Authorization": "Bearer "+supervisor_token, "content-type": "application/json" }, data=json.dumps({ "state": value, "attributes": {"friendly_name": friendly_name, "unit_of_measurement": unit, "icon": icon } 

	echo "repeating in 60 sec..."
	sleep 60
	
done
