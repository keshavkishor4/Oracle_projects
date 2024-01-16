#!/bin/bash

function_update_packages() {
 os_type=$(uname -s)
 if [[ "${os_type}" = "Linux" ]]; then
   os_ver=$(cat /etc/redhat-release)
   if [[ $os_ver =~ "7" ]];then
    os_rel="el7"
   elif [[ $os_ver =~ "6" ]];then
    os_rel="el6"
   fi
 fi
 FILE_NAME="python3_${os_rel}.zip"
 FILE="/tmp/python3_${os_rel}"
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
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade oracledb
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade bs4
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade oracledb
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade python-dotenv

 cd /usr/local/python3
 zip -r $FILE ${os_rel} openssl

 test=$(curl -k --connect-timeout 5 $url > /dev/null 2>&1)
 oci_region=$(curl -sL http://169.254.169.254/opc/v1/instance/canonicalRegionName)
 if [[ $? -eq 0 ]];then
  echo "-$oci_region" > /etc/yum/vars/ociregion
  #yum repolist
 else
  :
 fi
 url="https://catalogdb-dev-oci.falcm.ocs.oc-test.com"
 test=$(curl -k --connect-timeout 5 $url > /dev/null 2>&1)
 if [ $? -ne 0 ];then
        echo "Unable to connect to $url "
        exit 1
 else
    echo "Uploading the zip file"
        out=$(curl -k --connect-timeout 30 --retry 5 --retry-delay 5 -w "%{http_code}" -H "Authorization:Basic ZmFvcHNjYjpGQTBuMENJMjAyMCM=" -F "file_name=@${FILE}.zip" "https://catalogdb-dev-oci.falcm.ocs.oc-test.com/ords/ocibakrev/upload/?file=${FILE_NAME}")
    echo $out
 fi
}

function_update_packages
