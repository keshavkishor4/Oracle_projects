#!/bin/bash
#########################################################################
#
# rman_upload_metadata.sh: Wrapper of rman_upload_metadata.py used to upload post.json (backup metadata) to oss bucket.
# Functionality is being provided as an alternative to cataloddb 
# 
# Vipin Azad   - 06/08/2023
#########################################################################
BASE_DIR="/opt/faops/spe/ocifabackup"
BACKUP_LOGS_BASE_DIR="/u02/backup/log/$(hostname -s)"
EXA_LOGS_DIR="${BACKUP_LOGS_BASE_DIR}/exalogs"
BACKUP_ARTIFACTS_PATH="/fss/oci_backup/artifacts/$(hostname -s)"
source ${BASE_DIR}/lib/python/common/setpyenv.sh
source ${BASE_DIR}/utils/db/scripts/shell/env.sh

DATE=$(date +'%Y%m%d_%H%M%S')
METADATA_UPLOAD_LOG="${EXA_LOGS_DIR}/rman_upload_metadata_${DATE}.log"
/usr/bin/script -f $METADATA_UPLOAD_LOG /bin/bash -c "${BASE_DIR}/bin/rman_upload_metadata.py $*"