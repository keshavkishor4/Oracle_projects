#!/bin/bash
RPMBUILD_DIR="build/rpmbuild"
RPM_REPO_DIR="/repo/fa-oci-backup"
PROD_RPM_REPO_DIR="/repo/fa-oci-backup-prod"
REPO_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/rpm-fa-backup-dev"
PROD_REPO_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/rpm-fa-backup"
ARTIFACTORY_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/generic-fa/"
HOST=$(hostname -f)
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
BASE_DIR=".."
RPMBUILD_DIR="${BASE_DIR}/build/rpmbuild/build/rpmbuild/"
ARTIFACT_DIR_LOC="${BASE_DIR}/build/rpmbuild/build/rpmbuild/artifacts"
CHECK_PROXY="n"
LOGDIR="/tmp"
DATE=$(date +"%Y-%b-%d-%H-%M-%S" )
LOGFILE="${LOGDIR}/rpm_tests_${DATE}.log"

function test_rpm() {
    version=$1
    iteration=$2
    DB_RPM="fa-spe-oci-backup-db"
    DB_RPM_FILE="fa-spe-oci-backup-db-${version}-${iteration}.x86_64.rpm"
    MT_RPM="fa-spe-oci-backup-mt"
    MT_RPM_FILE="fa-spe-oci-backup-mt-${version}-${iteration}.x86_64.rpm"
    
    if [[ -f ${RPMBUILD_DIR}/${DB_RPM_FILE} ]];then
        echo "Testing ${RPMBUILD_DIR}/${DB_RPM_FILE} rpm " | tee -a $LOGFILE
        rpm -ivvvh --test $DB_RPM_FILE | tee -a $LOGFILE
    elif [[ -f ${RPMBUILD_DIR}/${MT_RPM_FILE} ]];then
        echo "Testing ${RPMBUILD_DIR}/${MT_RPM_FILE} rpm " | tee -a $LOGFILE
        rpm -ivvvh --test $MT_RPM_FILE | tee -a $LOGFILE
    else 
        echo "No rpm $DB_RPM_FILE or  $MT_RPM_FILE found " | tee -a $LOGFILE
    fi

}

function test_artifacts() {
    # test JQ
    echo "Testing JQ version " | tee -a $LOGFILE
    $ARTIFACT_DIR_LOC/jq --version
    # test opc_linux64.zip
    unzip -t $ARTIFACT_DIR_LOC/opc_linux64.zip | tee -a $LOGFILE
}

ver=$1
rev=$2
test_rpm $ver $rev
test_artifacts