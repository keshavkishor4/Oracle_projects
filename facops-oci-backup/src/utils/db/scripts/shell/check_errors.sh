#!/bin/bash
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh

error_patterns=$BASE_DIR/config/db/error_patterns.txt
HOST_NAME=$(hostname -s)

IFS=| read -ra values <<< "$(cat $error_patterns)"
for pattern in $;do
    echo $pattern
    # ls -latr /u02/backup/log/${HOST_NAME}/exalogs/*run* |tail -30 | awk '{print $9}' | xargs grep -i $pattern
done