#!/bin/bash
#########################################################################
#
# oci_setup.sh: Setup backup configuration for PREPOEPROD environment.
#
# Chenlu Chen - 01/10/2019 created
#
#################################################################################################################

function oci-setup {
    local setup_type=$1

    case $setup_type in
        "wallet")
        local oci_config_obj="https://objectstorage.us-phoenix-1.oraclecloud.com/p/oYtl0_oMZFONvT15ZN3ISyJPKcV-mPtewcfELtJhlX4/n/p1-saasfapreprod1/b/rman_wallet_backup/o/config-oci.json";
        local oci_api_key_obj="https://objectstorage.us-phoenix-1.oraclecloud.com/p/Hc43tbCdcRjSHRGhvOjTubZ2YcarOq8g0amTr7CrNGw/n/p1-saasfapreprod1/b/rman_wallet_backup/o/oci_api_key.pem";
        local dest_dir="/opt/faops/spe/ocifabackup/config/wallet/";
        ;;				

        "mt")
        local oci_config_obj="https://objectstorage.us-phoenix-1.oraclecloud.com/p/up8opWouNMZkI04enT7l476H5SZhGJxdeuLje1RYwSs/n/p1-saasfapreprod1/b/MT_BACKUP/o/config-oci.json";
        local oci_api_key_obj="https://objectstorage.us-phoenix-1.oraclecloud.com/p/3Bj_xqi09uLWp1u0ToV4wA51vLALPNnMzUbBaLVEOW0/n/p1-saasfapreprod1/b/MT_BACKUP/o/oci_api_key.pem";
        local dest_dir="/opt/faops/spe/ocifabackup/config/mt/";
        ;;		

        *) echo "invalid type"; return;;
    esac

    local config_file=${dest_dir}"config-oci.json"
    if [[ -e ${config_file} ]]; then
        rm -rf ${config_file}
    fi

    local key_file=${dest_dir}"oci_api_key.pem"
    if [[ -e ${key_file} ]]; then
        rm -rf ${key_file}
    fi

    wget ${oci_config_obj} -P ${dest_dir}
    wget ${oci_api_key_obj} -P ${dest_dir}
}				

######################## Main ################################
# Usage:
# oci_setup.sh <backup_type>
#
# ex:
# oci_setup.sh mt
# oci_setup.sh wallet

oci-setup $@
