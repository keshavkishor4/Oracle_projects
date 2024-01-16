#!/bin/bash

# Your curl command here
curl_cmd="curl -H 'Authorization: Bearer Oracle' -L -s -o /dev/null -w '%{http_code}' http://169.254.169.254/opc/v1/identity/cert.pem"

# Execute the curl command and capture the output in a variable
curl_output=$(eval $curl_cmd)

# Extract only the HTTP status code from the output using awk
http_status=$(echo "$curl_output" | awk '{print $NF}')

# Check if the HTTP status code is not in the 2xx range (successful)
if [[ "$http_status" != 2* ]]; then
    echo "Curl command failed. HTTP Status: $http_status"
else
    echo "Curl command successful. HTTP Status: $http_status"
fi
