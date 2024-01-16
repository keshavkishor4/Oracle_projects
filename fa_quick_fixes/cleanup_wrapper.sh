#!/bin/bash
BASE_DIR="/opt/faops/spe/ocifabackup"
catalogdb_bucket_cleanup="${BASE_DIR}/catalogdb_bucket_cleanup"
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
DATE=$(date +'%Y%m%d_%H%M%S')
if [[ ! -d $catalogdb_bucket_cleanup ]];then
    mkdir -p $catalogdb_bucket_cleanup
fi

host=`hostname  -f| awk -F'.' '{print $3}'`

if [[ $host =~ 'dev' ]]; then
    env="DEV"
fi
if [[ $host =~  'ppd01' ]]; then
    env="PPD"
fi
if [[ $host =~  'prd01' ]]; then
    env="PRD"
fi

bucket="${env}_FAOPS_CB_MT"
echo "Data will be purge from bucket:${bucket}"
# echo "Do you want to proceed with this action :"  
# #Take the input
# read  
# #Print the input value
# if [[ $REPLY = "yes" || $REPLY = "Yes" ||  $REPLY = "YES" ]] ;then
echo "proceeding with purging ..."
CLEANUP_LOG="${catalogdb_bucket_cleanup}/catalogdb_bucket_cleanup_oss_${DATE}.log"
echo $CLEANUP_LOG
/usr/bin/script -f $CLEANUP_LOG /bin/bash -c "$catalogdb_bucket_cleanup/cleanup.py --bucket-name $bucket $*"
# else
#     echo "Your ans is $REPLY hence exited"
#     echo "accecpted ans to proceed for purging are - yes,Yes,YES"
# fi
