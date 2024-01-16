#!/bin/bash
# #################################################
# To be run by ROOT user
#                                      
# Author:       Jayant Mahishi        
# Description:  To download, configure OPC Backup libraries for FA databases - SOEDEVSECOPS-1792
# Created:      04/26/22           
# Modified: 
#
# #################################################

#Variables used in the script
GREEN='\e[32m'
YELLOW='\e[33m'
RED='\e[31m'
NC='\e[0m'
OPC_SETUP_INFO="${GREEN}[INFO]${NC}  [opc_setup_info] - "
OPC_SETUP_WARN="${YELLOW}[WARN]${NC}  [opc_setup_info] - "
OPC_SETUP_ERR="${RED}[ERR]${NC}  [opc_setup_info] - "
# FILE_NAME="opc_install.zip"
BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
FILE_DOWNLOAD_PATH="/tmp"
FILE_LOCAL_PATH="${BACKUP_BASE_DIR}/config"
METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
HOST_TYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
REGION=$(echo "${INST}"| "${JQ_TOOL}" -r '.canonicalRegionName')
realm=$(echo "${INST}"| "${JQ_TOOL}" -r '.regionInfo.realmKey')
DATE=$(date +'%Y%m%d_%H%M%S')
if [ -z $1 ];then
  echo -e "${OPC_SETUP_ERR}The dbname was not passed as an argument while executing opc_install. Please verify"
  exit 1
else 
  DBNAME=$1
fi
ENV_FILE="/opt/faops/spe/ocifabackup/utils/db/scripts/shell/env.sh"
source /opt/faops/spe/ocifabackup/utils/db/scripts/shell/env.sh
OPC_LIB_PATH="/var/opt/oracle/dbaas_acfs/oci_backup"
EXA_OPC_FABKP_CONFIG="${OPC_LIB_PATH}/${DBNAME}"
EXA_DB_LIB="${EXA_OPC_FABKP_CONFIG}/lib"
EXA_DB_WALLET="${EXA_OPC_FABKP_CONFIG}/wallet"
EXA_DB_ORA="${EXA_OPC_FABKP_CONFIG}/opc${DBNAME}.ora"
LOGFILE=${DBNAME}_opc_backup_install_${DATE}.log
OPC_CONFIG_LOG=${DBNAME}_opc_backup_config_${DATE}.log
DB_CONFIG="${BACKUP_BASE_DIR}/config/db/db_config.json"
#OPC_LIBRARIES="opc_install_lib_latest.zip"
OPC_LIBRARIES="opc_linux64.zip"
OPC_JAR_INSTALL="opc_installer.zip"

# For DBAAS we don't need this block so commenting out
# if [[ "${HOST_TYPE}" != *"Exa"* ]];then
#   echo -e "${OPC_SETUP_INFO}This is not an Exadata host. Skipping OPC libopc.so config."
#   exit 1
# fi   
if [ -z $2 ];then
  echo -e "${OPC_SETUP_ERR}The /opt/faops/spe/ocifabackup/config/db/sre_db{prod/stage}.cfg was not passed as an argument while executing opc_install. Please verify."
  exit 1
else
  DB_CONFIG_FILE=$2
fi  
#if [ -z $3 ];then
#  echo -e "${OPC_SETUP_ERR} Bucket name is not present. Please verify and reinitiate the backup"
#  exit 1
#else
#  BKUP_OSS_CONTAINER=$3
#fi  
#End of Variables block

function log()
{
  local status=$1
  local sleep_seconds="$2 secs"
  if [ "$status" == "SLEEP STOP" ];then local message="Starting downloading lib files ";else local message="Starting to sleep for";fi

  echo "$status : $message - $sleep_seconds"
  logger "`hostname` -> ocifsbackup -> $status -> `date`"
}

function sleeper(){
  octet=$( hostname -i|cut -d'.' -f4 )
  mod_octet=$((octet%2))

  local r=$(( $RANDOM % 60 +1))

  if [[ $mod_octet -eq 1 ]];then
    sleep_time=$r
  else
    sleep_time=`expr $r + 300`
  fi

  log "SLEEP START" $sleep_time
  sleep $sleep_time
  log "SLEEP STOP" $sleep_time

}


