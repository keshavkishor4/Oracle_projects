#!/bin/bash
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
#verify permissions of cron
verify_cron() {
   echo "verify_cron starts here ######################" >> $test_log
   #testing
    count=`ls -ltr /etc/cron.d/ocifsbackup* | wc -l`
   if [[ $count -eq 0 ]];then
    output=1
   else
    output=0
  fi
  echo $output
}
verify_retention_policy() {
  echo "verify_retention_policy starts here ######################" >> $test_log
  ret_file='/opt/faops/spe/ocifabackup/config/mt/config-retention-policy_v2.json'
  ret_file_temp='/opt/faops/spe/ocifabackup/utils/test/templates/config-retention-policy_v2.json.template'
  cat /opt/faops/spe/ocifabackup/config/mt/config-retention-policy_v2.json >> $test_log
  file_diff=$(diff -y -B -w --suppress-common-lines $ret_file $ret_file_temp | wc -l)
  if [[ $file_diff -eq 0 ]];then
    output=0
  else
    output=1
  fi
  echo $output
}
fss_list_backup() {
  echo "fss_list_backup starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup.py --action list-backups --catalog-type local >> $test_log
  output=$?
  echo $output
}

fss_cleanup() {
  echo "fss_cleanup starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup.py --action cleanup --catalog-type local >>$test_log
  output=$?
   echo $output
}
fss_backup() {
  echo "fss_backup starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup.py --action backup --storage-type fss --backup-options snapshot --catalog-type local >>$test_log
  output=$?
   echo $output
}
bv_verfify_config_file() {
  echo "bv_verfify_config_file starts here ######################" >> $test_log
  cat /opt/faops/spe/ocifabackup/config/mt/backup_config/bv_backup.json >>$test_log
  output=$?
   echo $output
}
bv_list() {
  echo "bv_list starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup_v2.py --action list-backups --target oss >>$test_log
  output=$?
   echo $output
}
bv_post_metada() {
  echo "bv_post_metada starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup_v2.py --action post-metadata >>$test_log
  output=$?
  echo $output

}
bv_cleanup() {
  echo "bv_cleanup starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup_v2.py --action cleanup --target oss >>$test_log
  output=$?
   echo $output
}
bv_backup() {
  echo "bv_backup starts here ######################" >> $test_log
  python /opt/faops/spe/ocifabackup/bin/ocifsbackup_v2.py --action backup --target oss >>$test_log
  output=$?
   echo $output
}

#main starts here
source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
CT_METHOD=$1
test_log=$2
#test validate method
result=$($CT_METHOD)
echo $result