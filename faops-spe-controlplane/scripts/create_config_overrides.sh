#!/bin/bash -x

#
# Copyright (c) 2018, Oracle and/or its affiliates. All rights reserved.
#

REGION=$1
CONFIG_DIR=$2
SERVER=$3
OVR_DIR=$4

SCRIPTPATH=$(cd `dirname $0` && pwd)

data_enc_secret=`python ${SCRIPTPATH}/get_data_enc_secret.py --region ${REGION} --config_dir ${CONFIG_DIR} --server ${SERVER}`
case "$data_enc_secret" in
  *Exception*)
   echo "$data_enc_secret"
   exit -1
  ;;
esac
echo "DataEncSecret=${data_enc_secret}" >> ${OVR_DIR}/override.properties
