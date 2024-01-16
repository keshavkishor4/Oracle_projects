#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      update_password_json.py
    DESCRIPTION
      Update Password json into buckets
    NOTES

    MODIFIED        (MM/DD/YY)

    Keshav Kishor     08/04/22 - initial version (code refactoring)
"""
import os
import shutil
import socket
import sys
import json
from datetime import datetime, timedelta
import glob
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import multiprocessing
import instance_metadata
import commonutils,apscom
import globalvariables
import backoff
import ociSDK,post_backup_metadata
from datetime import datetime
import traceback
from time import strftime, gmtime
from pathlib import Path
global log_dir 
global logfile 
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
lock_file_path = globalvariables.lock_file_path
lock_file_name = globalvariables.lock_file_name
password_file_name = globalvariables.password_file_name
password_file_path = globalvariables.password_file_path
config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
oci_sdk=ociSDK.ociSDK(config_file)
Passwd_update_enable_file = "{0}/.passwd_enable_flag.json".format(globalvariables.CONFIG_PATH)

def update_password_json_oss(logfile):
    try:
        oss_bucket = commonutils.get_bucket_details_from_oss()
        my_date = datetime.now()
        day = my_date.day
        day_name = datetime.today().strftime('%A')
        format_data1 = globalvariables.format_data1
        if os.path.exists(Passwd_update_enable_file):
            with open(Passwd_update_enable_file) as f:
                enable_flag=json.load(f)
                enable_flag = enable_flag["enable_flag_value"].strip()
        if enable_flag == "y":
            if day_name == "Thursday" and  day <= 7:
                gen_json_password_file(logfile, "PRE", "START")
                status = oci_sdk.get_object_lock_passwdjson(lock_file_name,oss_bucket)
                if (status != 404):
                    message = "File name {0} avaialable in oss bucket {1}".format(lock_file_name,oss_bucket)
                    apscom.info(message)
                    gen_json_password_file(logfile, "POST", "STOP")
                else:
                    if os.path.exists(lock_file_path):
                        oci_sdk.upload_file_passwdjson(lock_file_path, lock_file_name,oss_bucket)
                        file_data = oci_sdk.list_object_passwdjson(oss_bucket)
                        time_file1 = json.loads(file_data)
                        time_file = time_file1[0]['time_created'][0:19]
                        object_time = datetime.strptime(time_file, format_data1)
                        time_diff = (my_date - object_time).days
                        if time_diff > 60:
                            oci_sdk.update_passwdjson(password_file_path,password_file_name,oss_bucket)
                            oci_sdk.delete_object_OSS_passwdjson(lock_file_name,oss_bucket)
                            gen_json_password_file(logfile, "POST", "SUCCESS")
                        else:
                            oci_sdk.delete_object_OSS_passwdjson(lock_file_name,oss_bucket)
                            gen_json_password_file(logfile, "POST", "SUCCESS")
                    else:
                        Path(lock_file_path).touch()
                        oci_sdk.upload_file_passwdjson(lock_file_path, lock_file_name,oss_bucket)
                        file_data = oci_sdk.list_object_passwdjson(oss_bucket)
                        time_file1 = json.loads(file_data)
                        time_file = time_file1[0]['time_created'][0:19]
                        object_time = datetime.strptime(time_file, format_data1)
                        time_diff = (my_date - object_time).days
                        if time_diff > 60:
                            oci_sdk.update_passwdjson(password_file_path,password_file_name,oss_bucket)
                            oci_sdk.delete_object_OSS_passwdjson(lock_file_name,oss_bucket)
                            gen_json_password_file(logfile, "POST", "SUCCESS")
                        else:
                            oci_sdk.delete_object_OSS_passwdjson(lock_file_name,oss_bucket)
                            gen_json_password_file(logfile, "POST", "SUCCESS")
        else:
            message = "Host {0} is not authorised to update password file into bucket".format(globalvariables.HOST_NAME)
            apscom.info(message)
                      
    except Exception as e:
        gen_json_password_file(logfile, "POST", "FAILED")
        message = "{0} file not updated peoperly in bucket {1}".format(password_file_name,oss_bucket)
        apscom.warn(message)

def gen_json_password_file(logfile,pre_post_flag,status):
    try:
        timestamp = strftime("%m%d%Y%H%M%S", gmtime())
        logfile_location = globalvariables.EXALOGS_PATH + "/"
        file_name=logfile_location+globalvariables.HOST_NAME+"_password_json_upload_"+"_"+timestamp+"_"+pre_post_flag+".json"
        data=create_backup_metadata(logfile,pre_post_flag,status)
        with open(file_name, 'w') as outfile:
            json.dump(data, outfile,indent=4, sort_keys=True)
        outfile.close()
    except Exception as e:
        message = "Failed to generate json!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

def create_backup_metadata(logfile,pre_post_flag,status,host=None):
    """ Create backup metadata.
    Args:
        log_file (str): oss/fss
        type (str): backup path if backup target is fss
                           object name if backup target is oss
    Returns:
        backup_metadata (dict): Info of backup metadata.
    """
    single_tag = ""
    target_location = ""
    target_type = ""
    db_info = []
    start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    BREAKGLASS_ENABLED = ''
    DB_BACKUP_SIZE = ''
    json_query_output = {}
    piece_info = ''
    tag=''
    try:
        backup_end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        backup_metadata = {}
        metadata_t = open(globalvariables.BACKUP_METADATA_TEMPLATE, 'r')
        metadata_data = json.load(metadata_t)
        metadata_t.close()

        # retention_days=14
        retention_days = globalvariables.ENV_TYPE_PROD
        try:
            if logfile:
                tag_str = "grep \'^piece handle=\' {0} | grep tag|awk -F'[ =]'  \'{{print $5}}\'| sort -u |tr '\\n' ','| sed 's/,$//g'|sed 's/^,\{{1\}}//'".format(logfile)
                tag = commonutils.execute_shell(tag_str)[0]
                single_tag=tag.split(',')[0]
            else:
                tag=''
        except Exception as e:
            message = "failed to get piece info , error: {0}".format(e)
            apscom.warn(message)
            single_tag=""
            pass


        if not host:
           host = globalvariables.LOCAL_HOST
        # whenever a file name starts with pdb_ , should pass the container value query_output["PDB_NAME"]
        # if file name starts with cdb_ , dont pass container name
        # get metadata from commonutils
        #db_unique_name=json_query_output["DB_UNIQUE_NAME"]
        #general_metadata = get_metadata_info(db_unique_name)
        # Generate backup metadata
        backup_metadata["BACKUP_TOOL"] = ".passwd.json"
        backup_metadata["BACKUP_TYPE"] = "update_password_to_oss"
        backup_metadata["TAG"] = tag
        backup_metadata["PRE_POST_FLAG"] = pre_post_flag
        backup_metadata["LOG_FILE"] = logfile
        backup_metadata["BTIMESTAMP"] = start_time
        backup_metadata["ETIMESTAMP"] = backup_end_time
        backup_metadata["HOSTNAME"] = host
        backup_metadata["CLIENT_TYPE"] = "database"
        backup_metadata["FUSION_PDB"] = json_query_output["FUSION_PDB"] if json_query_output else ""
        backup_metadata["TARGET_TYPE"] = "OSS"
        backup_metadata["TARGET_LOCATION"] = target_location
        backup_metadata["PIECE_NAME"] = piece_info
        backup_metadata["RETENTION_DAYS"] = retention_days
        backup_metadata["STATUS"] = status
        backup_metadata["DB_INCR_ID"] = db_info[1] if db_info else ""
        backup_metadata["DB_ID"] = db_info[0] if db_info else ""
        backup_metadata["POD_NAME"] = ""
        backup_metadata["DB_ROLE"] = db_info[2] if db_info else ""
        #backup_metadata["RPM_VER"] = general_metadata["rpm_ver"]
        #backup_metadata["DBAAS_VER"] = general_metadata["dbaas_ver"]
        backup_metadata["DB_SIZE_GB"]=json_query_output["DB_SIZE_GB"] if json_query_output else ""
        backup_metadata["DB_INSTANCE_VERSION"]=json_query_output["INSTANCE_VERSION"] if json_query_output else ""
        backup_metadata["DB_BACKUP_SIZE"] = DB_BACKUP_SIZE
        backup_metadata["BREAKGLASS_ENABLED"] =BREAKGLASS_ENABLED
        backup_metadata["DB_CREATED"] =json_query_output["DB_CREATED"] if json_query_output else ""
        backup_metadata["INSTANCE_START_TIME"] =json_query_output["INSTANCE_START_TIME"] if json_query_output else ""
        backup_metadata["DB_UNIQUE_NAME"] =json_query_output["DB_UNIQUE_NAME"] if json_query_output else ""
        backup_metadata["OSS_NAMESPACE"] = post_backup_metadata.get_namespace_from_sre()
        #backup_metadata["OS_VER"] = general_metadata["os_ver"]
        #backup_metadata["LIBOPC_BUILD_VER"] = general_metadata["libopc_build_ver"]
        #backup_metadata["LDB_REMOTE_SCALING"] = general_metadata["ldb_remote_scaling"]
        backup_metadata["EXADATA_SHAPE"] = instance_metadata.ins_metadata().system_type
        backup_metadata["DB_SHAPE"] =json_query_output["DB_SHAPE"] if json_query_output else ""
        backup_metadata["RMAN_SESSION_GT24HRS"] =json_query_output["RMAN_SESSION_GT24HRS"] if json_query_output else ""
        metadata_data["backup"]["db_mt_os"][0] = backup_metadata
        # Save the backup metadata to a json file.
        logfile_location = globalvariables.EXALOGS_PATH + "/"
        file_name=logfile_location+globalvariables.HOST_NAME+"_password_json_upload_"+"_"+timestamp+"_"+pre_post_flag+".json"
        metadata_report = open(file_name, 'w')
        json.dump(metadata_data, metadata_report, indent=4, sort_keys=True,separators=(',', ':'))
        metadata_report.close()
        try:
            if os.path.exists(file_name):
                shutil.chown(file_name,"oracle", "oinstall")
        except Exception as e:
            message = "Failed to change permission {0}".format(file_name)
            apscom.warn(message)
        return backup_metadata

    except Exception as e:
        message=traceback.print_exc()
        apscom.error(message)
        message = "Failed to create metadata for this backup!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def main():
    log_dir = globalvariables.EXALOGS_PATH + "/"
    logfile = log_dir + globalvariables.HOST_NAME+"_password_json_upload_"+timestamp+".log"
    apscom.init_logger(__file__,log_dir=log_dir, logfile=logfile)
    update_password_json_oss(logfile)
    
if __name__ == "__main__":
    main()