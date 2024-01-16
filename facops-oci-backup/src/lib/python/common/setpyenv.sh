#!/bin/bash
BASE_DIR="/opt/faops/spe/ocifabackup"
os_ver=$(uname -r)
HOSTNAME=$(hostname -s)
# 

#SOEDEVSECOPS-1657:- Enhancement to use region certificates from server default location instead of using it from the python packages location


if [[ $os_ver =~ "el7" ]];then
  export PYTHONPATH=${BASE_DIR}/utils/python3/el7
  export PATH=$PYTHONPATH/bin:$BASE_DIR/utils:$BASE_DIR/utils/vnstat/bin:$PATH
  export LD_LIBRARY_PATH=$PYTHONPATH/lib:/opt/facs/casrepos/fa/APPLTOP/dbclient_12c/lib:$LD_LIBRARY_PATH
elif [[ $os_ver =~ "el6" ]];then
  export PYTHONPATH=${BASE_DIR}/utils/python3/el6
  export PATH=$PYTHONPATH/bin:$BASE_DIR/utils:$PATH
  export LD_LIBRARY_PATH=$PYTHONPATH/lib:/opt/facs/casrepos/fa/APPLTOP/dbclient_12c/lib:$LD_LIBRARY_PATH
fi
# 
if [[ -f "${BASE_DIR}/config/${HOSTNAME}_instance_md.json" ]];then
  realm=$(jq -r '.regionInfo.realmKey' ${BASE_DIR}/config/${HOSTNAME}_instance_md.json 2>/dev/null)
else
  curlto=10
  realm=$(curl -m ${curlto} -L http://169.254.169.254/opc/v1/instance/regionInfo/realmKey 2>/dev/null)
fi

if [ "${realm}" != "oc1" ] && [ "${realm}" != "oc4" ];then
  export REQUESTS_CA_BUNDLE=/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
fi

