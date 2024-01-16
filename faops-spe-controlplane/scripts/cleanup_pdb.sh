#!/bin/bash
PDB_NAME=apexpdb

function check_version() {
source /home/oracle/.bash_profile
VER=$(sqlplus -version |grep -i 19 |grep -v SQL|awk '{print $2}')
if [ "${VER}" == "19.14.0.0.0" ]
then
  cleanup
else
  echo ${VER} "is lower than 19c. Please verify before executing the clean up script"
  exit 1
fi  
}

function cleanup() {
echo "Cleaning up the expdir"
cd /u01/app/oracle/expdir/
rm *
echo "Dropping the ${PDB_NAME}"  
sqlplus -s / as sysdba << EOF
spool drop_${PDB_NAME}.log
alter pluggable database ${PDB_NAME} close;
drop pluggable database ${PDB_NAME} including datafiles;
select name,open_mode from v\$pdbs;
EOF
}

check_version
