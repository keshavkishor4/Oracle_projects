#!/bin/bash

# https://confluence.oraclecorp.com/confluence/display/SOPT/MidTier+Backup+Validation+-+Automation+Test+Cases
# https://confluence.oraclecorp.com/confluence/display/SOPT/MT+Backup+Validation+%3A+Latest+TestCases
# Usage: /tmp/MTBackupValidateRun.sh fa-peo-oci-backup-1.0.3.0.191115-1.noarch 12345


[[ "$BASH_VERSION" =~ ^4 ]] && shopt -s compat31
export SCR_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]:-$0}")")"
clear
new_bkup_rpm=$1
[[ -n $2 ]] && TOKEN=$2 || TOKEN=$$

REPORT="/tmp/mtbkupvalid_$TOKEN.out"
rm -f $REPORT
REGION=$(curl -s -H "http://169.254.169.254/opc/v2/instance/region")
MTBKUPLOG=''
SYSTYPE=$(grep -i systemType /var/mcollective/facts.yaml | awk '{print $2}')

function print_report {
    echo "$1" >> $REPORT
}

function chk_mt_bkup_host {
    systyp=$(grep -i systemType /var/mcollective/facts.yaml | awk '{print $2}')
    if [[ -n $(echo $systyp | egrep 'ADMIN|OPT|AUXVM|FA1|OHS|IDM') ]];then
        print_report "chk_mt_bkup_host,PASS,Host $(hostname) is MT host for Backup Validations"
    else
        print_report "chk_mt_bkup_host,FAIL,Host $(hostname) should be MT host for Backup Validations. Script Exiting!!"
        cat $REPORT | column -t -s","
        exit 1
    fi
}

function chk_oss_buk {
    echo "Function chk_oss_buk"
}

function chk_bkup_users_groups_exists {
    echo "Function chk_oss_buk"
}

function chk_mt_bkup_rpm {
    rpms=$(rpm -qa  | grep backup)
    status='FAIL'
    for r in $(echo "$rpms")
    do
        if [[ "$r" == "$new_bkup_rpm" ]];then
            status=PASS
            print_report "chk_mt_bkup_rpm,$status,$r matched $new_bkup_rpm"
            break
        fi
    done
    if [[ $status == "FAIL" ]];then
        print_report "chk_mt_bkup_rpm,FAIL,rpm not matching the expected rpm $new_bkup_rpm. Script Exiting!!"
        cat $REPORT | column -t -s","
        exit 1
    fi
}

function chk_mt_bkup_log_validations {
    # Check for backup log files
    bkuplog=/var/log/ocifsbackup

    for bklog in $bkuplog
    do
        if [[ -e $bklog ]];then
            read user group permiss <<< $(stat -c '%U %G %a' $bklog)

            [[ $user == "root" ]] && status=PASS || status=FAIL
            msg="$bklog LOG file exists :: USER:$user:$status"

            [[ $permiss =~ '750|755' ]] && status=PASS || status=FAIL
            msg="$msg :: PERMISSION:$permiss:$status"

            [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
            print_report "chk_mt_bkup_log_validations,$status,$msg"
        else
            print_report "chk_mt_bkup_log_validations,FAIL,BackupLog $bklog does not exist"
        fi

    done

}


function chk_db_run_mt_bkup {

    logpath="/var/log/ocifsbackup"

    # Test for the Archive backup
    mtbkup_cmd="/opt/faops/spe/ocifabackup/bin/ocifsbackup.sh --action backup --storage-type fss --backup-options snapshot --catalog-type local"

    mtbkup_log="/tmp/mtbkup_${TOKEN}.log"
    $mtbkup_cmd &> $mtbkup_log

    if [[ $? -eq 0 ]];then
        mtrunlog=$(grep 'logging started' $mtbkup_log | cut -d' ' -f3)
        MTBKUPLOG=$mtrunlog
        runcomplete=$(grep 'Succeed to do backup' $mtrunlog)
        if [[ -n $runcomplete ]];then
            print_report "chk_db_run_archive_bkup,PASS,MT backup run succeed"
        else
            print_report "chk_db_run_archive_bkup,FAIL,MT backup run not succeed"
        fi

        runstatus=$(grep '"STATUS": "ACTIVE"' $mtrunlog)
        if [[ -n $runstatus ]];then
            print_report "chk_db_run_archive_bkup,PASS,MT backup status ACTIVE"
        else
            print_report "chk_db_run_archive_bkup,FAIL,MT backup status not in ACTIVE"
        fi
    else
        print_report "chk_db_run_archive_bkup,FAIL,Archive backup failed"
    fi

}


function chk_mt_snapshots_validations {
    # Check for mt apikey files

    allsnapshots=$(grep 'create_fs_snapshots' $MTBKUPLOG | awk '{print $(NF-1)}')

    # for snapshot in /u01/.snapshot /u02/.snapshot /u04/.snapshot /podscratch/.snapshot /opt/facs/casrepos/.snapshot/
    sstoverify=''
    if [[ $SYSTYPE =~ 'ADMIN' ]]; then
        ss=$(echo "$allsnapshots" | grep '_fainstance')
        [[ -n $ss ]] && sstoverify="/u01/.snapshot/$ss /u02/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_podscratch')
        [[ -n $ss ]] && sstoverify="$sstoverify /podscratch/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_perstscratch')
        [[ -n $ss ]] && sstoverify="$sstoverify /u04/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_fa\.')
        [[ -n $ss ]] && sstoverify="$sstoverify /opt/facs/casrepos/.snapshot/$ss"
    fi

    if [[ $SYSTYPE =~ 'IDM' ]]; then
        ss=$(echo "$allsnapshots" | grep '_idm_split')
        [[ -n $ss ]] && sstoverify="/u01/.snapshot/$ss /u02/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_podscratch')
        [[ -n $ss ]] && sstoverify="$sstoverify /podscratch/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_idm\.')
        [[ -n $ss ]] && sstoverify="$sstoverify /opt/facs/casrepos/.snapshot/$ss"
    fi

    if [[ $SYSTYPE =~ 'OHS' ]]; then
        ss=$(echo "$allsnapshots" | grep '_ohs_split')
        [[ -n $ss ]] && sstoverify="/u01/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_podscratch')
        [[ -n $ss ]] && sstoverify="$sstoverify /podscratch/.snapshot/$ss"

        ss=$(echo "$allsnapshots" | grep '_idm\.')
        [[ -n $ss ]] && sstoverify="$sstoverify /opt/facs/casrepos/.snapshot/$ss"
    fi

    for ssdir in $(echo $sstoverify)
    do
        if [[ -e $ssdir ]];then
            print_report "chk_mt_snapshots_validations,PASS,snapshot dir $ssdir exists"
        else
            print_report "chk_mt_snapshots_validations,FAIL,snapshot dir $ssdir does not exist"
        fi
    done

}


function main {
    echo "CHECK_NAME,TEST_RESULT,MESSAGE" >> $REPORT
    echo "===========================================,============,====================================================" >> $REPORT

    # TEST CASES calls
    chk_mt_bkup_host
    chk_mt_bkup_rpm
    chk_mt_bkup_log_validations
    chk_db_run_mt_bkup
    chk_mt_snapshots_validations

    # REPORT GENERATION
    cat $REPORT | column -t -s","
    rm -f $REPORT
}


###### Main run ######
main
