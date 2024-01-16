#!/bin/bash
#########################################################################
#
# rman_wrapper_oss.sh.sh: Wrapper of rman_wrapper_oss.sh used to take backup of database.
#
# Saritha Gireddy - 09/17/2020 created
# Zakki Ahmed - 10/01/2021 - updates
# Zakki Ahmedd - 03/01/2022 - Bug 33883250
# Vipin Azad   - 05/01/2023 - Bug 35246879
#########################################################################
BASE_DIR="/opt/faops/spe/ocifabackup"
BACKUP_LOGS_BASE_DIR="/u02/backup/log/$(hostname -s)"
EXA_LOGS_DIR="${BACKUP_LOGS_BASE_DIR}/exalogs"
BACKUP_ARTIFACTS_PATH="/fss/oci_backup/artifacts/$(hostname -s)"
source ${BASE_DIR}/lib/python/common/setpyenv.sh
source ${BASE_DIR}/utils/db/scripts/shell/env.sh
JQ_TOOL="${BASE_DIR}/utils/jq"
validate_json="${BASE_DIR}/config/db/backup_priority.json"
validate_lock="${EXA_LOGS_DIR}/.validate_lock"
validate_queue_flag=$("${JQ_TOOL}" -r '.Validate_backup_priority_enabled' ${validate_json})
validate_delta=$(date --date="4 days ago" +%s) 
# Check invokation
# if [ -t 1 ] ; then 
#     export BKP_INVOCATION="manual"
# else
#     export BKP_INVOCATION="cron"
# fi

function pre_checks() {
    [ `whoami` != "root" ] && echo "Error: this script should be executed as root." && exit 1
    # 
    if [ ! -z $ADP_ENABLED ];then
        if [ $ADP_ENABLED == "True" ] || [ $ADP_ENABLED == "true" ];then
            echo "Error: this exa is ADP enabled." && exit 1
        fi
    fi
    #
    if [[ ! -d $EXA_LOGS_DIR ]];then
        mkdir -p $EXA_LOGS_DIR
        chown -Rh oracle:oinstall $EXA_LOGS_DIR
    fi
    # 
    if [[ -f /tmp/libopc.so ]];then
        chown -Rh oracle:oinstall /tmp/libopc.so
    fi
    # 
    if [[ -d ${BASE_DIR}/config/db ]];then
        chown -Rh oracle:oinstall ${BASE_DIR}/config/db
    fi
    # 
    if [[ ! -d $BACKUP_ARTIFACTS_PATH ]];then
        mkdir -p $BACKUP_ARTIFACTS_PATH
        chown -Rh oracle:oinstall ${BACKUP_ARTIFACTS_PATH}
    fi
    # 
    if [[ -f ${BASE_DIR}/config/db/sre_db.cfg ]];then
        # bug 33883250 
        sed -i -e 's/bkup_oss_recovery_window=30/bkup_oss_recovery_window=61/g' ${BASE_DIR}/config/db/sre_db.cfg
        cp -P ${BASE_DIR}/config/db/sre_db.cfg ${BACKUP_ARTIFACTS_PATH}/bkup_ocifsbackup_sre.cfg
        chown -Rh oracle:oinstall ${BACKUP_ARTIFACTS_PATH}
    fi
    #precheck for validate queue backup priority enablement
    if [ "$validate_queue_flag" = false ]; then
        if [[ "$1" = "--action=validate" || "$1" = "--action=restore_validate" ]] ;then
            if [[ -e "$validate_lock" ]];then
                file_time=$(stat -c '%Y' ${validate_lock})
                if [[ "$file_time" < "$validate_delta" ]];then
                    touch "$validate_lock" && echo "Validae backup can proceed";
                else
                    echo "Error: validate queue flag is disabled, multiple validate backup iteration not allowed" && exit 1
                fi
            else
                touch "$validate_lock" && echo "Validate backup can proceed";
            fi
        fi
    fi

    # fix exalogs dir permissions
    chown -Rh oracle:oinstall $EXA_LOGS_DIR
    # cleanup aud files #!/bin/bash
    # find /u02/app/oracle/product/*/*/rdbms/audit/ -name *.aud -type f -mtime +3 | xargs rm -fr

}



