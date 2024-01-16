#!/bin/bash

# https://confluence.oraclecorp.com/confluence/display/SOPT/Database+Backup+Validation+-+Automation+Test+Cases
# https://confluence.oraclecorp.com/confluence/pages/editpage.action?pageId=1680911225
# https://confluence.rightnowtech.com/pages/viewpage.action?spaceKey=TECHTEAM&title=OCI_BACKUP_RESTORE

[[ "$BASH_VERSION" =~ ^4 ]] && shopt -s compat31
export SCR_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]:-$0}")")"
clear

new_bkup_rpm=$1
sid=$2
[[ -n $3 ]] && TOKEN=$3 || TOKEN=$$
REPORT="/tmp/dbbkupvalid_$TOKEN.out"
rm -f $REPORT
REGION=$(curl -sL -H "Authorization: Bearer Oracle" "http://169.254.169.254/opc/v2/instance/region")
hn=$(hostname)
dbname=$(ps -ef | grep pmon | grep xmgou6i | awk -F_ '{print $NF}')
logpath="/u02/backup/log/${hn}/$dbname"

function print_report {
    echo "$1" >> $REPORT
}

function chk_db_bkup_host {
    h=$(hostname | tail -c 2)
    if [[ -n $(echo "02468" | grep $h) ]];then
        print_report "chk_db_bkup_host,FAIL,Host $(hostname) should be odd host for Backup Validations. Script Exiting!!"
        cat $REPORT | column -t -s","
        exit 1
    else
        print_report "chk_db_bkup_host,PASS,Host $(hostname) is odd host for Backup Validations"
    fi
}

function chk_db_bkup_rpm {
    rpms=$(rpm -qa  | grep backup)
    status='FAIL'
    for r in $(echo "$rpms")
    do
        if [[ "$r" == "$new_bkup_rpm" ]];then
            status=PASS
            print_report "chk_db_bkup_rpm,$status,$r matched $new_bkup_rpm"
            break
        fi
    done
    if [[ $status == "FAIL" ]];then
        print_report "chk_db_bkup_rpm,FAIL,rpm not matching the expected rpm $new_bkup_rpm. Script Exiting!!"
        cat $REPORT | column -t -s","
        exit 1
    fi
}

