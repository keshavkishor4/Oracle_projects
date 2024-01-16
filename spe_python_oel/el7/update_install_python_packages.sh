#!/bin/bash

export http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"

function update_go_packages() {
  mkdir -p /opt/faops/spe/ocifabackup/utils/develop
  export GOROOT=/opt/faops/spe/ocifabackup/utils/go
  export GOBIN=$GOROOT/bin
  export GOPATH=/opt/faops/spe/ocifabackup/utils/develop
  export PATH=$GOBIN:$PATH
  $GPBIN/go get -u github.com/godror/godror
  $GPBIN/go get -u github.com/oracle/oci-go-sdk
  $GPBIN/go get github.com/pterm/pterm
  $GPBIN/go get -u github.com/mattn/go-sqlite3
  $GPBIN/go get -u go.uber.org/zap
}

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
 FILE_NAME="python3_latest_${os_rel}.zip"
 FILE="/tmp/python3_latest_${os_rel}"
 BASE_DIR="/opt/faops/spe/ocifabackup/utils/python3"
 GO_DIR="/opt/faops/spe/ocifabackup/utils/"
 GO_FILE="/tmp/go_${os_rel}"
 
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
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade beautifulsoup4
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade dnspython
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade configparser
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade jproperties
 ${BASE_DIR}/${os_rel}/bin/pip3 install --upgrade Jinja2
 
# PYTHON_VER=$(python --version)
#  if [[ "$PYTHON_VER" =~ "3" ]];then
#   echo "Python version is $PYTHON_VER"
#   :
#  else 
#   exit 1
#  fi 

 cd $BASE_DIR
 echo "compressing the archive with file name $FILE_NAME ..."
 zip -q -r $FILE ${os_rel} openssl
#  Go Actions
#  cd $GO_DIR
#  update_go_packages
#  zip -r $GO_FILE go/ develop/

#  test=$(curl -k --connect-timeout 5 $url > /dev/null 2>&1)
#  oci_region=$(curl -sL http://169.254.169.254/opc/v1/instance/canonicalRegionName)
#  if [[ $? -eq 0 ]];then
#   echo "-$oci_region" > /etc/yum/vars/ociregion
#   #yum repolist
#  else
#   :
#  fi
#  url="https://catalogdb-dev-oci.falcm.ocs.oc-test.com"
#  test=$(curl -k --connect-timeout 5 $url > /dev/null 2>&1)
#  if [ $? -ne 0 ];then
#         echo "Unable to connect to $url "
#         exit 1
#  else
#     echo "Uploading the zip file"
          # out=""
#     echo $out
#  fi
}

function_update_packages
