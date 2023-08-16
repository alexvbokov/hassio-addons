#!/usr/bin/with-contenv bashio


printf "[INFO] json config is:"
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
		printf "\n[INFO] [=${n}=] sensor_name: ${sensor_name} remote_command: ${remote_command}\n"

		if [ ! -z "$remote_command" ]; then
			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
			printf "[INFO] command: ${command}\n"
			value=$(${command})
			printf "[INFO] value: ${value}\n"
			json_data="{\"state\": \"${value}\" }"
			printf "[INFO] json_data: '${json_data}'\n"
			url="http://supervisor/core/api/states/sensor.${sensor_name}"
			printf "[INFO] url: ${url}\n"
			curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
		fi

	done

	printf "repeating in 60 sec...\n"
	sleep 60
	
done
