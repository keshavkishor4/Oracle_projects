# Hello packaging friend!
#
# If you find yourself using this 'fpm --edit' feature frequently, it is
# a sign that fpm is missing a feature! I welcome your feature requests!
# Please visit the following URL and ask for a feature that helps you never
# need to edit this file again! :)
#   https://github.com/jordansissel/fpm/issues
# ------------------------------------------------------------------------

# Disable the stupid stuff rpm distros include in the build process by default:
#   Disable any prep shell actions. replace them with simply 'true'
%define __spec_prep_post true
%define __spec_prep_pre true
#   Disable any build shell actions. replace them with simply 'true'
%define __spec_build_post true
%define __spec_build_pre true
#   Disable any install shell actions. replace them with simply 'true'
%define __spec_install_post true
%define __spec_install_pre true
#   Disable any clean shell actions. replace them with simply 'true'
%define __spec_clean_post true
%define __spec_clean_pre true
# Disable checking for unpackaged files ?
#%undefine __check_files

# Allow building noarch packages that contain binaries
%define _binaries_in_noarch_packages_terminate_build 0

# Use md5 file digest method. 
# The first macro is the one used in RPM v4.9.1.1
%define _binary_filedigest_algorithm 1
# This is the macro I find on OSX when Homebrew provides rpmbuild (rpm v5.4.14)
%define _build_binary_file_digest_algo 1

# Use gzip payload compression
%define _binary_payload w9.gzdio 


Name: fa-spe-oci-backup-db
Version: 2.0.0.0.210815.1
Release: 4
Summary: SPE OCI backup and restore tool
AutoReqProv: no
# Seems specifying BuildRoot is required on older rpmbuild (like on CentOS 5)
# fpm passes '--define buildroot ...' on the commandline, so just reuse that.
BuildRoot: %buildroot

Prefix: /

Group: default
License: Property of Oracle Corp.
Vendor: SaaS Performance Engineering
URL: https://confluence.rightnowtech.com/display/SAAS/FA+on+OCI+Backup+Restore+Package+Release+Notes
Packager: zakki.ahmed@oracle.com

Obsoletes: fa-peo-oci-backup
%description
no description given

%prep
# noop

%build
# noop

%install
# noop

%clean
# noop


