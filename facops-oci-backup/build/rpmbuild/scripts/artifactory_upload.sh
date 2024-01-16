#!/bin/bash
function upload_artifact() {
    FILE=$1
    FILE_NAME=$(basename $FILE)
    curl -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' -T $FILE "https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/generic-fa/${FILE_NAME}"  | tee -a $LOGFILE  
    if [[ $? -ne 0 ]];then
        "failed to update artifactory rpm repo ..." | tee -a $LOGFILE
        exit 1
    fi
}

upload_artifact $1
