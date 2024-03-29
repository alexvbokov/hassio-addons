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


options_json="/data/options.json"
servers_config="/data/options-unquoted.json"


jq -r '.["servers"]' < "$options_json" > "$servers_config"
printf "[$(date)] servers:\n"
jq < "$servers_config" 


server_count=$(jq length "$servers_config")
printf "[$(date)] $server_count servers in list:\n"


while true
do

	for (( s=0; s<${server_count}; s++ ))
	do 
		
		datetime=$(date)
		
		server_ip=$(jq -r "keys[${s}]" $servers_config)
		printf "[$datetime] server_ip: ${server_ip}\n"

		ssh_login=$(jq -r ".[\"${server_ip}\"][\"login\"]" $servers_config)
#		ssh_pass=$(jq -r ".[\"${server_ip}\"][\"password\"]" $servers_config)
		printf "[$datetime] login: ${ssh_login}\n"	#  password: ${ssh_pass} 

		sensors=$(jq ".[\"${server_ip}\"][\"sensors\"] | length" $servers_config)

		for (( n=0; n<${sensors}; n++ ))
		do 
		
			datetime=$(date)
	
			sensor_name=$(jq -r ".[\"${server_ip}\"][\"sensors\"] | keys[${n}]" $servers_config)
			printf "[$datetime]    sensor: ${sensor_name}\n"
			remote_command=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"command\"]" $servers_config)
			unit=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"unit\"]" $servers_config)
			icon=$(jq -r ".[\"${server_ip}\"][\"sensors\"][\"${sensor_name}\"][\"icon\"]" $servers_config)
			printf "[$datetime]    remote_command: ${remote_command} \n"

			# 		 /usr/bin/sshpass -p ${ssh_pass} 
			command="/usr/bin/ssh -i ${KEY_PATH}/autossh_ed25519 -o StrictHostKeyChecking=no -o ConnectTimeout=10 ${ssh_login}@${server_ip} ${remote_command}"
			printf "[$datetime]    command: ${command}\n"

			value=$(${command}) || true
			
			if [ "${value}" == "" ]; then 
				value="unavailable"
			fi

			printf "[$datetime]    value: ${value}\n"
			json_data="{\"state\": \"${value}\", \"attributes\": {\"unit_of_measurement\": \"${unit}\", \"icon\": \"$icon\" } }"
			printf "[$datetime]    json_data: '${json_data}'\n"
			url="http://supervisor/core/api/states/sensor.${sensor_name}"
			printf "[$datetime]    url: ${url}\n"
			curl -s -X POST -d "${json_data}" -H "Authorization: Bearer ${SUPERVISOR_TOKEN}" -H "Content-Type: application/json" "${url}"
			
		done

	done

	printf "\nrepeating in 60 sec...\n"
	sleep 60
	
done

# 			command="/usr/bin/sshpass -p ${ssh_pass} /usr/bin/ssh -o StrictHostKeyChecking=no ${ssh_login}@${server_ip} ${remote_command}"
# 			printf "[INFO] command: ${command}\n"
