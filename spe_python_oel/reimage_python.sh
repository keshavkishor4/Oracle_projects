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
LOGFILE="${LOGDIR}/spe_build_${DATE}.log"
export http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"

if [[ -d ${OUT_DIR} ]];then
    mkdir -p ${OUT_DIR}
fi

if [[ "$HOST" == *"us.oracle.com" ]];then
    CHECK_PROXY="y"
fi
# 

function upload_to_artifactory() {
    FILE=$1
    FILE_NAME=$(basename ${FILE})
    # upload to artifactory
    TOKEN=$(cat fsre-mw-deployer-token-test.json | jq -r '.access_token')
    URL="https://artifactory.oci.oraclecorp.com:443/fsre-mw-release-generic-local/${FILE_NAME}"
    unset http_proxy
    unset https_proxy
    unset no_proxy
    # export https_proxy=www-proxy.us.oracle.com:80
    # export http_proxy=www-proxy.us.oracle.com:80
    # curl -H "X-JFrog-Art-Api:$TOKEN" -X PUT $URL -T $FILE | tee -a $LOGFILE
    curl -X PUT -H "Authorization: Bearer $TOKEN" -T $FILE $URL

    # CDAAS 
    KEY="AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F"
    URL_CDAAS="https://artifactory-master.cdaas.oraclecloud.com/artifactory/generic-fa-local/${FILE_NAME}"
    curl -H "X-JFrog-Art-Api:$KEY" -T ${FILE} -X PUT $URL_CDAAS
}

function action_el6(){
 action=$1
 DOCKER_NAME="spe_python_ol6"
 DOCKER_IMAGE_NAME="${DOCKER_NAME}:v2"
 FILE_NAME="python3_latest_el6.zip"
 
 cd $PWD/el6
 
#  if [[ "$action" == "build" ]];then
#     echo "clean up docker/images ..." | tee -a $LOGFILE
#     docker-compose down | tee -a $LOGFILE
#     docker rmi ${DOCKER_IMAGE_NAME} | tee -a $LOGFILE
#     docker rmi container-registry.oracle.com/os/oraclelinux:6-slim
#     echo "building docker image" | tee -a $LOGFILE
#     docker-compose up -d | tee -a $LOGFILE
#  fi

 cd ..

 if [[ -f $OUT_DIR/${FILE_NAME} ]];then 
    rm -f $OUT_DIR/${FILE_NAME}
 fi

#  docker cp el6/update_install_python_packages.sh ${DOCKER_NAME}:/usr/local/bin/ | tee -a $LOGFILE
#  docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh | tee -a $LOGFILE
echo "Update install package running"
echo "${OUT_DIR}/${FILE_NAME}"
el6/update_install_python_packages.sh | tee -a $LOGFILE
cp /tmp/${FILE_NAME} ${OUT_DIR}/${FILE_NAME} | tee -a $LOGFILE
#  CONTAINER_ID=$(docker ps --format "{{.ID}}")
#  docker cp $CONTAINER_ID:/tmp/${FILE_NAME} /scratch/faopscb/python_zip
 echo "Uploading file into artifactory"
 upload_to_artifactory ${OUT_DIR}/${FILE_NAME} | tee -a $LOGFILE

}

function action_el7(){
 action=$1
 DOCKER_NAME="spe_python_ol7"
 DOCKER_IMAGE_NAME="${DOCKER_NAME}:v2"
 FILE_NAME="python3_latest_el7.zip"
 EL7_ARTIFACTORY_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa/python3_latest_el7.zip"
 EL7_FILE_SIZE=$(curl -sI $EL7_ARTIFACTORY_URL | grep -i Content-Length | awk '{print $2}')
 if [[ $EL7_FILE_SIZE < 200000000 ]];then
   exit 1
 fi
 cd $PWD/el7
#  if [[ "$action" == "build" ]];then
#     echo "clean up docker/images ..." | tee -a $LOGFILE
#     docker-compose down | tee -a $LOGFILE
#     docker rmi ${DOCKER_IMAGE_NAME} | tee -a $LOGFILE
#     docker rmi container-registry.oracle.com/os/oraclelinux:7-slim | tee -a $LOGFILE
#     echo "building docker image" | tee -a $LOGFILE
#     docker-compose up -d | tee -a $LOGFILE
#  fi

 cd ..
 if [[ -f $OUT_DIR/${FILE_NAME} ]];then 
    rm -f $OUT_DIR/${FILE_NAME}
 fi

 #docker cp el7/update_install_python_packages.sh ${DOCKER_NAME}:/usr/local/bin/ | tee -a $LOGFILE
 #docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh | tee -a $LOGFILE
 echo "Update install package running"
 echo "${OUT_DIR}/${FILE_NAME}"
 el7/update_install_python_packages.sh el7 | tee -a $LOGFILE
 cp /tmp/${FILE_NAME} ${OUT_DIR}/${FILE_NAME} | tee -a $LOGFILE
#  CONTAINER_ID=$(docker ps --format "{{.ID}}")
#  docker cp $CONTAINER_ID:/tmp/${FILE_NAME} /scratch/faopscb/python_zip
 echo "Uploading file into artifactory"
 upload_to_artifactory ${OUT_DIR}/${FILE_NAME} | tee -a $LOGFILE
#  upload_to_oss ${FILE_NAME}
}

function update_go() {
 DOCKER_NAME="spe_python_ol7"
 GO_FILE="go_el7.zip"
 rm -f $OUT_DIR/$GO_FILE
 docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh
 docker cp ${DOCKER_NAME}:/tmp/${GO_FILE} ${OUT_DIR}
#  upload_to_oss $GO_FILE
}


action=$1
if [[ -z "$action" ]];then
    echo "no argument passed, exitting, accepted args: build_el6,build_el7,update_el7,update_el6"
    exit 1
elif [[ "${action}" == "build_el6" ]];then
    action_el6 build
elif [[ "${action}" == "update_el6" ]];then
    action_el6
elif [[ "${action}" == "build_el7" ]];then
    action_el7 build
elif [[ "${action}" == "update_el7" ]];then
    action_el7
else
    echo "no argument passed, exitting, accepted args: build_el6,build_el7,update_el7,update_el6"
    exit 1
fi