%pre 
upgrade() {
    :
}
_install() {
    :
#!/bin/bash
PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
BASE_DIR="/opt/faops/spe/ocifabackup"

# declare -a FILE_LIST("${PREV_DIR}/utils/db/conf/*cfg" "${PREV_DIR}/config/wallet/config-oci.json""${PREV_DIR}/config/wallet/oci_api_key.pem")

if [[ -f $BASE_DIR/db/conf/sre_db.cfg ]];then
    # Check contents
    new_output=$(grep -i swiftobjectstorage $BASE_DIR/db/conf/sre_db.cfg)
    if [[ ! -z "$new_output" ]];then
        :
    elif [[ -f $PREV_DIR/db/conf/sre_db.cfg ]];then
        old_output=$(grep -i swiftobjectstorage $PREV_DIR/db/conf/sre_db.cfg)
        if [[ ! -z "$old_output" ]];then
            cp -P $PREV_DIR/db/conf/sre_db.cfg $BASE_DIR/db/conf/sre_db.cfg
        fi
    fi
    # exit 0
elif [[ -f $PREV_DIR/db/conf/sre_db.cfg ]];then
    old_output=$(grep -i swiftobjectstorage $PREV_DIR/db/conf/sre_db.cfg)
    if [[ ! -z "$old_output" ]];then
        cp -P $PREV_DIR/db/conf/sre_db.cfg $BASE_DIR/db/conf/sre_db.cfg
    fi
fi

# config-oci json
if [ -d $BASE_DIR/config/wallet ] && [ -d ${PREV_DIR}/config/wallet ];then
    if [[ -f $BASE_DIR/config/wallet/config-oci.json ]];then
        config_out=$(grep -i ocid1.user.oc1 ${BASE_DIR}/config/wallet/config-oci.json)
        if [[ ! -z "$config_out" ]];then
            :
        elif [[ -f ${PREV_DIR}/config/wallet/config-oci.json ]];then
            config_out=$(grep -i ocid1.user.oc1 ${PREV_DIR}/config/wallet/config-oci.json)
            if [[ ! -z "$config_out" ]];then
                cp -P ${PREV_DIR}/config/wallet/config-oci.json ${BASE_DIR}/config/wallet
            fi
        fi
    elif [[ -f ${PREV_DIR}/config/wallet/config-oci.json ]];then
        config_out=$(grep -i ocid1.user.oc1 ${PREV_DIR}/config/wallet/config-oci.json)
        if [[ ! -z "$config_out" ]];then
            cp -P ${PREV_DIR}/config/wallet/config-oci.json ${BASE_DIR}/config/wallet
        fi
    fi
fi

# pem
if [ -d $BASE_DIR/config/wallet ] && [ -d ${PREV_DIR}/config/wallet ];then
    if [[ -f $BASE_DIR/config/wallet/oci_api_key.pem ]];then
        verify_pem=$(openssl rsa -in ${BASE_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
        if [[ ! -z "$verify_pem" ]];then
            :
        elif [[ -f ${PREV_DIR}/config/wallet/oci_api_key.pem ]];then
            verify_pem=$(openssl rsa -in ${PREV_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
            if [[ ! -z "$verify_pem" ]];then
                cp -P ${PREV_DIR}/config/wallet/oci_api_key.pem ${BASE_DIR}/config/wallet
            fi
        fi
    elif [[ -f ${PREV_DIR}/config/wallet/oci_api_key.pem ]];then
        verify_pem=$(openssl rsa -in ${PREV_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
        if [[ ! -z "$verify_pem" ]];then
            cp -P ${PREV_DIR}/config/wallet/oci_api_key.pem ${BASE_DIR}/config/wallet
        fi 
    fi
fi
# 
# clean up old python
if [[ -d "$PREV_DIR/utils/python3" ]]; then
    rm -rf $PREV_DIR/utils/python3/
fi

echo "uninstall of old rpm, clearing out old files"
rm -f /etc/cron.d/ocifsbackup
}
if [ "${1}" -eq 1 ]
then
    # "before install" goes here
    _install
elif [ "${1}" -gt 1 ]
then
    # "before upgrade" goes here
    upgrade
fi

%post 
upgrade() {
    :
#!/bin/bash -x
LOGGER="logger -s -t fa-spe-oci-backup-[$$] -- "
BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
chmod 755 ${JQ_TOOL}
METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
REGION=$(echo "${INST}"| "${JQ_TOOL}" -r '.canonicalRegionName')
DB_BACKUP_LOG_DIR="/u02/backup/log/$(hostname -s)"

if [[ $? -ne 0 ]]; then
    $LOGGER "fa-spe:ERROR: This rpm package does not apply to current machine, please uninstall the package."
    rm -rf /etc/cron.d/ocifsbackup_v2
    exit 1
fi

echo "${METADATA}" | "${JQ_TOOL}" -e . >/dev/null 2>&1
if [ $? -ne 0 ]; then
    $LOGGER "fa-spe:ERROR: Could not get a valid json format metadata. Please check and uninstall this package."
    echo "${METADATA}"
    rm -rf /etc/cron.d/ocifsbackup_v2
    exit 1
fi
#

# unload python
download_python() {
    os_ver=$(uname -r)
    # PYTHON_FILE="python3_el7.zip"
    PYTHON_FILE="python39_el7.zip"
    if [[ $os_ver =~ "el7" ]];then
        curl -o /tmp/${PYTHON_FILE} -s -L --fail https://objectstorage.us-ashburn-1.oraclecloud.com/n/p1-saasfapreprod1/b/FAOPS/o/${PYTHON_FILE} 2>/dev/null
        if [ $? -eq 0 ]; then
            unzip -q -o /tmp/${PYTHON_FILE} -d ${BACKUP_BASE_DIR}/utils/python3
            rm -f /tmp/${PYTHON_FILE}
        else
            echo "WARN: download of python3_el7 has failed, backups will not perform as desired"
        fi
    elif [[ $os_ver =~ "el6" ]];then
        curl -o /tmp/python3_el6.zip -s -L --fail https://objectstorage.us-ashburn-1.oraclecloud.com/n/p1-saasfapreprod1/b/FAOPS/o/python3_el6.zip 2>/dev/null
        if [ $? -eq 0 ]; then
            unzip -q -o /tmp/python3_el6.zip -d ${BACKUP_BASE_DIR}/utils/python3
            rm -f /tmp/python3_el6.zip
        else
            echo "WARN: download of python3_el6 has failed, backups will not perform as desired"
        fi

    fi
}
# Generate cron
# updates for 31979818 and 32033704
generate_cron(){
    type=$1
    region=$2
    CRONFILE="/etc/cron.d/ocifsbackupv2"
    #
    case "$region" in
        # Sat - 2300 JST - Sat - 1400 UTC  - APAC
        *"ap-"*)
            CRON_HR="14"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        
        # Sat 2300 UTC = Sat 2300 UTC 
        *"eu-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"me-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"uk-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        # Sat 2300 PST = Sun 0700 UTC
        *"ca-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"sa-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"us-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
    esac
    # Generate BV cron
        read -r -d '' GEN_BV_CRON << GEN_BV_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS - for BV pods
30 ${CRON_HR} * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --target oss) > /dev/null 2>&1
00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_BV_CRON
    # Generate FSS cron
        read -r -d '' GEN_FSS_CRON << GEN_FSS_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS domU (Snapshot daily)
00 ${CRON_HR} * * * root ${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --storage-type fss --backup-options snapshot --catalog-type local > /dev/null 2>&1
00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_FSS_CRON

# Generate DB Cron
    read -r -d '' GEN_DB_CRON << GEN_DB_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS DB Backup
0 ${CRON_HR} * * ${FULL_BKP_DAY} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 ${CRON_HR} * * ${INCR_DAYS} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 0,4,8,12,16,20 * * * root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b archivelog_to_oss 2>&1  #NEWBKPSCRIPT20190126

GEN_DB_CRON
# 
    if [[ $type == "bv" ]];then
        echo "$GEN_BV_CRON" > "${CRONFILE}"
    elif [[ $type == "fss" ]];then
        echo "$GEN_FSS_CRON" > "${CRONFILE}"
    elif [[ $type == "db" ]];then
        echo "$GEN_DB_CRON" > "${CRONFILE}"
    fi
}
# Post task for MT
mt_host() {
    # Remove old cron
    OLD_CRON="/etc/cron.d/ocifsbackup"
    if [[ -f "${OLD_CRON}" ]];then
        rm -f ${OLD_CRON}ß
    fi
    # create necessary direcotories
    mkdir -p /var/log/ocifsbackupv2
    mkdir -p /var/log/ocifsbackup/
    # Identify block enabled pod
    # isbv=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.userdata.block_enabled')
    # curl -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/
    #isbv=$(curl -s -k -H "Authorization: Bearer Oracle" -X GET http://169.254.169.254/opc/v2/instance/metadata/userdata/block_enabled)
    #if [[ $isbv == "true" ]]
    #then
    hostname -s| egrep '\-fa' > /dev/null 2>&1
    if [[ $? -ne 0 ]];then
        $LOGGER 'not installing v2 backup - Not FA MT host type'
        exit 0
    fi
    # crond_file="${BACKUP_BASE_DIR}/config/mt/ocifsbackup_v2.crond"
    crond_file="/etc/cron.d/ocifsbackupv2"
    generate_cron bv $REGION
    if [[ -f "${crond_file}" ]]; then
        # cp -f "${crond_file}" /etc/cron.d/ocifsbackupv2
        chmod 644 /etc/cron.d/ocifsbackupv2
        touch /etc/cron.d/ocifsbackupv2
        if [[ $? -eq 0 ]];then
            $LOGGER 'fa-spe: install cron for faoci backups'
        else
            $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
        fi
    fi
    #else
    # componentType is included in metadata of non DB node.
    #    COMPONENTTYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.componentType')
    #    if [[ "${COMPONENTTYPE}" != "null" ]]; then
    #        if [[ "${COMPONENTTYPE}" == "ADMIN" ]]; then
    #            echo "ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #            $LOGGER "fa-spe:ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #            rm -rf /etc/cron.d/ocifsbackupv2
    #            exit 1
    #        fi
    #
    #        if [[ "${REGION}" != "null" ]]; then
    #            # crond_file="${BACKUP_BASE_DIR}/config/mt/ocifsbackup.crond.""${REGION}"
    #            crond_file="/etc/cron.d/ocifsbackupv2"
    #            generate_cron fss $REGION
    #            if [ -f "${crond_file}" ]; then
    #                # cp -rf "${crond_file}" /etc/cron.d/ocifsbackupv2
    #                chmod 644 /etc/cron.d/ocifsbackupv2
    #                touch /etc/cron.d/ocifsbackupv2
    #            else
    #                echo "WARN: Cron file of this region does not exist, will use default cron schedule."
    #            fi
    #        else
    #            echo "WARN: Failed to get the region, will use default cron schedule."
    #        fi
    #    fi
    #fi
    # download_python
    download_python
    if [ -d ${BACKUP_BASE_DIR}/bin ] || [ -d ${BACKUP_BASE_DIR}/lib/python/common ];then
        chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
        chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
    fi
    # 
    if [ -d ${BACKUP_BASE_DIR}/lib/python/mt ];then
        chmod -R 755 ${BACKUP_BASE_DIR}/lib/python/mt/*
    fi
}


db_host() {
    # Remove old cron
    OLD_CRON="/etc/cron.d/ocifsbackup"
    if [[ -f "${OLD_CRON}" ]];then
        rm -f ${OLD_CRON}
    fi
    # 
    if [ -d ${BACKUP_BASE_DIR}/ ];then
            chown -Rh oracle:oinstall ${BACKUP_BASE_DIR}
    fi
    # dbSystemShape is included in metadata of DB node.
    DBSHAPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
    if [[ "${DBSHAPE}" != "null" ]]; then
        # INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
        # Schedule rman backup on all DB nodes.
        crond_file="/etc/cron.d/ocifsbackupv2"
        generate_cron db $REGION
        if [[ -f "${crond_file}" ]]; then
            # cp -f "${crond_file}" /etc/cron.d/ocifsbackupv2
            chmod 644 /etc/cron.d/ocifsbackupv2
            touch /etc/cron.d/ocifsbackupv2
            if [[ $? -eq 0 ]];then
                $LOGGER 'fa-spe: install cron for faoci backups'
            else
                $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
            fi
        fi
        # 
        # Deliver wallet config files
        # fix permissions
        if [ -d ${BACKUP_BASE_DIR}/bin ] || [ -d ${BACKUP_BASE_DIR}/lib/python/db ] || [ -d ${BACKUP_BASE_DIR}/lib/python/common ];then
            chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
            chmod -R 755 ${BACKUP_BASE_DIR}/lib/python/db/*
            chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
        fi
        if [ -f ${BACKUP_BASE_DIR}/config/db/decrypt ];then
            chmod 755 ${BACKUP_BASE_DIR}/config/db/decrypt
        fi
        if [ -d "${BACKUP_BASE_DIR}/utils/db/scripts" ];then
            chmod -R 755 ${BACKUP_BASE_DIR}/utils/db/scripts
        fi
        # make directories and fix permissions
        if [[ -d "${DB_BACKUP_LOG_DIR}" ]];then
            chown oracle:oinstall ${DB_BACKUP_LOG_DIR}
        else 
            mkdir -p ${DB_BACKUP_LOG_DIR}/exalogs
            chown oracle:oinstall ${DB_BACKUP_LOG_DIR}
        fi
        # Only for DB, make oracle:oinstall for code base
        if [ -d ${BACKUP_BASE_DIR}/ ];then
            chown -Rh oracle:oinstall ${BACKUP_BASE_DIR}
        fi

        if [ -d "/fss" ];then
            # create stage/scripts directories in /fss
            mkdir -p /fss/oci_backup/stage;mkdir -p /fss/oci_backup/scripts
            # fix ownership
            chown -Rh oracle:oinstall /fss/oci_backup/stage;chown -Rh oracle:oinstall /fss/oci_backup/scripts
        fi
        # 
        # copy vnstatrc file
        if [[ -f ${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf ]];then
            cp -P ${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf $HOME/.vnstatrc
        fi
        # install service
        # if [[ -f /etc/systemd/system/faocibkp.service ]];then
        #     systemctl start faocibkp.service 
        #     systemctl enable faocibkp.service 
        # fi
        # 
        download_python
       
    fi
}


HOST_TYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
case "$HOST_TYPE" in
    *"Exa"*) 
        db_host
        ;;
    *"VM.Standard"*) 
        db_host
        ;;
    *)
        mt_host
        ;;
esac

# Remove .password.json
# rm -f ${BACKUP_BASE_DIR}/utils/db/conf/.passwd.json

# Restart crond
os_type=$(uname -s)
if [[ "${os_type}" = "Linux" ]]; then
   os_ver=$(uname -r)
   if [[ $os_ver =~ "el7" ]];then
       systemctl restart crond.service
   elif [[ $os_ver =~ "el6" ]];then
       /etc/init.d/crond reload  > /dev/null 2>&1;
   fi
fi

}
_install() {
    :
#!/bin/bash -x
LOGGER="logger -s -t fa-spe-oci-backup-[$$] -- "
BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
chmod 755 ${JQ_TOOL}
METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
REGION=$(echo "${INST}"| "${JQ_TOOL}" -r '.canonicalRegionName')
DB_BACKUP_LOG_DIR="/u02/backup/log/$(hostname -s)"

if [[ $? -ne 0 ]]; then
    $LOGGER "fa-spe:ERROR: This rpm package does not apply to current machine, please uninstall the package."
    rm -rf /etc/cron.d/ocifsbackup_v2
    exit 1
fi

echo "${METADATA}" | "${JQ_TOOL}" -e . >/dev/null 2>&1
if [ $? -ne 0 ]; then
    $LOGGER "fa-spe:ERROR: Could not get a valid json format metadata. Please check and uninstall this package."
    echo "${METADATA}"
    rm -rf /etc/cron.d/ocifsbackup_v2
    exit 1
fi
#

# unload python
download_python() {
    os_ver=$(uname -r)
    # PYTHON_FILE="python3_el7.zip"
    PYTHON_FILE="python39_el7.zip"
    if [[ $os_ver =~ "el7" ]];then
        curl -o /tmp/${PYTHON_FILE} -s -L --fail https://objectstorage.us-ashburn-1.oraclecloud.com/n/p1-saasfapreprod1/b/FAOPS/o/${PYTHON_FILE} 2>/dev/null
        if [ $? -eq 0 ]; then
            unzip -q -o /tmp/${PYTHON_FILE} -d ${BACKUP_BASE_DIR}/utils/python3
            rm -f /tmp/${PYTHON_FILE}
        else
            echo "WARN: download of python3_el7 has failed, backups will not perform as desired"
        fi
    elif [[ $os_ver =~ "el6" ]];then
        curl -o /tmp/python3_el6.zip -s -L --fail https://objectstorage.us-ashburn-1.oraclecloud.com/n/p1-saasfapreprod1/b/FAOPS/o/python3_el6.zip 2>/dev/null
        if [ $? -eq 0 ]; then
            unzip -q -o /tmp/python3_el6.zip -d ${BACKUP_BASE_DIR}/utils/python3
            rm -f /tmp/python3_el6.zip
        else
            echo "WARN: download of python3_el6 has failed, backups will not perform as desired"
        fi

    fi
}
# Generate cron
# updates for 31979818 and 32033704
generate_cron(){
    type=$1
    region=$2
    CRONFILE="/etc/cron.d/ocifsbackupv2"
    #
    case "$region" in
        # Sat - 2300 JST - Sat - 1400 UTC  - APAC
        *"ap-"*)
            CRON_HR="14"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        
        # Sat 2300 UTC = Sat 2300 UTC 
        *"eu-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"me-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"uk-"*)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        # Sat 2300 PST = Sun 0700 UTC
        *"ca-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"sa-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"us-"*)
            CRON_HR="07"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *)
            CRON_HR="23"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
    esac
    # Generate BV cron
        read -r -d '' GEN_BV_CRON << GEN_BV_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS - for BV pods
30 ${CRON_HR} * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --target oss) > /dev/null 2>&1
00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_BV_CRON
    # Generate FSS cron
        read -r -d '' GEN_FSS_CRON << GEN_FSS_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS domU (Snapshot daily)
00 ${CRON_HR} * * * root ${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --storage-type fss --backup-options snapshot --catalog-type local > /dev/null 2>&1
00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_FSS_CRON

# Generate DB Cron
    read -r -d '' GEN_DB_CRON << GEN_DB_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS DB Backup
0 ${CRON_HR} * * ${FULL_BKP_DAY} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 ${CRON_HR} * * ${INCR_DAYS} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 0,4,8,12,16,20 * * * root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b archivelog_to_oss 2>&1  #NEWBKPSCRIPT20190126

GEN_DB_CRON
# 
    if [[ $type == "bv" ]];then
        echo "$GEN_BV_CRON" > "${CRONFILE}"
    elif [[ $type == "fss" ]];then
        echo "$GEN_FSS_CRON" > "${CRONFILE}"
    elif [[ $type == "db" ]];then
        echo "$GEN_DB_CRON" > "${CRONFILE}"
    fi
}
# Post task for MT
mt_host() {
    # Remove old cron
    OLD_CRON="/etc/cron.d/ocifsbackup"
    if [[ -f "${OLD_CRON}" ]];then
        rm -f ${OLD_CRON}ß
    fi
    # create necessary direcotories
    mkdir -p /var/log/ocifsbackupv2
    mkdir -p /var/log/ocifsbackup/
    # Identify block enabled pod
    # isbv=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.userdata.block_enabled')
    # curl -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/
    #isbv=$(curl -s -k -H "Authorization: Bearer Oracle" -X GET http://169.254.169.254/opc/v2/instance/metadata/userdata/block_enabled)
    #if [[ $isbv == "true" ]]
    #then
    hostname -s| egrep '\-fa' > /dev/null 2>&1
    if [[ $? -ne 0 ]];then
        $LOGGER 'not installing v2 backup - Not FA MT host type'
        exit 0
    fi
    # crond_file="${BACKUP_BASE_DIR}/config/mt/ocifsbackup_v2.crond"
    crond_file="/etc/cron.d/ocifsbackupv2"
    generate_cron bv $REGION
    if [[ -f "${crond_file}" ]]; then
        # cp -f "${crond_file}" /etc/cron.d/ocifsbackupv2
        chmod 644 /etc/cron.d/ocifsbackupv2
        touch /etc/cron.d/ocifsbackupv2
        if [[ $? -eq 0 ]];then
            $LOGGER 'fa-spe: install cron for faoci backups'
        else
            $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
        fi
    fi
    #else
    # componentType is included in metadata of non DB node.
    #    COMPONENTTYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.componentType')
    #    if [[ "${COMPONENTTYPE}" != "null" ]]; then
    #        if [[ "${COMPONENTTYPE}" == "ADMIN" ]]; then
    #            echo "ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #            $LOGGER "fa-spe:ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #            rm -rf /etc/cron.d/ocifsbackupv2
    #            exit 1
    #        fi
    #
    #        if [[ "${REGION}" != "null" ]]; then
    #            # crond_file="${BACKUP_BASE_DIR}/config/mt/ocifsbackup.crond.""${REGION}"
    #            crond_file="/etc/cron.d/ocifsbackupv2"
    #            generate_cron fss $REGION
    #            if [ -f "${crond_file}" ]; then
    #                # cp -rf "${crond_file}" /etc/cron.d/ocifsbackupv2
    #                chmod 644 /etc/cron.d/ocifsbackupv2
    #                touch /etc/cron.d/ocifsbackupv2
    #            else
    #                echo "WARN: Cron file of this region does not exist, will use default cron schedule."
    #            fi
    #        else
    #            echo "WARN: Failed to get the region, will use default cron schedule."
    #        fi
    #    fi
    #fi
    # download_python
    download_python
    if [ -d ${BACKUP_BASE_DIR}/bin ] || [ -d ${BACKUP_BASE_DIR}/lib/python/common ];then
        chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
        chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
    fi
    # 
    if [ -d ${BACKUP_BASE_DIR}/lib/python/mt ];then
        chmod -R 755 ${BACKUP_BASE_DIR}/lib/python/mt/*
    fi
}


db_host() {
    # Remove old cron
    OLD_CRON="/etc/cron.d/ocifsbackup"
    if [[ -f "${OLD_CRON}" ]];then
        rm -f ${OLD_CRON}
    fi
    # 
    if [ -d ${BACKUP_BASE_DIR}/ ];then
            chown -Rh oracle:oinstall ${BACKUP_BASE_DIR}
    fi
    # dbSystemShape is included in metadata of DB node.
    DBSHAPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
    if [[ "${DBSHAPE}" != "null" ]]; then
        # INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
        # Schedule rman backup on all DB nodes.
        crond_file="/etc/cron.d/ocifsbackupv2"
        generate_cron db $REGION
        if [[ -f "${crond_file}" ]]; then
            # cp -f "${crond_file}" /etc/cron.d/ocifsbackupv2
            chmod 644 /etc/cron.d/ocifsbackupv2
            touch /etc/cron.d/ocifsbackupv2
            if [[ $? -eq 0 ]];then
                $LOGGER 'fa-spe: install cron for faoci backups'
            else
                $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
            fi
        fi
        # 
        # Deliver wallet config files
        # fix permissions
        if [ -d ${BACKUP_BASE_DIR}/bin ] || [ -d ${BACKUP_BASE_DIR}/lib/python/db ] || [ -d ${BACKUP_BASE_DIR}/lib/python/common ];then
            chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
            chmod -R 755 ${BACKUP_BASE_DIR}/lib/python/db/*
            chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
        fi
        if [ -f ${BACKUP_BASE_DIR}/config/db/decrypt ];then
            chmod 755 ${BACKUP_BASE_DIR}/config/db/decrypt
        fi
        if [ -d "${BACKUP_BASE_DIR}/utils/db/scripts" ];then
            chmod -R 755 ${BACKUP_BASE_DIR}/utils/db/scripts
        fi
        # make directories and fix permissions
        if [[ -d "${DB_BACKUP_LOG_DIR}" ]];then
            chown oracle:oinstall ${DB_BACKUP_LOG_DIR}
        else 
            mkdir -p ${DB_BACKUP_LOG_DIR}/exalogs
            chown oracle:oinstall ${DB_BACKUP_LOG_DIR}
        fi
        # Only for DB, make oracle:oinstall for code base
        if [ -d ${BACKUP_BASE_DIR}/ ];then
            chown -Rh oracle:oinstall ${BACKUP_BASE_DIR}
        fi

        if [ -d "/fss" ];then
            # create stage/scripts directories in /fss
            mkdir -p /fss/oci_backup/stage;mkdir -p /fss/oci_backup/scripts
            # fix ownership
            chown -Rh oracle:oinstall /fss/oci_backup/stage;chown -Rh oracle:oinstall /fss/oci_backup/scripts
        fi
        # 
        # copy vnstatrc file
        if [[ -f ${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf ]];then
            cp -P ${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf $HOME/.vnstatrc
        fi
        # install service
        # if [[ -f /etc/systemd/system/faocibkp.service ]];then
        #     systemctl start faocibkp.service 
        #     systemctl enable faocibkp.service 
        # fi
        # 
        download_python
       
    fi
}


HOST_TYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
case "$HOST_TYPE" in
    *"Exa"*) 
        db_host
        ;;
    *"VM.Standard"*) 
        db_host
        ;;
    *)
        mt_host
        ;;
esac

# Remove .password.json
# rm -f ${BACKUP_BASE_DIR}/utils/db/conf/.passwd.json

# Restart crond
os_type=$(uname -s)
if [[ "${os_type}" = "Linux" ]]; then
   os_ver=$(uname -r)
   if [[ $os_ver =~ "el7" ]];then
       systemctl restart crond.service
   elif [[ $os_ver =~ "el6" ]];then
       /etc/init.d/crond reload  > /dev/null 2>&1;
   fi
fi

}
if [ "${1}" -eq 1 ]
then
    # "after install" goes here
    _install
elif [ "${1}" -gt 1 ]
then
    # "after upgrade" goes here
    upgrade
fi

%preun 
if [ "${1}" -eq 0 ]
then
    :
#!/bin/bash
BASE_DIR="/opt/faops/spe/ocifabackup"
echo "uninstall of old rpm, clearing out old files"
# if old cron exist
if [[ -f "/etc/cron.d/ocifsbackup" ]];then
    rm -f /etc/cron.d/ocifsbackup
fi
# wallet configs 
if [[ -d "$BASE_DIR/wallet/" ]]; then
    rm -rf $BASE_DIR/wallet/*
fi
# clean up old python
if [[ -d "$BASE_DIR/utils/python3" ]]; then
    rm -rf $BASE_DIR/utils/python3/
fi
#
if [[ -f "$BASE_DIR/config/db/decrypt" ]]; then
    rm -f $BASE_DIR/config/db/decrypt*
fi
fi


%files
%defattr(-,root,root,-)

# Reject config files already listed or parent directories, then prefix files
# with "/", then make sure paths with spaces are quoted. I hate rpm so much.
/etc/systemd/system/faocibkp.service
/opt/faops/spe/ocifabackup/bin/__init__.py
/opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py
/opt/faops/spe/ocifabackup/bin/db_tasks.py
/opt/faops/spe/ocifabackup/bin/db_wallet_backup.py
/opt/faops/spe/ocifabackup/bin/faocibkp
/opt/faops/spe/ocifabackup/bin/rman_oss.py
/opt/faops/spe/ocifabackup/bin/rman_oss.sh
/opt/faops/spe/ocifabackup/bin/rman_wrapper.py
/opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh
/opt/faops/spe/ocifabackup/config/.creds.json
/opt/faops/spe/ocifabackup/config/backup-metadata.json_template
/opt/faops/spe/ocifabackup/config/catalog_url.json
/opt/faops/spe/ocifabackup/config/db/Readme_all_pod_info.txt
/opt/faops/spe/ocifabackup/config/db/db_artifacts.json
/opt/faops/spe/ocifabackup/config/db/db_backup_exceptions.txt
/opt/faops/spe/ocifabackup/config/db/db_node_exceptions.txt
/opt/faops/spe/ocifabackup/config/db/db_size.json
/opt/faops/spe/ocifabackup/config/db/db_wallet.json
/opt/faops/spe/ocifabackup/config/db/decrypt
/opt/faops/spe/ocifabackup/config/db/housekeeping-db_v2.json
/opt/faops/spe/ocifabackup/config/db/libs/libopc.so
/opt/faops/spe/ocifabackup/config/db/nonfa_db_artifacts.json
/opt/faops/spe/ocifabackup/config/db/nonfa_db_wallet.json
/opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json
/opt/faops/spe/ocifabackup/config/faops-backup-ver.json
/opt/faops/spe/ocifabackup/config/faops-backup-ver_api_update.json
/opt/faops/spe/ocifabackup/config/key_archive/oci_api_key.pem
/opt/faops/spe/ocifabackup/config/key_archive/oci_api_key_public.pem
/opt/faops/spe/ocifabackup/config/wallet/.oci/config-oci-p1-saasfapreprod1.json.crypt
/opt/faops/spe/ocifabackup/config/wallet/.oci/config-oci-saasfaprod1.json.crypt
/opt/faops/spe/ocifabackup/config/wallet/.oci/config-oci-saasfaukgovprod1.json.crypt
/opt/faops/spe/ocifabackup/config/wallet/config-oci-template.json
/opt/faops/spe/ocifabackup/config/wallet/enc_files_mapping.json
/opt/faops/spe/ocifabackup/lib/python/common/__init__.py
/opt/faops/spe/ocifabackup/lib/python/common/apscom.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/__init__.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/_common.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/_decorator.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/_jitter.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/_sync.py
/opt/faops/spe/ocifabackup/lib/python/common/backoff/_wait_gen.py
/opt/faops/spe/ocifabackup/lib/python/common/commonutils.py
/opt/faops/spe/ocifabackup/lib/python/common/fssSDK.py
/opt/faops/spe/ocifabackup/lib/python/common/globalvariables.py
/opt/faops/spe/ocifabackup/lib/python/common/instance_metadata.py
/opt/faops/spe/ocifabackup/lib/python/common/jwt_encode.py
/opt/faops/spe/ocifabackup/lib/python/common/load_oci_config.py
/opt/faops/spe/ocifabackup/lib/python/common/load_oci_config.py.bkp20210211
/opt/faops/spe/ocifabackup/lib/python/common/ociSDK.py
/opt/faops/spe/ocifabackup/lib/python/common/oci_curl.sh
/opt/faops/spe/ocifabackup/lib/python/common/oci_setup.sh
/opt/faops/spe/ocifabackup/lib/python/common/post_backup_metadata.py
/opt/faops/spe/ocifabackup/lib/python/common/rpmupdates.py
/opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
/opt/faops/spe/ocifabackup/lib/python/common/traceerrors.py
/opt/faops/spe/ocifabackup/lib/python/common/v1/__init__.py
/opt/faops/spe/ocifabackup/lib/python/common/v1/apsbkcom.py
/opt/faops/spe/ocifabackup/lib/python/common/v1/apsbkcom_v2.py
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup-eura.crond.eu-amsterdam-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup-eura.crond.eu-frankfurt-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-hyderabad-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-melbourne-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-mumbai-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-osaka-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-sydney-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ap-tokyo-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ca-montreal-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.ca-toronto-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.eu-amsterdam-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.eu-frankfurt-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.eu-zurich-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.me-jeddah-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.sa-saopaulo-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.uk-london-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.us-ashburn-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup.crond.us-phoenix-1
/opt/faops/spe/ocifabackup/lib/python/common/v1/ocifsbackup_eura.crond
/opt/faops/spe/ocifabackup/lib/python/common/validate_config.sh
/opt/faops/spe/ocifabackup/lib/python/db/__init__.py
/opt/faops/spe/ocifabackup/lib/python/db/all_pod_oratab_modify.py
/opt/faops/spe/ocifabackup/lib/python/db/database_config.py
/opt/faops/spe/ocifabackup/lib/python/db/db_query_pool.py
/opt/faops/spe/ocifabackup/lib/python/db/remote_exec.py
/opt/faops/spe/ocifabackup/lib/python/db/remote_test.py
/opt/faops/spe/ocifabackup/lib/python/db/validate_sbt_test.py
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_archive_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_archive_to_oss_bv.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_compressed_to_oss.rman_pdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_full_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_to_reco.rman_pdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/database_to_reco_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/fra_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/incremental_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/incremental_to_oss.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/incremental_to_oss.rman_pdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/incremental_to_reco.rman_pdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/obsolete_backupset.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/report.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archive/rman_sync.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archivelog_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/archivelog_to_oss.rman_cf_ab_on
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/configuration.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/configuration_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/configuration_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_compressed_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_compressed_to_oss.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_compressed_to_oss_12.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_compressed_to_oss_12.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_to_reco.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_to_reco_12.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_to_reco_12.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/incremental_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/incremental_to_oss.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/incremental_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/incremental_to_reco.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_archivelog_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_archivelog_to_oss.rman_cf_ab_on
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_configuration.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_configuration_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_database_compressed_to_oss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_database_compressed_to_oss.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_database_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_database_to_reco.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_incremental_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_incremental_to_reco.rman_cdb
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_obsolete_backupset_withoss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/nonfa_dbaas/nonfa_pdbseed_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/obsolete_backupset_withoss.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/rman/pdbseed_to_reco.rman
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/backup_tests.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/check_swiftobj_oss.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/cleanup_reco.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/dbBackupValidatePre.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/dbBackupValidateRun.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/env.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/gen_crs_db_inv.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/mtBackupValidatePre.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/mtBackupValidateRun.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/remote_actions.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/rpm_uninstall.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/rpm_upgrade.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/rpm_verify.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/set_ora_env.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/setup_backup_lib_wrapper.sh
/opt/faops/spe/ocifabackup/utils/db/scripts/shell/upload_rpm_vers_and_rpm.sh
/opt/faops/spe/ocifabackup/utils/db/sql/cdb_db_backup_size.sql
/opt/faops/spe/ocifabackup/utils/db/sql/cdb_db_backup_size1.sql
/opt/faops/spe/ocifabackup/utils/db/sql/cdb_db_backup_size2.sql
/opt/faops/spe/ocifabackup/utils/db/sql/db_query_sql.txt
/opt/faops/spe/ocifabackup/utils/db/sql/pdb_get_bg_status.sql
/opt/faops/spe/ocifabackup/utils/db/sql/query.txt
/opt/faops/spe/ocifabackup/utils/db/sql/sofar.sql
/opt/faops/spe/ocifabackup/utils/fa-oci-backup.repo
/opt/faops/spe/ocifabackup/utils/jq
/opt/faops/spe/ocifabackup/utils/vnstat/bin/vnstat
/opt/faops/spe/ocifabackup/utils/vnstat/bin/vnstatd
/opt/faops/spe/ocifabackup/utils/vnstat/etc/.vnstatrc
/opt/faops/spe/ocifabackup/utils/vnstat/etc/vnstat.conf
/opt/faops/spe/ocifabackup/utils/vnstat/share/man/man1/vnstat.1
/opt/faops/spe/ocifabackup/utils/vnstat/share/man/man1/vnstati.1
/opt/faops/spe/ocifabackup/utils/vnstat/share/man/man5/vnstat.conf.5
/opt/faops/spe/ocifabackup/utils/vnstat/share/man/man8/vnstatd.8

%changelog

