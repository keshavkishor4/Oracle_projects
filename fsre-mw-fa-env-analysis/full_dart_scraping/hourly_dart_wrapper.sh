BASE_DIR="/scratch/faopscb/fa_env_analysis"
LOG_DIR="${BASE_DIR}/mining_logs"
DATE=$(date +'%Y%m%d_%H%M%S')
source "${BASE_DIR}/setpyenv.sh"
proj_path="/scratch/faopscb/fa_env_analysis/fsre-mw-fa-env-analysis"
# json_path="${proj_path}/out_data/dart_data/${dart_date_2}"

function start_mining(){
    # start_date=$1
    # end_date=$2
    # DART_data_start="${start_date}:01"
    # DART_data_end="${end_date}:23"

    LOG_FILE="${LOG_DIR}/mining_logs_${DATE}.log"
    /usr/bin/script -f $LOG_FILE /bin/bash -c "${proj_path}/full_dart_scraping/hourly_dart_mining_wrapper.py"
    # python3 ${proj_path}/full_dart_scraping/dart_mining_wrapper.py "${DART_data_start}" "${DART_data_end}" >> ${json_dump_log} 2>> ${json_dump_log}

    if [[ $? -eq 0 ]]; then
    echo "exec status :: SUCCESS" >> ${LOG_FILE}
    else
    echo "exec status :: ### FAIL ###" >> ${LOG_FILE}
    fi

    script_end_time=$(date '+%Y-%m-%d %H:%M')
    echo -e "#script_end_time => ${script_end_time}" >> ${LOG_FILE}

    echo -e "\n-----------------------------------------------------------------\n" >> ${LOG_FILE}

    # echo -e "\nMost recent json dumps at: ${json_path}" >> ${LOG_FILE}
    # $(ls -lrt ${json_path} | tail -6 >> ${json_dump_log}) 

}

# start_date=$1
# end_date=$2

# if [ ! -z "$start_date" ] && [ ! -z "$end_date" ] ;then
    # pre_checks
start_mining 
# else
#     echo "usage: ./dart_mining_wrapper_new.sh 2023-12-08 2023-12-09"
#     echo "nohup usage: nohup sh full_dart_scraping/dart_mining_wrapper_new.sh 2023-10-25 2023-10-25 >/dev/null 2>&1 &"
#     exit 1
# fi

#done
