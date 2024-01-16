#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      commonutils.py
    DESCRIPTION
      implement all common methods
    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
"""
#### imports start here ##############################
import re
import socket
import ssl
import sys
import os
import urllib.request
import json
from subprocess import Popen, PIPE
from time import strftime, gmtime

import requests
import traceback
try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import globalvariables,instance_metadata,commonutils,apscom,ociSDK
try:
    from db import database_config 
except ImportError:
    pass
# 
try:
    from mt import apssqldb
except:
    pass
#### imports end here ##############################
# Fix metadata urls
log_file = ""
status_code=''
 
def get_namespace_from_sre():
    try:
        namespace = ''
        inst_meta = instance_metadata.ins_metadata()
        sytem_cata = inst_meta.system_category
        if sytem_cata == 'Exadata':
            if not os.path.exists("{0}/sre_db.cfg".format(globalvariables.DB_CONFIG_PATH)):
                database_config.gen_sre_db_config()
            with open(globalvariables.ARTIFACTS_BACKUP_PATH + '/bkup_ocifsbackup_sre.cfg', 'r') as fp:
                lines = fp.readlines()
                for line in lines:
                    if "swiftobjectstorage" in line:
                        namespace = line.split("=")[1].split("/")[-2]
            if namespace == '':
                if os.path.exists(globalvariables.OCI_SDK_META_FILE):
                    with open(globalvariables.OCI_SDK_META_FILE,'r') as data:
                        oci_meta_data=json.load(data)
                        namespace = oci_meta_data["ns"]

        else:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600)
            namespace = object_storage.get_namespace().data
        return namespace
    except Exception as e:
        message = "Failed to get namespace  {0}".format(e)
        apscom.warn(message)
        raise
def validate_namespace():
    try:
        # Get Env and set catalog db URL
        valid_ns = False
        namespace=get_namespace_from_sre()
        if not namespace:
            message = "oss_user or tenancy cannot be determined, ensure {0} is correctly filled".format(
                globalvariables.ARTIFACTS_BACKUP_PATH + '/bkup_ocifsbackup_sre.cfg')
            apscom.warn(message)
            return False
        with open(globalvariables.CONFIG_PATH+'/faops-backup-oss-info.json','r') as oss_info:
            data = json.load(oss_info)
            for val in data:
                if namespace in val:
                    valid_ns=True
        if not valid_ns:
            message = "{0} do not belongs to standard FA tenancy  ".format(namespace)
            apscom.warn(message)
        return valid_ns,namespace
    except Exception as e:
        message = "Failed to validate namespace ! {0}".format(e)
        apscom.warn(message)
        raise

def create_backup_metadata(action, backup_type, backup_list, retention_days, tag, catalog_type, backup_status,log_file):
    """ Create backup metadata.
    Args:
        backup_type (str): combine argument storage-type and backup-options
                           snapshost_to_fss - Both files and fs snapshot to fss.
                           full_to_fss - To be supported.
                           snapshot_to_oss - Files to oss, fs snapshot to fss.
                           full_to_oss - Both files and fs to oss.

        backup_list (list): List of backup data, the last one is info of backup files.
                            If snapshot_to_fss and full_to_fss, [snap_ocid_1, ..., snap_ocid_n, files_path]
                            If snapshot_to_oss, [snap_ocid_1, ..., snap_ocid_n, files_obj_name]
                            If full_to_oss, [snap_obj_name_1, ..., snap_obj_name_n, files_path]
                                - For this backup, only snapshot object is sent to oss,
                                - as backup files also included in some snapshot object.
                                - files_path is only used for recovery to get the backup files.
        retention_days (int): Retention days of this backup.
    Returns:
        backup_metadata (dict): Info of backup metadata.
    """
    try:
        backup_start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        inst_meta=instance_metadata.ins_metadata()
        mt_backup_db = None
        backup_tool = "faops_ocifsbkup"

        backup_end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        # backup_status = "UNKNOWN"
        backup_metadata = {}

        metadata_t = open(globalvariables.BACKUP_METADATA_TEMPLATE, 'r')
        metadata_data = json.load(metadata_t)
        metadata_t.close()

        piece_name = ",".join(backup_list)
        client_type = inst_meta.system_type
        pod_name = inst_meta.fa_service_name
        region_name = inst_meta.region
        fadb_connstr = inst_meta.fadb_connstr
        # Instance metadata
        inst_metadata = inst_meta.post_inst_metadata
        # Format fadb_connstr
        p = re.compile('[A-Za-z0-9=._-]+')
        strings = p.findall(fadb_connstr)
        DBHOSTS = ""
        DBSERVICE = ""
        for val in strings:
            if 'HOST' in val:
                key, value = val.split('=')
                DBHOSTS += value + ','
            if 'SERVICE_NAME' in val:
                key, value = val.split('=')
                DBSERVICE = value
        if not DBHOSTS:
            pass
        else:
            DBHOSTS = DBHOSTS[:-1]
        #

        # if action == "backup" or action == "create-snapshot":
        #   backup_status = "ACTIVE"
        #
        #
        backup_metadata["BACKUP_TOOL"] = backup_tool
        backup_metadata["BTIMESTAMP"] = backup_start_time
        backup_metadata["ETIMESTAMP"] = backup_end_time
        backup_metadata["HOSTNAME"] = globalvariables.LOCAL_HOST
        backup_metadata["CLIENT_NAME"] = globalvariables.LOCAL_HOST
        backup_metadata["CLIENT_TYPE"] = client_type
        backup_metadata["PODNAME"] = pod_name
        backup_metadata["LOG_FILE"] = log_file
        backup_metadata["BACKUP_TYPE"] = backup_type
        backup_metadata["TARGET_TYPE"] = backup_type.rsplit("_", 1)[1].upper()
        backup_metadata["TARGET_LOCATION"] = backup_type.rsplit("_", 1)[1].upper()
        backup_metadata["PIECE_NAME"] = piece_name
        backup_metadata["RETENTION_DAYS"] = retention_days
        backup_metadata["STATUS"] = backup_status
        backup_metadata["TAG"] = tag
        backup_metadata["DBSERVICE"] = DBSERVICE
        backup_metadata["DBHOSTS"] = DBHOSTS
        backup_metadata["RPM_VER"] = commonutils.get_rpm_ver()
        backup_metadata["OS_VER"] = commonutils.get_os_ver()
        backup_metadata["OSS_NAMESPACE"] = get_namespace_from_sre()

        if catalog_type == "local":
            # Upload to Catalog DB
            mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
            mt_backup_db.init_table(mt_backup_db, "backup_history_table_v2")

            # Update backup metadata to local backup DB.
            value_list = [backup_tool, backup_start_time.replace(" ", "T") + "Z",
                          backup_end_time.replace(" ", "T") + "Z", backup_type, piece_name, str(retention_days),
                          backup_status, pod_name, globalvariables.LOCAL_HOST, client_type, globalvariables.LOCAL_HOST,
                          log_file, tag]
            mt_backup_db.insert_table(mt_backup_db, "backup_history_table_v2", value_list)

            mt_backup_db.close()

            # Send local backup db to oss.
            oss_bucket = inst_meta.default_bucket
            object_created = ociSDK.ociSDK().put_object_multipart(globalvariables.BACKUP_SQLDB_PATH, oss_bucket,
                                                         globalvariables.OBJ_BACKUP_SQLDB)
            if not object_created:
                message = "Failed to upload backup db to oss!"
                apscom.warn(message)
            else:
                message = "Succeed to upload backup db to oss."
                apscom.info(message)
            # Upload to Catalog DB
            try:
                #
                metadata_data["backup"]["db_mt_os"][0] = backup_metadata
                # Save the backup metadata to a json file.
                metadata_report = open(globalvariables.BACKUP_METADATA_PATH, 'w')
                json.dump(metadata_data, metadata_report, indent=4, sort_keys=True)
                metadata_report.close()
                # Update backup metadata to central catalog DB.
                # Update CatalogdB log
                # post_backup_metadata_v2(region_name, metadata_data, inst_metadata)
                # post_backup_md(region_name, globalvariables.LOCAL_HOST, log_file)
                # oci_api.download_latest_ver_json()
               # rpmupdates.verify_upgrade_rpm()
            except Exception as e:
                message = "Failed to create metadata for this backup!, retrying ...\n{0}".format(sys.exc_info()[1:2])
                apscom.warn(message)
                pass
        else:
            metadata_data["backup"]["db_mt_os"][0] = backup_metadata

            # Save the backup metadata to a json file.
            metadata_report = open(globalvariables.BACKUP_METADATA_PATH, 'w')
            json.dump(metadata_data, metadata_report, indent=4, sort_keys=True)
            metadata_report.close()

            # Update backup metadata to central catalog DB.
            # if tag != "ocifsbackup_v2":
            #     post_backup_metadata_v2(region_name, metadata_data, inst_metadata)
            #
            # post_backup_md(region_name, globalvariables.LOCAL_HOST, log_file)
           # rpmupdates.verify_upgrade_rpm()

        return backup_metadata

    except Exception as e:
        message = "Failed to create metadata for this backup!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def post_database_exception():
    try:
        timestamp = strftime("%m%d%Y%H%M%S", gmtime())
        exce_dict = {}
        exceptions = ''
        except_path='{0}/{1}_db_backup_exceptions_{2}.json'.format(globalvariables.DB_CONFIG_PATH,globalvariables.HOST_NAME,timestamp)        
        with open(globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt", "r") as fp:
            lines = fp.readlines()
        for line in lines:
            if exceptions:
                exceptions = exceptions + ',' + line.rstrip()
            else:
                exceptions = line.rstrip()
        exce_dict['db_host'] = globalvariables.HOST_NAME
        exce_dict['db_backup_exceptipons']=exceptions
        exce_dict['timestamp'] = timestamp
        exce_report = open(except_path, 'w')
        json.dump(exce_dict, exce_report, indent=4, sort_keys=True, separators=(',', ':'))
        exce_report.close()
        # post_backup_md(instance_metadata.ins_metadata().region,globalvariables.HOST_NAME,except_path)
        os.remove(except_path)
    except Exception as e:
        message = "Failed to do post database exceptions"
        apscom.warn(message)
