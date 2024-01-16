#!/bin/bash

function_update_packages() {
#  os_type=$(uname -s)
#  if [[ "${os_type}" = "Linux" ]]; then
#    os_ver=$(cat /etc/redhat-release)
#    if [[ $os_ver =~ "7" ]];then
#     os_rel="el7"
#    elif [[ $os_ver =~ "6" ]];then
#     os_rel="el6"
#    fi
#  fi
os_rel="el6"
 FILE_NAME="python3_latest_${os_rel}.zip"
 echo $FILE_NAME
 FILE="/tmp/python3_latest_${os_rel}"
 echo $FILE
 BASE_DIR="/opt/faops/spe/ocifabackup/utils/python3"

 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade pip
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade oci
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade retrying
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade requests
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade oci-cli
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade cx_Oracle
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade paramiko
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade psutil
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade ipykernel
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade progress
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade pycryptodome
# 
 cd $BASE_DIR
 echo "compressing the archive with file name $FILE_NAME ..."
 zip -q -r $FILE ${os_rel}
 
}

function_update_packages
