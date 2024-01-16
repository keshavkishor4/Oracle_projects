#!/bin/bash
# as root user
# 1. mkdir -p /opt/faops/scripts /opt/faops/logs
# 2.(copy the entire script) vi /opt/faops/scripts/db_tasks.sh
# 3. chmod 755 /opt/faops/scripts/db_tasks.sh && vi /etc/cron.d/faops_db_tasks
# 4. 10 16 * * 4 root /opt/faops/scripts/db_tasks.sh >> /opt/faops/logs/db_tasks_run_$(date +"\%Y\%m\%d_\%H\%M\%S").log
# 5. chmod 644 /etc/cron.d/faops_db_tasks
# 6. run /opt/faops/scripts/db_tasks.sh once to ensure all looks

# select decode( nvl( space_used, 0),0, 0,ceil ( ( space_used / space_limit) * 100) ) pct_used  from  v$recovery_file_dest where name like '%RECO%';

function daily_restart_db() {
    su - oracle -c "sqlplus -S / as sysdba <<EOF
    startup force;
    exit;
EOF
"
}

function check_space() {
    df -H | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{ print $5 " " $1 }' | while read output;
    do
    echo $output
    used=$(echo $output | awk '{ print $1}' | cut -d'%' -f1  )
    partition=$(echo $output | awk '{ print $2 }' )
    if [ $used -ge 80 ]; then
        echo "The partition \"$partition\" on $(hostname) has used $used% at $(date)" | mail -s "Disk space alert: $used% used" zakki.ahmed@oracle.com
    fi
    done
}

function oracle_daily_dbtasks() {
    # perform rman tasks
    su - oracle -c "rman target / <<EOF
    CROSSCHECK BACKUP;
    DELETE NOPROMPT EXPIRED BACKUP;
    CROSSCHECK BACKUPSET;
    DELETE NOPROMPT EXPIRED BACKUPSET;
    crosscheck archivelog all;
    delete noprompt expired archivelog all;
    exit;
EOF
"
    # DB tasks
    su - oracle -c "sqlplus -S / as sysdba <<EOF
    alter session set container=APEXPDB;
    SET SERVEROUTPUT ON;
    -- REM -- Tablespace increase
    DECLARE
    V_TS_METRICS dba_tablespace_usage_metrics%rowtype;
    V_ADD_TS VARCHAR2(200);
    BEGIN
        BEGIN
            select * into V_TS_METRICS from dba_tablespace_usage_metrics where USED_PERCENT>80 and rownum=1;
        EXCEPTION
        WHEN NO_DATA_FOUND THEN
            V_TS_METRICS := NULL;
        END;

        CASE
            WHEN V_TS_METRICS.TABLESPACE_NAME IS NULL THEN
            dbms_output.put_line('no action needed');
            ELSE
                V_ADD_TS := 'ALTER TABLESPACE '||V_TS_METRICS.TABLESPACE_NAME||' add datafile size 10G ';
                execute immediate V_ADD_TS;
                dbms_output.put_line(V_TS_METRICS.TABLESPACE_NAME||' has been extended by 10G');
        END CASE;
    END;
    /
    -- REM db_recovery_dest
    DECLARE
    V_RECO_DEST_METRICS FLOAT;
    V_ADD_RECO_DEST VARCHAR2(200);
    BEGIN
        BEGIN
            select decode( nvl( space_used, 0),0, 0,ceil ( ( space_used / space_limit) * 100) ) pct_used into V_RECO_DEST_METRICS from  v"'\$'"recovery_file_dest where name like '%RECO%';
        EXCEPTION
        WHEN NO_DATA_FOUND THEN
            V_RECO_DEST_METRICS := NULL;
        END;

        CASE
            WHEN V_RECO_DEST_METRICS IS NULL THEN
            dbms_output.put_line('problem with database');
            WHEN V_RECO_DEST_METRICS > 70 THEN
                V_ADD_RECO_DEST := 'alter system set db_recovery_file_dest_size=500G scope=both';
                execute immediate V_ADD_RECO_DEST;
                dbms_output.put_line(' db_recovery_file_dest_size has been set to 500G');
            ELSE
                dbms_output.put_line('no action needed');

        END CASE;
    END;
    /

    -- REM purge entries older than 60 days
    delete from FAOPS.BKPJSONTAB where created < SYSDATE - 60;
    alter table FAOPS.BKPJSONTAB enable row movement;
    alter table FAOPS.BKPJSONTAB shrink space compact;
    alter table FAOPS.BKPJSONTAB disable row movement;
    -- REM -- MDJSONTAB
    delete from FAOPS.MDJSONTAB where created < SYSDATE - 60;
    alter table FAOPS.MDJSONTAB enable row movement;
    alter table FAOPS.MDJSONTAB shrink space compact;
    alter table FAOPS.MDJSONTAB disable row movement;

    -- REM Gather schema stats FAOPS
    SET SERVEROUTPUT ON;
    EXECUTE DBMS_STATS.GATHER_SCHEMA_STATS('FAOPS',DBMS_STATS.AUTO_SAMPLE_SIZE);

    -- REM GATHER Table stats
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'BKPJSONTAB',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'BKPJSONTAB_ARCHIVE',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'BKPJSONTAB_MASTER',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'MDJSONTAB',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'MDJSONTAB_ARCHIVE',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);
    EXECUTE DBMS_STATS.GATHER_TABLE_STATS(ownname=>'FAOPS',tabname=>'MDJSONTAB_MASTER',estimate_percent=>DBMS_STATS.AUTO_SAMPLE_SIZE);

    exit;
