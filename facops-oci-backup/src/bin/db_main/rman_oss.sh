#!/bin/bash
BASE_DIR=/opt/faops/spe/ocifabackup
EXA_LOGS_DIR="/u02/backup/log/$(hostname -s)/exalogs"
BACKUP_ARTIFACTS_PATH="/fss/oci_backup/artifacts/$(hostname -s)"
CRSOUT=${EXA_LOGS_DIR}/crsctl_output.json
OLSOUT=${EXA_LOGS_DIR}/ols_nodes.json
source "${BASE_DIR}/utils/db/scripts/shell/env.sh"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPT_NAME=$(basename $0)
LIBOPC_FILE=${BASE_DIR}/config/db/libs/libopc.so
# MD5SUM_LIBOPC_FILE="394abb3e48b1047b142d5b4c225db2fd"
YELLOW='\033[0;33m'
ORANGE='\033[1;33m'
RED='\033[1;31m'
# Check invokation
# if [ -t 1 ] ; then 
#     export BKP_INVOCATION="manual"
# else
#     export BKP_INVOCATION="cron"
# fi

function pre_checks() {
    [ `whoami` != "oracle" ] && echo -e "${ORANGE} Error: this script should be executed as oracle." && exit 1
    # 
    if [ ! -z $ADP_ENABLED ];then
        if [ $ADP_ENABLED == "True" ] || [ $ADP_ENABLED == "true" ];then
            echo "Error: this exa is ADP enabled." && exit 1
        fi
    fi
    #
    if [[ ! -d $EXA_LOGS_DIR ]];then
        mkdir -p $EXA_LOGS_DIR
    fi
    # 
    if [[ ! -f "$CRSOUT" ]];then
        echo -e "${RED} Error, $CRSOUT is not present, ensure you run /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh first as root user"
        exit 1
    fi
    # 
    if [[ -f /tmp/libopc.so ]];then
        chown -Rh oracle:oinstall /tmp/libopc.so
    fi
    # 
    if [[ ! -d $BACKUP_ARTIFACTS_PATH ]];then
        mkdir -p $BACKUP_ARTIFACTS_PATH
        chown -Rh oracle:oinstall ${BACKUP_ARTIFACTS_PATH}
    fi
}

# function sleeper(){
#   ORACLE_SHORT_HOSTNAME=$(hostname -s)
#   NODE_NUM=$(jq -r ".[] | select(."node_name"==\"$ORACLE_SHORT_HOSTNAME\") | ."node_num"" $OLSOUT)

#   local r=$(( $RANDOM % 60 +1))

#   if [[ `expr $NODE_NUM % 2` -eq 0 ]];then
#     sleep_time=$r
#   elif [[ `expr $NODE_NUM % 2` -eq 0 ]] && [[ $NODE_NUM -gt 3 ]]
#     sleep_time= 300
#   elif [[ `expr $NODE_NUM % 2` -eq 0 ]] && [[ $NODE_NUM -gt 5 ]]
#     sleep_time= 600
#   fi

#   log "SLEEP START" $sleep_time
#   sleep $sleep_time
#   log "SLEEP STOP" $sleep_time

