#!/bin/bash -x
LOGGER="logger -s -t fa-spe-oci-backup-[$$] -- "
BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
chmod 755 ${JQ_TOOL}
METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
DB_SYSTEM=$(echo "${METADATA}"| "${JQ_TOOL}" -r '.dbSystemShape')
INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
REGION=$(echo "${INST}"| "${JQ_TOOL}" -r '.canonicalRegionName')
DB_BACKUP_LOG_DIR="/u02/backup/log/$(hostname -s)"
BACKUP_ARTIFACTS_PATH="/fss/oci_backup/artifacts/$(hostname -s)"
PACK_DIR="${BACKUP_BASE_DIR}/utils/python3/el7/lib/python3.10/site-packages"
PACK="oci_cli notebook IPython"
SUB_HOSTNAME=$(hostname -f | awk -F'.' '{print $2}')

if [[ "$?" -ne 0 ]]; then
    $LOGGER "fa-spe:ERROR: This rpm package does not apply to current machine, please uninstall the package."
    rm -rf /etc/cron.d/ocifsbackup_v2
    rm -rf /etc/cron.d/ocifsbackupv2
    exit 1
fi

echo "${METADATA}" | "${JQ_TOOL}" -e . >/dev/null 2>&1
if [ "$?" -ne 0 ]; then
    $LOGGER "fa-spe:ERROR: Could not get a valid json format metadata. Please check and uninstall this package."
    echo "${METADATA}"
    rm -rf /etc/cron.d/ocifsbackup_v2
    rm -rf /etc/cron.d/ocifsbackupv2
    exit 1
fi
#

# unload python
download_file() {
    FILE=$1
    FILE_NAME=$(basename $FILE)

    #Defining artifact and OSS URLs for python3_latest_el7/el6.zip
    if [[ ${REGION} == *"uk-gov"* ]];then
        OBJ_URL="https://objectstorage.uk-gov-london-1.oraclegovcloud.uk/p/wT7PZt-pWPNsIsrMHY2FE4deFsrplg5wUgKSir6XSIK5lYzRVA15LURG_oPkschG/n/axqqulwjr5ll/b/FSRE-MW-BINARIES/o/${FILE_NAME}"
        ARTFCT_URL="https://artifactory-ltn-prod.cdaas.ocs.oraclegovcloud.uk/artifactory/list/generic-fa/${FILE_NAME}"
    else
        OBJ_URL="https://objectstorage.us-phoenix-1.oraclecloud.com/p/BqFqDUq48bLrkbxducBUXMgEHaH2MqCb9HhqejJWca-a3fC3wTEfhCoUpHgkDe10/n/p1-saasfapreprod1/b/BACKUP_SUPPORT/o/${FILE_NAME}"
        #OBJ_URL="https://objectstorage.us-phoenix-1.oraclecloud.com/p/rl3oNxpWGVcbNtehJ6YDRhftswJ3Fz2mvsFAcyy0qgcUQjAY5ipWVQWiEMkK2loM/n/p1-saasfapreprod1/b/BACKUP_SUPPORT/o/${FILE_NAME}"
        ARTFCT_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa/${FILE_NAME}"
    fi
    
    #Downloading python3_latest_el7/el6.zip from OSS
    OBJRESP=$(curl --connect-timeout 30 --retry 30 -o /tmp/$FILE_NAME -w "%{http_code}" -s -L --fail -O $OBJ_URL 2>/dev/null)
    if [[ -f "/tmp/$FILE_NAME" ]];then
        CHECK=$(unzip -q -t /tmp/$FILE_NAME 2>/dev/null)
    fi
    if [ "$OBJRESP" == "200" ] && [[ "$CHECK" =~ "No errors" ]]; then
        chmod 755 /tmp/$FILE_NAME
        echo  "/tmp/$FILE_NAME"
    else
        # Downloading python3_latest_el7/el6.zip from artifactiry 
        #=> need to remove "/tmp/$FILE_NAME"
        if [[ -f "/tmp/$FILE_NAME" ]];then
            rm -f /tmp/$FILE_NAME
        fi
        ARTRESP=$(curl --connect-timeout 30 --retry 30 -o /tmp/$FILE_NAME -w "%{http_code}" -s -L --fail -O $ARTFCT_URL 2>/dev/null)
        if [ "$ARTRESP" == "200" ]; then
            CHECK=$(unzip -q -t /tmp/$FILE_NAME 2>/dev/null)
            if [[ "$CHECK" =~ "No errors" ]];then
                chmod 755 /tmp/$FILE_NAME
                echo  "/tmp/$FILE_NAME"
            else
                echo "File is corrupted :- $FILE_NAME"
            fi
        else
            echo "failed to download /tmp/$FILE_NAME"
        fi
    fi    
}

