#!/bin/bash

SHARED_STAGE=/fss/oci_backup/stage
CURRENT_RPM=`rpm -qa|grep backup`

RPM_TO_INSTALL=$1

if [ ! -z "${RPM_TO_INSTALL}" ]; then
   rpm -e $CURRENT_RPM
   rpm -ivh $RPM_TO_INSTALL
else
   rpm -ivh $RPM_TO_INSTALL
fi