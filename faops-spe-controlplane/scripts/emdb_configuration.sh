##########################################################################
#  For RAC, when run . oraenv, ORACLE_SID IS the "database unique name", #
#  but beofre run "sqlplus...", the ORACLE_SID must be set to real sid   #
#  The fourth paramemter $4 "RAC" specific code is for this purpose.      #
##########################################################################
#!/bin/bash -x

if [ -z "$2" ]
then
  echo "Usage : $0 <ORACLE_SID> <PASSWORD> <DB_RECOVERY_FILE_DEST_SIZE>G [RAC|SINGLE]"
else
  ORAPWD="$2"
fi

if [ -z "$3" ]
then
  echo "Usage : $0 <ORACLE_SID> <PASSWORD> <DB_RECOVERY_FILE_DEST_SIZE>G [RAC|SINGLE]"
else
  DB_RFDS="$3"
fi

if [ "$4" = "RAC" ]
then
   TEMP_SID=$(grep ^$1 /etc/oratab | awk -F':' '{ print $1 }')
   export ORACLE_SID=${TEMP_SID}
   export ORAENV_ASK=NO

   . oraenv
   REAL_SID=$(lsnrctl status listener|grep -E "Instance .$1" |head -n 1|awk -F' ' '{ print $2 }'|sed 's/\"//g'|sed 's/,//g')
fi

  sudo su - oracle -c "

  if [ -z "$4" ] || [ "$4" != "RAC" ]
  then
    export ORACLE_SID=$1
    export ORAENV_ASK=NO

    . oraenv

  else

    export ORACLE_SID=${TEMP_SID}

    export ORAENV_ASK=NO

    . oraenv
    export ORACLE_SID=${REAL_SID}

  fi

  sqlplus / as sysdba <<EOF
  ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = "${DB_RFDS}" SCOPE=BOTH;
  alter session set container = pdbName;

  CREATE USER FASSM IDENTIFIED BY "${ORAPWD}"
  DEFAULT TABLESPACE "USERS"
  TEMPORARY TABLESPACE "TEMP";

  ALTER USER FASSM ACCOUNT UNLOCK;

  GRANT SELECT_CATALOG_ROLE TO FASSM;
  GRANT CONNECT TO FASSM;
  GRANT RESOURCE TO FASSM;

  ALTER USER FASSM QUOTA UNLIMITED ON USERS;
  EOF

"
