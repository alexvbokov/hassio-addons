#!/usr/bin/with-contenv bashio


options_json="/data/options.json"
servers_config="/data/options-unquoted.json"


jq -r '.["servers"]' < "$options_json" > "$servers_config"
printf "[INFO] servers:\n"
jq < "$servers_config" 


server_count=$(jq length "$servers_config")
printf "[INFO] $server_count servers in list:\n"


while true
do

	for (( s=0; s<${server_count}; s++ ))
	do 
		
		server_ip=$(jq -r "keys[${s}]" $servers_config)
		printf "[INFO] server_ip: ${server_ip}\n"

		ssh_login=$(jq -r ".[\"${server_ip}\"][\"login\"]" $servers_config)
		ssh_pass=$(jq -r ".[\"${server_ip}\"][\"password\"]" $servers_config)
		printf "[INFO] login: ${ssh_login} password: ${ssh_pass} \n"

		sensors=$(jq ".[\"${server_ip}\"][\"sensors\"] | length" $servers_config)

		for (( n=0; n<${sensors}; n++ ))
		do 

			sensor_name=$(jq -r ".[\"${server_ip}\"][\"sensors\"] | keys[${n}]" $servers_config)
			printf "[INFO]    sensor: ${sensor_name}\n"
			remote_command=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"command\"]" $servers_config)
			unit=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"unit\"]" $servers_config)
			icon=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"icon\"]" $servers_config)
			printf "[INFO]    remote_command: ${remote_command} \n"

			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
			printf "[INFO]    command: ${command}\n"

			value=$(${command}) || true
			printf "[INFO]    value: ${value}\n"
			json_data="{\"state\": \"${value}\", \"attributes\": {\"unit_of_measurement\": \"${unit}\", \"icon\": \"$icon\" } }"
			printf "[INFO]    json_data: '${json_data}'\n"
			url="http://supervisor/core/api/states/sensor.${sensor_name}"
			printf "[INFO]    url: ${url}\n"
			curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
			
		done

	done

	printf "\nrepeating in 60 sec...\n"
	sleep 60
	
done

# 			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
# 			printf "[INFO] command: ${command}\n"
