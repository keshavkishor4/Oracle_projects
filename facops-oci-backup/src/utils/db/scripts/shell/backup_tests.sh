#!/bin/bash
# USER=$(whoami)
# DATE=$(date +'%Y%m%d_%H%M%S')
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
EXCEPTIONS_FILE="${BASE_DIR}/config/db/db_backup_exceptions.txt"
BKP_EXCEPTIONS_FILE=${EXCEPTIONS_FILE}.${DATE}
DB_SIZES_CSV="/tmp/db_sizes.csv"
DB_SIZE_JSON="${BASE_DIR}/config/db/db_size.json"
DB_CONFIG_JSON="${BASE_DIR}/config/db/db_config.json"
SMALL_DB=80
MEDIUM_DB=110
LARGE_DB=130
# EXA_LOGS_DIR="/u02/backup/log/$(hostname -s)/exalogs"
# change buckets for /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json
# for node in $(cat dbs_group);do echo "***********$node**********"; ssh $node "sed -i 's/BACKUP_PROD/RMAN_BACKUP/g' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json;sed -i 's/BACKUP_STAGE/RMAN_BACKUP/g' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json ;  sed -i 's/BACKUP_W_PROD/RMAN_WALLET_BACKUP/g' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json ;  sed -i 's/BACKUP_W_STAGE/RMAN_WALLET_BACKUP/g' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json";done

# verify /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json

# for node in $(cat dbs_group);do echo "***********$node - fa_rman_oss_bn **********"; ssh $node "source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh;jq '.[].fa_rman_oss_bn' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json";done
# for node in $(cat dbs_group);do echo "***********$node - fa_rman_oss_bn **********"; ssh $node "source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh;jq '.[].fa_rman_wallet_bn' /opt/faops/spe/ocifabackup/config/faops-backup-oss-info.json" ;done
# set gi home
function get_gi_home() {

    local bname=`ps -ewaf|grep grid|grep ocssd.bin|grep -v grep|awk '{print $NF}'`
    local gbin=""

    if [ "$bname" = "" ];  then
        echo "Found crs not running (cannot determine if host is 1st db node ) ..." 
    fi

    local gbin=`dirname $bname`

    GI_HOME=`echo "$gbin" | sed -e "s/\/bin$//g"`

    [ ! -d "$GI_HOME" ] && echo "Not able to find proper GI HOME ..." 

    [ ! -f "$GI_HOME/bin/olsnodes" ] && echo "Not able to find 'olsnodes' command ..." 
}

GI_BIN=""
host=`hostname -s`
get_gi_home
GI_BIN="$GI_HOME/bin"

# fetch databases
function fetch_db_size() {
    dbname=$1
    source $PWD/set_ora_env.sh $dbname
#     DBVAL=$(sqlplus -S / as sysdba )<<EOF
#     set head off
#     set feed off
#     set serveroutput on
#     declare 
#      v_count_pdbs number;
#      v_db_sum number;
#     begin
#         select count(*) into v_count_pdbs from v$pdbs where name not like '%SEED%' and open_mode='READ WRITE';        
#         if v_count_pdbs > 1 then
#             SELECT ROUND(SUM(bytes)/1024/1024/1024,2) into v_db_sum FROM CDB_DATA_FILES;
#         end if;
#         dbms_output.put_line( v_db_sum );
#     END;
#      /
#      exit;
# EOF
    DB_SIZE=$(sqlplus -S / as sysdba <<EOF
    set head off
    set feed off
    SELECT ROUND(SUM(bytes)/1024/1024/1024,2) FROM CDB_DATA_FILES;
    exit;
EOF
    )
    echo $DB_SIZE | xargs printf "%.*f\n" "$p"

}

function add_db_exceptions() {
    if [[ -f $EXCEPTIONS_FILE ]];then
        cp $EXCEPTIONS_FILE $BKP_EXCEPTIONS_FILE
    fi
    $GI_BIN/srvctl config database -v | awk '{print $1}' | tee -a $EXCEPTIONS_FILE
}
function capture_databases() {

    # declare array
    DB_SIZES_CSV="/tmp/db_sizes.csv"
    touch $DB_SIZES_CSV
    >$DB_SIZES_CSV

    SIDS=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3)
    for SID in $SIDS;do
        db=$(echo $SID | sed 's/.$//')
        OUT=$(fetch_db_size $db)
        if [[ "$OUT" -gt "86" && "$OUT" -lt "96" ]];then
            count=$(grep -i small $DB_SIZES_CSV | wc -l)
            if [[ $count -gt "0" ]];then
                :
            else
                echo "${db},small,${OUT}" | tee -a $DB_SIZES_CSV
            fi
        elif [[ "$OUT" -gt "96" && "$OUT" -lt "97" ]];then
            count=$(grep -i medium $DB_SIZES_CSV | wc -l)
            if [[ $count -gt "0" ]];then
                :
            else
                echo "${db},medium,${OUT}" | tee -a $DB_SIZES_CSV
            fi
        elif [[ "$OUT" -gt "99" ]];then
            count=$(grep -i large $DB_SIZES_CSV | wc -l)
            if [[ $count -gt "1" ]];then
                :
            else
                echo "${db},large,${OUT}" | tee -a $DB_SIZES_CSV
            fi
        fi
    done
}

