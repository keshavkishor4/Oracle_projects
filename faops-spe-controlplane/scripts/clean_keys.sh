#!/bin/bash

# This script must be executed as root, it does some house cleaning before executing merge_config_plan.sh

# we ship keys OOTB now, so we don't want to delete them...
#for file in "/u01/oracle/configs/.falcm/cfg/.prod-priv.key" "/u01/oracle/configs/.falcm/cfg/prod-pub.key"
#do
#  if [ -f "$file" ]
#  then
#	  echo "$file found, Deleting."
#	  rm -f $file
#  fi
#done

chown oracle:oracle /u01/oracle/configs/.falcm/cfg/prod-cfg.json