#!/bin/bash

#days_back=57
#dart_date_1=$(date --date="${days_back} days ago" "+%Y-%m-%d")
#dart_date_2=$(date --date="${days_back} days ago" "+%Y%m%d")
dart_date_1="2023-11-02"
dart_date_2=$(echo ${dart_date_1} | sed 's/-//g')

proj_path="/scratch/faopscb/fa_env_analysis/fsre-mw-fa-env-analysis"
json_path="${proj_path}/out_data/dart_data/${dart_date_2}"
mkdir -p $json_path
json_dump_log="${proj_path}/out_data/dart_data/${dart_date_2}/dart_dump_${dart_date_2}_cron.log"

echo "" > ${json_dump_log}
echo "json_dump_log = ${json_dump_log}"

echo -e "\n-----------------------------------------------------------------\n" >> ${json_dump_log}

DART_data_start="${dart_date_1}:01"
DART_data_end="${dart_date_1}:23"
echo -e "DART data fetch Duration = ${DART_data_start} -- ${DART_data_end}" >> ${json_dump_log}

script_start_time=$(date '+%Y-%m-%d %H:%M')
echo -e "\nscript_start_time => ${script_start_time}" >> ${json_dump_log}

source /scratch/faopscb/fa_env_analysis/setpyenv.sh
#python3 ${proj_path}/full_dart_scraping/dart_mining_wrapper.py "${DART_data_start}" "${DART_data_end}" ['HCRI'] >> ${json_dump_log}
python3 ${proj_path}/full_dart_scraping/dart_mining_wrapper.py "${DART_data_start}" "${DART_data_end}" >> ${json_dump_log} 2>> ${json_dump_log}

if [[ $? -eq 0 ]]; then
  echo "exec status :: SUCCESS" >> ${json_dump_log}
else
  echo "exec status :: ### FAIL ###" >> ${json_dump_log}
fi

script_end_time=$(date '+%Y-%m-%d %H:%M')
echo -e "#script_end_time => ${script_end_time}" >> ${json_dump_log}

echo -e "\n-----------------------------------------------------------------\n" >> ${json_dump_log}

echo -e "\nMost recent json dumps at: ${json_path}" >> ${json_dump_log}
$(ls -lrt ${json_path} | tail -6 >> ${json_dump_log}) 

#done
