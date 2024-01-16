#!/bin/bash
#get odd hosts
#HOSTS=$(olsnodes | sed -n 'p;n')
#
DATE=$1
if [[ -z $DATE ]];then
 echo "exit 1, argument needs to be passed, like YYYY_MM_DD, eg: 2020_11_07"
 exit 1
fi

function cleanup() {
    DY=$(echo $DATE | awk -F_ '{print $1}')
    DM=$(echo $DATE | awk -F_ '{print $2}')
    DD=$(echo $DATE | awk -F_ '{print $3}')
    SIDS=$(grep -i "recovery manager complete" /u02/backup/log/*/*/*database_to_reco*${DM}*${DD}*${DY}*log | awk -F: '{print $1}' | awk -F\/ '{print $6}' | sed 's/.$//')
    # SIDS=$(ps -ef|grep pmon|grep -v '+ASM'|grep -v '+APX' |grep -v grep|awk -F'_' '{print $NF}')
    for DB in $SIDS;do
        #DB=$(echo $SID|sed 's/.$//')
        echo "checking +RECO/${DB}/BACKUPSET/${DATE}"
        asmcmd -p ls -l +RECO/${DB}/BACKUPSET/${DATE}*/*
        asmcmd -p rm -rf +RECO/${DB}/BACKUPSET/${DATE}*/nnndn*_BACKUPSET_LEVEL_0*
    done
}

function cleanup_15_days(){
    BKUP_OLD_DATE=$(date -d "$date -15 days" +"%Y_%m_%d")
    BKUP_OLD_MONTH=$(echo $BKUP_OLD_DATE | awk -F_ '{print $2}')
    BKUP_OLD_DAY=$(echo $BKUP_OLD_DATE | awk -F_ '{print $3}')
    echo "deleting backups older than 15 days"
    for i in {15..45};do 
        BKUP_DEL_DATE=$(date -d "$date -${i} days" +"%Y_%m_%d")
        echo "deleting backups for ${BKUP_DEL_DATE} ..."
        asmcmd -p ls -l +RECO/e*/BACKUPSET/${BKUP_DEL_DATE}/*
        asmcmd -p rm -rf +RECO/e*/BACKUPSET/${BKUP_DEL_DATE}*/nnndn*
    done 
}
#

function check_old() {
    DAYS=$1
    BKUP_OLD_DATE=$(date -d "$date -$DAYS days" +"%Y_%m_%d")
    BKUP_OLD_MONTH=$(echo $BKUP_OLD_DATE | awk -F_ '{print $2}')
    BKUP_OLD_DAY=$(echo $BKUP_OLD_DATE | awk -F_ '{print $3}')
    # 
    for i in {${DAYS}..45};do
        echo $i
        BKUP_DEL_DATE=$(date -d "$date -${i} days" +"%Y_%m_%d")
        # asmcmd -p find --type BACKUPSET +reco/ "*"
        echo $BKUP_DEL_DATE
    done
}

#  --
SIDS=$(ps -ef|grep pmon|grep -v '+ASM' | grep -v 'APX' | grep -v grep | grep -v dummy |awk -F'_' '{print $NF}' | sed 's/.$//')
for SID in $SIDS;do
echo $SID
source $HOME/${SID}.env
sqlplus / as sysdba <<EOF
    set lines 200
    col WRL_PARAMETER form a30
    col STATUS form a20
    select DB.name,EW.STATUS,EW.WRL_PARAMETER,EW.WALLET_TYPE from V\$ENCRYPTION_WALLET EW,v\$database DB;
    exit;
EOF
done
# 
set lines 100
col name format a60

select
   name,
   floor(space_limit / 1024 / 1024) "Size MB",
   ceil(space_used / 1024 / 1024)   "Used MB"
from
   v$recovery_file_dest
order by name;

# ---

echo "==============="

SID=$(ps -ef|grep pmon|grep '+ASM' | awk -F'_' '{print $NF}')
export ORACLE_SID=$SID;
export ORACLE_HOME=`grep $SID /etc/oratab|awk -F':' '{print $2}'|head -1`
export PATH=$PATH:$ORACLE_HOME/bin
#temp fix change below dates
#SIDS=$(grep -i "recovery manager complete" /u02/backup/log/*/*/*database_to_reco*${DM}*${DD}*${DY}*log | awk -F: '{print $1}' | awk -F\/ '{print $6}' | sed 's/.$//')
#SIDS=$(grep -i "recovery manager complete" /u02/backup/log/*/*/*database_to_reco*103[0-1]2020*log | awk -F: '{print $1}' | awk -F\/ '{print $6}' | sed 's/.$//')

echo "-------"
# cleanup
cleanup_15_days