function pre_tasks() {
  if [ -f ${ENV_FILE} ]
    then
      source ${ENV_FILE}
    else
      EXA_LOGS_DIR=/u02/backup/log/$(hostname -s)/exalogs
  fi
  echo -e "${OPC_SETUP_INFO}Verify if ${DB_CONFIG_FILE} file exists" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  if [ -f ${DB_CONFIG_FILE} ]
    then
      BKUP_OSS_URL=$(cat ${DB_CONFIG_FILE} |grep -i bkup_oss_url | cut -d = -f2 | sed 's|\(.*\)/.*|\1|')
      BKUP_OSS_USER=$(cat ${DB_CONFIG_FILE} |grep -i bkup_oss_user | cut -d = -f2)
      BKUP_OSS_PASS=$(cat ${DB_CONFIG_FILE} |grep -i bkup_oss_passwd | cut -d = -f2 | sort --unique)
      if [ -z $3 ];then
        BKUP_OSS_CONTAINER=$(cat ${DB_CONFIG_FILE} |grep -i bkup_oss_url | cut -d = -f2 | sed 's|.*/||' )
      else
        BKUP_OSS_CONTAINER=$3
      fi  
  else
       echo -e "${OPC_SETUP_ERR}${DB_CONFIG_FILE} do not exist. Please verify and rerun the backup" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
       exit 1
  fi

  if [[ -n $BKUP_OSS_URL ]]
    then
      echo -e "${OPC_SETUP_INFO}Populated OSS URL from ${DB_CONFIG_FILE}." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_ERR} OSS URL is missing from ${DB_CONFIG_FILE}. Exiting the script" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
  fi

  if [[ -n $BKUP_OSS_USER ]]
    then
      echo -e "${OPC_SETUP_INFO}Populated OSS User from ${DB_CONFIG_FILE}." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_ERR} OSS User is missing from ${DB_CONFIG_FILE}. Exiting the script" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
  fi

  if [[ -n $BKUP_OSS_CONTAINER ]]
    then
      echo -e "${OPC_SETUP_INFO}Populated OSS Container from ${DB_CONFIG_FILE}." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_ERR} OSS Container is missing from ${DB_CONFIG_FILE}. Exiting the script" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
  fi

  if [[ -n $BKUP_OSS_PASS ]]
    then
      echo -e "${OPC_SETUP_INFO}Populated OSS User password from ${DB_CONFIG_FILE}." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_ERR} OSS User password is missing from ${DB_CONFIG_FILE}. Exiting the script" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
  fi

  if [ -d ${EXA_OPC_FABKP_CONFIG} ]
  then
    echo -e "${OPC_SETUP_INFO}Directory ${EXA_OPC_FABKP_CONFIG} already exists." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  else
    echo -e "${OPC_SETUP_INFO}Creating directory ${EXA_OPC_FABKP_CONFIG}"
    mkdir -p ${EXA_OPC_FABKP_CONFIG}
  fi

  if [ -d ${EXA_DB_WALLET} ]
  then
    echo -e "${OPC_SETUP_INFO}Directory ${EXA_DB_WALLET} already exists." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  else
    echo -e "${OPC_SETUP_INFO}Creating directory ${EXA_DB_WALLET}" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    mkdir -p ${EXA_DB_WALLET}
  fi

  if [ -d ${EXA_DB_LIB} ]
  then
    echo -e "${OPC_SETUP_INFO}Directory ${EXA_DB_LIB} already exists." | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  else
    echo -e "${OPC_SETUP_INFO}Creating directory ${EXA_DB_LIB}" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    mkdir -p ${EXA_DB_LIB}
  fi
}

get_lib_opc_url()
{
    FILE_NAME=$2
    lib_name="$(echo "$FILE_NAME" | awk -F. '{print $1}')"
    LIB_URL="$(cat ${DB_CONFIG} | jq -r ".opc_lib_urls.$realm.$lib_name[$1|tonumber]")"
    LIB_OPC_URL="${LIB_URL}${FILE_NAME}"
    if [[ ! -z ${LIB_OPC_URL} ]];then
      echo -e "${OPC_SETUP_INFO} lib opc download url set " | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_ERR} lib download url is not set check fun - get_lib_opc_url" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
    fi
}

