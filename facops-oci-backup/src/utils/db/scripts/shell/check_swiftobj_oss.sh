#!/usr/bin/env bash
# ########################################################################            
# Modified               (MM/DD/YY)
# Jayant Mahishi          04/26/22 - SOEDEVSECOPS-1792
# ########################################################################

function check_oss() {
    # if [ -f $HOME/${db_name}.env ]; then
    #     source $HOME/${db_name}.env
    # else
    #     echo "ERROR:$HOME/${db_name}.env not available"
    #     exit 1
    # fi
    source "${BASE_DIR}/utils/db/scripts/shell/env.sh"
    BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
    JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
    source ${PWD}/set_ora_env.sh $db_name
    METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
    HOST_TYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
    OPC_ORA_BASE="/var/opt/oracle/dbaas_acfs/oci_backup/${db_name}/lib"
    BKUP_ORA_BASE="/var/opt/oracle/dbaas_acfs/${db_name}/opc"
    if [[ ! -d "${OPC_ORA_BASE}" && "${HOST_TYPE}" == *"Exa"* ]];then
        echo "${OPC_ORA_BASE} does not exist"
        exit 1
    fi   
    if [ ! -f "$OPC_ORA_BASE/opc${db_name}.ora" ];then
        OPC_ORA_FILE="${BKUP_ORA_BASE}/opc${db_name}.ora"
        OPC_LIB_FILE="${BKUP_ORA_BASE}/libopc.so"
      else
        OPC_ORA_FILE="${OPC_ORA_BASE}/opc${db_name}.ora"  
        OPC_LIB_FILE="${OPC_ORA_BASE}/libopc.so"
    fi
    case "$HOST_TYPE" in
        *"Exa"*) 
            RMAN_CMD="ALLOCATE CHANNEL C1_SBT DEVICE TYPE SBT_TAPE  PARMS 'SBT_LIBRARY=${OPC_LIB_FILE}, ENV=(OPC_PFILE=${OPC_ORA_FILE})';"
            ;;
        *"VM.Standard"*) 
            OPC_FILE=$(ls  /opt/oracle/dcs/commonstore/objectstore/opc_pfile/*/*${db_name}*ora  | tail -1)
            if [[ ! -z $OPC_FILE ]];then 
                OPC_FILE_VAL=$OPC_FILE
            fi
            RMAN_CMD="ALLOCATE CHANNEL C1_SBT DEVICE TYPE SBT_TAPE  PARMS 'SBT_LIBRARY=/opt/oracle/dcs/commonstore/pkgrepos/oss/odbcs/libopc.so, ENV=(OPC_PFILE=${OPC_FILE_VAL})';"
            ;;
        *)
            echo "not a valid host"
            exit 1
            ;;
    esac
    source ${PWD}/set_ora_env.sh $db_name
    #
    if [[ ! -z $ORACLE_SID ]];then
        LOGFILE=${log_path}/${ORACLE_SID}/check_object_storage_conn_${db_name}_${DATE}.log
    else
        echo "environment not set for db ${db_name}"
        exit 1        
    fi
    rman target / log=${LOGFILE} <<EOF
    #rman target /  <<EOF
    run {
         ${RMAN_CMD}
    }
    exit;
EOF
#    OUT=$(grep -i "KBHS-00700" ${LOGFILE})
   OUT=$(grep -i "KBHS-" ${LOGFILE})
   if [[ ! -z $OUT ]];then
    echo $OUT
    exit 1
   fi
}

PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
db_name=$1
log_path=$2
DATE=$(date +"%Y-%m-%d-%H_%M_%S")
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ "${USER}" == "oracle" ]];then
    check_oss
else
    echo "script should be run as oracle user"
    exit 1
fi
