#!/bin/bash
#
function execute_rman_backup() {
   dbname=$1
   type=$2
   tag=$3
   retention=$4
   nohup $BASE_DIR/bin/rman_oss.sh --dbname=${dbname} -b ${type} --tag=${tag} --retention-days=${retention}> /dev/null 2>&1 &
   sleep 5
   PID=$(ps -ax | grep -w "rman_oss.py --dbname=${dbname} -b ${type}" | grep -v '/usr/bin/script'  | grep -v grep | awk '{print $1}')
   if [[ ! -z $PID ]];then
    echo $PID
   fi
}
function check_rman_backup() {
   dbname=$1
   type=$2
   PID=$(ps -ax | grep -w "rman_oss.py --dbname=${dbname} -b ${type}" | grep -v '/usr/bin/script'  | grep -v grep | awk '{print $1}')
   if [[ ! -z $PID ]];then
    echo $PID
   fi
}
function check_rman_pid() {
   dbname=$1
   type=$2
   #PID=$(ps -ax | grep -i ${dbname} | grep -v '/usr/bin/script'  | grep -v grep | awk '{print $1}' | wc -l)
   #PID=$(ps --pid $$ -N -a | grep -i ${dbname})
   PID=$(ps --pid $$ -N -a | grep "\b${dbname}\b" | awk '{print $1}')
   if [[ ! -z $PID ]];then
    echo $PID
   fi
}
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
action=$1
dbname=$2
type=$3
tag=$4
retention=$5
if [ ! -z $action ] && [ ! -z $dbname ]  && [ ! -z $type ] ;then
    if [[ "$action" == "backup" ]];then
        execute_rman_backup $dbname $type $tag $retention
    elif [[ "$action" == "check" ]];then
        check_rman_backup $dbname $type
    fi
    # in below case , dbname translates to PID --> temp fix
elif [ ! -z $action ] && [ ! -z $dbname ];then
    if [[ "$action" == "check" ]] ;then
        check_rman_pid $dbname
    fi
else
    exit 1
fi