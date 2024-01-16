#!/bin/bash
BASE_DIR=/opt/faops/spe/ocifabackup
SHELL_SCRIPTS_DIR="${BASE_DIR}/utils/db/scripts/shell"
SQL_SCRIPTS_DIR="${BASE_DIR}/utils/db/sql"
RMAN_SCRIPTS_DIR="${BASE_DIR}/utils/db/scripts/rman"
EXA_LOGS_DIR=/u02/backup/log/$(hostname -s)/exalogs
EXA_LOGS_ARCHIVE_DIR=/u02/backup/log/$(hostname -s)/exalogs/archive
BACKUP_CFG_CMD_LOCATION=/var/opt/oracle/ocde/assistants/bkup
BACKUP_CFG_LOCATION=/opt/faops/spe/ocifabackup/config/db
BACKUP_CFG_LOG=$SCRIPT_DIR/backup-cfg_$hostnm.log
BACKUP_ARTIFACTS_PATH="/fss/oci_backup/artifacts/$(hostname -s)"
BKP_API_LOC=/var/opt/oracle/bkup_api
USER=$(whoami)
DATE=$(date +'%Y%m%d_%H%M%S')
OPC_LIB_PATH="/var/opt/oracle/dbaas_acfs/oci_backup"
ADP_ENABLED=`grep -i "isADP" /var/mcollective/facts.yaml | awk -F':' '{print $2 }'|sed  "s/'//g"`
