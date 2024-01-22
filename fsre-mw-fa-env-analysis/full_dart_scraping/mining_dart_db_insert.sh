#!/bin/bash


days_back=59
dart_date_1=$(date --date="${days_back} days ago" "+%Y-%m-%d")
dart_date_2=$(date --date="${days_back} days ago" "+%Y%m%d")

proj_path="/scratch/faopscb/fa_env_analysis/fsre-mw-fa-env-analysis"
json_path="${proj_path}/out_data/dart_data/${dart_date_2}"

json_files=$(ls ${proj_path}/out_data/dart_data/${dart_date_2}/*.json | wc -l)
echo "ls ${proj_path}/out_data/dart_data/${dart_date_2}/*.json"

if [[ $json_files > 0 ]]; then
  echo "DB insert"
  json_dbinsert_log="${proj_path}/out_data/dart_data/${dart_date_2}/json_dump_cron.log"
  echo "" > ${json_dbinsert_log}
  echo "json_dbinsert_log = ${json_dbinsert_log}"

  echo -e "\n-------------------------------------------------------\n" >> ${json_dbinsert_log}

  script_start_time=$(date '+%Y-%m-%d %H:%M')
  echo -e "\nscript_start_time => ${script_start_time}" >> ${json_dbinsert_log}

  echo -e "DART data Date = ${dart_date_1}" >> ${json_dbinsert_log}
  source /scratch/faopscb/fa_env_analysis/setpyenv.sh
  source /scratch/faopscb/fa_env_analysis/faopsdb.env
  python3 ${proj_path}/full_dart_scraping/mining_dart_db_insert.py >> ${json_dbinsert_log} 
  echo "python3 ${proj_path}/full_dart_scraping/mining_dart_db_insert.py >> ${json_dbinsert_log}"

  if [[ $? -eq 0 ]]; then
    echo "script exec status :: SUCCESS" >> ${json_dbinsert_log}
  else
    echo "script exec status :: ### FAIL ###" >> ${json_dbinsert_log}
  fi

  script_end_time=$(date '+%Y-%m-%d %H:%M')
  echo -e "#script_end_time => ${script_end_time}" >> ${json_dbinsert_log}

  echo -e "\n-------------------------------------------------------\n" >> ${json_dbinsert_log}
else
  echo -e "\n # NO json to insert #, exiting ..."
  exit
fi




