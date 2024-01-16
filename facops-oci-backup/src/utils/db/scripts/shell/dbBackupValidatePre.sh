#!/bin/bash

# https://confluence.oraclecorp.com/confluence/display/SOPT/Database+Backup+Validation+-+Automation+Test+Cases
# https://confluence.oraclecorp.com/confluence/pages/editpage.action?pageId=1680911225
# https://confluence.rightnowtech.com/pages/viewpage.action?spaceKey=TECHTEAM&title=OCI_BACKUP_RESTORE
source "${BASE_DIR}/utils/db/scripts/shell/env.sh"
[[ "$BASH_VERSION" =~ ^4 ]] && shopt -s compat31
export SCR_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]:-$0}")")"
clear

new_bkup_rpm=$1
sid=$2
[[ -n $3 ]] && TOKEN=$3 || TOKEN=$$
REPORT="/tmp/dbbkupvalid_$TOKEN.out"
rm -f $REPORT
REGION=$(curl -sL -H "Authorization: Bearer Oracle" "http://169.254.169.254/opc/v2/instance/region")

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

function chk_oss_buk {
    echo "Function chk_oss_buk"
}

function chk_bkup_users_groups_exists {
    echo "Function chk_oss_buk"
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

function chk_cron_for_oracle {
    if [[ -e /etc/cron.allow ]];then
        status=''
        [[ -n $(grep oracle /etc/cron.allow) ]] && status=PASS || status=FAIL
        print_report "chk_cron_for_oracle,$status,cron.allow for oracle"
    else
        print_report "chk_cron_for_oracle,FAIL,cron.allow file does not exist"
    fi
}

function chk_fs_bkup_cron_validations {
    if [[ -e /etc/cron.d/ocifsbackup ]];then
        bkup_entries=$(grep 'rman_wrapper_oss.sh' /etc/cron.d/ocifsbackup)
        status=''
        msg=''
        if [[ -n $bkup_entries ]];then
            if [[ $(grep 'rman_wrapper_oss.sh' /etc/cron.d/ocifsbackup | egrep 'db_to_reco_db_arch_to_oss|incre_to_reco_arch_to_oss|archivelog_to_oss' | wc -l) -eq 3 ]]; then
                print_report "chk_fs_bkup_cron_validations,PASS,rman_wrapper_oss.sh <db_to_reco_db_arch_to_oss|incre_to_reco_arch_to_oss|archivelog_to_oss> entries found in /etc/cron.d/ocifsbackup"
            else
                print_report "chk_fs_bkup_cron_validations,FAIL,Partial entries for rman_wrapper_oss.sh found in /etc/cron.d/ocifsbackup"
            fi
        else
            print_report "chk_fs_bkup_cron_validations,FAIL,rman_wrapper_oss.sh entries not found in /etc/cron.d/ocifsbackup"
        fi
    else
        print_report "chk_fs_bkup_cron_validations,FAIL,/etc/cron.d/ocifsbackup file does not exist"
    fi

    # Check for main backup script
    bkupscr=/opt/faops/spe/ocifabackup/utils/db/rman_wrapper_oss.sh
    if [[ -e $bkupscr ]];then
        read user group permiss <<< $(stat -c '%U %G %a' $bkupscr)
        status=''
        msg=''

        [[ $user == "root" ]] && status=PASS || status=FAIL
        msg="$bkupscr file exists :: USER:$user:$status"

        [[ $permiss == "755" ]] && status=PASS || status=FAIL
        msg="$msg :: PERMISSION:$permiss:$status"

        [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
        print_report "chk_fs_bkup_cron_validations,$status,$msg"
    else
        print_report "chk_fs_bkup_cron_validations,FAIL,$bkupscr file does not exist"
    fi
}

function chk_db_cfg_validations {
    # Check for backup cfg files
    bkupcfg=/var/opt/oracle/ocde/assistants/bkup/bkup.cfg
    sredbcfg=/opt/faops/spe/ocifabackup/utils/db/conf/sre_db.cfg

    for cfg in $bkupcfg $sredbcfg
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
            print_report "chk_db_cfg_validations,$status,$msg"
        else
            print_report "chk_db_cfg_validations,FAIL,$cfg file does not exist"
        fi

    done

}

function chk_db_wallet_validations {
    # Check for db wallet cfg files
    walletcfg=/opt/faops/spe/ocifabackup/config/wallet/config-oci.json

    status=''
    msg=''
    if [[ -e $walletcfg ]];then
        read user group permiss <<< $(stat -c '%U %G %a' $walletcfg)

        [[ $user == "root" ]] && status=PASS || status=FAIL
        msg="$walletcfg wallet CFG file exists :: USER:$user:$status"

        [[ $permiss == "644" ]] && status=PASS || status=FAIL
        msg="$msg :: PERMISSION:$permiss:$status"

        # Check the URL having the correct region
        reg_flag=$(grep $REGION $walletcfg | tr ',' ' ')
        [[ -n $reg_flag ]] && status=PASS || status=FAIL
        msg="$msg :: REGION:$reg_flag:$status"

        [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
        print_report "chk_db_wallet_validations,$status,$msg"
    else
        print_report "chk_db_wallet_validations,FAIL,$walletcfg wallet CFG file does not exist"
    fi

}

function chk_db_wallet_apikey_validations {
    # Check for db wallet apikey files
    apikeyfile=/opt/faops/spe/ocifabackup/config/wallet/oci_api_key.pem

    status=''
    msg=''
    if [[ -e $apikeyfile ]];then
        read user group permiss <<< $(stat -c '%U %G %a' $apikeyfile)

        [[ $user == "root" ]] && status=PASS || status=FAIL
        msg="$apikeyfile wallet apikey file exists :: USER:$user:$status"

        [[ $permiss == "644" ]] && status=PASS || status=FAIL
        msg="$msg :: PERMISSION:$permiss:$status"

        [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
        print_report "chk_db_wallet_apikey_validations,$status,$msg"
    else
        print_report "chk_db_wallet_apikey_validations,FAIL,$apikeyfile wallet apikey file does not exist"
    fi

}

function chk_db_opc_ewallet_cwallet_validations {
    # Check for opc , ewallet and cwallet files
    opcfile="${OPC_LIB_PATH}/$sid/lib/libopc.so"
    ewallet="${OPC_LIB_PATH}/$sid/tde_wallet/ewallet.p12"
    cwallet="${OPC_LIB_PATH}/$sid/tde_wallet/cwallet.sso"

    for wallet in $opcfile $ewallet $cwallet
    do
        status=''
        msg=''
        if [[ -e $wallet ]];then
            read user group permiss <<< $(stat -c '%U %G %a' $wallet)

            [[ $user == "oracle" ]] && status=PASS || status=FAIL
            msg="$wallet file exists :: USER:$user:$status"

            [[ -n $(echo "$wallet" | grep wallet) ]] && exppermission=600 || exppermission=755
            [[ $permiss == $exppermission ]] && status=PASS || status=FAIL
            msg="$msg :: PERMISSION:$permiss:$status"

            [[ -z $(echo "$msg" | grep FAIL) ]] && status=PASS || status=FAIL
            print_report "chk_db_opc_ewallet_cwallet_validations,$status,$msg"
        else
            print_report "chk_db_opc_ewallet_cwallet_validations,FAIL,$wallet file does not exist"
        fi

    done

}

function chk_db_wallet_status {

    #wstatus=$(su oracle -c "source $sid.env; echo 'select WRL_PARAMETER||\":\"||STATUS from v\$encryption_wallet;' | sqlplus -s / as sysdba")

    wstatus=$(su oracle -c "source /home/oracle/$sid.env 2>/dev/null; echo 'select WRL_PARAMETER,STATUS,WALLET_TYPE from v\$encryption_wallet;' | sqlplus -s / as sysdba")
    #wstatus=$(su oracle -c "source $sid.env; echo 'select * from v\$encryption_wallet;' | sqlplus -s / as sysdba")
    autologin_open=$(echo "$wstatus" | egrep 'tde_wallet|AUTOLOGIN|OPEN' | grep 'AUTOLOGIN' | grep 'OPEN')
    if [[ -n $autologin_open ]];then
         print_report "chk_db_wallet_status,PASS,TDE_WALLET AUTOLOGIN in OPEN status"
    else
         print_report "chk_db_wallet_status,FAIL,TDE_WALLET AUTOLOGIN not in OPEN status"
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
    chk_cron_for_oracle
    chk_fs_bkup_cron_validations
    chk_db_cfg_validations
    chk_db_wallet_validations
    chk_db_wallet_apikey_validations
    chk_db_opc_ewallet_cwallet_validations
    chk_db_wallet_status
    chk_db_cleanup_scripts

    # REPORT GENERATION
    cat $REPORT | column -t -s","
    rm -f $REPORT
}

#### Main run ####
main