download() {
  local url="$1"
  local dest="${FILE_DOWNLOAD_PATH}"
  local filename=$(echo $url | awk -F'/' '{print $NF}')
  sleeper
  local artifact_response_oss=$(curl --connect-timeout 30 --retry 3  -o "$dest/$filename" -s -L -w "%{http_code}" --fail "${LIB_OPC_URL}" 2>/dev/null)
  if [ "$artifact_response_oss" != "200" ]; then
      get_lib_opc_url "1" $filename
      echo -e "${OPC_SETUP_INFO} 1st retry for lib opc download" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      local artifact_response=$(curl --connect-timeout 30 --retry 3 -o "$dest/$filename" -s -L -w "%{http_code}" --fail "${LIB_OPC_URL}" 2>/dev/null)
      if [ "$artifact_response" != "200" ]; then
        get_lib_opc_url "2" $filename
        echo -e "${OPC_SETUP_INFO} 2nd retry for lib opc download" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
        local final_response=$(curl --connect-timeout 30 --retry 3 -o "$dest/$filename" -s -L -w "%{http_code}" --fail "${LIB_OPC_URL}" 2>/dev/null)
        if [ "$final_response" != "200" ]; then
          echo -e "${OPC_SETUP_ERR} Issue downloading $filename from $url. Please verify and rerun the backup" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
          exit 1
        fi
      fi
  fi

  
  if [[ "$filename" = "$OPC_LIBRARIES" ]];then
    CHECK=$(unzip -q -t ${dest}/${filename} 2>/dev/null)
    if [[ "$CHECK" =~ "No errors" ]];then
      echo -e "${OPC_SETUP_INFO}Extracting $filename to $EXA_DB_LIB" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      cp ${FILE_DOWNLOAD_PATH}/${filename} ${FILE_LOCAL_PATH}/${filename}
      unzip -q -o ${FILE_LOCAL_PATH}/${filename} -d $EXA_DB_LIB | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else 
      echo "WARN: ${dest}/${filename} is corrupt, not deploying" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      if [ "$2" -eq 7 ];then
        unzip -q -o ${FILE_LOCAL_PATH}/${filename} -d $EXA_DB_LIB | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      fi
    fi
  elif [[ "$filename" = "$OPC_JAR_INSTALL" ]];then
    CHECK=$(unzip -q -t ${dest}/${filename} 2>/dev/null)
    if [[ "$CHECK" =~ "No errors" ]];then
      echo -e "${OPC_SETUP_INFO}Extracting $filename to $EXA_OPC_FABKP_CONFIG" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      cp ${FILE_DOWNLOAD_PATH}/${filename} ${FILE_LOCAL_PATH}/${filename}
      unzip -q -o ${FILE_LOCAL_PATH}/${filename} -d ${EXA_OPC_FABKP_CONFIG} | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else 
      echo "WARN: ${dest}/${filename} is corrupt, not deploying" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      if [ "$2" -eq 7 ];then
        unzip -q -o ${FILE_LOCAL_PATH}/${filename} -d $EXA_DB_LIB | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      fi
    fi
  fi
  
}


download_lib() {
  if [ -e "${FILE_LOCAL_PATH}/${OPC_LIBRARIES}" ]; then
    FILEAGE=$(( ($(date +%s) - $(stat -c %Y ${FILE_LOCAL_PATH}/${OPC_LIBRARIES})) / 60 ))
    if [ ${FILEAGE} -gt 10080 ]; then
      echo -e "${OPC_SETUP_INFO}local ${OPC_LIBRARIES} is 7 days older downloading latest " | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      file_age=7
      get_lib_opc_url "0" $OPC_LIBRARIES
      download "${LIB_OPC_URL}" $file_age
    else
      echo -e "${OPC_SETUP_INFO}Using local latest  ${OPC_LIBRARIES}" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      unzip -q -o ${FILE_LOCAL_PATH}/${OPC_LIBRARIES} -d ${EXA_DB_LIB}
    fi
  else
    echo -e "${OPC_SETUP_INFO}Downloading ${OPC_LIBRARIES} " | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    get_lib_opc_url "0" $OPC_LIBRARIES
    download "${LIB_OPC_URL}"
  fi
}

