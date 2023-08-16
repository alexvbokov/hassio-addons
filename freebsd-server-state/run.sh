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
	fi

	echo "repeating in 60 sec..."
	sleep 60
	
done
