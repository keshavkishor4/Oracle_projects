#!/bin/bash
PWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
source ${PWD}/env.sh
source ${BASE_DIR}/lib/python/common/setpyenv.sh
ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3 | grep $1