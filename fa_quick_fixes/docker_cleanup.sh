#!/bin/bash

faops_docker_repo="iad.ocir.io/saasfaprod1/faops/faopscbapi"
faops_docker_release_version="v1_07172020"
faops_api_external_port=8023
faops_api_internal_port=8023
faops_apex_external_port=8080
faops_apex_internal_port=8080
VM_HOSTNAME_ENV_VAR="VM_HOSTNAME=`hostname`"
DOCKER_DEFAULT_USER_ID=1000
DOCKER_DEFAULT_GROUP_ID=1000
CONTAINER_LOGS_DIR=/u01/faopscbnode/logs
HOST_LOGS_DIR=~/volumes/faopscbmt/logs

LOGGING_PARAMS=" -e ${VM_HOSTNAME_ENV_VAR} -v ${HOST_LOGS_DIR}:${CONTAINER_LOGS_DIR}"

# Function to stop and remove a Docker container
stop_and_remove_docker_container() {
    container_name="faopscbapi"
    echo "Stopping and removing Docker container: $container_name"
    docker stop "$container_name"
    docker rm "$container_name"
}

# Function to prune unused Docker networks
prune_docker_networks() {
    echo "Pruning unused Docker networks"
    docker network prune -f
}

# Function to delete old and stale Docker images
delete_stale_docker_images() {
    echo "Deleting old and stale Docker images"
    docker rm -f $(docker ps -a -q)
}

# Function to remove a Docker image
remove_docker_image() {
    image_name="$1"
    echo "Removing Docker image: $image_name"
    docker image rm "$image_name"
}

# # Restart Docker service
# restart_docker_service() {
#     echo "Restarting Docker service"
#     service docker restart
# }

# Main script starts here

# Stop and remove the specified Docker container
container=faopscbapi
stop_and_remove_docker_container "$container"

# Prune unused Docker networks
prune_docker_networks

# Delete old and stale Docker images
delete_stale_docker_images

# Remove the specified Docker image
image=iad.ocir.io/saasfaprod1/faops/faopscbapi:v1_07172020
remove_docker_image "$image"

# # Restart Docker service
# restart_docker_service

