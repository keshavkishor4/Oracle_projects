#!/bin/bash
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
BASE_DIR="/opt/faops/spe/ocifabackup"
#verify permissions of cron
verify_cron() {
   echo "verify_cron starts here ######################" >> $test_log
   chmod 755 ${BASE_DIR}/utils/test/templates/ocifabackupv2.template
   ret_file_temp="${BASE_DIR}/utils/test_automation/templates/ocifsbackupv2.template"
   count=$(diff <(cat $ret_file_temp| awk '{print $7}') <(cat /etc/cron.d/ocifsbackupv2|awk '{print $7}') |wc -l)
   cat /etc/cron.d/ocifsbackupv2 >> $test_log
   if [[ $count -eq 0 ]];then
    output=0
  else
    output=1
  fi
  echo $output
}
verify_oci_config() {
  echo "verify_oci_config starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils; commonutils.download_passwd_file()' >> $test_log
  output=$?
  if [[ $output -eq 0 ]];then
    rm -f $BACKUP_CFG_LOCATION/.passwd.json
  fi
  echo $output
}
verify_passwd_json() {
  echo "verify_passwd_json starts here ######################" >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/.passwd.json | wc -l >> $test_log)
   if [[ $count -eq 0 ]];then
    output=0
  else
    output=1#should not be available
  fi
  echo $output
}
verify_backup_artifacts() {
  echo "verify_backup_artifacts starts here ######################" >> $test_log
  art_file='${BASE_DIR}/config/db/db_artifacts.json'
  chmod 755 ${BASE_DIR}/utils/test/templates/db_artifacts.json.template
  ret_file_temp='${BASE_DIR}/utils/test/templates/db_artifacts.json.template'
  cat ${BASE_DIR}/config/mt/config-retention-policy_v2.json >> $test_log
  file_diff=$(diff -y -B -w --suppress-common-lines $ret_file $ret_file_temp | wc -l)
  if [[ $file_diff -eq 0 ]];then
    output=0
  else
    output=1
  fi
  echo $output
}
verify_backup_exception() {
  echo "verify_backup_exception starts here ######################" >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/db_backup_exceptions.txt | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    cat ${BASE_DIR}/config/db/db_backup_exceptions.txt >> $test_log
    output=0
  fi
  echo $output
}
verify_node_exception() {
  echo "verify_node_exception starts here ######################" >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/db_node_exceptions.txt | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    cat ${BASE_DIR}/config/db/db_node_exceptions.txt >> $test_log
    output=0
  fi
  echo $output
}
verify_housekeeping() {
  echo "verify_housekeeping starts here ######################" >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/housekeeping-db_v2.json | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    cat ${BASE_DIR}/config/db/housekeeping-db_v2.json >> $test_log
    output=0
  fi
  echo $output
}
verify_sre_db_config() {
  echo "verify_sre_db_config starts here ######################" >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/sre_db.cfg | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    cat ${BASE_DIR}/config/db/sre_db.cfg >> $test_log
    output=0
  fi
  echo $output
}
verify_database_config() {
  echo "verify_oci_config starts here ######################" >> $test_log
  BACKUP_CFG_LOCATION="${BASE_DIR}/config/db/"
  python ${BASE_DIR}/lib/python/db/database_config.py >> $test_log
  output=$?
  if [[ $output -eq 0 ]];then
    rm -f $BACKUP_CFG_LOCATION/.passwd.json
  fi
  echo $output
}
db_archivelog_to_oss(){
  echo "verify_archivelog_to_oss starts here ######################" >> $test_log
  commandstr="su oracle -c 'source /home/oracle/$dbname.env ;${BASE_DIR}/bin/rman_oss.sh --dbname=$dbname -b archivelog_to_oss' >> $test_log"
  eval $commandstr
  output=$?
  echo $output
}
db_incre_to_reco_arch_to_oss() {
  echo "verify_incre_to_reco_arch_to_oss starts here ######################" >> $test_log
  commandstr="su oracle -c 'source /home/oracle/$dbname.env ;${BASE_DIR}/bin/rman_oss.sh --dbname=$dbname -b incre_to_reco_arch_to_oss' >> $test_log"
  eval $commandstr
  output=$?
  echo $output
}
db_to_reco_db_arch_to_oss() {
   echo "verify_db_to_reco_db_arch_to_oss starts here ######################" >> $test_log
   commandstr="su oracle -c 'source /home/oracle/$dbname.env ;${BASE_DIR}/bin/rman_oss.sh --dbname=$dbname -b db_to_reco_db_arch_to_oss' >> $test_log"
   eval $commandstr
   output=$?
   echo $output
  }

