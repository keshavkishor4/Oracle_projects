#!/bin/bash

source $HOME/.bash_profile
#Variables used in the script
DATE=$(date +'%Y%m%d_%H%M%S')
HOSTNAME=$(hostname -f)
PDB_NAME=apexpdb
SERVICENAME=$(lsnrctl status |grep -i ${PDB_NAME} | awk '{print $2}'|sed 's/"//g')
EXP_BASE_DIR='/u01/app/oracle/expdir'
LOGFILE=faops_export_${DATE}.log
CATALOG_URL="https://catalogdb-dev-oci.falcm.ocs.oc-test.com"

function pre_tasks() {
  # Creating Export Directory
  if [ -d "/u01/app/oracle/expdir" ]
  then
      echo "Directory $EXP_BASE_DIR already exists." | tee ${EXP_BASE_DIR}/${LOGFILE}
  else
      echo "Creating directory $EXP_BASE_DIR"
      mkdir -p $EXP_BASE_DIR
  fi
  # Verify if the parameter file exists
  echo "Verifying parameter file" | tee ${EXP_BASE_DIR}/${LOGFILE}
  if [ -f "/u01/app/oracle/expdir/faops_exp.par" ]
  then
      echo "Parameter file faops_exp.par already exists." | tee ${EXP_BASE_DIR}/${LOGFILE}
  else
      echo "Creating parameter file faops_exp.par" | tee ${EXP_BASE_DIR}/${LOGFILE}
      echo -e "directory=faops_exp \ndumpfile=faops_exp%U.dmp \nlogfile=faops_exp.log \nschemas=faops \ncontent=all \nexclude=TABLE:\"= 'MDJSONTAB'\" \nEXCLUDE=STATISTICS \nexclude=table:\"like 'BIN$%'\" \nexclude=sequence:\"like 'BIN$%'\" \nexclude=view:\"like 'BIN$%'\" \nexclude=type:\"like 'BIN$%'\" \nCLUSTER=N \nparallel=8 \nREUSE_DUMPFILES=YES " > ${EXP_BASE_DIR}/faops_exp.par
      echo "Creating parameter file for MDJSONTAB export"
      echo -e "directory=faops_exp \ndumpfile=faops_mdjsontab_exp%U.dmp \nlogfile=faops_mdjsontab_exp.log \ntables=faops.mdjsontab \nquery=\"where CREATED > sysdate - 3\" \ncontent=all \nCLUSTER=N \nparallel=8 \nREUSE_DUMPFILES=YES " > ${EXP_BASE_DIR}/faops_mdjsontab_exp.par
  fi

  # Verifying if export log exists and back it up
  echo "Verifying if old export log file exists and backing it up" | tee ${EXP_BASE_DIR}/${LOGFILE}
  if [ -f "/u01/app/oracle/expdir/faops_exp.log" ]
  then
      echo "Log file faops_exp.log exists, renaming it." | tee ${EXP_BASE_DIR}/${LOGFILE}
      mv /u01/app/oracle/expdir/faops_exp.log /u01/app/oracle/expdir/faops_exp_${DATE}.log
  fi
}

function db_tasks() {
  #Create a temporary account, directory and execute export of the FAOPS schema
  echo "Performing DB tasks, creating a new user, grant privs and create directory" | tee ${EXP_BASE_DIR}/${LOGFILE}
  sqlplus -s / as sysdba << EOF
  spool  /u01/app/oracle/expdir/database.log
  alter session set container=${PDB_NAME};
  create user upguser identified by upguser default tablespace faopscbdb quota unlimited on faopscbdb;
  grant connect,resource to upguser;
  alter user upguser account unlock;
  grant dba to upguser;
  create or replace directory faops_exp as '/u01/app/oracle/expdir';
  spool off
EOF

  echo "Changing directory to /tmp/expdir" | tee ${EXP_BASE_DIR}/${LOGFILE}
  cd  $EXP_BASE_DIR

  echo "Running Export of FAOPS schema" | tee ${EXP_BASE_DIR}/${LOGFILE}
  expdp userid=upguser/upguser@//$HOSTNAME/$SERVICENAME parfile=faops_exp.par
  echo "Running Export of FAOPS mdjsontab table" | tee ${EXP_BASE_DIR}/${LOGFILE}
  expdp userid=upguser/upguser@//$HOSTNAME/$SERVICENAME parfile=faops_mdjsontab_exp.par
}

function post_tasks() {
  # Verify if there were any errors in the log else drop the temporary user
  ORA_ERR="$(grep ORA- $EXP_BASE_DIR/faops_exp.log |wc -l)"
  if [ "$ORA_ERR" != "0" ]
    then
        echo "Errors found in log faops_exp.log, ending this session" | tee ${EXP_BASE_DIR}/${LOGFILE}
        exit 1
      else
        echo "No errors found. Dropping the upguser from database" | tee ${EXP_BASE_DIR}/${LOGFILE}
        sqlplus -s / as sysdba << EOF
        alter session set container=${PDB_NAME};
        drop user upguser;
EOF
  fi
}

function upload() {

  echo "Zipping dump, pararameter and log files" | tee ${EXP_BASE_DIR}/${LOGFILE}
  cd $EXP_BASE_DIR

  zip FAOPS_EXP_DMP.zip *.dmp
  md5sum FAOPS_EXP_DMP.zip | awk '{print $1}' > source_md5.txt
  
}

echo "Exporting FAOPS schema from the catalogdb"
echo "Performing the pre-check tasks" 
pre_tasks
echo "Performing the db tasks" | tee ${EXP_BASE_DIR}/${LOGFILE}
db_tasks
echo "Performing the post-check tasks" | tee ${EXP_BASE_DIR}/${LOGFILE}
post_tasks
echo "Uploading the exported data to OSS" | tee ${EXP_BASE_DIR}/${LOGFILE}
upload