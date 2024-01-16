#!/bin/bash

# https://confluence.oraclecorp.com/confluence/display/SOPT/MidTier+Backup+Validation+-+Automation+Test+Cases
# https://confluence.oraclecorp.com/confluence/display/SOPT/MT+Backup+Validation+%3A+Latest+TestCases
# Usage: /tmp/MTBackupValidate.sh fa-peo-oci-backup-1.0.3.0.191115-1.noarch 12345


[[ "$BASH_VERSION" =~ ^4 ]] && shopt -s compat31
export SCR_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]:-$0}")")"
clear
new_bkup_rpm=$1
[[ -n $2 ]] && TOKEN=$2 || TOKEN=$$

REPORT="/tmp/mtbkupvalid_$TOKEN.out"
rm -f $REPORT
REGION=$(curl -sL -H "Authorization: Bearer Oracle" "http://169.254.169.254/opc/v2/instance/region")

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

function chk_mt_bkup_cron_validations {
    if [[ -e /etc/cron.d/ocifsbackup ]];then
        bkup_entries=$(grep 'ocifsbackup.sh' /etc/cron.d/ocifsbackup)
        status=''
        msg=''
        if [[ -n $bkup_entries ]];then
            if [[ -n $(grep 'ocifsbackup.sh' /etc/cron.d/ocifsbackup | grep '^#') ]]; then
                print_report "chk_mt_bkup_cron_validations,FAIL,ocifsbackup.sh is commented in /etc/cron.d/ocifsbackup"
            else
                print_report "chk_mt_bkup_cron_validations,PASS,ocifsbackup.sh entries found in /etc/cron.d/ocifsbackup"
            fi
        else
            print_report "chk_mt_bkup_cron_validations,FAIL,ocifsbackup.sh entries not found in /etc/cron.d/ocifsbackup"
        fi
    else
        print_report "chk_mt_bkup_cron_validations,FAIL,/etc/cron.d/ocifsbackup file does not exist"
    fi

    # Check for main mt backup script
    bkupscr=/opt/faops/spe/ocifabackup/bin/ocifsbackup.sh
    if [[ -e $bkupscr ]];then
        read user group permiss <<< $(stat -c '%U %G %a' $bkupscr)
        status=''
        msg=''

        [[ $user == "root" ]] && status=PASS || status=FAIL
        msg="$bkupscr file exists :: USER:$user:$status"

        [[ $permiss == "755" ]] && status=PASS || status=FAIL
        msg="$msg :: PERMISSION:$permiss:$status"

        [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
        print_report "chk_mt_bkup_cron_validations,$status,$msg"
    else
        print_report "chk_mt_bkup_cron_validations,FAIL,$bkupscr file does not exist"
    fi
}

function chk_mt_cfg_validations {
    # Check for backup cfg files
    bkupcfg=/opt/faops/spe/ocifabackup/config/mt/config-oci.json

    for cfg in $bkupcfg
    do
        status=''
        msg=''
        if [[ -e $cfg ]];then
            read user group permiss <<< $(stat -c '%U %G %a' $cfg)

            [[ $user == "root" ]] && status=PASS || status=FAIL
            msg="$cfg CFG file exists :: USER:$user:$status"

            [[ $permiss == "600" ]] && status=PASS || status=FAIL
            msg="$msg :: PERMISSION:$permiss:$status"

            # Check the URL having the correct region
            reg_flag=$(grep $REGION $cfg)
            [[ -n $reg_flag ]] && status=PASS || status=FAIL
            msg="$msg :: REGION:$reg_flag:$status"

            [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
            print_report "chk_mt_cfg_validations,$status,$msg"
        else
            print_report "chk_mt_cfg_validations,FAIL,$cfg file does not exist"
        fi

    done

}


function chk_mt_apikey_validations {
    # Check for mt apikey files
    apikeyfile=/opt/faops/spe/ocifabackup/config/mt/oci_api_key.pem

    status=''
    msg=''
    if [[ -e $apikeyfile ]];then
        read user group permiss <<< $(stat -c '%U %G %a' $apikeyfile)

        [[ $user == "root" ]] && status=PASS || status=FAIL
        msg="$apikeyfile apikey file exists :: USER:$user:$status"

        [[ $permiss == "600" ]] && status=PASS || status=FAIL
        msg="$msg :: PERMISSION:$permiss:$status"

        [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
        print_report "chk_mt_apikey_validations,$status,$msg"
    else
        print_report "chk_mt_apikey_validations,FAIL,$apikeyfile apikey file does not exist"
    fi

}

function chk_mt_utils_validations {
    # Check for utils like oci_curl, oci_setup, jq files
    ocicurl="/opt/faops/spe/ocifabackup/utils/oci_curl.sh"
    ocisetup="/opt/faops/spe/ocifabackup/utils/oci_setup.sh"
    jq="/opt/faops/spe/ocifabackup/utils/jq"

    for util in $ocicurl $ocisetup $jq
    do
        status=''
        msg=''
        if [[ -e $util ]];then
            read user group permiss <<< $(stat -c '%U %G %a' $util)

            [[ $user == "root" ]] && status=PASS || status=FAIL
            msg="$util file exists :: USER:$user:$status"

            [[ $permiss == '755' ]] && status=PASS || status=FAIL
            msg="$msg :: PERMISSION:$permiss:$status"

            [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
            print_report "chk_mt_utils_validations,$status,$msg"
        else
            print_report "chk_mt_utils_validations,FAIL,$util file does not exist"
        fi

    done

}


function chk_mt_retention_cfg_scripts {
    # Check for MT retention scripts
    retention_cfg="/opt/faops/spe/ocifabackup/config/mt/config-retention-policy.json"

    if [[ -e $retention_cfg ]];then
        print_report "chk_mt_retention_cfg_scripts,PASS,$retention_cfg retention script exists"
    else
        print_report "chk_mt_retention_cfg_scripts,FAIL,$retention_cfg retention script does not exist"
    fi

}

function main {
    echo "CHECK_NAME,TEST_RESULT,MESSAGE" >> $REPORT
    echo "===========================================,============,====================================================" >> $REPORT

    # TEST CASES calls
    chk_mt_bkup_host
    chk_mt_bkup_rpm
    chk_mt_bkup_cron_validations
    chk_mt_cfg_validations
    chk_mt_utils_validations
    chk_mt_apikey_validations
    chk_mt_retention_cfg_scripts

    # REPORT GENERATION
    cat $REPORT | column -t -s","
    rm -f $REPORT
}


###### Main run ######
main
