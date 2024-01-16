#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    NAME
      db_wallet_backup.py

    DESCRIPTION
      Do backup of DB wallet.

    NOTES

    MODIFIED        (MM/DD/YY)
    Vipin Azad         12/06/22 - jira FSRE-94 test
    Keshav Kishor      12/05/2022 - Updating logic for fss cleanup # Enh 33817372 - WALLET BACKUP FOR EVAC + REPLICATION
    Zakki Ahmed        02/05/2020 - updating version to support python3 
    Chenlu Chen        01/23/19 - compatibility of python 2 and 3
    Chenlu Chen        12/07/18 - wallet backup created
    
"""

from __future__ import absolute_import, division, print_function
import traceback
import json

__version__ = "2.0.0.0.201002.1"

import glob
import os
import socket
import sys
import time
import optparse
import tarfile
from datetime import datetime
from time import gmtime, strftime
import calendar
import atexit
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom, ociSDK, post_backup_metadata, instance_metadata, commonutils, globalvariables
from db import all_pod_oratab_modify
#################Global Variables#################
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
LOCAL_HOST = socket.gethostname()
BACKUP_WALLET_PATH = "/fss/oci_backup/wallet/{0}/".format(LOCAL_HOST)
WALLET_RESTORE_OBJ_PATH = "/u01/SRE/oci_restore/wallet/{0}/obj/".format(
    LOCAL_HOST)

try:
    if not os.path.exists(BACKUP_WALLET_PATH):
        os.makedirs(BACKUP_WALLET_PATH)

    if not os.path.exists(globalvariables.BACKUP_LOG_PATH):
        os.makedirs(globalvariables.BACKUP_LOG_PATH)

    if not os.path.exists(WALLET_RESTORE_OBJ_PATH):
        os.makedirs(WALLET_RESTORE_OBJ_PATH)

except Exception as e:
    message = "Failed to create backup directories!\n{0}..{1}".format(sys.exc_info()[
                                                                      1:2], e)
    apscom.error(message)
    sys.exit(1)

backup_start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
flock_file = None


def create_backup_metadata(action, dbname, backup_target, backup_info, retention_days, tag=None, oss_region=None,
                           backup_status="ACTIVE"):
    """ Create backup metadata.
    Args:
        dbname:
        backup_status:
        oss_region:
        tag:
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
        backup_metadata["BACKUP_TYPE"] = "wallet_to_{0}".format(backup_target)
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
        # apsbkcom.post_backup_metadata(BACKUP_METADATA_PATH)
        if backup_info:
            logfile_location = globalvariables.EXALOGS_PATH + "/"
            file_name = logfile_location+"dbwalletbackup" + "_" + globalvariables.HOST_NAME+"_" + \
                dbname + "_" + timestamp + "_" + "post" + ".json"
            with open(file_name, 'w') as outfile:
                json.dump(metadata_data, outfile, indent=4, sort_keys=True)
            if os.path.exists(file_name) and not commonutils.check_em_systemtype() and not commonutils.check_dbaas_systemtype():
                commonutils.oss_upload_backup_metadata(file_name)
        # post_backup_metadata.post_backup_md(region_name, globalvariables.LOCAL_HOST, log_file)
        return backup_metadata

    except Exception:
        message = "Failed to create metadata for this backup!\n{0}".format(sys.exc_info()[
                                                                           1:2])
        apscom.warn(message)
        raise


