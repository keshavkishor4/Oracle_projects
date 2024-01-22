#!/bin/bash

# Read values from .env file
while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" == "oci_user="* ]]; then
        oci_user=${line#*=}
    elif [[ "$line" == "oci_fingerprint="* ]]; then
        oci_fingerprint=${line#*=}
    elif [[ "$line" == "oci_tenancy="* ]]; then
        oci_tenancy=${line#*=}
    elif [[ "$line" == "oci_region="* ]]; then
        oci_region=${line#*=}
    elif [[ "$line" == "oci_key_file="* ]]; then
        oci_key_file=${line#*=}
    fi
done < ../creds/.env

# Check if ~/.oci directory exists, create it if not
oci_dir=~/.oci/
if [ ! -d "$oci_dir" ]; then
    mkdir "$oci_dir"
    echo "Created directory $oci_dir"
fi

# Create the config file
config_file="$oci_dir/config"
cat > "$config_file" <<EOL
[fapod_oci_config]
user=$oci_user
fingerprint=$oci_fingerprint
tenancy=$oci_tenancy
region=$oci_region
key_file=~/.oci/$oci_key_file
EOL

echo "Config file created and placed at $config_file"

sed -i 's/"//g' $config_file
oci_key_file=$(echo "$oci_key_file" | tr -d '"')

if [ ! -f "$oci_dir/$oci_key_file" ]; then
    echo "Pem file not available placing...."
    cp ../creds/$oci_key_file ${oci_dir}
fi