#!/bin/bash

PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh

function get_gi_home() {

    local bname=`ps -ewaf|grep grid|grep ocssd.bin|grep -v grep|awk '{print $NF}'`
    if [[ "${bname}" != *"ocssd.bin"* ]];then
        bname=`ps -ewaf|grep grid|grep ocssd.bin|grep -v grep|awk '{print $8}'`
    fi  
    local gbin=""

    if [ "$bname" = "" ];  then
        echo "Found crs not running (cannot determine if host is 1st db node ) ..."
    fi

    local gbin=`dirname $bname`

    GI_HOME=`echo "$gbin" | sed -e "s/\/bin$//g"`

    [ ! -d "$GI_HOME" ] && echo "Not able to find proper GI HOME ..."

    [ ! -f "$GI_HOME/bin/olsnodes" ] && echo "Not able to find 'olsnodes' command ..."
}

function gen_crsctl_dump() {
    local GI_BIN=""
    local host=`hostname -s`

    get_gi_home

    GI_BIN="$GI_HOME/bin"
    #generate crsctl dump
    # hang check
    /usr/bin/timeout --signal=10 300 $GI_BIN/crsctl stat res -f > ${EXA_LOGS_DIR}/crsctl_output_${DATE}.txt
    if [[ $? -ne 0 ]];then
        exit 1
    fi
#     Get unique dbs
    UNIQ_DBS=$($GI_BIN/crsctl stat res -t | grep "\.db")
    OUT=""
    for UDB in $UNIQ_DBS;do
        DB_INFO_FILE=${EXA_LOGS_DIR}/.${UDB}.txt
        $GI_BIN/crsctl stat res $UDB -f | tee $DB_INFO_FILE >/dev/null
        if [ -f $DB_INFO_FILE ] && [ $? -eq 0 ];then
          DB_UNIQUE_NAME=$(grep '^DB_UNIQUE_NAME=' $DB_INFO_FILE | awk -F= '{print $2}')
          DB_NAME=$(grep -i '^USR_ORA_DB_NAME=' $DB_INFO_FILE | awk -F= '{print $2}')
          if [[ -z "$DB_NAME" ]];then 
            DB_NAME=$DB_UNIQUE_NAME
          fi
          DB_HOME=$(grep '^ORACLE_HOME=' $DB_INFO_FILE | awk -F= '{print $2}')
          DB_SID_LIST=$(grep -i '^GEN_USR_ORA_INST_NAME@SERVERNAME' $DB_INFO_FILE | awk -F= '{print $2}' |xargs | sed 's/ /,/g')
          DB_HOST_LIST=$(grep -i '^GEN_USR_ORA_INST_NAME@SERVERNAME' $DB_INFO_FILE | awk -F"[()]" '{print $2}' |xargs | sed 's/ /,/g')
          CRS_DB_STATE=$(grep '^STATE=' $DB_INFO_FILE | awk -F= '{print $2}')
           #gen json
           JSON_FMT='
           "%s": { 
               "db_name":"%s",
               "db_unique_name":"%s",
               "db_crs_state":"%s",
               "db_sid_list":"%s",
               "db_host_list":"%s",
               "db_home":"%s"
               }
            \n'
#            printf "$JSON_FMT" "$DB_NAME" "$DB_NAME" "$DB_UNIQUE_NAME" "$DB_SID_LIST" "$DB_HOST_LIST" "$DB_HOME" | jq .
           
           
           if [[ ! -z "$OUT" ]];then 
            OUT="$OUT,$(printf "$JSON_FMT" "$DB_NAME" "$DB_NAME" "$DB_UNIQUE_NAME" "$CRS_DB_STATE" "$DB_SID_LIST" "$DB_HOST_LIST" "$DB_HOME" )"
           else
            OUT="{$(printf "$JSON_FMT" "$DB_NAME" "$DB_NAME" "$DB_UNIQUE_NAME" "$CRS_DB_STATE" "$DB_SID_LIST" "$DB_HOST_LIST" "$DB_HOME" )"
           fi
        fi
    done
    
    OUT="$(echo $OUT | sed 's/.$//g')}}"
#     echo $OUT
    VALID_JSON=$(echo $OUT | jq .)
    if [[ $? -eq 0 ]];then
     echo $OUT | jq -r . | tee ${EXA_LOGS_DIR}/crsctl_output.json
    fi
}

gen_crsctl_dump
