#!/bin/bash

source $HOME/.bash_profile

DATE=$(date +'%Y%m%d_%H%M%S')
HOSTNAME=$(hostname -f)
PDB_NAME=apexpdb
EXP_BASE_DIR='/u01/app/oracle/expdir'
LOGFILE=faops_import_${DATE}.log
FAOPS_PASS=$(echo $4 | base64 -d)
CATALOG_URL="https://catalogdb-dev-oci.falcm.ocs.oc-test.com"

function pre_tasks() {
  #Verify if the service is running
  if [ -z ${SERVICENAME} ]
   then
     echo "Service ${SERVICENAME} is not running" | tee ${EXP_BASE_DIR}/${LOGFILE}
     exit 1
  fi

  # Creating Import Directory
  if [ -d "/u01/app/oracle/expdir" ]
  then
      echo "Directory $EXP_BASE_DIR already exists." | tee ${EXP_BASE_DIR}/${LOGFILE}
  else
      echo "Creating directory $EXP_BASE_DIR"
      mkdir -p $EXP_BASE_DIR
  fi

  #Verify if import parameter file exists else create it
  echo "Creating parameter file" | tee ${EXP_BASE_DIR}/${LOGFILE}
  if [ -f "/u01/app/oracle/expdir/faops_imp.par" ]
  then
      echo "Parameter file faops_imp.par already exists." | tee ${EXP_BASE_DIR}/${LOGFILE}
  else
      echo "Creating parameter file faops_imp.par" | tee ${EXP_BASE_DIR}/${LOGFILE}
      echo -e "directory=faops_imp \ndumpfile=faops_exp%U.dmp \nlogfile=faops_imp.log \ncontent=all \nCLUSTER=N \nparallel=8 \nexclude=table:\"like 'BIN$%'\" \nexclude=sequence:\"like 'BIN$%'\" \nexclude=view:\"like 'BIN$%'\" \nexclude=type:\"like 'BIN$%'\" \nTABLE_EXISTS_ACTION=replace" > ${EXP_BASE_DIR}/faops_imp.par
      echo "Creating parameter file faops_mdjsontab_imp.par" | tee ${EXP_BASE_DIR}/${LOGFILE}
      echo -e "directory=faops_imp \ndumpfile=faops_mdjsontab_exp%U.dmp \nlogfile=faops_mdjsontab_imp.log \ncontent=all \nCLUSTER=N \nparallel=8 \nTABLE_EXISTS_ACTION=replace" > ${EXP_BASE_DIR}/faops_mdjsontab_imp.par
  fi
}

function download() {
  #Download the dump files from OSS
  cd $EXP_BASE_DIR
  echo "Verifying zip file" | tee ${EXP_BASE_DIR}/${LOGFILE}
  CHECK=$(unzip -q -t /tmp/FAOPS_EXP_DMP.zip 2>/dev/null)
  if [[ "$CHECK" =~ "No errors" ]];then
    echo "Unzipping dump files" | tee ${EXP_BASE_DIR}/${LOGFILE}
    unzip -o /tmp/FAOPS_EXP_DMP.zip 
  else
    echo "Downloaded Dump file zip is corrupted" | tee ${EXP_BASE_DIR}/${LOGFILE}
    exit 1
  fi
}

function db_tasks() {
  #Create a temporary account, directory and execute import of the FAOPS schema
  echo "Creating directory within Oracle and granting privs to temp user schema" | tee ${EXP_BASE_DIR}/${LOGFILE}
  sqlplus -s / as sysdba << EOF
  spool  /u01/app/oracle/expdir/database.log
  alter session set container=${PDB_NAME};
  create user upguser identified by upguser default tablespace faopscbdb quota unlimited on faopscbdb;
  grant connect,resource to upguser;
  alter user upguser account unlock;
  grant dba to upguser;
  create or replace directory faops_imp as '/u01/app/oracle/expdir';
  spool off
EOF

  echo "Changing directory to /tmp/expdir" | tee ${EXP_BASE_DIR}/${LOGFILE}
  cd  $EXP_BASE_DIR

  echo "Running Import of FAOPS schema" | tee ${EXP_BASE_DIR}/${LOGFILE}
  impdp userid=upguser/upguser@//$HOSTNAME/$SERVICENAME parfile=faops_imp.par
  echo "Running Import of FAOPS mdjsontab table" | tee ${EXP_BASE_DIR}/${LOGFILE}
  impdp userid=upguser/upguser@//$HOSTNAME/$SERVICENAME parfile=faops_mdjsontab_imp.par
}

function post_tasks() {
  # Verify if there were any errors in the log else drop the temporary user
  ORA_ERR="$(grep ORA- $EXP_BASE_DIR/faops_imp.log | grep -v ORA-31684 |wc -l)"
  if [ "$ORA_ERR" != "0" ]
    then
        echo "Errors found in log faops_imp.log, ending this session" | tee ${EXP_BASE_DIR}/${LOGFILE}
        exit 1
      else
        echo "No errors found. Dropping the upguser from database" | tee ${EXP_BASE_DIR}/${LOGFILE}
        sqlplus -s / as sysdba << EOF
        alter session set container=${PDB_NAME};
        drop user upguser;
EOF
  fi
}

function create_pdb() {
  #Create pluggable database, FAOPS schema
  sqlplus -s / as sysdba << EOF
  spool create_${PDB_NAME}.log
  CREATE PLUGGABLE DATABASE $1 ADMIN USER $2 IDENTIFIED BY $3;
  ALTER PLUGGABLE DATABASE $1 OPEN;
  ALTER PLUGGABLE DATABASE $1 SAVE STATE;
  select name,open_mode from v\$pdbs;
  ALTER SESSION SET CONTAINER=$1;
  ADMINISTER KEY MANAGEMENT SET KEY USING TAG '${PDB_NAME}tag' FORCE KEYSTORE IDENTIFIED BY $3 WITH BACKUP USING 'walletbackup-${PDB_NAME}';
  ALTER SESSION SET CONTAINER=$1;
  create tablespace faopscbdb datafile '+DATA' size 2G autoextend on next 100m maxsize unlimited;
  create user faops identified by ${FAOPS_PASS} DEFAULT TABLESPACE faopscbdb QUOTA UNLIMITED ON faopscbdb;
  grant connect,resource to faops;
  ALTER USER faops ACCOUNT UNLOCK;
  alter profile DEFAULT limit PASSWORD_REUSE_TIME unlimited;
  alter profile DEFAULT limit PASSWORD_LIFE_TIME  unlimited;
  ALTER PROFILE default LIMIT FAILED_LOGIN_ATTEMPTS UNLIMITED;
  spool off;
EOF
}

echo "Importing FAOPS schema into the catalogdb"
echo "Downloading and verifying the data dump from OSS" | tee ${EXP_BASE_DIR}/${LOGFILE}
download
echo "Creating ${PDB_NAME} and user schema"
create_pdb $*
SERVICENAME=$(lsnrctl status |grep -i ${PDB_NAME} | awk '{print $2}'|sed 's/"//g')
echo "Performing the pre-check tasks"
pre_tasks
echo "Performing the db tasks" | tee ${EXP_BASE_DIR}/${LOGFILE}
db_tasks
echo "Performing the post-check tasks" | tee ${EXP_BASE_DIR}/${LOGFILE}
post_tasks
