#!/bin/bash
#########################################################################
#
# ocifsbackup.sh: Wrapper of ocifsbackup.py to use oci env.
#
# Chenlu Chen - 01/23/2019 created
# Zakki Ahmed - 01/20/2020 Updates for BV and new python
# Srinivas Nallur - 04/06/2020 Created sleeper function to ensure staggered backup
# Vipin Azad      - 02/01/23 - removed the dependency on block_enabled instance metadata - FUSIONSRE-580
#################################################################################################################
function log()
{
  local status=$1
  local sleep_seconds="$2 secs"
  if [ "$status" == "SLEEP STOP" ];then local message="Starting backup after sleeping for ";else local message="Starting to sleep for";fi

  echo "$status : $message - $sleep_seconds"
  logger "`hostname` -> ocifsbackup -> $status -> `date`"
}
function sleeper(){
  octet=$( hostname -i|cut -d'.' -f4 )
  mod_octet=$((octet%2))

  local r=$(( $RANDOM % 60 +1))

  if [[ $mod_octet -eq 1 ]];then
    sleep_time=$r
  else
    sleep_time=`expr $r + 300`
  fi

  log "SLEEP START" $sleep_time
  sleep $sleep_time
  log "SLEEP STOP" $sleep_time

}

# source /opt/faops/tools/pyvenv-oci
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh

# Sleep
if [ "$2" == "backup" ];then
  sleeper
fi
# 
python /opt/faops/spe/ocifabackup/bin/ocifsbackupv2.py $@
