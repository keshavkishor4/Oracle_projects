#!/bin/bash
PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
BASE_DIR="/opt/faops/spe/ocifabackup"
MC_DIR="/var/mcollective"

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

# check for ADP enabled exadatas

if [[ -f ${MC_DIR}/facts.yml ]];then
    ADP_CHECK=$(grep -i "isADP" ${MC_DIR}/facts.yml | awk -F':' '{print $2 }'|sed  "s/'//g")
    if [[ ! -z "${ADP_CHECK}" ]];then
        if [ $ADP_CHECK == "True" ] || [ $ADP_CHECK == "true" ];then
            echo "ERROR: FAOCI Backup RPM is not supported on ADP enabled exadata" && exit 1
        fi
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