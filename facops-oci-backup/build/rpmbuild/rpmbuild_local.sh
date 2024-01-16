#!/bin/bash
# 
#   FAOCI Backup rpm build script
#   
#   Zakki Ahmed - 01-08-2021 - Initial Script to support ubuntu docker
#   Zakki Ahmed - 07-08-2021 - Update to add OEL
#   Zakki Ahmed - 17/08/2021 - Updates to rpm repo


RPMBUILD_DIR="build/rpmbuild"
RPM_REPO_DIR="/repo/fa-oci-backup"
REPO_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/rpm-fa-backup-dev"
unset http_proxy
unset https_proxy

function download_artifacts() {
    mkdir -p $RPMBUILD_DIR/artifacts
    # jq
    curl -o $RPMBUILD_DIR/artifacts/jq -O https://artifacthub-iad.oci.oraclecorp.com/facops-backup/jq
    # decrypt
    curl -o $RPMBUILD_DIR/artifacts/decrypt -O https://artifacthub-iad.oci.oraclecorp.com/facops-backup/decrypt
    # opc_linux64.zip 
    export https_proxy=www-proxy.us.oracle.com:80
    export http_proxy=www-proxy.us.oracle.com:80
    curl -o $RPMBUILD_DIR/artifacts/opc_linux64.zip -O https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa/opc_linux64.zip
    # 
    unzip -o $RPMBUILD_DIR/artifacts/opc_linux64.zip -d $RPMBUILD_DIR/artifacts
    # 
    chmod 755 $RPMBUILD_DIR/artifacts/*
    unset https_proxy
    unset http_proxy
}

function rpm_deploy() {
    export https_proxy=www-proxy.us.oracle.com:80
    export http_proxy=www-proxy.us.oracle.com:80
    if [[ -d ${RPM_REPO_DIR}/repodata ]];then
        createrepo --update $RPM_REPO_DIR
    else
        createrepo $RPM_REPO_DIR
    fi
    find $RPM_REPO_DIR -type f -exec curl -s -H 'X-JFrog-Art-Api:AKCp8jQwqTVLHXuJ3wqGNMrYLBPpRvZX5FtDdNQjHdGXze1iX8Rcxm6vTUV9WthL7EZwx3W3F' -X PUT ${REPO_URL}/{} -T {} \;
    if [[ $? -ne 0 ]];then
        "failed to update artifactory rpm repo ..."
        exit 1
    fi
}

function build_rpm() {
    version=$1
    iteration=$2
    DB_RPM="fa-spe-oci-backup-db"
    DB_RPM_FILE="fa-spe-oci-backup-db-${version}-${iteration}.x86_64.rpm"
    MT_RPM="fa-spe-oci-backup-mt"
    MT_RPM_FILE="fa-spe-oci-backup-mt-${version}-${iteration}.x86_64.rpm"
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
        SCL_RUN="scl enable rh-ruby23 -- " 
    else
        unset SCL_RUN
    fi
    # DB RPM
    $SCL_RUN fpm --verbose -s dir -t rpm -n $DB_RPM -v $version --iteration $iteration \
    --replaces fa-peo-oci-backup \
    --inputs inputs_db.txt \
    --exclude-file excludes.txt \
    --rpm-compression-level 9 \
    --license "Property of Oracle Corp." --vendor "SaaS Performance Engineering" \
    --rpm-summary "SPE OCI backup and restore tool" -m "zakki.ahmed@oracle.com" \
    --url "https://confluence.rightnowtech.com/display/SAAS/FA+on+OCI+Backup+Restore+Package+Release+Notes" \
    --before-install ../../src/rpm_preinstall.sh \
    --after-install ../../src/post_install_v2.sh \
    --after-upgrade ../../src/post_install_v2.sh \
    --after-remove ../../src/rpm_uninstall.sh 
    
    if [[ $? -ne 0 ]];then
        "fpm build faced error ..."
        exit 1
    fi

    #MT RPM
    # $SCL_RUN fpm --verbose -s dir -t rpm -n $MT_RPM -v $version --iteration $iteration \
    # --replaces fa-peo-oci-backup \
    # --inputs inputs_mt.txt \
    # --exclude-file excludes.txt \
    # --rpm-compression-level 9 \
    # --license "Property of Oracle Corp." --vendor "SaaS Performance Engineering" \
    # --rpm-summary "SPE OCI backup and restore tool" -m "zakki.ahmed@oracle.com" \
    # --url "https://confluence.rightnowtech.com/display/SAAS/FA+on+OCI+Backup+Restore+Package+Release+Notes" \
    # --before-install ../../src/rpm_preinstall.sh \
    # --after-install ../../src/post_install_v2.sh \
    # --after-upgrade ../../src/post_install_v2.sh \
    # --after-remove ../../src/rpm_uninstall.sh 

    if [[ $? -ne 0 ]];then
        "fpm build faced error ..."
        exit 1
    fi
    # 
    mkdir -p $RPM_REPO_DIR
    cp $DB_RPM_FILE $RPM_REPO_DIR
    cp $MT_RPM_FILE $RPM_REPO_DIR
   
    # rpm deploy
    rpm_deploy
}
# 

# build_rpm 2.0.0.0.210515.1 7
ver=$1
rev=$2
build_rpm $ver $rev