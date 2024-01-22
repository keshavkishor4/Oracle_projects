#!/bin/bash

# Perform pre-checks
BASE_DIR=$HOME/creds
ENV_FILE=$HOME/creds/.env
OS=$(uname -a | grep -i darwin)
OS_ARCH=$(uname -m)

function install_prereqs() {
    BREW_CHECK=$(which brew)
    if [[ -z "${BREW_CHECK}" ]];then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    fi
    # Install podman and podman-compose
    PODMAN_CHECK=$(which podman)
    if [[ -z "${PODMAN_CHECK}" ]];then
        brew install podman podman-compose podman-desktop jq wget
    fi
}
# Download docker

function podman_tasks() {
    PODMAN_MACHINE_CHECK=$(podman machine list | grep -i default)
    if [[ -z "${PODMAN_CHECK}" ]];then
        podman machine init
        podman machine start
    fi
    #
    PODMAN_MACHINE_RUN_CHECK=$(podman machine list | grep -i running)
    if [[ -z "${PODMAN_MACHINE_RUN_CHECK}" ]];then
        podman machine start
    fi
    #
    if [[ ! -f $BASE_DIR/.env_sample ]];then
        read -r -d '' ENV_SAMPLE_FILE << ENV_SAMPLE_FILE
# please create .env file in base directory ( fapod )
# below is the content for the env file
# Commercial JC
JC_COMM_URL="https://cloudmeta.itpa.cyf.oraclecloud.com"
JC_COMM_USER_NAME="user@oracle.com"
JC_COMM_USER_PASS=""
# UKGov JC
JC_UKG_URL="https://cloudmeta-ukg.itpa.cyf.oraclecloud.com"
JC_UKG_USER_NAME="user@oracle.com"
JC_UKG_USER_PASS=""
# BOAT OCI Setup
# oc1 - saasfaprod1
# Place the keys and .env under $HOME/creds
oci_user="<<oci_uid>>"
oci_fingerprint="<<oci fingerprint data >>"
oci_tenancy="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_region="us-phoenix-1"
oci_key_file="<< key file location >>"
oci_oc1_comm_boat_user="<oci boat user ocid>"
oci_oc1_comm_boat_fingerprint="<oci_boat_user_fingerprint>"
oci_oc1_comm_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_comm_boat_key_file="<oci_boat_user_pem_key_file ukgov place just put the file name and ensure file is at $HOME/creds > "
oci_oc1_comm_region="us-phoenix-1"
oci_oc1_comm_tenancy_name="saasfaprod1"
oci_oc1_comm_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaajgaoycccrtt3l3vnnlave6wkc2zbf6kkksq66begstczxrmxjlia"
# oc4 - saasfaukgovprod1 - UKG
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc4_ukg_boat_user="<oci ukgov boat user ocid>"
oci_oc4_ukg_boat_fingerprint="<oci_ukgov_boat_user_fingerprint>"
oci_oc4_ukg_boat_tenancy_ocid="ocid1.tenancy.oc4..aaaaaaaak37nmbaszvdjdrmkvcvlypax53ila3yajff5tgdffk5njsm2czsa"
oci_oc4_ukg_boat_key_file="<oci_boat_user_pem_key_file ukgov place just put the file name and ensure file is at $HOME/fapodinv/creds > "
oci_oc4_ukg_region="uk-gov-london-1"
oci_oc4_ukg_tenancy_name="saasfaukgovprod1"
oci_oc4_ukg_tenancy_ocid="ocid1.tenancy.oc4..aaaaaaaaynkiunr3l4m66xb3w3rzkgiboivvfru6fxfidvx75ftfmn4pvkwa"
# oc1 - saasfaeuraprod1 - EURA
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc1_eura_boat_user=""
oci_oc1_eura_boat_fingerprint=""
oci_oc1_eura_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_eura_boat_key_file="./.oci/<pem_file>"
oci_oc1_eura_region="us-phoenix-1"
oci_oc1_eura_tenancy_name="saasfaeuraprod1"
oci_oc1_eura_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaajgaoycccrtt3l3vnnlave6wkc2zbf6kkksq66begstczxrmxjlia"
# oc1 - p1-saasfapreprod1 - PPD
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc1_ppd_boat_user=""
oci_oc1_ppd_boat_fingerprint=""
oci_oc1_ppd_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_ppd_boat_key_file="./.oci/<pem_file>"
oci_oc1_ppd_region="us-phoenix-1"
oci_oc1_ppd_tenancy_name="p1-saasfapreprod1"
oci_oc1_ppd_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaan3pnajtsevwlkiah5bop22sbd4fpynffoqxlkeehcsv2qxicqupq"

ENV_SAMPLE_FILE
        mkdir -p $BASE_DIR
    fi
}

