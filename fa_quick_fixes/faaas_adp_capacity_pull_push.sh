#!/bin/bash
source_bucket="ssdi-faoci-bucket" #Horizon bucket to download vpn file
source_ns="bmcdw" #Horizon bucket namespace

target_bucket="fsremw-artifacts" #local bucket to push vpn data
target_ns="axxyy35wuycx" #local namespace
dt_time=$(date --date="1 days ago" +%Y%m%d)

download(){
    # data=`oci os object list -bn $source_bucket -ns $source_ns --auth instance_principal --prefix faaas_compute_capacity  --region us-ashburn-1 | jq -r '.data[] .name'`
    FILE_NAME="faaas_adp_capacity_limits_${dt_time}.json"
    download_response=`oci os object get -bn ssdi-faoci-bucket -ns bmcdw --region us-ashburn-1 --file $FILE_NAME --name $FILE_NAME --auth instance_principal`
    if [[ $? -ne 0 ]];then
        echo "below error occured in file download from bucket";
        echo $download_response;
    else
        echo "$FILE_NAME file downloaded successfully"
        echo  $download_response
    fi
    #gzip --force -d $FILE_NAME
    #FILE_PUT=`echo $FILE_NAME | sed -e s/.gz//g`
    echo "File to be uploaded to dev bucket ==> $FILE_NAME"
    upload
}

upload(){
    upload_response=`oci os object put -ns $target_ns -bn $target_bucket --file $FILE_NAME --force --auth instance_principal`
    if [[ $? -ne 0 ]];then
        echo "Error occured in file upload to bucket";
        echo $upload_response;
    else
        echo "file uploaded successfully"
        echo  $upload_response
        rm -rf $FILE_NAME
    fi
}

download