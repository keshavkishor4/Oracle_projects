#!/bin/bash
#
#   NAME
#     setup_backup_lib_wrapper.sh
#
#   DESCRIPTION
#     setup_backup_lib wrapper script
#
#
#   2020/06/25: Srinivas Nallur
#   2022/08/04: Jayant Mahishi : Modified the file to use opc_libraries
#
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_NAME=$(basename $0)
hostnm=`hostname -s`

source ${SCRIPT_DIR}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh

os_ver=$(uname -r)
if [[ $os_ver =~ "el7" ]];then
    export PYTHONPATH=${BASE_DIR}/utils/python3/el7
elif [[ $os_ver =~ "el6" ]];then
    export PYTHONPATH=${BASE_DIR}/utils/python3/el6
fi
export PATH=$PYTHONPATH/bin:$PATH:${BASE_DIR}/utils
export LD_LIBRARY_PATH=$PYTHONPATH/lib:$LD_LIBRARY_PATH

usage() {
    cat << EOF
    Usage: To be run as root user
         /opt/faops/spe/ocifabackup/utils/db/scripts/shell/setup_backup_lib_wrapper.sh <dbname> <sre_db.cfg>

EOF
    exit 1
}


function pre_checks() {
    if [ ! -z $ADP_ENABLED ];then
        if [ $ADP_ENABLED == "True" ] || [ $ADP_ENABLED == "true" ];then
            echo "Error: this exa is ADP enabled." && exit 1
        fi
    fi
}
restore_backup_oss_passwd(){
    DECRYPT_TOOL=${BACKUP_CFG_LOCATION}/decrypt
    ns=$(grep -i swiftobjectstorage $sre_cfg | awk -F'/' '{print $5}')
    if [ -z ${ns} ];then
        echo "tenancy cannot be determined, ensure $sre_cfg is correctly filled" >> $BACKUP_CFG_LOG
        return 1
    fi
    oss_user=$(grep -i bkup_oss_user $sre_cfg | awk -F'=' '{print $2}')
    if [ -z ${oss_user} ];then
        echo "oss_user cannot be determined, ensure $sre_cfg is correctly filled" >> $BACKUP_CFG_LOG
        return 1
    fi
    
    cd $BASE_DIR/lib/python/db/;python -c "import database_config; database_config.restore_backup_oss_passwd('$sre_cfg');";cd $SCRIPT_DIR

    local downloaded_pwd_file=$?
    if [ $downloaded_pwd_file -ne 0 ]; then
        echo "Failed to download file .passwd.json"
        exit 1
    fi
    backup_oss_passwd=$(cat $BACKUP_CFG_LOCATION/.passwd.json | jq -r '.["'${ns}'"].'${oss_user}'')
    tenancy=$(cat $BACKUP_CFG_LOCATION/.passwd.json | jq -r '.["'${ns}'"].'tenancy'')

    if [ ! -z "${backup_oss_passwd}" ]; then
        passwd=$(${DECRYPT_TOOL} --key ${backup_oss_passwd})
        # echo "bkup_oss_passwd=${passwd}" >> $BACKUP_CFG_LOCATION/sre_db.cfg
        echo "successfully updated bkup_oss_passwd in $sre_cfg " >> $BACKUP_CFG_LOG
        # copy contents to $BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg
        chown root:root $sre_cfg
        chmod 600 $sre_cfg
        #/bin/cp -p $BACKUP_CFG_LOCATION/$sre_cfg $BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg
        #
        rm -f $BACKUP_CFG_LOCATION/.passwd.json
        return 0
    else
        rm -f $BACKUP_CFG_LOCATION/.passwd.json
        echo "backup_oss_password cannot be determined for ${tenancy} in $sre_cfg " >> $BACKUP_CFG_LOG
        return 1
    fi

    rm -f $BACKUP_CFG_LOCATION/.passwd.json
}

remove_backup_oss_passwd()
{
    if [ -f "$sre_cfg" ]; then
        sed -i '/bkup_oss_passwd/d' $sre_cfg
        echo "successfully deleted bkup_oss_passwd in $sre_cfg "
    else
        echo "$sre_cfg file not available" >> $BACKUP_CFG_LOG
    fi
     #if [ -f "$BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg" ]; then
     #   sed -i '/bkup_oss_passwd/d' $BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg
     #   echo "successfully deleted bkup_oss_passwd in $BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg "
    #else
     # echo "$BACKUP_CFG_LOCATION/bkup_ocifsbackup_sre.cfg  file not available"
    #fi
}
[ `whoami` != "root" ] && echo "Error: this script should be executed as root." && exit 1

[ $# -lt 2 ] && usage

#dbname=$2

dbname=$1
sre_cfg=$2

if [ ! -z "$dbname" ] && [ ! -z "$sre_cfg" ];then
    pre_checks
    restore_backup_oss_passwd
    #/var/opt/oracle/ocde/assistants/bkup/bkup -cfg $BACKUP_CFG_LOCATION/sre_db.cfg -dbname=$dbname
    /opt/faops/spe/ocifabackup/utils/db/scripts/shell/opc_install_config.sh $dbname $sre_cfg
    remove_backup_oss_passwd
else
    echo "usage: To be run as root user
         /opt/faops/spe/ocifabackup/utils/db/scripts/shell/setup_backup_lib_wrapper.sh <dbname> <sre_db.cfg with path>"
    exit 1
fi