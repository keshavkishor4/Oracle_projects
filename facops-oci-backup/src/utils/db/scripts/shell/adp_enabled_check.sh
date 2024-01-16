#!/bin/bash
#adp exa check as part of FAOCI-775#
BASE_DIR="/opt/faops/spe/ocifabackup"
source ${BASE_DIR}/utils/db/scripts/shell/env.sh

function pre_checks() {
    if [ ! -z $ADP_ENABLED ];then
        if [ $ADP_ENABLED == "True" ] || [ $ADP_ENABLED == "true" ];then
            echo "Error: this exa is ADP enabled." && exit 1
        fi
    fi
}

pre_checks