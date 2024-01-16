#!/bin/bash
#start docker
# docker run --name spe-el7 -d spe-el7:v1_180820
# docker run --name spe-el6 -d spe-el6:v1_180820
# export https_proxy=http://www-proxy.us.oracle.com:80
# export http_proxy=http://www-proxy.us.oracle.com:80

OUT_DIR="/Users/zakahmed/workspace/backups/uno/den02ofs/backup/spe_python_ol7"

function upload_to_oss() {
    FILE=$1
    oci --profile PREPRODSTAGE-IAD1 os object delete -bn FAOPS --object-name $FILE --force
    oci --profile PREPRODSTAGE-IAD1 os object put -bn FAOPS --file ${OUT_DIR}/$FILE --verify-checksum --force
    oci --profile PREPRODSTAGE-IAD1 os object list -bn FAOPS -ns p1-saasfapreprod1 --prefix $FILE
}

function update_el6(){
 DOCKER_NAME="spe_python_ol6"
 FILE_NAME="python3_el6.zip"

 rm -f $OUT_DIR/${FILE_NAME}
 docker cp el6/update_install_python_packages.sh ${DOCKER_NAME}:/usr/local/bin/
 docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh
 docker cp ${DOCKER_NAME}:/tmp/${FILE_NAME} ${OUT_DIR}
 upload_to_oss ${FILE_NAME}

}

function update_el7(){
 DOCKER_NAME="spe_python_ol7"
 FILE_NAME="python39_el7.zip"
 
 rm -f $OUT_DIR/${FILE_NAME}
 docker cp el7/update_install_python_packages.sh ${DOCKER_NAME}:/usr/local/bin/
 docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh
 docker cp ${DOCKER_NAME}:/tmp/${FILE_NAME} ${OUT_DIR}
#  upload_to_oss ${FILE_NAME}
}

function update_go() {
 DOCKER_NAME="spe_python_ol7"
 GO_FILE="go_el7.zip"
 rm -f $OUT_DIR/$GO_FILE
 docker exec ${DOCKER_NAME} /usr/local/bin/update_install_python_packages.sh
 docker cp ${DOCKER_NAME}:/tmp/${GO_FILE} ${OUT_DIR}
 upload_to_oss $GO_FILE
}

echo "-----------updating el6------------"
update_el6
echo "-----------updating el7------------"
# update_el7
echo "-----------updating go------------"
# update_go