# }
function run_backup() {
    dbname=$(echo $1|cut -d'=' -f2)
    bkup_type=$(echo $@|awk -F"-b" '{print $2}'| xargs | awk '{print $1}')
    # source /home/oracle/$dbname.env
    source ${BASE_DIR}/utils/db/scripts/shell/set_ora_env.sh $dbname
    source ${BASE_DIR}/lib/python/common/setpyenv.sh
    export NLS_DATE_FORMAT='DD-MON-YYYY HH24:MI:SS'
    #
    
    # SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3 | grep ${dbname})
    ORA_DB_NAME=$(jq -r ".\"$dbname\".db_name" $CRSOUT)
    ORACLE_SHORT_HOSTNAME=$(hostname -s)
    NODE_NUM=$(jq -r ".[] | select(."node_name"==\"$ORACLE_SHORT_HOSTNAME\") | ."node_num"" $OLSOUT)
    # ORA_DB_SID="${ORA_DB_NAME}${NODE_NUM}"
    # ORA_DB_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $ORA_DB_NAME)
    # SID_LIST=$(jq ".\"$.db_sid_list\".db_home" $CRSOUT)
    # IFS=, read -r -a SIDLIST <<<"$(jq -r ".\"$dbname\".db_sid_list" $CRSOUT)"
    # Adding code to manage empty SIDLIST- Jira task is 1446
    IFS=, read -r SIDLIST <<<"$(jq -r --arg dbname "$dbname" '(.[$dbname] // empty) |.db_sid_list' "$CRSOUT")"
    for SIDVAL in $SIDLIST;do
        if [[ ! -z "$SIDVAL" ]];then
             CHECK_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $ORA_DB_NAME | grep -w $SIDVAL 2> /dev/null )
             if [[ ! -z "$CHECK_SID" ]];then
                ORACLE_SID=$CHECK_SID
                break
             fi
        else
            echo -e "${RED}$dbname is empty so exiting"
            exit 1
            fi
    done
    if [[ -z $ORACLE_SID ]];then
    #    SID="${dbname}_notpresent"
    #    LOGS_DIR="/u02/backup/log/$(hostname -s)/exalogs"
       echo -e "${RED}$dbname is not running on this server , exitting ..."
       exit 1
    else
        LOGS_DIR="/u02/backup/log/$(hostname -s)/${ORACLE_SID}"
        mkdir -p $LOGS_DIR
    fi
    
    # libopc.so delivery
    # 
    if [[ -f ${BASE_DIR}/config/.md5sum_verify.txt ]];then
        MD5SUM_LIBOPC_FILE="$(grep -i libopc.so ${BASE_DIR}/config/.md5sum_verify.txt | awk -F, '{print $2}' 2> /dev/null)"
        TARGET_LIBOPC_FILE="${OPC_LIB_PATH}/${ORA_DB_NAME}/lib/libopc.so"
        TARGET_BKUP_ORA_BASE="/var/opt/oracle/dbaas_acfs/${db_name}/opc"
        MD5_LIBOPC_OUTPUT=$(md5sum ${LIBOPC_FILE} | awk '{print $1}')
        if [ -f $LIBOPC_FILE ] && [ -f $TARGET_LIBOPC_FILE ];then
            chmod 755 $TARGET_LIBOPC_FILE
            MD5_TARGET_LIBOPC_OUTPUT=$(md5sum ${TARGET_LIBOPC_FILE} | awk '{print $1}')
            # 
            if [ "$MD5_LIBOPC_OUTPUT" == "${MD5SUM_LIBOPC_FILE}" ] && [ "$MD5_TARGET_LIBOPC_OUTPUT" != "${MD5SUM_LIBOPC_FILE}" ];then
                yes | cp $LIBOPC_FILE $TARGET_LIBOPC_FILE
            fi
        fi

        #
        if [ -f $LIBOPC_FILE ] && [ -f $TARGET_BKUP_ORA_BASE/libopc.so ];then
            chmod 755 $TARGET_BKUP_ORA_BASE/libopc.so
            MD5_TARGET_BKUP_ORA_BASE=$(md5sum ${TARGET_BKUP_ORA_BASE}/libopc.so | awk '{print $1}')
            if [ -f "$TARGET_BKUP_ORA_BASE/libopc.so" ];then
                if [ "$MD5_LIBOPC_OUTPUT" == "${MD5SUM_LIBOPC_FILE}" ] && [ "$MD5_TARGET_BKUP_ORA_BASE" != "${MD5SUM_LIBOPC_FILE}" ];then
                    yes | cp $LIBOPC_FILE $TARGET_BKUP_ORA_BASE/libopc.so
                fi
            fi
        fi    
    fi
    
    
    DATE=$(date +'%Y%m%d_%H%M%S')
    DB_LOG="${LOGS_DIR}/rman_oss_${ORACLE_SID}_${bkup_type}_run_${DATE}.log"
    # echo $DB_LOG
    if [ -z "$SCRIPT" ];then
        /usr/bin/script -f $DB_LOG /bin/bash -c "${BASE_DIR}/bin/rman_oss.py $*"
        exit 0
    fi
}


# python  /opt/faops/spe/ocifabackup/bin/rman_oss.py $@


action=$1
backup_p=$2
backup_type=$3

if [ ! -z "$action" ] && [ ! -z "$backup_p" ] && [ ! -z "$backup_type" ];then
    pre_checks
    run_backup $*
else
    echo "usage: ./rman_oss.sh --dbname=<dbname> -b <backup>"
    exit 1
fi