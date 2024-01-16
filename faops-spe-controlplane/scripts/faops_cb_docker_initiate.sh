#!/bin/bash -x
faops_docker_repo=$1
faops_docker_release_version=$2
faops_api_external_port=$3
faops_api_internal_port=$4
faops_apex_external_port=$5
faops_apex_internal_port=$6

# faops_docker_repo="iad.ocir.io/saasfaprod1/faops/faopscbapi"
# faops_docker_release_version="v1_01202020"
# faops_api_external_port=8023
# faops_api_internal_port=8023
# faops_apex_external_port=8080
# faops_apex_internal_port=8080

stamp=`date -u '+%Y%m%d%H%M%S'`

# Fetch hostname of the VM so that it may be passed down to the Docker Container. This is picked up in the Log4j2
# configs and is added to the json logging output.
VM_HOSTNAME_ENV_VAR="VM_HOSTNAME=`hostname`"

DOCKER_DEFAULT_USER_ID=1000
DOCKER_DEFAULT_GROUP_ID=1000


CONTAINER_LOGS_DIR=/u01/faopscbnode/logs
HOST_LOGS_DIR=~/volumes/faopscbmt/logs

# Since we are doing read/write to this directory, lets ensure it exists and has global permissions
# A more correct way would be to use docker volumes instead of mounts, however, the contents of the volume require the
# use of a container in order to view the files. So we instead use bind mounts to the host VM.
mkdir -p ${HOST_LOGS_DIR}
chown -R $DOCKER_DEFAULT_USER_ID:$DOCKER_DEFAULT_GROUP_ID ${HOST_LOGS_DIR}
LOGGING_PARAMS=" -e ${VM_HOSTNAME_ENV_VAR} -v ${HOST_LOGS_DIR}:${CONTAINER_LOGS_DIR}"

# 
backup_dir="/u01/faops/faopscb/backup"
files_dir="/u01/faops/faopscb/public/data/"
mkdir -p ${backup_dir}
mkdir -p ${files_dir}/configs
mkdir -p ${files_dir}/uploads/files
mkdir -p ${files_dir}/uploads/logs

EXTRA_MOUNTS=" -v ${backup_dir}:/u01/backup/:z -v ${data_dir}:/u01/faopscbnode/public/data/:z"

# Check if the container with the appropriate name has been made. If so, stop the container if it hasn't been already
# and remove the container so that we can run a potentially new image with potentially new flags.
cleanup_container()
{
  container=$1
  running=`sudo docker ps -a -q -f name=${container} | wc -l`
  echo "########## Docker running ${container} ##########"
  if [ "$running" == "1" ]; then
    echo "########## Stopping Container ${container} ##########"
    sudo docker stop ${container}
    sudo docker rm ${container}
  fi
}


# Handle the setup of the Docker Image, running the requisite config management commands on the mounted volume,
# and then finally running the image.
startFaopsCB()
{
  managerName=$1

  docker pull ${faops_docker_repo}:${faops_docker_release_version} 
  docker run --net=host --privileged=true ${EXTRA_MOUNTS} ${LOGGING_PARAMS} --restart unless-stopped -it --name ${managerName} -d ${faops_docker_repo}:${faops_docker_release_version}
  #docker run --privileged=true ${LOGGING_PARAMS} --restart unless-stopped -it --name ${managerName} -p ${faops_api_external_port}:${faops_api_internal_port} -p ${faops_apex_external_port}:${faops_apex_internal_port} -d ${faops_docker_repo}:${faops_docker_release_version}
}

faopscbapi()
{
  echo '################### FAOPS CB DB specific install begins #####################'
  touch /tmp/userdata.`date +%s`.start

  echo '########## Deploy docker container ##############'
  cleanup_container faopscbapi

  startFaopsCB faopscbapi

  echo "$stamp : $faops_docker_repo:$faops_docker_release_version" >> ~opc/deployments.txt
  touch /tmp/userdata.`date +%s`.finish
  echo '################### FAOPS CB DB specific install ends #######################'
}

# Ensure that this is running as root
if [ "$EUID" -ne 0 ]
then
  echo "Please run as root"
  exit 1
fi

#Run the container
faopscbapi