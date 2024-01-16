#!/bin/bash -x
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh


function set_env() {
    dbname=$1
    CRSOUT=${EXA_LOGS_DIR}/crsctl_output.json
    OLSOUT=${EXA_LOGS_DIR}/ols_nodes.json
    ORACLE_UNQNAME=$(jq -r ".\"$dbname\".db_unique_name" $CRSOUT)

    if [[ $ORACLE_UNQNAME == *"_dr" ]];then
        #need to validate for dr pods
        # dr_dbname=$(cat ${EXA_LOGS_DIR}/crsctl_output.json | jq -r ".[].\"$dbname\".db_name")
        dr_dbname=$(cat ${EXA_LOGS_DIR}/crsctl_output.json | jq -r ". |select(.\"$dbname\") | .\"$dbname\".db_name")
        ORA_DB_NAME=$(jq -r ".\"$dr_dbname\".db_name" $CRSOUT)
        ORACLE_SHORT_HOSTNAME=$(hostname -s)
        NODE_NUM=$(jq -r ".[] | select(."node_name"==\"$ORACLE_SHORT_HOSTNAME\") | ."node_num"" $OLSOUT)
        # ORA_DB_SID="${dr_dbname}${NODE_NUM}"
        #dr_dbname=$(echo $DB_NAME| sed 's/_dr//'g)
        # ORA_DB_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $dr_dbname )
        # SID_LIST=$(jq ".\"$.db_sid_list\".db_home" $CRSOUT)
        # IFS=, read -r -a SIDLIST <<<"$(jq -r ".\"$dbname\".db_sid_list" $CRSOUT)"
        SIDLIST=$(jq -r ".\"$dbname\".db_sid_list" $CRSOUT | sed "s/,/ /g")
        for SIDVAL in $SIDLIST;do
            if [[ ! -z "$SIDVAL" ]];then
             CHECK_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $ORA_DB_NAME | grep -w $SIDVAL )
             if [[ ! -z "$CHECK_SID" ]];then
                ORACLE_SID=$CHECK_SID
                break
             fi
            fi
        done
        ORA_HOME=$(jq -r ".\"$dbname\".db_home" $CRSOUT)
    else
        # ORA_DB_NAME=$(cat ${EXA_LOGS_DIR}/crsctl_output.json | jq -r ".[].\"$dbname\".db_name")
        #ORA_DB_NAME=$(cat ${EXA_LOGS_DIR}/crsctl_output.json | jq  -r ".[] |select(.\"$dbname\") | .\"$dbname\".db_name")
        ORA_DB_NAME=$(jq -r ".\"$dbname\".db_name" $CRSOUT)
        ORACLE_SHORT_HOSTNAME=$(hostname -s)
        NODE_NUM=$(jq -r ".[] | select(."node_name"==\"$ORACLE_SHORT_HOSTNAME\") | ."node_num"" $OLSOUT)
        # ORA_DB_SID="${ORA_DB_NAME}${NODE_NUM}"
        # ORA_DB_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $ORA_DB_NAME)
        # SID_LIST=$(jq ".\"$.db_sid_list\".db_home" $CRSOUT)
        # IFS=, read -r -a SIDLIST <<<"$(jq -r ".\"$dbname\".db_sid_list" $CRSOUT)"
        SIDLIST=$(jq -r ".\"$dbname\".db_sid_list" $CRSOUT | sed "s/,/ /g")
        for SIDVAL in $SIDLIST;do
            if [[ ! -z "$SIDVAL" ]];then
             CHECK_SID=$(ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3| grep $ORA_DB_NAME | grep -w $SIDVAL )
             if [[ ! -z "$CHECK_SID" ]];then
                ORACLE_SID=$CHECK_SID
                break
             fi
            fi
        done
        # 
        
        
        ORA_HOME=$(jq -r ".\"$dbname\".db_home" $CRSOUT)
    fi

    

    if [ ! -z "$ORA_HOME" ] && [ ! -z "$ORACLE_SID" ];then
        export ORACLE_UNQNAME=$ORACLE_UNQNAME
        export ORACLE_HOME=$ORA_HOME
        export OH=$ORA_HOME
#         export ORACLE_BASE="/u02/app/oracle"
        export PATH=$ORACLE_HOME/bin:$ORACLE_HOME/bin/OPatch:$PATH
        export LD_LIBRARY_PATH=$ORACLE_HOME/lib
        export ORACLE_HOSTNAME=$(hostname -f)
        export ORACLE_SID=$ORACLE_SID
    fi
}

db_name=$1

[ `whoami` != "oracle" ] && echo "Error: this script should be executed as oracle." && exit 1
if [[ -z "$db_name" ]]; then
    :
else
    set_env $db_name
fi
