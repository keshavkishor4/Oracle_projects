#!/bin/bash
#start docker
# docker run --name spe-el7 -d spe-el7:v1_180820
# docker run --name spe-el6 -d spe-el6:v1_180820
# export https_proxy=http://www-proxy.us.oracle.com:80
# export http_proxy=http://www-proxy.us.oracle.com:80
HOST=$(hostname -f)
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# OUT_DIR="/Users/zakahmed/workspace/backups/uno/den02ofs/backup/spe_python_ol7"
OUT_DIR="${PWD}/out"
CHECK_PROXY="n"
LOGDIR="/tmp"
DATE=$(date +"%Y-%b-%d-%H-%M-%S" )
os_rel="el6"
LOGFILE="${LOGDIR}/spe_build_tests_${os_rel}_${DATE}.log"

export https_proxy=www-proxy.us.oracle.com:80
export http_proxy=www-proxy.us.oracle.com:80

function test_el7() {
    FILE_NAME="python39_el7.zip"
    # 
    URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa/${FILE_NAME}" 
    echo "testing local $FILE_NAME ..." | tee -a $LOGFILE
    OUTPUT=$(curl -s -o /tmp/${FILE_NAME} -O ${URL} &&  unzip -q -t /tmp/${FILE_NAME} && rm -f /tmp/${FILE_NAME} | tee -a $LOGFILE)
    if [[ "$OUTPUT" == *"No errors detected"* ]];then
        echo "test_el6 passed for $FILE_NAME ..."
    else
        echo "test_el6 failed for $FILE_NAME ..."
        exit 1
    fi
}

function test_el6() {
    FILE_NAME="python39_el6.zip"
    # 
    URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa/${FILE_NAME}" 
    echo "testing remote $URL ..." | tee -a $LOGFILE
    OUTPUT=$(curl -s -o /tmp/${FILE_NAME} -O ${URL} &&  unzip -q -t /tmp/${FILE_NAME} && rm -f /tmp/${FILE_NAME} | tee -a $LOGFILE)
    if [[ "$OUTPUT" == *"No errors detected"* ]];then
        echo "test_el6 passed for $FILE_NAME ..."
    else
        echo "test_el6 failed for $FILE_NAME ..."
        exit 1
    fi

}

action=$1
if [[ -z $action ]];then 
    echo "wrong argument test_el6 or test_el7" | tee -a $LOGFILE
elif [[ "$action" == "test_el6" ]];then
    test_el6
elif [[ "$action" == "test_el7" ]];then
    test_el7
fi