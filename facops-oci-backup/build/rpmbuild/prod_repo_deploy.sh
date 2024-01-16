#!/bin/bash
#
#   FAOCI Backup rpm build script
#
#   Zakki Ahmed - 01-08-2021 - Initial Script to support ubuntu docker
#   Zakki Ahmed - 07-08-2021 - Update to add OEL
#   Zakki Ahmed - 17/08/2021 - Updates to rpm repo


RPMBUILD_DIR="build/rpmbuild"
RPM_REPO_DIR="/repo/fa-oci-backup"
PROD_RPM_REPO_DIR="/repo/fa-oci-backup-prod"
CDAAS_REPO_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/rpm-fa-backup-dev"
REPO_URL="https://artifactory.oci.oraclecorp.com:443/fsre-mw-dev-yum-local/"
PROD_REPO_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/rpm-fa-backup"
ARTIFACTORY_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/generic-fa/"
unset http_proxy
unset https_proxy
unset HTTPS_PROXY
unset no_proxy
unset HTTP_PROXY
HOST=$(hostname -f)
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
# OUT_DIR="/Users/zakahmed/workspace/backups/uno/den02ofs/backup/spe_python_ol7"
OUT_DIR="${PWD}/out"
CHECK_PROXY="n"
LOGDIR="/tmp"
DATE=$(date +"%Y-%b-%d-%H-%M-%S" )
LOGFILE="${LOGDIR}/rpm_build_${DATE}.log"

