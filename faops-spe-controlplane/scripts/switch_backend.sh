#!/usr/bin/env bash

if [ -z "$1" ]
then
  back_end_config_file="back_end_config.tfvars"
else
  back_end_config_file="$1"
fi

terraform init --backend-config="${back_end_config_file}"
