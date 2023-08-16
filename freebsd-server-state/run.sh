#!/usr/bin/with-contenv bashio


echo "[INFO] json config is:"
cat /data/options.json 

server_ip=$(jq -r ".server" /data/options.json)
ssh_login=$(jq -r ".login" /data/options.json)
ssh_pass=$(jq -r ".password" /data/options.json)


while true
do

	for n in 1 2 3 4 5
	do 

		remote_command=$(jq -r ".command${n}" /data/options.json)
		sensor_name=$(jq -r ".name${n}" /data/options.json)
		echo "[INFO] ${n} sensor_name: ${sensor_name} remote_command: ${remote_command}"

		if [ ! -z "$remote_command" ]; then
			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
			echo "[INFO] command: ${command}"
			value=$(${command})
			echo "[INFO] value: ${value}"
			json_data="{\"state\": \"${value}\" }"
			echo "[INFO] json_data: '${json_data}'"
			url="http://supervisor/core/api/states/sensor.${sensor_name}"
			echo "[INFO] url: ${url}"
			curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
		fi

	done

	echo "repeating in 60 sec..."
	sleep 60
	
done
