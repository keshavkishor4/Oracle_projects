#!/bin/bash -x
DATE=$(date +'%Y%m%d_%H%M%S')

function oracle_exec() {
  sudo su oracle -c "
    source /home/oracle/.bash_profile
    sqlplus / as sysdba <<EOF
      ALTER SYSTEM SET DB_RECOVERY_FILE_DEST_SIZE = "${DB_RFDS}" SCOPE=BOTH;
      alter session set container = pdbName;
      create tablespace faopsts datafile '+DATA' size 2G autoextend on next 100m maxsize unlimited;
      create user faops identified by "${ORAPWD}" DEFAULT TABLESPACE faopsts QUOTA UNLIMITED ON faopsts;
      grant connect,resource to faops;
      ALTER USER FAOPS ACCOUNT UNLOCK;
      alter profile DEFAULT limit PASSWORD_REUSE_TIME unlimited;
      alter profile DEFAULT limit PASSWORD_LIFE_TIME  unlimited;
      ALTER PROFILE default LIMIT FAILED_LOGIN_ATTEMPTS UNLIMITED;
      ALTER USER FAOPS ACCOUNT UNLOCK;
EOF
  "
}

function os_tmp_fixes() {
  sudo useradd -g oinstall oraimp; echo 'oraimp:welcome@123'| sudo /usr/sbin/chpasswd
  # preserve sshd_config
  sudo cp -P /etc/ssh/sshd_config /etc/ssh/sshd_config.premig19c
  #
  sudo sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' /etc/ssh/sshd_config
  echo "AllowUsers oraimp" | sudo tee -a /etc/ssh/sshd_config
  #
  sudo systemctl restart sshd
}

#
if [ -z "$2" ]
then
  echo "Usage : $0 <ORACLE_SID> <PASSWORD> <DB_RECOVERY_FILE_DEST_SIZE>G [RAC|SINGLE]"
  exit 1
else
  ORAPWD="$2"
fi

if [ -z "$3" ]
then
  echo "Usage : $0 <ORACLE_SID> <PASSWORD> <DB_RECOVERY_FILE_DEST_SIZE>G [RAC|SINGLE]"
  exit 1
else
  DB_RFDS="$3"
fi

#
oracle_exec
os_tmp_fixes