def backup_wallet(prefix, dbname, backup_target, path_list, oci_config_path):
    try:
        backup_list = []
        # load config data
        oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        # fix for 31050647 - $ORACLE_HOME/DBS/DBCS/${CDBNAME}/WALLET IS NOT BACKED UP
        # it will get the oracle hone to get wallet path
        with open(globalvariables.pod_wallet_file, "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if dbname in line:
                    dbsid = line.split(":")[2]
        fp.close()
        backup_name = BACKUP_WALLET_PATH + prefix + '_' + globalvariables.HOST_NAME + '_' + dbname + "." + strftime(
            "%Y-%m-%d.%H%M%S", gmtime()) + ".tgz"
        # Preserve top dir permission of WALLET_BASE_PATH
        # path_list = [globalvariables.ARTIFACTS_BASE_PATH]
        dir_perm = commonutils.get_top_dir_perm(path_list)
        tar = tarfile.open(backup_name, "w:gz")

        # Preserve top dir permission of WALLET_BASE_PATH
        for top_dir in dir_perm.keys():
            ti = tarfile.TarInfo(top_dir)
            ti.mode = int(dir_perm[top_dir], 8)
            ti.type = tarfile.DIRTYPE
            ti.mtime = os.path.getmtime(top_dir)
            tar.addfile(ti)
        for backup_file in path_list:
            # print("###############",backup_file)
            if os.path.exists(backup_file):
                message = "Backing up wallet of {0} ...".format(backup_file)
                exclude_files = ["{0}/lib/libopc.so".format(backup_file)]
                if os.path.isdir(backup_file):
                    message = "Backing up wallet of {0}, backup file {1} ...".format(dbname, backup_file)
                    apscom.info(message)
                    # tar.add(backup_src, exclude=lambda x: x in exclude_files)
                    tar.add(
                        backup_file, filter=lambda x: None if x.name in exclude_files else x)
            else:
                message = "Wallet does {0} not exist!".format(backup_file)
                apscom.warn(message)
        tar.close()
        backup_list.append(dbname)

        if not backup_list:
            message = "No valid locations to backup, please check {0} location>".format(
                globalvariables.NONFA_WALLET_BACKUP_CONFIG_PATH)
            apscom.warn(message)

            if os.path.isfile(backup_name):
                os.remove(backup_name)

            return None
        else:
            message = "Succeeds to backup wallet of {0}.".format(backup_list)
            apscom.info(message)
        # Upload backup wallet to oss
        if backup_target == "oss":
            files_object_name = backup_name.split("/")[-1]
            out = oci_sdk.put_object(
                backup_name, oss_namespace, oss_bucket, files_object_name)
            if out:
                message = "Succeed to upload wallet {0} to oss.".format(
                    files_object_name)
                apscom.info(message)
            else:
                message = "Failed to upload wallet {0} to oss.".format(
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
        message = "Failed to backup wallet!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


def cleanup_obsolete_wallet(dbname, oss_namespace, oss_bucket):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
       # backup_metadata_list = post_backup_metadata.get_backup_metadata_list(LOCAL_HOST, "ACTIVE")
        backup_metadata_list = []
        for backup_metadata in backup_metadata_list:
            backup_db = backup_metadata["client_name"]

            if backup_db != dbname:
                continue

            backup_ts = backup_metadata["etimestamp"]
            retention_days = backup_metadata["retention_days"]

            backup_ts_epoch = calendar.timegm(
                time.strptime(backup_ts, "%Y-%m-%dT%H:%M:%SZ"))
            obsolete_ts_epoch = backup_ts_epoch + \
                retention_days * globalvariables.SECONDS_PER_DAY
            current_ts_epoch = calendar.timegm(gmtime())

            if current_ts_epoch >= obsolete_ts_epoch:
                # Cleanup obsolete backup data
                backup_info = backup_metadata["piece_name"]
                backup_target = backup_metadata["target_type"]
                backup_id = backup_metadata["backup_id"]

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

                # Update status of this backup metadata to OBSOLETE
                #post_backup_metadata.update_backup_status(backup_id, "OBSOLETE")
                obsolete_log_file = backup_metadata["log_file"]
                if obsolete_log_file and os.path.isfile(obsolete_log_file):
                    os.remove(obsolete_log_file)

                message = "Succeed to cleanup obsolete backup data of backup id {0}.".format(
                    backup_id)
                apscom.info(message)

        return ret_val

    except Exception:
        message = "Failed to cleanup obsolete wallet!\n{0}".format(sys.exc_info()[
                                                                   1:2])
        apscom.warn(message)
        raise

# Enh 33817372 - WALLET BACKUP FOR EVAC + REPLICATION


def cleanup_obsolete_wallets(backup_target, oss_namespace, oss_bucket, backup_list, comp_backup_list):
    """Cleanup old backup files from fss and oss

    Args:
        backup_target (str): _description_
        oss_namespace (str): Value of Namespace
        oss_bucket (str): Name of bucket
        backup_list (list): List of backup tar files whcih is older than 60 days
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

# Enh 33817372 - WALLET BACKUP FOR EVAC + REPLICATION


def list_fss_backup(dbname, prefix1, retention_days):
    """Function to list files from fss location 

    Args:
        dbname (str): Name of database
        prefix1 (str): Prefix of object or file name in fss location

    Returns:
        bkp_object_list: List of file which is latest 60 days
        comp_backup_list: Complete list of file avaialable for database
    """
    try:
        if dbname == 'all':
            comp_backup_list = glob.glob(
                "{0}/{1}*".format(BACKUP_WALLET_PATH, prefix1))
        else:
            comp_backup_list = glob.glob(
                "{0}/{1}_{2}*".format(BACKUP_WALLET_PATH, prefix1, dbname))
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

#Bug 35433487 - WALLET BACKUPS ARE CONSUMING TERA BYTES OF SPACE ON FSS  
def check_obsolete_fss_backups(wallet_path, retention_days):
    try: 
        now = datetime.now()
        obsolete_backups = []
        obsolete_time = now - timedelta(days=retention_days)
        for filename in os.listdir(wallet_path):
            file_path = os.path.join(wallet_path, filename)
            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_mtime < obsolete_time:
                obsolete_backups.append(file_path)
        return obsolete_backups
    except Exception as e:
        message = "Failed to get obsolete backup list!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)

def purge_fss_obsolete_backups(wallet_path, retention_days):
    try:
        obsolete_backups = check_obsolete_fss_backups(wallet_path, retention_days)
        if obsolete_backups:
            for backup in obsolete_backups:
                os.remove(backup)
                message = "Succeed to remove backup piece!\n{0}".format(backup)
                apscom.info(message)
        else:
            message = "No eligible  backup piece for cleanup!\n"
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
        # dbname = options.dbname
        prefix = options.prefix
        backup_target = options.backup_target
        oci_config_path = options.oci_config_path
        region = instance_metadata.ins_metadata().region
        oss_bucket = commonutils.get_bucket_details(dbname, oss_namespace)
        env_type = commonutils.get_db_env_type(dbname)
        retention_days = globalvariables.backup_opts_wallet_artifact[
            "wallet_artifacts"][env_type]["retention"]
        offline_db_retention_days = globalvariables.backup_opts_wallet_artifact[
            "wallet_artifacts"]["offline_db"]["retention"]
        listprefix = [prefix + '_' + globalvariables.HOST_NAME]
        apscom.info(listprefix)
        if backup_target == 'fss':
            purge_fss_obsolete_backups(BACKUP_WALLET_PATH, offline_db_retention_days)
        for prefix1 in listprefix:
            if backup_target == 'oss':
                backup_list, comp_backup_list, bucket_name = oci_sdk.list_wallet_backup(
                    dbname, prefix1, globalvariables.DB_CONFIG_PATH_DEFAULT, retention_days)
            elif backup_target == 'fss':
                backup_list, comp_backup_list = list_fss_backup(
                    dbname, prefix1, retention_days)

            if len(comp_backup_list) > retention_days:
                ret_val = cleanup_obsolete_wallets(
                    backup_target, oss_namespace, oss_bucket, backup_list, comp_backup_list)
                if ret_val == globalvariables.BACKUP_SUCCESS:
                    message = "Succeed to cleanup obsolete backup data."
                    apscom.info(message)
                else:
                    message = "Failed to cleanup obsolete backup data!"
                    apscom.warn(message)

    except Exception:
        message = "Failed to do cleanup!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)


def take_action_backup(options=None, retention_days=None):
    action = ''
    backup_info = ''
    metadata_tag = ''
    try:
        env_type = commonutils.get_db_env_type(dbname)
        action = options.action
        if not retention_days:
            retention_days = globalvariables.backup_opts_wallet_artifact[
                "wallet_artifacts"][env_type]["retention"]
        oci_config_path = options.oci_config_path
        metadata_tag = options.metadata_tag
        prefix = options.prefix
        if("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            bkp_config_file = globalvariables.DB_CONFIG_PATH_JSON
        else:
            bkp_config_file = globalvariables.NONFA_WALLET_BACKUP_CONFIG_PATH
        with open(bkp_config_file, 'r') as config:
            wallet_data = json.load(config)
            wallet_data = wallet_data["db_wallet"]
            path_list = []
            for val in wallet_data:
                path = wallet_data[val]["base_path"]
                if "ora_" in val:
                    dbsid = None
                    with open(globalvariables.pod_wallet_file, "r") as fp:
                        lines = fp.readlines()
                        for line in lines:
                            if dbname in line:
                                dbsid = line.split(":")[2]
                    fp.close()
                    oracle_home = commonutils.get_oracle_home(dbsid)
                    # print("oracle_home="+oracle_home)
                    backup_path = oracle_home + path
                    if "_db" in val:
                        backup_path = backup_path + "/" + dbname
                elif "_db" in val:
                    backup_path = path + "/" + dbname
                else:
                    backup_path = path
                if (wallet_data[val]["post_path"]):
                    backup_path = backup_path + wallet_data[val]["post_path"]
                backup_info = ""
                if os.path.exists(backup_path):
                    path_list.append(backup_path.strip())
            backup_info = backup_wallet(
                prefix, dbname, backup_target, path_list, oci_config_path)
            if backup_info:
                # Create Backup Metadata
                backup_metadata = create_backup_metadata(action, dbname, backup_target, backup_info, retention_days,
                                                         metadata_tag, instance_metadata.ins_metadata().region, "ACTIVE")
                message = "Succeed backup wallet to {0}.".format(backup_target)
                apscom.info(message)

                message = json.dumps(backup_metadata, sort_keys=True, indent=4)
                apscom.info(message)
            else:
                message = "No valid locations to backup wallet to {0}!".format(
                    backup_target)
                apscom.warn(message)
                create_backup_metadata(action, dbname, backup_target, backup_info, retention_days,
                                       metadata_tag, instance_metadata.ins_metadata().region, "FAILED")

    except Exception as e:
        message = "Failed to do backup!\n{0},{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        create_backup_metadata(action, dbname, backup_target, backup_info, retention_days,
                               metadata_tag, instance_metadata.ins_metadata().region, "FAILED")
        raise


def take_action_list_backups(options):
    """To list objects from oss and fss whose age is more than retention days
    """
    tag = "wallet_backup"
    backup_status = options.backup_status.upper()
    #dbname = options.dbname
    prefix = options.prefix
    action = options.action
    metadata_tag = options.metadata_tag
    backup_target = options.backup_target
    env_type = commonutils.get_db_env_type(dbname)
    retention_days = globalvariables.backup_opts_wallet_artifact["wallet_artifacts"][env_type]["retention"]
    try:
        listprefix = [prefix + '_' + globalvariables.HOST_NAME]
        #apscom.info(listprefix)
        for prefix1 in listprefix:
            if backup_target == 'oss':
                backup_list, comp_backup_list, oss_bucket = oci_sdk.list_wallet_backup(
                    dbname, prefix1, globalvariables.DB_CONFIG_PATH_DEFAULT, retention_days)
            elif backup_target == 'fss':
                backup_list, comp_backup_list = list_fss_backup(
                    dbname, prefix1,retention_days)

            if backup_target == 'oss':
                apscom.info("{2}Listing all the backups for {0} on {1} for DB {3} for bucket {4} ".format(
                    prefix1, backup_target, globalvariables.GREEN, dbname, oss_bucket))
                apscom.info("========================================")
            else:
                apscom.info("{2}Listing all the backups for {0} on {1} for DB {3} ".format(
                    prefix1, backup_target, globalvariables.GREEN, dbname))
                apscom.info("========================================")
            if not comp_backup_list:
                message = "{2}list_backups not working for DB ==> {1},Please check the prefix provided prefix list:{0}".format(
                    listprefix,dbname,globalvariables.RED)
                apscom.warn(message)
                # sys.exit(1)
            else:
                for val in comp_backup_list:
                    if dbname in val:
                        apscom.info(val)
    except Exception:
        message = "Failed to list wallet backup history!\n{0}".format(sys.exc_info()[
            1:2])
        apscom.warn(message)
        create_backup_metadata(dbname, "oss", "", "",
                               metadata_tag, "FAILED", instance_metadata.ins_metadata().region)


usage_str = """
    db_wallet_backup.py - Backup tool for db wallet in OCI environment.

    # User Case 1: Do backup action
    db_wallet_backup.py --action backup -t <fss|oss> --dbname <dbname> --retention-days <retention_days>
        -t 
            fss - Backup data to file storage.
            oss - Backup data to object storage.

    # User Case 2: Check the backup history
    db_wallet_backup.py --action list-backups --backup-status <backup_status>
        --backup-status
            - This is optional, only active backups will be shown by default.

    # User Case 3: Do restore action
    db_wallet_backup.py --action restore --backup-id <backup_id>

    # User Case 1: Do backup action
    db_wallet_backup.py --action cleanup --dbname <dbname>
    --debug_log         - Optional Use this oprion to enable logging as debug mode

"""


def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('--action', action='store', dest='action',
                          choices=['backup', 'list-backups',
                                   'cleanup', 'restore', 'download-wallet'],
                          help='Specify the action from the following list("backup", "list-backups", "cleanup", "restore", "download-wallet").')
        parser.add_option('-c', '--config-file', action='store', dest='oci_config_path',
                          default=globalvariables.DB_CONFIG_PATH_DEFAULT, type='string',
                          help='Path of oci config file.')
        parser.add_option('-t', '--storage-type', action='store', dest='backup_target', default='fss',
                          choices=['fss', 'oss'], help='Storage type of backup target.')
        parser.add_option('--dbname', action='store', dest='dbname', default='all',
                          help='Specify which wallet to be backup. If not set, will backup wallet of all databases..')
        parser.add_option('--tag', action='store', dest='metadata_tag', default='wallet_backup',
                          help='Used to specify tag in backup metadata')
        parser.add_option('--prefix', action='store', dest='prefix', default='dbwalletbackup', type='string',
                          help='Prefix of the backup name.')
        parser.add_option('--retention-days', action='store', dest='retention_days', default=7, type=int,
                          help='Retention days of current backup.')
        parser.add_option('--backup-status', action='store', dest='backup_status', default='active',
                          choices=['active', 'obsolete', 'all'], help='List backup with backup-status.')
        parser.add_option('--backup-id', action='store', dest='backup_id', type='string',
                          help='Backup id to be restored.')
        parser.add_option('--wallet-name', action='store', dest='wallet_name', type='string',
                          help='Wallet Name to be downloaded')
        parser.add_option('--download_dir', action='store', dest='download_loc', default='./',
                          help='Specify the directory in which to download wallet')
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
        raise


def take_action_download_wallet_backups(options):
    action = options.action
    try:
        walletname = options.wallet_name
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
            walletname, download_dir, config_path, oss_bucket)
        message = "Downloaded {0} to {1}".format(walletname, download_dir)
        apscom.info(message)
    except Exception as e:
        message = "Failed to download file {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        create_backup_metadata(action, "", "oss", "", "",
                               "", instance_metadata.ins_metadata().region, "FAILED")
        raise


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
        filename = log_file_path + "{0}_{1}_{2}_{3}_{4}.log".format(globalvariables.HOST_NAME, dbsid,action,
                                                                os.path.basename(
                                                                    __file__).split(".")[0],
                                                                datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file = apscom.init_logger(
            __file__ + dbname, log_dir=log_file_path, logfile=filename)
        fp.close()
    except Exception as e:
        message = "Failed to init logger {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


TAKE_ACTION = {
    "backup": take_action_backup,
    "cleanup": take_action_cleanup,
    "list-backups": take_action_list_backups,
    "download-wallet": take_action_download_wallet_backups
}


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
                                if (ok2backup.strip() == "y") or (env_type == "non_fa"):
                                    db_name_pod.append(db)
            except Exception:
                message = "pod_wallet_file file is not available"
                apscom.warn(message)
    else:
        dbname = db_name
    # FUSION_PDB = commonutils.get_db_env_type(dbname)
    # if not FUSION_PDB:
    #     env="stage"
    # else:
    #     env="prod"
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
                    message = "Failed to to identify environment {0}\n{0} ...".format(dbname)
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
        apscom.warn(traceback.print_exc())
        message = "Failed to do {0}!".format(action)
        apscom.error(message)


if __name__ == "__main__":
    main()
