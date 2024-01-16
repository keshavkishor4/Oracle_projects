#!/bin/bash
#########################################################################
# ocifsbackup_test.sh: Wrapper of ocifsbackup_test.py to use oci env.
# Saritha Gireddy - 01/02/2021 Created sleeper function to ensure staggered backup
#################################################################################################################

# source /opt/faops/tools/pyvenv-oci
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh

#test_enabled=`python /opt/faops/spe/ocifabackup/utils/test_automation/ocifsbackup_test`
mkdir -p "/opt/faops/spe/ocifabackup/utils/test_automation"
unzip -o "/opt/faops/spe/ocifabackup/utils/test_automation/faops_spe_backup_test.zip" -d "/opt/faops/spe/ocifabackup/utils/test_automation"
python /opt/faops/spe/ocifabackup/utils/test_automation/ocifsbackup_test.py