EOF
"

# clean up trace files /etc
    echo "cleaning oracle trace files...."
    adr_base=$(su - oracle -c "adrci exec=\"show base\" | awk '{print \$4}' | sed 's/\"//g'")
    adr_home=$(su - oracle -c "adrci exec=\"show homes\" | grep -i \$ORACLE_UNQNAME")
    oracle_full_path="${adr_base}/${adr_home}"
    # clear files
    find ${oracle_full_path} -type f -mtime +7 -exec rm {} \;
    # clear run logs
    find /opt/faops/logs/ -type f -mtime +7 -exec rm {} \;
    # truncate
    find ${oracle_full_path} -type f -size +100M -exec truncate -s10M {} \;
    # clear run logs
    find /opt/faops/logs/ -type f -mtime +7 -exec rm {} \;
    # ntp tasks
    os_ver=$(uname -r)
    if [[ $os_ver =~ "el7" ]];then
        echo "time handled by chrony"
    elif [[ $os_ver =~ "el6" ]];then
        echo "updating ntpd..."
        iptables -I BareMetalInstanceServices 8 -d 169.254.169.254/32 -p udp -m udp --dport 123 -m comment --comment "Allow access to OCI local NTP service" -j ACCEPT
        service iptables save
        service ntpd stop
        ntpdate 169.254.169.254
        service ntpd start
    fi
}


function grid_daily_tasks() {
    echo "cleaning grid trace files...."
    grid_adr_base=$(su - grid -c "adrci exec=\"show base\" | awk '{print \$4}' | sed 's/\"//'g")
    lsnr_adr_home=$(su - grid -c "adrci exec=\"show homes\" | grep -i listener")
    grid_full_path="${grid_adr_base}/${lsnr_adr_home}"
    # clear files
    find ${grid_full_path} -type f -mtime +7 -exec rm {} \;
    # truncate
    find ${grid_full_path} -type f -size +100M -exec truncate -s10M {} \;
    if [ -d  /opt/oracle/oak/pkgrepos/orapkgs/clones ];then
        find /opt/oracle/oak/pkgrepos/orapkgs/clones -type f -mtime +7 -exec rm {} \;
    fi
}

function bkup_check_fixes() {
    mco rpc -v --json --sort -I '/dbfrontend/' mc_admin adhoccommand command='curl -s https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/saasfaprod1/b/REQUIRE_STAGE/o/deploy_database_to_compress_to_oss_rman.sh | bash -s --' |jq -r '.[] |"\(.sender) \(.data.output)"'
#
    mco rpc -v --json --sort -I '/dbfrontend/' mc_admin adhoccommand command='cat /opt/faops/spe/ocifabackup/utils/db/scripts/rman/database_compressed_to_oss_12.rman_cdb' |jq -r '.[] |"\(.sender) \(.data.output)"'
#
    mco rpc -v --json --sort -I '/dbfrontend/' mc_admin adhoccommand command='rpm -qa | grep -i backup' |jq -r '.[] |"\(.sender) \(.data.output)"'
}

function bkup_rpm_fixes() {
    HOSTS=$(mco rpc -v --json --sort -I '/dbfrontend/' mc_admin adhoccommand command='rpm -qa | grep -i backup' |jq -r '.[] |"\(.sender) \(.data.output)"' | grep -v fa-spe-oci-backup-db-2.0.0.0.210515.1-6.x86_64 | awk '{print $1}' | grep -v emdbfrontend)
    HOST_LIST=$(echo $HOSTS | sed 's/ /|/g')
    echo "upgrading rpm ..."
    if [[ ! -z $HOST_LIST ]];then
        mco rpc -v --json --sort -I "/${HOST_LIST}/"  mc_admin adhoccommand command='curl -s https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/saasfaprod1/b/REQUIRE_STAGE/o/rpm_upgrade.sh | bash -s -- fa-spe-oci-backup-db-2.0.0.0.210515.1-6.x86_64.rpm' |jq -r '.[] |"\(.sender) \(.data.output)"'
    else
        echo "no hosts to update"
    fi
}

# oracle tasks
daily_restart_db
check_space
oracle_daily_dbtasks
grid_daily_tasks