function chk_db_bkup_log_validations {
    # Check for backup log files
    bkuplog=/u02/backup/log

    for bklog in $bkuplog
    do
        if [[ -e $bklog ]];then
            read user group permiss <<< $(stat -c '%U %G %a' $bklog)

            [[ $user == "oracle" ]] && status=PASS || status=FAIL
            msg="$bklog LOG file exists :: USER:$user:$status"

            [[ $permiss == "755" ]] && status=PASS || status=FAIL
            msg="$msg :: PERMISSION:$permiss:$status"

            [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
            print_report "chk_db_bkup_log_validations,$status,$msg"
        else
            print_report "chk_db_bkup_log_validations,FAIL,BackupLog $bklog does not exist"
        fi

    done

}

function chk_db_run_archive_bkup {

    logpath="/u02/backup/log/${hn}/$dbname"

    # Test for the Archive backup
    arcbkup_cmd="/opt/faops/spe/ocifabackup/utils/db/rman_wrapper_oss.sh -b archivelog_to_oss"

    arcbkup_log="/tmp/arcbkup_${TOKEN}.log"
    $arcbkup_cmd &> $arcbkup_log

    if [[ $? -eq 0 ]];then
        postjson=$(ls -tr $logpath/${dbname}_archivelog_to_oss_*_post.json | tail -1)
        runstatus=$(grep '"STATUS":' $postjson | grep SUCCESS)
        if [[ -n $runstatus ]];then
            print_report "chk_db_run_archive_bkup,PASS,Archive backup Success"
        else
            print_report "chk_db_run_archive_bkup,FAIL,Post json status not Success. Archive backup failed"
        fi
    else
        print_report "chk_db_run_archive_bkup,FAIL,Archive backup failed"
    fi

}


function chk_db_run_incre_bkup {

    # Test for the Incremental backup
    incrbkup_cmd="/opt/faops/spe/ocifabackup/utils/db/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss"

    # Run the incrhive backup
    incrbkup_log="/tmp/incrbkup_${TOKEN}.log"
    $incrbkup_cmd &> $incrbkup_log

    if [[ $? -eq 0 ]];then
        postjson=$(ls -tr $logpath/${dbname}_incremental_to_reco_*_post.json | tail -1)
        runstatus=$(grep '"STATUS":' $postjson | grep SUCCESS)
        if [[ -n $runstatus ]];then
            print_report "chk_db_run_incre_bkup,PASS,Incremental backup Success"
        else
            print_report "chk_db_run_incre_bkup,FAIL,post json status not success. Incremental backup failed"
        fi
    else
        print_report "chk_db_run_incre_bkup,FAIL,Incremental backup failed"
    fi

}

function chk_db_run_full_bkup {

    # Test for the Full backup
    fullbkup_cmd="/opt/faops/spe/ocifabackup/utils/db/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss"

    # Run the Full backup
    incrbkup_log="/tmp/fullbkup_${TOKEN}.log"
    $fullbkup_cmd &> $fullbkup_log

    if [[ $? -eq 0 ]];then
        reco_postjson=$(ls -tr $logpath/${dbname}_database_to_reco_*_post.json | tail -1)
        runstatus=$(grep '"STATUS":' $reco_postjson | grep SUCCESS)
        if [[ -n $runstatus ]];then
            print_report "chk_db_run_full_bkup,PASS,Full backup post json for database_to_reco status Success"
        else
            print_report "chk_db_run_full_bkup,FAIL,Full backup post json for database_to_reco status not success. Full backup failed"
        fi
    else
        print_report "chk_db_run_full_bkup,FAIL,Full backup post json for database_to_reco failed"
    fi

    if [[ $? -eq 0 ]];then
        postjson=$(ls -tr $logpath/${dbname}_database_compressed_to_oss_*_post.json | tail -1)
        runstatus=$(grep '"STATUS":' $postjson | grep SUCCESS)
        if [[ -n $runstatus ]];then
            print_report "chk_db_run_full_bkup,PASS,Full backup post json for database_compressed_to_oss status Success"
        else
            print_report "chk_db_run_full_bkup,FAIL,Full backup post json for database_compressed_to_oss status not success. Full backup failed"
        fi
    else
        print_report "chk_db_run_full_bkup,FAIL,Full backup post json for database_compressed_to_oss failed"
    fi
}

function chk_db_cleanup_scripts {
    # Check for DB cleanup scripts
    bkup_api="/var/opt/oracle/bkup_api/bkup_api"
    cleandblogs="/var/opt/oracle/cleandb/cleandblogs.cfg"

    if [[ -e $bkup_api ]];then
        print_report "chk_db_cleanup_scripts,PASS,$bkup_api cleanup script exists"
    else
        print_report "chk_db_cleanup_scripts,FAIL,$bkup_api cleanup script does not exist"
    fi

    if [[ -e $cleandblogs ]];then
        print_report "chk_db_cleanup_scripts,PASS,$cleandblogs cleanup script exists"
    else
        print_report "chk_db_cleanup_scripts,FAIL,$cleandblogs cleanup script does not exist"
    fi

}

function main {
    echo "CHECK_NAME,TEST_RESULT,MESSAGE" >> $REPORT
    echo "===========================================,============,====================================================" >> $REPORT

    # TEST CASES calls
    chk_db_bkup_host
    chk_db_bkup_rpm
    chk_db_bkup_log_validations
    chk_db_run_archive_bkup
    chk_db_run_incre_bkup
    chk_db_run_full_bkup

    # REPORT GENERATION
    cat $REPORT | column -t -s","
    rm -f $REPORT

}

#### Main run ####
main