download_python() {
    os_ver=$(uname -r)
        
    if [[ "$os_ver" =~ "el7" ]];then
        PYTHON_FILE="python3_latest_el7.zip"
    elif [[ "$os_ver" =~ "el6" ]];then
        PYTHON_FILE="python3_latest_el6.zip"
    fi
    
    TMP_FILE=$(download_file $PYTHON_FILE)
    if [[ "$TMP_FILE" =~ "fail"* ]];then
        echo "WARN: $TMP_FILE has failed, backups will not perform as desired"
    else
        unzip -q -o $TMP_FILE -d ${BACKUP_BASE_DIR}/utils/python3
        if [[ -f "/tmp/$PYTHON_FILE" ]];then
            rm -f /tmp/$PYTHON_FILE
        fi
        
    fi
    
    if [ -f "${BACKUP_BASE_DIR}/lib/python/common/setpyenv.sh" ] && [ -f "${BACKUP_BASE_DIR}/utils/python3/el7/bin/pip3" ];then
        source ${BACKUP_BASE_DIR}/lib/python/common/setpyenv.sh
        for i in $PACK;do 
            if [[ -d "${PACK_DIR}/${i}" ]];then
                export PIP_REQUIRE_VIRTUALENV=false
                ${BACKUP_BASE_DIR}/utils/python3/el7/bin/pip3 uninstall -y $i >/dev/null 2>&1
            fi
        done
    fi
}

# Generate cron
# updates for 31979818 and 32033704
generate_cron(){
    type=$1
    region=$2
    CRONFILE="/etc/cron.d/ocifsbackupv2"
    DB_VALIDATE_CRONFILE="/etc/cron.d/ocifsbkpvalidate"
    #
    case "$region" in
        # Sat - 2300 JST - Sat - 1400 UTC  - APAC
        *"ap-"*)
            WALLET_CRON_HR="13"
            CRON_HR="14"
            CRON_HR_VALIDATE="0-12,18-23" #      CRON_HR + 4       
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        
        # Sat 2300 UTC = Sat 2300 UTC 
        *"eu-"*)
            WALLET_CRON_HR="19"
            CRON_HR="23"
            CRON_HR_VALIDATE="3-21"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"me-"*)
            WALLET_CRON_HR="19"
            CRON_HR="23"
            CRON_HR_VALIDATE="3-21"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        *"uk-"*)
            WALLET_CRON_HR="19"
            CRON_HR="23"
            CRON_HR_VALIDATE="3-21"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
        # Sat 2300 PST = Sun 0700 UTC
        *"ca-"*)
            WALLET_CRON_HR="03"
            CRON_HR="07"
            CRON_HR_VALIDATE="0-5,11-23"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"sa-"*)
            WALLET_CRON_HR="03"
            CRON_HR="07"
            CRON_HR_VALIDATE="0-5,11-23"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *"us-"*)
            WALLET_CRON_HR="03"
            CRON_HR="07"
            CRON_HR_VALIDATE="0-5,11-23"
            FULL_BKP_DAY="0"
            INCR_DAYS="1-6"
            ;;
        *)
            WALLET_CRON_HR="19"
            CRON_HR="23"
            CRON_HR_VALIDATE="3-21"
            FULL_BKP_DAY="6"
            INCR_DAYS="0-5"
            ;;
    esac
    # Generate BV cron
        read -r -d '' GEN_BV_CRON << GEN_BV_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS - for BV pods
30 ${CRON_HR} * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --target oss) > /dev/null 2>&1
# 00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_BV_CRON
    # Generate FSS cron
        read -r -d '' GEN_FSS_CRON << GEN_FSS_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS domU (Snapshot daily)