function validate_fapodlookup_setup() {
    REALM=$1
    TOKEN_CMD=
    if [[ -f $ENV_FILE ]];then
        if [[ "$REALM" == "ukg" ]];then
            JC_URL=$(grep -i JC_UKG_URL $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
            JC_USER_NAME=$(grep -i JC_UKG_USER_NAME $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
            JC_USER_PASS=$(grep -i JC_UKG_USER_PASS $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
        elif [[ "$REALM" == "comm" ]];then
            JC_URL=$(grep -i JC_COMM_URL $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
            JC_USER_NAME=$(grep -i JC_COMM_USER_NAME $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
            JC_USER_PASS=$(grep -i JC_COMM_USER_PASS $ENV_FILE | awk -F= '{print $2}' | sed 's/"//g')
        fi
        #
        # curl -s -X POST --header 'Content-Type: application/x-www-form-urlencoded' --header 'Accept: application/json' -d 'email=zakki.ahmed%40oracle.com&password=r0lNg%23eta' https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/v1/login | jq -r '.bearer'
        TOKEN_CMD="curl -s -X POST --header 'Content-Type: application/x-www-form-urlencoded' --header 'Accept: application/json' -d 'email=${JC_USER_NAME}&password=${JC_USER_PASS}' ${JC_URL}/cloudmeta-api/v2/login | jq -r '.bearer'"
        echo "Validate using below curl command ... "
        echo $TOKEN_CMD
        # echo $(${TOKEN_CMD)
    fi
}

function FAPODLOOKUP_TASKS() {
    #
    install_prereqs
    #
    podman_tasks
    #
    read -r -d '' ENV_SAMPLE_FILE << ENV_SAMPLE_FILE
# please create .env file in base directory ( fapod )
# below is the content for the env file
# Commercial JC
JC_COMM_URL="https://cloudmeta.itpa.cyf.oraclecloud.com"
JC_COMM_USER_NAME="user@oracle.com"
JC_COMM_USER_PASS=""
# UKGov JC
JC_UKG_URL="https://cloudmeta-ukg.itpa.cyf.oraclecloud.com"
JC_UKG_USER_NAME="user@oracle.com"
JC_UKG_USER_PASS=""
# BOAT OCI Setup
# oc1 - saasfaprod1
# Place the keys and .env under $HOME/fapodinv/creds
oci_user="<<oci_uid>>"
oci_fingerprint="<<oci fingerprint data >>"
oci_tenancy="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_region="us-phoenix-1"
oci_key_file="<< key file location >>"
oci_oc1_comm_boat_user="<oci boat user ocid>"
oci_oc1_comm_boat_fingerprint="<oci_boat_user_fingerprint>"
oci_oc1_comm_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_comm_boat_key_file="<oci_boat_user_pem_key_file ukgov place just put the file name and ensure file is at $HOME/fapodinv/creds > "
oci_oc1_comm_region="us-phoenix-1"
oci_oc1_comm_tenancy_name="saasfaprod1"
oci_oc1_comm_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaajgaoycccrtt3l3vnnlave6wkc2zbf6kkksq66begstczxrmxjlia"
# oc4 - saasfaukgovprod1 - UKG
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc4_ukg_boat_user="<oci ukgov boat user ocid>"
oci_oc4_ukg_boat_fingerprint="<oci_ukgov_boat_user_fingerprint>"
oci_oc4_ukg_boat_tenancy_ocid="ocid1.tenancy.oc4..aaaaaaaak37nmbaszvdjdrmkvcvlypax53ila3yajff5tgdffk5njsm2czsa"
oci_oc4_ukg_boat_key_file="<oci_boat_user_pem_key_file ukgov place just put the file name and ensure file is at $HOME/fapodinv/creds > "
oci_oc4_ukg_region="uk-gov-london-1"
oci_oc4_ukg_tenancy_name="saasfaukgovprod1"
oci_oc4_ukg_tenancy_ocid="ocid1.tenancy.oc4..aaaaaaaaynkiunr3l4m66xb3w3rzkgiboivvfru6fxfidvx75ftfmn4pvkwa"
# oc1 - saasfaeuraprod1 - EURA
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc1_eura_boat_user=""
oci_oc1_eura_boat_fingerprint=""
oci_oc1_eura_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_eura_boat_key_file="./.oci/<pem_file>"
oci_oc1_eura_region="us-phoenix-1"
oci_oc1_eura_tenancy_name="saasfaeuraprod1"
oci_oc1_eura_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaajgaoycccrtt3l3vnnlave6wkc2zbf6kkksq66begstczxrmxjlia"
# oc1 - p1-saasfapreprod1 - PPD
# Place the keys and .env under $HOME/fapodinv/creds
oci_oc1_ppd_boat_user=""
oci_oc1_ppd_boat_fingerprint=""
oci_oc1_ppd_boat_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaagkbzgg6lpzrf47xzy4rjoxg4de6ncfiq2rncmjiujvy2hjgxvziq"
oci_oc1_ppd_boat_key_file="./.oci/<pem_file>"
oci_oc1_ppd_region="us-phoenix-1"
oci_oc1_ppd_tenancy_name="p1-saasfapreprod1"
oci_oc1_ppd_tenancy_ocid="ocid1.tenancy.oc1..aaaaaaaan3pnajtsevwlkiah5bop22sbd4fpynffoqxlkeehcsv2qxicqupq"
ENV_SAMPLE_FILE


    #
    mkdir -p ${BASE_DIR}
    DOCKER_URL=$1
    if [[ -f "$BASE_DIR/.env" ]];then
        podman pull $DOCKER_URL
        podman run --name fapodlookup -d -p 8999:8000 --mount src="${BASE_DIR}",target="/opt/faops/spe/fapodcapacity/creds",type=bind ${DOCKER_URL}
        podman ps -a
        STATUS=$(podman ps -a | grep -i fapodlookup | grep -i up)
        if [[ ! -z $STATUS ]];then
            echo "FAPODLOOKUP is running, launching browser"
            open "http://localhost:8999"
        else
            echo "ERROR: FAPODLOKUP has exited, refer to https://confluence.oraclecorp.com/confluence/display/FusionSRE/FA+POD+Look+Up"
            exit 1
        fi
    else
        echo "$ENV_SAMPLE_FILE" > ${BASE_DIR}/.env_sample
        echo "ERROR: Fill in ${BASE_DIR}/.env, refer to sample file ${BASE_DIR}/.env_sample , re-run fapodlookup.sh"
        exit 1
    fi
}

if [[ ! -z "$OS" ]];then
    if [[ "$OS_ARCH" == "arm64" ]];then
        FAPODLOOKUP_TASKS "phx.ocir.io/axxyy35wuycx/podcapacity_arm:1"
    else
        FAPODLOOKUP_TASKS "phx.ocir.io/axxyy35wuycx/podcapacity:1"
    fi
else
    echo "This script is not applicable to your OS, this script runs only on mac"
fi