#!/usr/bin/with-contenv bashio


printf "[INFO] /data/options.json is:"
cat /data/options.json 

# server_ip=$(jq -r ".server" /data/options.json)
# ssh_login=$(jq -r ".login" /data/options.json)
# ssh_pass=$(jq -r ".password" /data/options.json)


server_count=$(jq length /data/options.json)

while true
do

	for (( s=0; s<${server_count}; s++ ))
	do 
		
		server_ip=$(jq "keys[${s}]" /data/options.json)
		printf "[INFO] server_ip: ${server_ip}\n"

		ssh_login=$(jq -r ".[${server_ip}][\"login\"]" /data/options.json)
		ssh_pass=$(jq -r ".[${server_ip}][\"password\"]" /data/options.json)
		printf "[INFO] login: ${ssh_login} password: ${ssh_pass} \n"

		sensors=$(jq -r ".[${server_ip}][\"sensors\"] | length" /data/options.json)

		for (( n=0; n<${sensors}; n++ ))
		do 

			sensor=$(jq -r ".[${server_ip}][\"sensors\"] | keys[${n}]" /data/options.json)
			command=$(jq -r ".[${server_ip}][\"sensors\"][${sensor}]" /data/options.json)
			printf "[INFO] 	sensor: ${sensor} -> command: ${command} \n"

			value=$(${command})
			printf "[INFO] 	value: ${value}\n"
			json_data="{\"state\": \"${value}\" }"
			printf "[INFO] 	json_data: '${json_data}'\n"
			url="http://supervisor/core/api/states/sensor.${sensor_name}"
			printf "[INFO] 	url: ${url}\n"
			curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
			
		done

	done

	printf "repeating in 60 sec...\n"
	sleep 60
	
done

# 			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
# 			printf "[INFO] command: ${command}\n"