function remove_testdb_from_exception() {
    for db in $(cat $DB_SIZES_CSV | awk -F, '{print $1}');do
        sed -i "/$db/d" $EXCEPTIONS_FILE      
    done
}

function update_db_size() {
    small_val=$(grep -i small $DB_SIZES_CSV | awk -F, '{print $3}')
    large_val=$( grep -i large $DB_SIZES_CSV | awk -F, '{print $3}' | tail -1)
    small=$(( $small_val + 1 ))
    large=$(( $large_val - 1 ))

    
    if [[ -f $DB_CONFIG_JSON ]];then
        cp $DB_CONFIG_JSON ${DB_CONFIG_JSON}.${DATE}
    fi
    sed -i "s/.*large_db.*/\"large_db\":${large},/" ${DB_CONFIG_JSON}
    sed -i "s/.*small_db.*/\"small_db\":${small}/" ${DB_CONFIG_JSON}

}


function restore_config() {
    # restore db_size.json
    read -r -d '' DB_SIZE_JSON_VAL << DB_SIZE_JSON_VAL
{
  "large_db": 10000,
  "small_db": 1000
}
DB_SIZE_JSON_VAL
    echo $DB_SIZE_JSON_VAL > $DB_SIZE_JSON
    # restore db_backup_exceptions.txt
    echo "exacdb" > $EXCEPTIONS_FILE
}

action=$1

if [[ -z $action ]];then
    echo "error, pass correct option, config or test"
    exit 1
elif [[ "$action" == "config" ]];then
    if [[ "$USER" == "oracle" ]];then
        add_db_exceptions
        capture_databases
        remove_testdb_from_exception
        update_db_size
        echo "---->> db_size.json <<------"
        cat $DB_CONFIG_JSON
        
        echo "---->> $EXCEPTIONS_FILE <<------"
        cat $EXCEPTIONS_FILE

        echo "---->> List of DB's to be backed up <<------"
        cat $DB_SIZES_CSV

    else
        echo "config should be run as oracle user"
        exit 1
    fi
elif [[ "$action" == "test" ]];then
    if [[ "$USER" == "root" ]];then
        echo "---->> testing archivelog run  <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b archivelog_to_oss & 
        sleep 10
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        # 
        echo "---->> incremental run <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss &
        sleep 10
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        # 
        echo "---->> incremental to oss <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b incre_to_oss_arch_to_oss &
        sleep 10
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        # 
        echo "---->> full backup run <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss & 
        sleep 10
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        # 
        echo "---->> verify entries in ldb_csv <<------"
        while true;do
            CHECK=$(su oracle -c 'ssh lcm-exa02-ueyz02 "ps -ef | grep -i rman_oss.py | grep -i python | grep -v grep"')
            if [[ ! -z $CHECK ]];then
                echo "sleeping for 30 sec, $CHECK"; cat $EXA_LOGS_DIR/ldb_exec_states.csv;sleep 30
            else
                break
            fi
        done

        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b archivelog_to_oss &
        sleep 10
        echo "---->> verify entries in ldb_csv <<------"
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
            cat $EXA_LOGS_DIR/ldb_exec_states.csv
        done
        
        echo "---->> backup validate run <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=validate & 
        sleep 10
        while true;do  
            [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done

        echo "---->> backup restore validate run <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh --action=restore_validate & 
        sleep 10
        while true;do  
           [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        #
        # running backup for one db using rman_oss.sh

        # ONE_DB=$(grep -i small $DB_SIZES_CSV| awk -F, '{print $1}' )
        # echo "---->> running rman_oss.sh db_to_oss for ${ONE_DB} <<--------" 
        # su - oracle -c "$BASE_DIR/bin/rman_oss.sh --dbname=${ONE_DB} -b db_to_oss"
        echo "---->> Wallet and Artifact run <<------"
        nohup /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b wallet_artifacts &
        sleep 10
        while true;do  
           [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        echo "---->> Wallet and Artifact run for cleanup<<------"
        nohup /opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action cleanup  -t oss &
        nohup /opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action cleanup  -t oss &
        echo "---->>For FSS<<----"
        nohup /opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action cleanup  -t fss &
        nohup /opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action cleanup  -t fss &
        sleep 10
        while true;do  
           [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        echo "---->> Wallet and Artifact run for List backup<<------"
        nohup /opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action list-backups  -t oss &
        nohup /opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action list-backups  -t oss &
        echo "---->> For FSS<<----"
        nohup /opt/faops/spe/ocifabackup/bin/db_wallet_backup.py --action list-backups  -t fss &
        nohup /opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py --action list-backups  -t fss &
        sleep 10
        while true;do  
           [ ! -z "$(ps -ef | grep -i rman_wrapper.py | grep -i python | grep -v grep)" ] && echo $(ps -ef | grep -i rman) && echo "sleeping for 1 min" && sleep 60 || break
        done
        echo "----> tests complete <---------"

    else
        echo "config should be run as oracle user"
        exit 1
    fi
elif [[ "$action" == "restore" ]];then
    if [[ "$USER" == "oracle" ]];then
        restore_config
    fi
fi

