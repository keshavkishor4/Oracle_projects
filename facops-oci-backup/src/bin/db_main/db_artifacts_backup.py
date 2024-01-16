#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    NAME
      db_artifacts_backup.py

    DESCRIPTION
      Do backup of DB Articfacts.

    NOTES

    MODIFIED        (MM/DD/YY)
    Vipin Azad             12/06/22 - jira FSRE-94
    Saritha Gireddy        22/07/20 - initial Articfacts backup created
    Vipin Azad             10/05/22 -
    Added and Modified below Functions as part of requirement in SOEDEVSECOPS-1541
    Added : list_fss_backup,cleanup_obsolete_artifact
    Modified : take_action_list_backups,take_action_cleanup
    Asit Dey               26/06/23 - added logic for FSS artifact backup clean up as BUG - 35433487

"""

from __future__ import absolute_import, division, print_function
import json
from argparse import Namespace

__version__ = "2.0.0.0.201002.1"

import atexit
import calendar
import glob
import optparse
import os
import socket
import sys
import tarfile
import time
import shutil
from datetime import datetime, timedelta
from time import gmtime, strftime
#BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
BASE_DIR = os.path.abspath(__file__ + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom, ociSDK, post_backup_metadata, instance_metadata, globalvariables, commonutils
#
from db import all_pod_oratab_modify
#################Global Variables#################
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
LOCAL_HOST = socket.gethostname()
if __name__ == "__main__":
    BACKUP_CONFIG_PATH = globalvariables.CONFIG_PATH+"/artifacts"

    BACKUP_ARTIFACTS_PATH = "/fss/oci_backup/artifacts/{0}/".format(LOCAL_HOST)

    # osssdk = "/var/log/oci_backup/{0}/logs/".format(LOCAL_HOST)

    try:
        if not os.path.exists(globalvariables.BACKUP_LOG_PATH):
            os.makedirs(globalvariables.BACKUP_LOG_PATH)

        if not os.path.exists(BACKUP_ARTIFACTS_PATH):
            os.makedirs(BACKUP_ARTIFACTS_PATH)

        if not os.path.exists(BACKUP_CONFIG_PATH):
            os.makedirs(BACKUP_CONFIG_PATH)

    except Exception:
        message = "Failed to create backup directories!\n{0}".format(sys.exc_info()[
                                                                    1:2])
        apscom.error(message)
        sys.exit(1)


backup_start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
flock_file = None
log_file = ""


def create_backup_metadata(dbname, backup_target, backup_info, retention_days, tag=None, backup_status="ACTIVE", oci_region=None):
    """ Create backup metadata.
    Args:
        backup_target (str): oss/fss
        backup_info (str): backup path if backup target is fss
                           object name if backup target is oss
        retention_days : Retention days of this backup.
    Returns:
        backup_metadata (dict): Info of backup metadata.
    """
    try:
        oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        backup_end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        backup_metadata = {}

        metadata_t = open(globalvariables.BACKUP_METADATA_TEMPLATE, 'r')
        metadata_data = json.load(metadata_t)
        metadata_t.close()

        backup_metadata["BACKUP_TOOL"] = "tar"
        backup_metadata["BTIMESTAMP"] = backup_start_time
        backup_metadata["ETIMESTAMP"] = backup_end_time
        backup_metadata["HOSTNAME"] = globalvariables.LOCAL_HOST
        backup_metadata["CLIENT_NAME"] = dbname
        backup_metadata["CLIENT_TYPE"] = "database"
        backup_metadata["LOG_FILE"] = log_file
        backup_metadata["TARGET_TYPE"] = backup_target
        backup_metadata["BACKUP_TYPE"] = "dbartifacts_to_{0}".format(
            backup_target)
        backup_metadata["PIECE_NAME"] = backup_info
        backup_metadata["RETENTION_DAYS"] = retention_days
        backup_metadata["STATUS"] = backup_status
        backup_metadata["OSS_BUCKET"] = oss_bucket
        backup_metadata["OSS_NAMESPACE"] = post_backup_metadata.get_namespace_from_sre(
        )

        if tag:
            backup_metadata["TAG"] = tag

        metadata_data["backup"]["db_mt_os"][0] = backup_metadata

        # Update backup metadata to central catalog DB.
        if backup_info:
            logfile_location = globalvariables.EXALOGS_PATH + "/"
            file_name = logfile_location+"db_artifacts_backup_db" + "_" + globalvariables.HOST_NAME+"_" + \
                dbname + "_" + timestamp + "_" + "post" + ".json"
            with open(file_name, 'w') as outfile:
                json.dump(metadata_data, outfile, indent=4, sort_keys=True)
            if os.path.exists(file_name) and not commonutils.check_em_systemtype() and not commonutils.check_dbaas_systemtype():
                commonutils.oss_upload_backup_metadata(file_name)
        return backup_metadata

    except Exception:
        message = "Failed to create metadata for this backup!\n{0}".format(sys.exc_info()[
                                                                           1:2])
        apscom.warn(message)
        raise


def backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace, oss_bucket):
    try:
        backup_name = BACKUP_ARTIFACTS_PATH+prefix + '_' + globalvariables.HOST_NAME + '_' + dbname + "." + strftime(
            "%Y-%m-%d.%H%M%S", gmtime()) + ".tgz"
        # Preserve top dir permission of db_path_list
        tar = tarfile.open(backup_name, "w:gz")
        for backup_file in path_list:
            # print("###############",backup_file)
            if os.path.exists(backup_file):
                if backup_file == "/home/oracle/bkup":
                    pass
                else:
                    message = "Backing up artifacts of {0} ...".format(
                        backup_file)
                    for file in glob.glob(backup_file):
                        apscom.info(message)
                        tar.add(file)
            else:
                message = "artifact {0} not exist!".format(backup_file)
                apscom.warn(message)
        tar.close()

        # Upload backup artifacts to oss
        if backup_target == "oss":
            files_object_name = backup_name.split("/")[-1]
            out = oci_sdk.put_object(
                backup_name, oss_namespace, oss_bucket, files_object_name)
            if out:
                message = "Succeed to upload artifacts {0} to oss.".format(
                    files_object_name)
                apscom.info(message)
            else:
                message = "Failed to upload artifacts {0} to oss.".format(
                    files_object_name)
                apscom.warn(message)
                return None
                # Remove the local backup file after upload to oss.
                # if os.path.isfile(backup_name):
                #   os.remove(backup_name)

            return files_object_name
        else:
            return backup_name

    except Exception:
        message = "Failed to backup artifacts!\n{0}".format(
            sys.exc_info()[1:2])
        apscom.warn(message)

# Added as part of requirement in SOEDEVSECOPS-1541.


def cleanup_obsolete_artifact(backup_target, oss_namespace, oss_bucket, backup_list, comp_backup_list):
    """Cleanup old backup files from fss and oss

    Args:
        backup_target (str): _description_
        oss_namespace (str): Value of Namespace
        oss_bucket (str): Name of bucket
        backup_list (list): List of latest backup tar files for last 60 days
        comp_backup_list (list): List of complete backup tar files which is available

    Returns:
        _type_: _description_
    """

    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        for backup_info in comp_backup_list:
            if backup_info not in backup_list:
                if backup_target == 'fss':
                    # If backup to fss, backup_info is path of backup files
                    if os.path.isfile(backup_info):
                        os.remove(backup_info)
                        message = "Succeed to remove obsolete backup file {0}.".format(
                            backup_info)
                        apscom.info(message)

                elif backup_target == 'oss':
                    # If backup to oss, backup_info is object name

                    out = oci_sdk.delete_object(
                        oss_bucket, backup_info, oss_namespace)
                    if out:
                        if oci_sdk.check_object_exist(oss_bucket, backup_info, oss_namespace):
                            ret_val = globalvariables.BACKUP_FAILED

                            message = json.loads(out)
                            apscom.warn(message["message"])
                            continue

                        else:
                            message = "Succeed to delete obsolete object {0}.".format(
                                backup_info)
                            apscom.info(message)
        return ret_val

    except Exception:
        message = "Failed to cleanup obsolete artifacts!\n{0}".format(sys.exc_info()[
                                                                      1:2])
        apscom.warn(message)

# Added as part of requirement in SOEDEVSECOPS-1541.


def list_fss_backup(dbname, prefix1, retention_days):
    """Function to list files from fss location

    Args:
        dbname (str): Name of database
        prefix1 (str): Prefix of object or file name in fss location

    Returns:
        bkp_object_list: List of latest files for last 60 days
        comp_backup_list: Complete list of file avaialable for database
    """
    try:
        if dbname == 'all':
            comp_backup_list = glob.glob(
                "{0}/{1}*".format(BACKUP_ARTIFACTS_PATH, prefix1))
        else:
            comp_backup_list = glob.glob(
                "{0}/{1}_{2}*".format(BACKUP_ARTIFACTS_PATH, prefix1, dbname))
        dateList = []
        bkp_object_list = []
        for x in range(0, retention_days):
            date1 = datetime.now() - timedelta(days=x)
            strdate = date1.strftime('%Y-%m-%d')
            dateList.append(strdate)
        for obj in comp_backup_list:
            for d in dateList:
                if d in obj:
                    bkp_object_list.append(obj)
        return bkp_object_list, comp_backup_list
    except Exception as e:
        message = "Not able to list files for database {0}".format(dbname)
        apscom.warn(message)

# Modified as part of requirement in SOEDEVSECOPS-1541.

#Bug 35433487 - WALLET BACKUPS ARE CONSUMING TERA BYTES OF SPACE ON FSS  
def check_obsolete_fss_backups(artifact_path, retention_days):
    try: 
        
        now = datetime.now()
        obsolete_backups = []
        obsolete_time = now - timedelta(days=retention_days)
        for filename in os.listdir(artifact_path):
            file_path = os.path.join(artifact_path, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < obsolete_time:
                obsolete_backups.append(file_path)
        return obsolete_backups
    except Exception as e:
        message = "Failed to get obsolete backup list!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)

def purge_fss_obsolete_backups(artifact_path, retention_days):
    try:
        obsolete_backups = check_obsolete_fss_backups(artifact_path, retention_days)
        if obsolete_backups:
            for backup in obsolete_backups:
                os.remove(backup)
                message = "Succeed to remove backup piece!\n{0}".format(backup)
                apscom.info(message)
        else:
            message = "No eligible  backup piece for cleanup !\n"
            apscom.info(message)           
    except Exception as e:
        message = "Failed to do fss cleanup!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
    
    
def take_action_cleanup(options):
    """To clean objects whose retention days passed from oss and fss

    Args:
        options (str): Arguments passed while calling this function
    """

    try:
        prefix = options.prefix
        backup_target = options.backup_target
        oci_config_path = options.oci_config_path
        oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        env_type = commonutils.get_db_env_type(dbname)
        retention_days = globalvariables.backup_opts_wallet_artifact[
            "wallet_artifacts"][env_type]["retention"]
        offline_db_retention_days = globalvariables.backup_opts_wallet_artifact[
            "wallet_artifacts"]["offline_db"]["retention"]
        if prefix == "artifacts_backup_db":
            listprefix = ["db" + '_' + prefix + '_' + globalvariables.HOST_NAME, "db" + '_' + prefix + "_os" + '_' + globalvariables.HOST_NAME, "bg" + '_' + prefix +
                          '_' + globalvariables.HOST_NAME, "faops_oci_db" + '_' + prefix + '_' + globalvariables.HOST_NAME, "db_ini_backup" + '_' + globalvariables.HOST_NAME]
        else:
            listprefix = [prefix + '_' + globalvariables.HOST_NAME]
        # print(listprefix)
        if backup_target == 'fss':
            purge_fss_obsolete_backups(BACKUP_ARTIFACTS_PATH, offline_db_retention_days)
        for prefix1 in listprefix:
            if backup_target == 'oss':
                backup_list, comp_backup_list, bucket_name = oci_sdk.list_wallet_backup(
                    dbname, prefix1, globalvariables.DB_CONFIG_PATH_DEFAULT, retention_days)
            elif backup_target == 'fss':
                backup_list, comp_backup_list = list_fss_backup(
                    dbname, prefix1,retention_days)

            if len(comp_backup_list) > retention_days:
                ret_val = cleanup_obsolete_artifact(
                    backup_target, oss_namespace, oss_bucket, backup_list, comp_backup_list)
                if ret_val == globalvariables.BACKUP_SUCCESS:
                    message = "Succeed to cleanup obsolete backup data."
                    apscom.info(message)
                else:
                    message = "Failed to cleanup obsolete backup data!"
                    apscom.warn(message)

    except Exception as e:
        message = "Failed to do cleanup!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)


def take_action_backup(options=None, retention_days=None):
    """ take_action_backup will take the backup for files info present in artifact db spec file.
    Arg:
        options(str,optional):value of argument passed while calling this function.
        retention_days(str,optional):no of days backup needs to be retain

    Exception:
            backup failure Error

    """
    try:
        env_type = commonutils.get_db_env_type(dbname)
        metadata_tag = ''
        if not retention_days:
            retention_days = globalvariables.backup_opts_wallet_artifact[
                "wallet_artifacts"][env_type]["retention"]
        oci_config_path = options.oci_config_path
        prefix = None
        region = instance_metadata.ins_metadata().region
        oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        # get_crsctl_data
        # db_uniq_name=commonutils.get_crsctl_data(dbname,'db_unique_name')
        #
        # artifacts location path
        #
        backup_piece = ""
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            bkp_config_file = globalvariables.DB_CONFIG_PATH_JSON
        else:
            bkp_config_file = globalvariables.NONFA_ARTIFACTS_CONFIG_PATH
        if os.path.exists("/var/opt/oracle/dbaas_acfs/oci_backup/{0}".format(dbname)):
            gen_spec_file(dbname)
        else:
            message = "spec file can not be generated as spec file path not present"
            apscom.warn(message)
        with open(bkp_config_file, 'r') as config:
            artifact_data = json.load(config)
            artifact_data = artifact_data["db_artifacts"]
            for val in artifact_data:
                prefix = val
                path = artifact_data[val]["base_path"]
                if val == "faops_oci_db_artifacts_backup_db":
                    atifacts_path = path + "/" + dbname
                elif val == "db_artifacts_backup_db":
                    atifacts_path = path + "/" + dbname
                elif val == "bg_artifacts_backup_db":
                    atifacts_path = path + "/" + dbname + "*"
                else:
                    atifacts_path = path

                if (artifact_data[val]["post_path"]):
                    atifacts_path = atifacts_path + \
                        artifact_data[val]["post_path"]
                path_list = []
                backup_info = ""

                if val == "db_artifacts_backup_db":
                    backup_files = glob.glob(atifacts_path.strip() + "/*.spec")
                    for backup_file in backup_files:
                        path_list = commonutils.read_line_from_file(
                            backup_file)
                        if "os" in backup_file:
                            prefix = prefix + "_os"
                        backup_info = backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace,
                                                       oss_bucket)
                        if backup_piece:
                            backup_piece = backup_piece + "," + backup_info
                        else:
                            backup_piece = backup_info

                # added to take backup for spec file created from template
                elif val == "faops_oci_db_artifacts_backup_db":
                    backup_files = glob.glob(atifacts_path.strip() + "/*.spec")
                    for backup_file in backup_files:
                        path_list = commonutils.read_line_from_file(
                            backup_file)
                        if "os" in backup_file:
                            prefix = prefix + "_os"
                        backup_info = backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace,
                                                       oss_bucket)
                        if backup_piece:
                            backup_piece = backup_piece + "," + backup_info
                        else:
                            backup_piece = backup_info

                elif val == "bg_artifacts_backup_db":
                    backup_files = glob.glob(atifacts_path.strip() + "/*")
                    for backup_file in backup_files:
                        path_list.append(backup_file)
                    backup_info = backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace,
                                                   oss_bucket)
                    if backup_piece:
                        backup_piece = backup_piece + "," + backup_info
                    else:
                        backup_piece = backup_info

                elif val == "db_ini_backup":
                    if os.path.exists(atifacts_path):
                        path_list.append(
                            atifacts_path.strip()+"/"+dbname+".ini")
                        backup_info = backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace,
                                                       oss_bucket)
                        if backup_piece:
                            backup_piece = backup_piece + "," + backup_info
                        else:
                            backup_piece = backup_info
                else:
                    if os.path.exists(atifacts_path):
                        backup_files = glob.glob(atifacts_path.strip() + "/*")
                        for backup_file in backup_files:
                            path_list.append(backup_file)

                        path_list.append(atifacts_path.strip())
                        backup_info = backup_artifacts(prefix, dbname, backup_target, path_list, oss_namespace,
                                                       oss_bucket)
                        if backup_piece:
                            backup_piece = backup_piece + "," + backup_info
                        else:
                            backup_piece = backup_info
        if backup_piece:
            # Create Backup Metadata
            backup_metadata = create_backup_metadata(dbname, backup_target, backup_piece, retention_days,
                                                     metadata_tag, "ACTIVE", region)
            message = "Succeed backup artifacts to {0}.".format(backup_target)
            apscom.info(message)
            message = json.dumps(backup_metadata, sort_keys=True, indent=4)
            apscom.info(message)
        else:
            message = "No valid locations to backup artifacts to {0}! {0}.".format(
                backup_target)
            apscom.warn(message)
            create_backup_metadata(dbname, backup_target, backup_piece, retention_days,
                                   metadata_tag, "FAILED", region)
        config.close()
    except Exception as e:

        message = "Failed to do backup!\n{0},{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)


def take_action_list_backups(options):
    """To list latest objects from oss and fss for last 60 days
    """

    tag = "dbartifacts_backup"
    backup_status = options.backup_status.upper()
    #dbname = options.dbname
    prefix = options.prefix
    action = options.action
    metadata_tag = options.metadata_tag
    backup_target = options.backup_target
    env_type = commonutils.get_db_env_type(dbname)
        #print ("ENV TYPE is : ", env_type)
    retention_days = globalvariables.backup_opts_wallet_artifact["wallet_artifacts"][env_type]["retention"]
    try:
        if prefix == "artifacts_backup_db":
            listprefix = ["db" + '_' + prefix + '_' + globalvariables.HOST_NAME, "db" + '_' + prefix + "_os" + '_' + globalvariables.HOST_NAME, "bg" + '_' + prefix +
                          '_' + globalvariables.HOST_NAME, "faops_oci_db" + '_' + prefix + '_' + globalvariables.HOST_NAME, "db_ini_backup" + '_' + globalvariables.HOST_NAME]
        else:
            listprefix = [prefix + '_' + globalvariables.HOST_NAME]
        # print(listprefix)
        for prefix1 in listprefix:
            if backup_target == 'oss':
                backup_list, comp_backup_list, oss_bucket = oci_sdk.list_wallet_backup(
                    dbname, prefix1, globalvariables.DB_CONFIG_PATH_DEFAULT, retention_days)
            elif backup_target == 'fss':
                backup_list, comp_backup_list = list_fss_backup(
                    dbname, prefix1, retention_days)

            if backup_target == 'oss':
                apscom.info("{2}Listing all the backups for {0} on {1} for DB {3} for oss bucket {4} ".format(
                    prefix1, backup_target, globalvariables.GREEN, dbname, oss_bucket))
                apscom.info("========================================")
            else:
                apscom.info("{2}Listing all the backups for {0} on {1} for DB {3} ".format(
                    prefix1, backup_target, globalvariables.GREEN, dbname))
                apscom.info("========================================")
            if not comp_backup_list:
                message = "{2}list_backups not working for DB =====>{1},Please check the prefix provided :{0}".format(
                    prefix1,dbname,globalvariables.RED)
                apscom.warn(message)
                # sys.exit(1)
            else:
                for val in comp_backup_list:
                    if dbname in val:
                        apscom.info(val)

    except Exception:
        message = "Failed to list artifacts backup history!\n{0}".format(sys.exc_info()[
                                                                         1:2])
        apscom.warn(message)
        create_backup_metadata(dbname, "oss", "", "",
                               metadata_tag, "FAILED", instance_metadata.ins_metadata().region)


usage_str = """
    db_artifacts_backup.py - Backup tool for db artifacts in OCI environment.

    # User Case 1: Do backup action
    db_artifacts_backup.py --action backup -t <fss|oss> --dbname <dbname> --retention-days <retention_days>
        -t
            fss - Backup data to file storage.
            oss - Backup data to object storage.

    # User Case 2: Check the backup history
    db_artifacts_backup.py --action list-backups --backup-status <backup_status>
        --backup-status
            - This is optional, only active backups will be shown by default.

      # User Case 1: Do backup action
    db_artifacts_backup.py --action cleanup --dbname <dbname>
    --debug_log         - Optional Use this oprion to enable logging as debug mode