all_db_archivelog_to_oss() {
  echo "verify_archivelog_to_oss starts here ######################" >> $test_log
  ${BASE_DIR}/bin/rman_wrapper_oss.sh -b archivelog_to_oss >> $test_log
  output=$?
  echo $output
}
all_db_incre_to_reco_arch_to_oss() {
  echo "verify_incre_to_reco_arch_to_oss starts here ######################" >> $test_log
  ${BASE_DIR}/bin/rman_wrapper_oss.sh -b incre_to_reco_arch_to_oss >> $test_log
  output=$?
  echo $output
}
all_db_db_to_reco_db_arch_to_oss() {
  echo "verify_db_to_reco_db_arch_to_oss starts here ######################" >> $test_log
  ${BASE_DIR}/bin/rman_wrapper_oss.sh -b db_to_reco_db_arch_to_oss >> $test_log
  output=$?
  echo $output
}
verify_wallet_backup() {
  echo "verify_wallet_backup starts here ######################" >> $test_log
  python ${BASE_DIR}/bin/db_wallet_backup.py --action backup -t oss --dbname $dbname --retention-days 60
  output=$?
  echo $output
}
verify_artifacts_backup() {
  echo "verify_artifacts_backup starts here ######################" >> $test_log
  python ${BASE_DIR}/bin/db_artifacts_backup.py --action backup -t oss --dbname $dbname --retention-days 60
  output=$?
  echo $output
}
verify_db_query_pool() {
  echo "verify_db_to_reco_db_arch_to_oss starts here ######################" >> $test_log
  commandstr="su oracle -c 'source /home/oracle/{dbname}.env ;source ${BASE_DIR}/lib/python/common/setpyenv.sh ;python ${BASE_DIR}/lib/python/db/db_query_pool.py query.txt'>> $test_log"
  eval $commandstr
  output=$?
  echo $output
}
#common utils ############################
verify_sec_node_connectivity(){
  #implement here
  echo "verify_sec_node_connectivity starts here ######################" >> $test_log
  node_con=`python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/utils/test_automation");import common_test; print(common_test.get_ols_host_conn('\"$dbname\"'))'`
  echo $node_con >> $test_log
  if [[ $node_con == 'True' ]];then
    output=0
  else
    output=1
  fi
  echo $output
}
get_dbname_db_count(){
  #implement here
  echo "get_dbname_db_count starts here ######################" >> $test_log
  db_count=`python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils; print(commonutils.get_dbname_db_count('\"$dbname\"'))'`
  #db_count greater than 0 success else failed
  echo $db_count >> $test_log
  if [[ $db_count -eq 0 ]];then
    output=1
  else
    output=0
  fi
  echo $output

}
remove_backup_oss_passwd(){
  #implement here
  echo "remove_backup_oss_passwd starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils; commonutils.remove_backup_oss_passwd()' >> $test_log
  #get the count and display
  output=$?
  echo $output
}
get_dbname_db_nodes(){
  #implement here
  echo "get_dbname_db_nodes starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils; print(commonutils.get_dbname_db_nodes('\"$dbname\"'))' >> $test_log
  #get the count of db_nodes and list size greater than 0 its success else failed
  output=$?
  echo $output
}
gen_ols_node_csv(){
  #implement here
  echo "get_dbname_db_nodes starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils;commonutils.gen_ols_node_csv()' >> $test_log
  output=$?
  echo $output
}
get_gi_home(){
  #implement here
  echo "get_gi_home starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils;commonutils.get_gi_home()' >> $test_log
  output=$?
  echo $output
}
load_databse_variables(){
  #implement here
  echo "get_gi_home starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common");import commonutils;commonutils.load_databse_variables('\"$dbname\"')' >> $test_log
  output=$?
  echo $output
}

# database_config ############################
verify_passwd_download(){
  echo "verify_passwd_download starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/db");import commonutils; commonutils.download_passwd_file()' >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/.passwd.json | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    output=0
    rm -f ${BASE_DIR}/config/db/.passwd.json
  fi
  echo $output
}
restore_backup_oss_passwd(){
  echo "update_password starts here ######################" >> $test_log
  file="sre_db.cfg"
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/db");import database_config; print(database_config.restore_backup_oss_passwd('\"$file\"'))' >> $test_log
  count=$(ls -latr ${BASE_DIR}/config/db/.passwd.json | wc -l)
   if [[ $count -eq 0 ]];then
    output=1
  else
    output=0
    rm -f ${BASE_DIR}/config/db/.passwd.json
  fi
  echo $output
}

update_all_pod_flag(){
  echo "update_password starts here ######################" >> $test_log
  file="sre_db.cfg"
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/db");import database_config; database_config.update_all_pod_flag('\"$dbname\"')' >> $test_log
  output=$?
  cat "/opt/faops/spe/ocifabackup/utils/db/all-pod-info_"$hostname".txt"
  echo $output
}

#rman_wrapper ################

take_full_backup_other_node(){
  #implement here
  echo "take_full_backup_other_node starts here ######################" >> $test_log
  csv_file='/u02/backup/log/'+$hostname'/exalogs/ldb_exec_states.csv'
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/bin");import rman_wrapper;rman_wrapper.take_full_backup_other_node("",'\"$dbname\"','\"$csv_file\"')' >> $test_log
  output=$?
  echo $output
}

#validate rpmupdates
verify_upgrade_rpm(){
  #implement here
  echo "verify_upgrade_rpm starts here ######################" >> $test_log
  python -c 'import sys;sys.path.append("/opt/faops/spe/ocifabackup/lib/python/common")' >> $test_log
  output=$?
  echo $output
}

#validate even node

validate_sbttest(){
  #implement here
  echo "validate_sbttest starts here ######################" >> $test_log
  DB_SHELL_SCRIPT_PATH="${BASE_DIR}/utils/db/scripts/shell"
  DB_BACKUP_LOG_PATH="/u02/backup/log/${hostname}"
  su oracle -c "${DB_SHELL_SCRIPT_PATH}/check_swiftobj_oss.sh ${dbname}" >>$test_log
  output=$?
  echo $output
}

#main starts here
CT_METHOD=$1
test_log=$2
dbname=$3
#test validate method
result=$($CT_METHOD)
echo $result