function verify_config-oci() {
    PREV_DIR="/usr/local/bin/SRE/SRA_HOME/ocifsbackup"
    if [[ ! -f $BASE_DIR/config/wallet/config-oci.json ]];then
        $BASE_DIR/lib/python/common/load_oci_config.py
        # pem
        if [[ -f $BASE_DIR/config/wallet/oci_api_key.pem ]];then
            verify_pem=$(openssl rsa -in ${BASE_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
            if [[ ! -z "$verify_pem" ]];then
                :
            elif [[ -f ${PREV_DIR}/config/wallet/oci_api_key.pem ]];then
                verify_pem=$(openssl rsa -in ${PREV_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
                if [[ ! -z "$verify_pem" ]];then
                    cp -P ${PREV_DIR}/config/wallet/oci_api_key.pem ${BASE_DIR}/config/wallet
                    cp -P ${PREV_DIR}/config/wallet/config-oci.json ${BASE_DIR}/config/wallet
                fi
            fi
        elif [[ -f ${PREV_DIR}/config/wallet/oci_api_key.pem ]];then
            verify_pem=$(openssl rsa -in ${PREV_DIR}/config/wallet/oci_api_key.pem  -check 2>/dev/null | grep "RSA key ok")
            if [[ ! -z "$verify_pem" ]];then
                cp -P ${PREV_DIR}/config/wallet/oci_api_key.pem ${BASE_DIR}/config/wallet
                cp -P ${PREV_DIR}/config/wallet/config-oci.json ${BASE_DIR}/config/wallet
            fi
        fi
    fi
}
# temp fix to capture ldb_exec_states.csv
function preserve_key_files() {
    DATE=$(date +'%Y%m%d_%H%M%S')
    # ldb_exec_states.csv
    if [[ -f $EXA_LOGS_DIR/ldb_exec_states.csv ]];then
        cp -P ${EXA_LOGS_DIR}/ldb_exec_states.csv ${EXA_LOGS_DIR}/ldb_exec_states_${DATE}.csv
        # clear ldb_exec_states file on Fridays
        DAY=$(date +'%a')
        HOUR=$(date +'%H')
        if [ "${DAY}" == "Fri" ] && [ "$HOUR" == "20" ];then
            rm -f ${EXA_LOGS_DIR}/ldb_exec_states.csv
        fi
    fi
    # 
    if [[ -f $EXA_LOGS_DIR/ldb_exec_states_v2.csv ]];then        
        cp -P ${EXA_LOGS_DIR}/ldb_exec_states_v2.csv ${EXA_LOGS_DIR}/ldb_exec_states_v2_${DATE}.csv
        # clear ldb_exec_states file on Fridays
        DAY=$(date +'%a')
        HOUR=$(date +'%H')
        if [ "${DAY}" == "Fri" ] && [ "$HOUR" == "20" ];then
            rm -f ${EXA_LOGS_DIR}/ldb_exec_states_v2.csv
        fi
    fi
    

    # process_list
    if [[ -f $EXA_LOGS_DIR/process_list.txt ]];then
        cp -P ${EXA_LOGS_DIR}/process_list.txt ${EXA_LOGS_DIR}/process_list.txt_${DATE}.txt
    fi
}
#
pre_checks $1
# start network monitoring

# verify config-oci.json - restore configs only for saasfa* tenancies(rkadam)
verify_config-oci
#
preserve_key_files
# fix permissions - pre-run
if [[ -d $BASE_DIR/config ]];then
    chown -Rh oracle:oinstall $BASE_DIR/config
fi
# run backup
option=$2
EXA_LOGS_DIR="/u02/backup/log/$(hostname -s)/exalogs"
if [[ ! -d $EXA_LOGS_DIR ]];then
    mkdir -p $EXA_LOGS_DIR
fi
DATE=$(date +'%Y%m%d_%H%M%S')
BKUP_RUN_LOG="${EXA_LOGS_DIR}/rman_wrapper_oss_run_${DATE}.log"
if [ -z "$SCRIPT" ];then
    if [[ "$option" == "wallet_artifacts" ]];then
        WALLET_RUN_LOG="${EXA_LOGS_DIR}/rman_wrapper_wallet_backup_run_${DATE}.log"
        WALLET_CLEANUP_LOG_OSS="${EXA_LOGS_DIR}/rman_wrapper_wallet_cleanup_oss_${DATE}.log"
        WALLET_CLEANUP_LOG="${EXA_LOGS_DIR}/rman_wrapper_wallet_cleanup_fss_${DATE}.log"
        # perform artifacts backup
        /usr/bin/script -f $WALLET_RUN_LOG /bin/bash -c "$BASE_DIR/bin/db_wallet_backup.py --action backup -t oss"
        # perform artifacts cleanup older than 60 days
        /usr/bin/script -f $WALLET_CLEANUP_LOG_OSS /bin/bash -c "/opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action cleanup -t oss"
        /usr/bin/script -f $WALLET_CLEANUP_LOG /bin/bash -c "/opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action cleanup"
        # perform artifacts backup
        ARTIFACTS_RUN_LOG="${EXA_LOGS_DIR}/rman_wrapper_artifacts_backup_run_${DATE}.log"
        ARTIFACTS_CLEANUP_LOG_OSS="${EXA_LOGS_DIR}/rman_wrapper_artifacts_cleanup_oss_${DATE}.log"
        ARTIFACTS_CLEANUP_LOG="${EXA_LOGS_DIR}/rman_wrapper_artifacts_cleanup_fss_${DATE}.log"

        /usr/bin/script -f $ARTIFACTS_RUN_LOG /bin/bash -c "$BASE_DIR/bin/db_artifacts_backup.py --action backup -t oss"
        # perform artifacts cleanup older than 60 days
        /usr/bin/script -f $ARTIFACTS_CLEANUP_LOG_OSS /bin/bash -c "/opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action cleanup -t oss"
        /usr/bin/script -f $ARTIFACTS_CLEANUP_LOG /bin/bash -c "/opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action cleanup"

    else
        /usr/bin/script -f $BKUP_RUN_LOG /bin/bash -c "${BASE_DIR}/bin/rman_wrapper.py $*"
    fi
    # exit 0
fi

# fix permissions - post-run
if [[ -d $BASE_DIR/config ]];then
    chown -Rh oracle:oinstall $BASE_DIR/config
    chown -Rh oracle:oinstall $BACKUP_LOGS_BASE_DIR
fi
# Finish network monitoring