"""


def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('--action', action='store', dest='action',
                          choices=['backup', 'list-backups', 'cleanup', 'restore', 'download-artifacts'], help='Specify the action chose action from list ("backup", "list-backups", "cleanup", "restore", "download-artifacts".')
        parser.add_option('-c', '--config-file', action='store', dest='oci_config_path',
                          default=globalvariables.DB_CONFIG_PATH_DEFAULT, type='string', help='Path of oci config file.')
        parser.add_option('-t', '--storage-type', action='store', dest='backup_target', default='fss',
                          choices=['fss', 'oss'], help='Storage type of backup target.')
        parser.add_option('--dbname', action='store', dest='dbname', default='all',
                          help='Specify which artifacts to be backup. If not set, will backup artifacts of all databases..')
        parser.add_option('--tag', action='store', dest='metadata_tag', default='dbartifacts_backup',
                          help='Used to specify tag in backup metadata')
        parser.add_option('--prefix', action='store', dest='prefix', default='artifacts_backup_db', type='string',
                          help='Prefix of the backup name.')
        parser.add_option('--retention-days', action='store', dest='retention_days', default=7, type=int,
                          help='Retention days of current backup.')
        parser.add_option('--backup-status', action='store', dest='backup_status', default='active',
                          choices=['active', 'obsolete', 'all'], help='List backup with backup-status.')
        parser.add_option('--backup-id', action='store', dest='backup_id', type='string',
                          help='Backup id to be restored.')
        parser.add_option('--artifacts-name', action='store', dest='artifacts_name', type='string',
                          help='Wallet Name to be downloaded')
        parser.add_option('--download_dir', action='store', dest='download_loc', default='./',
                          help='Specify the directory in which to download artifacts')
        parser.add_option('-b', action='store',
                          dest='backup_type', default=' ')
        parser.add_option('--bucket-name', action='store',
                          dest='bucket_name', default=None)
        parser.add_option('-f', '--force', action='store',
                          dest='force_flag', default=False)
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log',
                          default="no", help='Optional - Get logs in debug mode')

        (opts, args) = parser.parse_args()
        return (opts, args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.warn(message)


def take_action_download_artifacts_backups(options):
    try:
        artifactsname = options.artifacts_name
        download_dir = options.download_loc
        config_path = options.oci_config_path
        dbname = options.dbname
        oss_bucket = options.bucket_name
        with open(globalvariables.OCI_SDK_META_FILE, 'r') as f:
            data = json.load(f)
            oss_namespace = data["ns"]
        if not oss_bucket:
            oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        oci_sdk.download_wallet_backup(
            artifactsname, download_dir, config_path, oss_bucket)
        message = "Downloaded {0} to {1}".format(artifactsname, download_dir)
        apscom.info(message)
    except Exception:
        message = "Failed to download file {0} ..."
        apscom.warn(message)
        raise


def gen_spec_file(dbname):
    """ 
    gen_spec_file : this function will generate the Db artificat spec file from Template file. 
    Template file : db_spect_file.spec
    Jira : SOEDEVSECOPS-1800
    Args:
        dbname = Name of the database.

    Exception:
            Gen_spec_file Error

    """
    try:
        crsctl_json = "{0}/crsctl_output.json".format(
            globalvariables.EXALOGS_PATH)
        with open(crsctl_json, 'r') as crs:
            data = json.load(crs)
            for i in data.keys():
                if i == dbname:
                    db_home = data[i]["db_home"]

            # Getting SID name from get_oracle_sids file
            list_of_files = glob.glob(
                "{0}/get_oracle_sids*".format(globalvariables.EXALOGS_PATH))
            list_of_files_sort = sorted(list_of_files,key=os.path.getmtime)
            latest_file = max(list_of_files_sort)
            file_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
            nw = datetime.now()
            lt_file_time = nw - timedelta(hours=4)
            if file_time > lt_file_time:
                with open(latest_file, 'r') as sd:
                    for i in sd:
                        if dbname in i:
                            sid = i

                    # checking if DB instance in open state or not from query.json
                    query_json_dir = "{0}/{1}".format(
                        globalvariables.DB_BACKUP_LOG_PATH, sid)
                    list_qr_json_files = glob.glob(
                        "{0}/*_query.json".format(query_json_dir.rstrip()))
                    latest_qr_json_file = max(
                        list_qr_json_files, key=os.path.getmtime)
                    jq_file_time = datetime.fromtimestamp(
                        os.path.getmtime(latest_qr_json_file))
                    if jq_file_time > lt_file_time:
                        with open(latest_qr_json_file, 'r') as data:
                            q_data = json.load(data)
                            if q_data["INSTANCE_STATUS"] == "OPEN":
                                vsid = q_data["ORACLE_SID"]
                            else:
                                message = "{0} is not in open state".format(
                                    dbname)
                                apscom.warn(message)
                    else:
                        message = "{0} is older file ".format(
                            latest_qr_json_file)
                        apscom.warn(message)
            else:
                message = "{0} file time stamp is older than 4 hrs, hence could not change sid in spec file".format(
                    latest_file)
                apscom.warn(message)
            db_spec_dir_path = "/var/opt/oracle/dbaas_acfs/oci_backup/{0}".format(
                dbname)
            db_spec_file_gen = "{0}/{1}_DB_SPEC_FILE.spec".format(
                db_spec_dir_path, dbname)
            try:
                if os.path.exists(db_spec_dir_path):
                    shutil.copy2(globalvariables.TEMP_DB_SPEC_FILE,
                                 db_spec_file_gen)
                    with open(db_spec_file_gen) as f:
                        newtext = f.read().replace("DB_HOME", db_home).replace(
                            "DB_UNIQ_NAME", dbname).replace("DB_SID", vsid)
                    with open(db_spec_file_gen, 'w') as r:
                        r.write(newtext)
                    shutil.chown(db_spec_file_gen, "oracle", "oinstall")
            except Exception as e:
                message = "{0} Path not exist for DB spec file. {1}".format(
                    db_spec_dir_path,e)
                apscom.warn(message)
    except Exception as e:
        message = "Failed to generate  {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


TAKE_ACTION = {
    "backup": take_action_backup,
    "cleanup": take_action_cleanup,
    "list-backups": take_action_list_backups,
    "download-artifacts": take_action_download_artifacts_backups
}


def init_logger(dbname,action):
    try:
        global log_file
        dbsid = None
        with open(globalvariables.pod_wallet_file, "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if dbname in line:
                    dbsid = line.split(":")[2]
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + \
            "/{0}/".format(dbsid)
        filename = log_file_path+"{0}_{1}_{2}_{3}_{4}.log".format(globalvariables.HOST_NAME, dbsid, action,os.path.basename(
            __file__).split(".")[0], datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file = apscom.init_logger(
            __file__+dbname, log_dir=log_file_path, logfile=filename)
        fp.close()
    except Exception as e:
        message = "Failed to init logger {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


def main(db_name=None, bkp_target=None, retention_days=None, action=None):
    global log_file
    global oci_sdk
    global dbname
    global backup_target
    global oss_namespace
    global db_name_pod
    db_name_pod = []
    with open(globalvariables.OCI_SDK_META_FILE, 'r') as f:
        data = json.load(f)
        oss_namespace = data["ns"]

    (options, args) = parse_opts()
    oci_config_path = options.oci_config_path
    if not action:
        action = options.action
    if not db_name:
        dbname = options.dbname
        if dbname == 'all':
            try:
                if not os.path.exists(globalvariables.pod_wallet_file):
                    all_pod_oratab_modify.main()
                with open(globalvariables.pod_wallet_file, "r") as fp:
                        lines = fp.readlines()
                        for line in lines:
                            if globalvariables.LOCAL_HOST in line:
                                db = line.split(":")[0]
                                env_type = commonutils.get_db_env_type(db)
                                ok2backup = line.split(":")[-1]
                                if ok2backup.strip() == "y" or env_type == "non_fa":
                                    db = line.split(":")[0]
                                    db_name_pod.append(db)
            except Exception:
                message = "pod_wallet_file file is not available"
                apscom.warn(message)
    else:
        dbname = db_name
    if not bkp_target:
        backup_target = options.backup_target
    else:
        backup_target = bkp_target
    if options.debug_log == "yes":
        import logging
        # Enable debug logging
        logging.getLogger('oci').setLevel(logging.DEBUG)
        # oci.base_client.is_http_log_enabled(True)
        # logging.basicConfig(filename='/tmp/test.log')
        log_file_path_for_debug = globalvariables.DB_BACKUP_LOG_PATH + \
            "/{0}/".format("exalogs")
        if not os.path.exists(log_file_path_for_debug):
            os.makedirs(log_file_path_for_debug)
        filename_debug = log_file_path_for_debug+"/oci_debug" + \
            "_{0}_{1}.log".format(globalvariables.HOST_NAME,
                                  datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        logging.basicConfig(filename=filename_debug)
    try:
        atexit.register(commonutils.db_backup_lock_exit, dbname)
        if not action:
            message = "Need to provide valid action by --action!"
            apscom.error(message)
            sys.exit(1)
        # Init logger

        if db_name_pod:
            for dbname in db_name_pod:
                env = commonutils.get_db_env_type(dbname)
                if env is None:
                    message = "Failed to to identify environment {0}\n{0}, skipping backup for  ...".format(dbname)
                    apscom.warn(message)
                else:
                    init_logger(dbname,action)
                    oci_sdk = ociSDK.ociSDK(oci_config_path)
                    ret_val = TAKE_ACTION.get(action)(options)
        elif dbname:
            init_logger(dbname,action)
            oci_sdk = ociSDK.ociSDK(oci_config_path)
            ret_val = TAKE_ACTION.get(action)(options)
        else:
            message="Failed to do {0}, because no dbname or dblist  available, Please check all_pod_info file {1}".format(action,globalvariables.pod_wallet_file)
            apscom.error(message)

        if ret_val:
            message = "Failed to do {0}!".format(action)
            apscom.error(message)
        else:
            message = "Succeed to do {0}.".format(action)
            apscom.info(message)

    except Exception:
        message = "Failed to do {0}!".format(action)
        apscom.error(message)


if __name__ == "__main__":
    main()
