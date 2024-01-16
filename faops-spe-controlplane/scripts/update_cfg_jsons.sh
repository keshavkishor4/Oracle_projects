#!/bin/bash -x

TYPE=$1
LOCAL_DIR=$2
DB_NAME=$3
DB_PWD=$4
DB_NODE=$5
DB_DOMAIN=$6
LBR=$8

function usage()
{
  echo "Usage: $0 type local_work_dir database_name database_password database_node database_domain [load_balancer]
Where
  type              : Instance type value can be podmgr or saasmgr
  database_name     : Database name to be update in config file
  database_password : Database password to be encoded and updated
  database_nodei    : Database node to be updated in JDBC URL
  database_domain   : Domain name of Database
  load_balancer     : Load Balancer Host, applies to saasmgr only"
  exit 1
}

if [ "$#" -eq 0 ]; then
  usage
fi

if [ "$LOCAL_DIR" == "" -o ! -d "$LOCAL_DIR" ]; then
  echo "Local Directory must be valid and existing"
  usage
fi

if [ "$TYPE" == "podmgr" ]
then
  OBJ_URL="https://objectstorage.us-phoenix-1.oraclecloud.com/p/XNFQR9RCN8nXl1vbQkyIZqOYY9KHiN4LXGaOk288DDs/n/oraclefaonbm/b/falcm-podmgr/o/falcm-podmgr-config.tgz"
  ARCHIVE="falcm-podmgr-config.tgz"
elif [ "$TYPE" == "saasmgr" ]
then
  OBJ_URL="https://objectstorage.us-phoenix-1.oraclecloud.com/p/Zo2Lx2ojMnFLazuNaRxjION0DWq-wllGHGIxaa3BFU0/n/oraclefaonbm/b/falcm-saasmgr/o/falcm-saasmgr-config.tgz"
  ARCHIVE="falcm-saasmgr-config.tgz"
else
  echo "TYPE must be 'podmgr' or 'saasmgr'"
  usage
fi

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

if [ -d "${LOCAL_DIR}/${TYPE}" ]
then
  echo "${LOCAL_DIR}/${TYPE} directory exists deleting it"
  rm -rf "${LOCAL_DIR}/${TYPE}"
fi

echo "Downloading ${ARCHIVE} from Object Store"
mkdir "${LOCAL_DIR}/${TYPE}"
cd $LOCAL_DIR/$TYPE
curl -O $OBJ_URL
echo "Untaring ${ARCHIVE}"
tar -xvzf $ARCHIVE

#
# HACK!!! ConfigHelper does not suppport produciton mode yet
#
mv ./.falcm/cfg/prod-cfg.json  ./.falcm/cfg/test-cfg.json
mv ./.falcm/cfg/.prod-priv.key ./.falcm/cfg/.test-priv.key
mv ./.falcm/cfg/prod-pub.key ./.falcm/cfg/test-pub.key

cd $SCRIPTPATH/../../modules/common

java  -Dfalcm.home=$LOCAL_DIR/$TYPE/.falcm -Dfalcm.cfg.home=$LOCAL_DIR/$TYPE/.falcm/cfg -cp build/libs/.:build/libs/* oracle.fa.lcm.config.impl.ConfigHelper -inject -subsystem persist -attrpath "password" -value "$DB_PWD" -enc
java  -Dfalcm.home=$LOCAL_DIR/$TYPE/.falcm -Dfalcm.cfg.home=$LOCAL_DIR/$TYPE/.falcm/cfg -cp build/libs/.:build/libs/* oracle.fa.lcm.config.impl.ConfigHelper -inject -subsystem persist -attrpath "url" -value "jdbc:oracle:thin:@//$DB_NODE:1521/${DB_NAME}.${DB_DOMAIN}"

if [ "$TYPE" == "saasmgr" ]
then
  java  -Dfalcm.home=$LOCAL_DIR/$TYPE.falcm -Dfalcm.cfg.home=$LOCAL_DIR/$TYPE/.falcm/cfg -cp build/libs/.:build/libs/* oracle.fa.lcm.config.impl.ConfigHelper -inject -subsystem rest -attrpath "public_url" -value "http://${LBR}:7001/falcm-saasmgr/provisioning"
fi

#
# HACK!!! Convert the test files to prod version 
#
cd $LOCAL_DIR/$TYPE
mv ./.falcm/cfg/test-cfg.json  ./.falcm/cfg/prod-cfg.json
mv ./.falcm/cfg/.test-priv.key ./.falcm/cfg/.prod-priv.key
mv ./.falcm/cfg/test-pub.key ./.falcm/cfg/prod-pub.key

