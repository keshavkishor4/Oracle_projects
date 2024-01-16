#!/bin/bash
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh
PY_VER=$(python -c "import oci;import paramiko;import sys;print(sys.version_info.major)" 2>/dev/null)

#echo $PY_VER
SCRIPT_FILE=${BASE_DIR}/lib/python/common/update_password_json.py
if [[ "$PY_VER" -eq 3 ]]; then
    if [[ -f "$SCRIPT_FILE" ]];then
        echo "File exist and now we will run to update password json file into bucket"
        ${BASE_DIR}/lib/python/common/update_password_json.py
    else
        echo "Script file does not exist"
    fi
else
    echo "Python version is not updated so exiting out..."
fi

if [ $? -ne 0 ]; then
    echo "Last command to execute python script does not executed successfully"
fi