00 ${CRON_HR} * * * root ${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action backup --storage-type fss --backup-options snapshot --catalog-type local > /dev/null 2>&1
# 00 23 * * * root (${BACKUP_BASE_DIR}/bin/ocifsbackup.sh --action post-metadata) > /dev/null 2>&1

GEN_FSS_CRON

# Generate DB Cron
    read -r -d '' GEN_DB_CRON << GEN_DB_CRON
# FILE: /etc/cron.d/ocifsbackupv2 -- 10/20
# Executing ocifsbackup for FA SaaS DB Backup
0 ${CRON_HR} * * ${FULL_BKP_DAY} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 ${CRON_HR} * * ${INCR_DAYS} root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss 2>&1 #NEWBKPSCRIPT20190126
0 0-23 * * * root [ \$(date +\%H) -ne ${CRON_HR} ] && ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b archivelog_to_oss 2>&1  #NEWBKPSCRIPT20190126
# Wallet and Artifacts
0 ${WALLET_CRON_HR} * * * root ${BACKUP_BASE_DIR}/bin/rman_wrapper_oss.sh -b wallet_artifacts 2>&1
GEN_DB_CRON

# Generate DB Backup/Restore Validate Cron
    read -r -d '' GEN_DB_VALIDATE_CRON << GEN_DB_VALIDATE_CRON
# FILE: /etc/cron.d/ocifsbkpvalidate -- 04/22
# Executing ocifsbkpvalidate for FA SaaS DB Backup Bug 34025807 
0 2 1-7,15-21 * * root [ \$(date +\%a) = "Thu" ] && /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=validate 2>&1
0 2 8-14,22-31 * * root [ \$(date +\%a) = "Thu" ] && /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=restore_validate 2>&1
GEN_DB_VALIDATE_CRON

read -r -d '' GEN_DB_VALIDATE_CRON_FA << GEN_DB_VALIDATE_CRON_FA
# FILE: /etc/cron.d/ocifsbkpvalidate -- 04/22
# Executing ocifsbkpvalidate for FA SaaS DB Backup Bug 34025807 
*/10 ${CRON_HR_VALIDATE} 1-7,15-21 * * root [ \$(date +\%a) = "Thu" ] || [ \$(date +\%a) = "Fri" ]  && /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=validate 2>&1
*/10 ${CRON_HR_VALIDATE} 8-14,22-31 * * root [ \$(date +\%a) = "Thu" ] || [ \$(date +\%a) = "Fri" ] && /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=restore_validate 2>&1

GEN_DB_VALIDATE_CRON_FA
# 
    if [[ "$type" == "bv" ]];then
        echo "$GEN_BV_CRON" > "${CRONFILE}"
    elif [[ "$type" == "fss" ]];then
        echo "$GEN_FSS_CRON" > "${CRONFILE}"
    elif [[ "$type" == "db" ]];then
        if [[ "$DB_SYSTEM" == *"Exa"* ]];then
            if [[ "$SUB_HOSTNAME" == *"emdb"* ]];then
                echo "$GEN_DB_CRON" > "${CRONFILE}"
                #echo "$GEN_DB_VALIDATE_CRON" > "${DB_VALIDATE_CRONFILE}" 
            else
                echo "$GEN_DB_CRON" > "${CRONFILE}"
                echo "$GEN_DB_VALIDATE_CRON_FA" > "${DB_VALIDATE_CRONFILE}" 
            fi
        else
            echo "$GEN_DB_CRON" > "${CRONFILE}"
            #echo "$GEN_DB_VALIDATE_CRON" > "${DB_VALIDATE_CRONFILE}" 
        fi
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
    # isbv=$(curl -s -k -H "Authorization: Bearer Oracle" -X GET http://169.254.169.254/opc/v2/instance/metadata/userdata/block_enabled)
    # if [[ "$isbv" == "true" ]]
    # then
    hostname -s| egrep '\-fa|ohs' > /dev/null 2>&1
    if [[ "$?" -ne 0 ]];then
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
        if [[ "$?" -eq 0 ]];then
            $LOGGER 'fa-spe: install cron for faoci backups'
        else
            $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
        fi
    fi
    # else
    # # componentType is included in metadata of non DB node.
    #     COMPONENTTYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.componentType')
    #     if [[ "${COMPONENTTYPE}" != "null" ]]; then
    #         if [[ "${COMPONENTTYPE}" == "ADMIN" ]]; then
    #             echo "ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #             $LOGGER "fa-spe:ERROR: This backup utility does not apply to admin host, please uninstall the package."
    #             rm -rf /etc/cron.d/ocifsbackupv2
    #             exit 1
    #         fi

    #         if [[ "${REGION}" != "null" ]]; then
    #             # crond_file="${BACKUP_BASE_DIR}/config/mt/ocifsbackup.crond.""${REGION}"
    #             crond_file="/etc/cron.d/ocifsbackupv2"
    #             generate_cron fss $REGION
    #             if [ -f "${crond_file}" ]; then
    #                 # cp -rf "${crond_file}" /etc/cron.d/ocifsbackupv2
    #                 chmod 644 /etc/cron.d/ocifsbackupv2
    #                 touch /etc/cron.d/ocifsbackupv2
    #             else
    #                 echo "WARN: Cron file of this region does not exist, will use default cron schedule."
    #             fi
    #         else
    #             echo "WARN: Failed to get the region, will use default cron schedule."
    #         fi
    #     fi
    #fi
    # download_python
    download_python
    if [ -d "${BACKUP_BASE_DIR}/bin" ] || [ -d "${BACKUP_BASE_DIR}/lib/python/common" ];then
        chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
        chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
    fi
    # 
    if [ -d "${BACKUP_BASE_DIR}/lib/python/mt" ];then
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
    if [ -d "${BACKUP_BASE_DIR}/" ];then
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
            # 
            chmod 644 /etc/cron.d/ocifsbkpvalidate
            touch /etc/cron.d/ocifsbkpvalidate
            if [[ "$?" -eq 0 ]];then
                $LOGGER 'fa-spe: install cron for faoci backups'
            else
                $LOGGER 'fa-spe:ERROR: install cron for faoci backups'
            fi
        fi
        # 
        # Deliver wallet config files
        # fix permissions
        if [ -d "${BACKUP_BASE_DIR}/bin" ] || [ -d "${BACKUP_BASE_DIR}/lib/python/db" ] || [ -d "${BACKUP_BASE_DIR}/lib/python/common" ];then
            chmod -R 755 ${BACKUP_BASE_DIR}/bin/*
            chmod -R 755 ${BACKUP_BASE_DIR}/lib/python/db/*
            chmod 755 ${BACKUP_BASE_DIR}/lib/python/common/*
        fi
        if [ -f "${BACKUP_BASE_DIR}/config/db/decrypt" ];then
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
        if [ -d "${BACKUP_BASE_DIR}/" ];then
            chown -Rh oracle:oinstall ${BACKUP_BASE_DIR}
        fi

        if [ -d "/fss" ];then
            # create stage/scripts directories in /fss
            mkdir -p /fss/oci_backup/stage;mkdir -p /fss/oci_backup/scripts;mkdir -p /fss/oci_backup/artifacts/$(hostname -s)
            # fix ownership
            chown -Rh oracle:oinstall /fss/oci_backup/stage;chown -Rh oracle:oinstall /fss/oci_backup/scripts; chown -Rh oracle:oinstall /fss/oci_backup/artifacts/$(hostname -s)
        fi
        # 
        # copy vnstatrc file
        # if [[ -f "${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf" ]];then
        #     cp -P ${BACKUP_BASE_DIR}/utils/vnstat/etc/vnstat.conf $HOME/.vnstatrc
        # fi
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
        # install service
        # %systemd_post faocibkp.service
        # /usr/bin/systemctl daemon-reload
        #/usr/bin/systemctl start faocibkp.service
        ;;
    *"VM.Standard"*) 
        db_host
        # install service
        # %systemd_post faocibkp.service
        # /usr/bin/systemctl daemon-reload
        #/usr/bin/systemctl start faocibkp.service
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
       # 
       if [[ -f "/tmp/.faocibkp.tmp" ]];then
           rm -f /tmp/.faocibkp.tmp
       fi
       #    
       systemctl restart crond.service
       
   elif [[ "$os_ver" =~ "el6" ]];then
       /etc/init.d/crond reload  > /dev/null 2>&1;
   fi
fi