config_opc_install() {
  if [ -e "$FILE_LOCAL_PATH/$OPC_JAR_INSTALL" ]; then
    FILEAGE=$(( ($(date +%s) - $(stat -c %Y $FILE_LOCAL_PATH/$OPC_JAR_INSTALL)) / 60 ))
    if [ ${FILEAGE} -gt 10080 ]; then
      echo -e "${OPC_SETUP_INFO}local ${OPC_LIBRARIES} is 7 days older downloading latest " | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      file_age=7
      get_lib_opc_url "0" $OPC_JAR_INSTALL 
      download "${LIB_OPC_URL}" $file_age
    else
      echo -e "${OPC_SETUP_INFO}Using local latest  ${OPC_JAR_INSTALL}" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      unzip -q -o ${FILE_LOCAL_PATH}/${OPC_JAR_INSTALL} -d ${EXA_OPC_FABKP_CONFIG}
      
    fi
  else
    echo -e "${OPC_SETUP_INFO}Downloading ${OPC_JAR_INSTALL} " | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    get_lib_opc_url "0" $OPC_JAR_INSTALL
    download "${LIB_OPC_URL}"
  fi



  cd ${EXA_OPC_FABKP_CONFIG}
  echo -e "${OPC_SETUP_INFO}Configuring opc backup" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  #echo -e "Backup container name is : ${BKUP_OSS_CONTAINER}"
  JAVA_VER=$(java -version 2>&1 >/dev/null | egrep "\S+\s+version" | awk '{print $3}' | tr -d '"')
  if [[ -n ${JAVA_VER} ]] 
    then
      echo -e "${OPC_SETUP_INFO}${JAVA_VER} is installed on this host" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
    else
      echo -e "${OPC_SETUP_INFO}Java is not installed on this host"  | tee -a ${EXA_LOGS_DIR}/${LOGFILE} 
      exit 1
  fi    
  OUTPUT=$(java -jar opc_install.jar -opcId ${BKUP_OSS_USER} -opcPass ${BKUP_OSS_PASS} -container ${BKUP_OSS_CONTAINER} -walletDir ${EXA_DB_WALLET}  -configfile ${EXA_DB_ORA} -host ${BKUP_OSS_URL} | tee -a ${EXA_LOGS_DIR}/${OPC_CONFIG_LOG})
  echo -e "${OPC_SETUP_INFO} Out put of the opc_install.jar execution: ${OUTPUT}"
  # # Not setting _OPC_DEFERRED_DELETE as per MOS note - Backup Files From Container Are not Getting Deleted Using RMAN in DBAAS Cloud (Doc ID 2373877.1)
  ERR="$(grep -i created ${EXA_LOGS_DIR}/${OPC_CONFIG_LOG} |wc -l)"
  if [ "$ERR" != "2" ]
  then
      echo -e "${OPC_SETUP_ERR} Errors found in log ${OPC_CONFIG_LOG}, ending this session" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
      exit 1
  fi

  echo -e "${OPC_SETUP_INFO}Changing permissions to Oracle" | tee -a ${EXA_LOGS_DIR}/${LOGFILE}
  chown -R oracle:oinstall $EXA_OPC_FABKP_CONFIG
}

#Moving existing BKUP API to oracle cloud module
##FLAG_STR=$(/var/opt/oracle/bkup_api/bkup_api bkup_chkcfg --dbname=${DBNAME} |grep "Config files"|cut -d: -f4)
##if [ ${FLAG_STR} == 'yes' ]
##  then
    pre_tasks
    download_lib
    config_opc_install
##  else
##    echo "fa-spe:ERROR: OPC Backup has been configured on this database"
##    exit 1
##fi   