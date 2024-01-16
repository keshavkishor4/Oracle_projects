#!/bin/bash

IP_ADDRESS=$1
PREV_FQDN=$(docker exec faopscbapi grep cbdb /u01/faopscbnode/public/db/dbConfig.js| awk -F':' '{ print $2 }')
if [[ -n "$IP_ADDRESS" ]];
then
    test=$(docker exec faopscbapi grep cbdb /u01/faopscbnode/public/db/dbConfig.js| awk -F':' '{ print $2 }')
    FQDN=$(nslookup ${IP_ADDRESS} | grep -m2 name | tail -n1 | cut -d = -f 2|sed 's/\.//5')
    DOMAIN_NAME=${FQDN#*.*}
    EZ_CONNECT=${FQDN}/apexpdb.${DOMAIN_NAME}
    docker exec faopscbapi sed -i -e "s#${test}#${EZ_CONNECT}#g" /u01/faopscbnode/public/db/dbConfig.js
    docker exec faopscbapi sed -i -e "s#${test}#${ez_str}#g" /u01/faopscbnode/public/db/sysDBConfig.js
else
    echo "Please provide ip address"

fi