function download_artifacts() {
    mkdir -p $RPMBUILD_DIR/artifacts
    # jq
    curl -o $RPMBUILD_DIR/artifacts/jq -O https://artifacthub-iad.oci.oraclecorp.com/facops-backup/jq | tee -a $LOGFILE
    # decrypt
    curl -o $RPMBUILD_DIR/artifacts/decrypt -O https://artifacthub-iad.oci.oraclecorp.com/facops-backup/decrypt | tee -a $LOGFILE
    # opc_linux64.zip
    #export https_proxy=www-proxy.us.oracle.com:80
    #export http_proxy=www-proxy.us.oracle.com:80
    curl -o $RPMBUILD_DIR/artifacts/opc_linux64.zip -O https://artifactory.oci.oraclecorp.com:443/fsre-mw-release-generic-local/opc_linux64.zip | tee -a $LOGFILE
    #
    unzip -o $RPMBUILD_DIR/artifacts/opc_linux64.zip -d $RPMBUILD_DIR/artifacts | tee -a $LOGFILE
    #
    chmod 755 $RPMBUILD_DIR/artifacts/*
    unset https_proxy
    unset http_proxy
    # upload artifacts
    # REPO_URL=https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/generic-fa
    # curl -s -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' $REPO_URL/libopc.so -T ./libopc.so
}

function upload_artifact() {
    FILE=$1
    FILE_NAME=$(basename $FILE)
    TOKEN=$(cat fsre-mw-deployer-token-test.json | jq -r '.access_token')
    curl -X PUT -H "Authorization: Bearer $TOKEN" -T $FILE "https://artifactory.oci.oraclecorp.com:443/fsre-mw-release-generic-local/${FILE_NAME}" | tee -a $LOGFILE
    #curl -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' -T $FILE "https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/generic-fa/${FILE_NAME}"  | tee -a $LOGFILE
    if [[ $? -ne 0 ]];then
        "failed to update artifactory rpm repo ..." | tee -a $LOGFILE
        exit 1
    fi
}
function rpm_deploy() {
    #export https_proxy=www-proxy.us.oracle.com:80
    #export http_proxy=www-proxy.us.oracle.com:80
    if [[ -d ${RPM_REPO_DIR}/repodata ]];then
        createrepo --update $RPM_REPO_DIR
    else
        createrepo $RPM_REPO_DIR
    fi
    TOKEN=$(cat fsre-mw-deployer-token-test.json | jq -r '.access_token')
    find $RPM_REPO_DIR -type f -exec curl -s -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' -X PUT ${CDAAS_REPO_URL}/{} -T {} \; | tee -a $LOGFILE
    find $RPM_REPO_DIR -type f -exec curl -s -H "Authorization: Bearer $TOKEN" -X PUT ${REPO_URL}/{} -T {} \; | tee -a $LOGFILE
    if [[ $? -ne 0 ]];then
        "failed to update artifactory rpm repo ..." | tee -a $LOGFILE
        exit 1
    fi
}


# function prod_deploy() {
#     echo "*************************---> PROD DEPLoY <----------- ***********************"
#     mkdir -p $PROD_RPM_REPO_DIR/repo/fa-oci-backup
#     cd $PROD_RPM_REPO_DIR/
#     if [[ -d $RPM_REPO_DIR ]];then
#         # DB
#         PROD_DB_RPM=$(curl -s https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/generic-fa/faops-backup-ver.json | jq  '.exa | to_entries[] |select(.value | contains("fa-spe"))'|jq -r '.value')
#         for DBRPM in $PROD_DB_RPM;do
#             if [[ -f ${RPM_REPO_DIR}/${DBRPM} ]];then
#                 cp ${RPM_REPO_DIR}/${DBRPM} ${PROD_RPM_REPO_DIR}/repo/fa-oci-backup
#             fi
#         done
#         #
#         # MT
#         PROD_MT_RPM=$(curl -s https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/generic-fa/faops-backup-ver.json | jq  '.mt | to_entries[] |select(.value | contains("fa-spe"))'|jq -r '.value')
#         for MTRPM in $PROD_MT_RPM;do
#             if [[ -f ${RPM_REPO_DIR}/${MTRPM} ]];then
#                 cp ${RPM_REPO_DIR}/${MTRPM} ${PROD_RPM_REPO_DIR}/repo/fa-oci-backup
#             fi
#         done
#         # create repo and upload
#         if [[ -d ${PROD_RPM_REPO_DIR}/repodata ]];then
#             createrepo --update $PROD_RPM_REPO_DIR/repo/fa-oci-backup
#         else
#             createrepo $PROD_RPM_REPO_DIR/repo/fa-oci-backup
#         fi
#         # find repo/fa-oci-backup -type f -exec curl -s -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' -X PUT ${PROD_REPO_URL}/{} -T {} \; | tee -a $LOGFILE
#         KEY="AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F"
#         # URL_CDAAS="https://artifactory-master.cdaas.oraclecloud.com/artifactory/generic-fa-local/${FILE_NAME}"
#         find repo/fa-oci-backup -type f -exec curl -s -H "X-JFrog-Art-Api:${KEY}"  -X PUT ${PROD_REPO_URL}/{} -T {} \; | tee -a $LOGFILE
#         if [[ $? -ne 0 ]];then
#             "failed to update artifactory rpm prod repo ..." | tee -a $LOGFILE
#             exit 1
#         fi

#     fi
# }

function build_rpm() {
    version=$1
    iteration=$2
    DB_RPM="fa-spe-oci-backup-db"
    DBAAS_EM_RPM="fa-spe-oci-backup-dbaas-em"
    DB_RPM_FILE="fa-spe-oci-backup-db-${version}-${iteration}.x86_64.rpm"
    MT_RPM="fa-spe-oci-backup-mt"
    MT_RPM_FILE="fa-spe-oci-backup-mt-${version}-${iteration}.x86_64.rpm"
    DBAAS_EM_RPM_FILE="fa-spe-oci-backup-dbaas-em-${version}-${iteration}.x86_64.rpm"
    # download artifacts
    download_artifacts
    #
    cd $RPMBUILD_DIR
    if [[ -f $DB_RPM_FILE ]];then
        rm -f $DB_RPM_FILE
    elif [[ -f $MT_RPM_FILE ]];then
        rm -f $MT_RPM_FILE
    fi

    SCL_RUN=""
    if [[ -f /usr/bin/scl ]];then
        RUBY_VER=$(rpm -qa | grep -i "\-ruby-"  | awk -F- '{print $1"-"$2}' | head -1)
        SCL_RUN="scl enable $RUBY_VER -- "
    else
        unset SCL_RUN
    fi
    # DB RPM
    echo "************ START - building db rpm ***************" | tee -a $LOGFILE
    $SCL_RUN fpm --verbose -s dir -t rpm -n $DB_RPM -v $version --iteration $iteration \
    --replaces fa-peo-oci-backup \
    --inputs inputs_db.txt \
    --exclude-file excludes.txt \
    --rpm-compression-level 9 \
    --license "Property of Oracle Corp." --vendor "SaaS Performance Engineering" \
    --rpm-summary "SPE OCI backup and restore tool" -m "zakki.ahmed@oracle.com" \
    --url "https://confluence.oraclecorp.com/confluence/display/SPTA/AREA%3A+FA+OCI+BACKUP" \
    --before-install ../../src/rpm_preinstall.sh \
    --after-install ../../src/post_install_v2.sh \
    --before-upgrade ../../src/rpm_preinstall.sh \
    --after-upgrade ../../src/post_install_v2.sh \
    --before-remove ../../src/rpm_beforeremove.sh \
    --after-remove ../../src/rpm_uninstall.sh  | tee -a $LOGFILE

    if [[ $? -ne 0 ]];then
        "fpm build faced error ..." | tee -a $LOGFILE
        exit 1
    fi
    echo "************ END - building db rpm ***************" | tee -a $LOGFILE
    #MT RPM
    echo "************ START - building mt rpm ***************" | tee -a $LOGFILE
    $SCL_RUN fpm --verbose -s dir -t rpm -n $MT_RPM -v $version --iteration $iteration \
    --replaces fa-peo-oci-backup \
    --inputs inputs_mt.txt \
    --exclude-file excludes.txt \
    --rpm-compression-level 9 \
    --license "Property of Oracle Corp." --vendor "SaaS Performance Engineering" \
    --rpm-summary "SPE OCI backup and restore tool" -m "zakki.ahmed@oracle.com" \
    --url "https://confluence.oraclecorp.com/confluence/display/SPTA/AREA%3A+FA+OCI+BACKUP" \
    --before-install ../../src/rpm_preinstall.sh \
    --after-install ../../src/post_install_v2.sh \
    --before-upgrade ../../src/rpm_preinstall.sh \
    --after-upgrade ../../src/post_install_v2.sh \
    --before-remove ../../src/rpm_beforeremove.sh \
    --after-remove ../../src/rpm_uninstall.sh | tee -a $LOGFILE

    if [[ $? -ne 0 ]];then
        "fpm build faced error ..." | tee -a $LOGFILE
        exit 1
    fi
    echo "************ END - building mt rpm ***************" | tee -a $LOGFILE
    echo "************ START - building DBAAS and EM rpm ***************" | tee -a $LOGFILE
    $SCL_RUN fpm --verbose -s dir -t rpm -n $DBAAS_EM_RPM -v $version --iteration $iteration \
    --replaces fa-peo-oci-backup \
    --inputs inputs_db.txt \
    --exclude-file excludes.txt \
    --rpm-compression-level 9 \
    --license "Property of Oracle Corp." --vendor "SaaS Performance Engineering" \
    --rpm-summary "SPE OCI backup and restore tool" -m "zakki.ahmed@oracle.com" \
    --url "https://confluence.oraclecorp.com/confluence/display/SPTA/AREA%3A+FA+OCI+BACKUP" \
    --before-install ../../src/rpm_preinstall.sh \
    --after-install ../../src/post_install_v2.sh \
    --before-upgrade ../../src/rpm_preinstall.sh \
    --after-upgrade ../../src/post_install_v2.sh \
    --before-remove ../../src/rpm_beforeremove.sh \
    --after-remove ../../src/rpm_uninstall.sh  | tee -a $LOGFILE

    if [[ $? -ne 0 ]];then
        "fpm build faced error ..." | tee -a $LOGFILE
        exit 1
    fi
    echo "************ END - building DBAAS and EM rpm ***************" | tee -a $LOGFILE
    #
    mkdir -p $RPM_REPO_DIR
    cp $DB_RPM_FILE $RPM_REPO_DIR
    cp $MT_RPM_FILE $RPM_REPO_DIR
    cp $DBAAS_EM_RPM_FILE $RPM_REPO_DIR

    # rpm deploy
    rpm_deploy

    # upload artifacts
    upload_artifact "../../src/config/common/.artifacts_db.txt"  | tee -a $LOGFILE
    upload_artifact "../../src/config/common/.artifacts_mt.txt"  | tee -a $LOGFILE
    upload_artifact "../../src/config/common/faops-backup-ver.json" | tee -a $LOGFILE
    #
    # prod_deploy
}
#


# build_rpm 2.0.0.0.210515.1 7
ver=$1
rev=$2
build_rpm $ver $rev
# prod_deploy