#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      ocifsbackup.py

    DESCRIPTION
      Do backup of FA MT.

    NOTES

    MODIFIED        (MM/DD/YY)
    Chenlu Chen        06/28/19 - Add list and cleanup orphan support
    Chenlu Chen        04/11/19 - List file system per display name
    Chenlu Chen        02/20/19 - Separate local and central catalog db
    Chenlu Chen        01/23/19 - Add Instance Principal support
    Chenlu Chen        12/26/18 - Create snapshot with tag
    Chenlu Chen        11/09/18 - Add central catalog support
    Chenlu Chen        10/25/18 - Add restore support
    Chenlu Chen        10/11/18 - Add retention support
    Chenlu Chen        10/10/18 - Add full_to_oss support
    Chenlu Chen        10/10/18 - Add log and backup metadata
    Chenlu Chen        09/29/18 - Backup files
    Chenlu Chen        09/28/18 - Create file system snapshot
    Chenlu Chen        09/27/18 - created

"""

from __future__ import absolute_import, division, print_function

__version__ = "1.0.0.0.190628"

import os
import sys
import time
import optparse
from optparse import OptionParser
from subprocess import Popen, PIPE
import tarfile
import glob
from time import gmtime, strftime
import calendar
import atexit
import re
from datetime import datetime

BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,fssSDK,post_backup_metadata,commonutils,ociSDK
from mt import apssqldb,mt_backup
import globalvariables
import json
import instance_metadata

if not os.path.isfile("/usr/bin/parcp"):
    print("[ERROR] The dependent package fss-parallel-tools is not installed!")
    sys.exit(1)
else:
    CP_TOOL = "/usr/bin/parcp"

#################Global Variables#################

backup_start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
fs_config_path = None
flock_file = None
log_file = ""
FILE_PATTERN_PATH = BASE_DIR + "/config/mt/config-file-patterns.json"

def backup_files(config_path, prefix):
    """ Backup files per config file
    Args:
        config_path (str): config file with backup file list
        prefix (str): prefix of backup file name
    Returns:
        str: full path of backup files
    Raises:
    """
    try:
        f = None
        tar = None
        backup_list = None
        backup_name = globalvariables.BACKUP_FILES_PATH + "/" + prefix + "_" + globalvariables.LOCAL_HOST + "." + strftime("%Y-%m-%d.%H%M%S",
                                                                                           gmtime()) + ".tgz"
        backup_files = []
        backup_dirs = []
        path_list = []

        # Get backup file list
        f = open(config_path, 'r')
        backup_list = json.load(f)
        if "backup_file" in backup_list.keys():
            backup_files = backup_list["backup_file"]
            path_list.extend(backup_files)
        if "backup_dir" in backup_list.keys():
            backup_dirs = backup_list["backup_dir"]
            path_list.extend(backup_dirs)
        f.close()

        dir_perm = commonutils.get_top_dir_perm(path_list)

        # Backup files to backup_name.
        tar = tarfile.open(backup_name, "w:gz")

        # Preserve top dir permission of backup files
        for top_dir in dir_perm.keys():
            ti = tarfile.TarInfo(top_dir)
            ti.mode = int(dir_perm[top_dir], 8)
            ti.type = tarfile.DIRTYPE
            tar.addfile(ti)

        for backup_file in backup_files:
            if "*" in backup_file:
                for matched_file in glob.glob(backup_file):
                    message = "Backing up file {0} ...".format(matched_file)
                    apscom.info(message)
                    tar.add(matched_file)
            else:
                if os.path.exists(backup_file):
                    message = "Backing up file {0} ...".format(backup_file)
                    apscom.info(message)
                    tar.add(backup_file)

        for backup_dir in backup_dirs:
            if "*" in backup_dir:
                for matched_dir in glob.glob(backup_dir):
                    message = "Backing up dir {0} ...".format(matched_dir)
                    apscom.info(message)
                    tar.add(matched_dir)
            else:
                if os.path.exists(backup_dir):
                    message = "Backing up dir {0} ...".format(backup_dir)
                    apscom.info(message)
                    tar.add(backup_dir)

        tar.close()
        return backup_name

    except Exception as e:
        message = "Failed to backup files in {0}!\n{1}{2}".format(config_path, sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

    finally:
        if f:
            f.close()
        if tar:
            tar.close()


def backup_files_from_snapshot(snapshot_info, prefix):
    try:
        mount_point = snapshot_info["mount_point"]
        backup_name = globalvariables.BACKUP_FS_PATH + "/" + prefix + "_" + "_".join(snapshot_info["name"].split("_")[2:]) + ".tgz"
        backup_dir = mount_point + "/.snapshot/" + snapshot_info["name"]
        backup_list = []

        # Generate tarball from relative path
        os.chdir(backup_dir)

        backup_list = os.listdir(backup_dir)
        # print os.listdir(backup_dir)

        # For test usage, only backup part of mount_point for large mount
        # if mount_point == "/u01":
        #    backup_list = ["SRE/oci_backup"]
        # elif mount_point == "/podscratch":
        #    backup_list = ["ratsclient"]
        # elif mount_point == "/opt/facs/casrepos":
        #    backup_list = ["jdk"]

        # Backup files to backup_name.
        tar = tarfile.open(backup_name, "w:gz")

        message = "Backing up {0} from snapshot {1} ...".format(mount_point, snapshot_info["name"])
        apscom.info(message)

        for backup in backup_list:
            if not ((mount_point == "/u01" and backup == "SRE") or (mount_point == "/podscratch" and backup.endswith("-artifacts"))) and \
                    os.path.exists(backup):
                # Exclude /u01/SRE and /podscratch/*-artifacts from backup files.
                tar.add(backup)

        tar.close()

        message = "Succeed to backup {0} from snapshot {1} ...".format(mount_point, snapshot_info["name"])
        apscom.info(message)

        return backup_name

    except Exception as e:
        message = "Failed to backup files from snapshot!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

    finally:
        if tar:
            tar.close()


def backup_files_from_snapshots(snapshot_list, prefix, preserve_snapshot=False):
    """Backup files from snapshot list
    Args:
        snapshot_list (list): List of snapshots
        prefix (str): Prefix of backup name
        preserve_snapshot (bool): If True, will not remove the snapshot after backup.
                                  If False, snapshot will be removed once backup finished.
    Returns:
        backup_list (list): List of backup files.
    """
    try:
        backup_list = []

        for snapshot in snapshot_list:
            backup_file = backup_files_from_snapshot(snapshot, prefix)
            backup_list.append(backup_file)

            # Delete the snapshot if not preserve.
            if not preserve_snapshot:
                snapshot_ocid = snapshot["id"]
                message = "Deleting snapshot {0} ...".format(snapshot["name"])
                apscom.info(message)
                if ("DO_NOT_DELETE" not in snapshot["name"]):
                    if fsssdk.delete_fs_snapshot(snapshot_ocid):
                        message = "Succeed to delete snapshot {0}.".format(snapshot["name"])
                        apscom.info(message)
                    else:
                        if not mt_backup.check_snapshot_deleted(snapshot_ocid):
                            ret_val = globalvariables.BACKUP_FAILED

                            message = "Failed to delete snapshot {0}!".format(snapshot["name"])
                            apscom.warn(message)

        return backup_list

    except Exception as e:
        message = "Failed to backup files from snapshots!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def take_action_update_fs_list(options):
    try:
        global fs_config_path
        fs_config_path = options.fs_config_path

        if (not fs_config_path) or (not os.path.isfile(fs_config_path)):
            message = "The config file to be updated needs specified by -f!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        else:
            fs_config_path = mt_backup.create_fs_list(fs_config_path)
            message = "The file system backup config file {0} is updated successfully!".format(fs_config_path)
            apscom.info(message)

            return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to update file system backup config file {0}!\n{1}{2}".format(fs_config_path,
                                                                                     sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def take_action_backup(options):
    """ Action of Backup
    Args:
         options: Program options
    Returns:
    Raises:
    """
    try:
        global fs_config_path
        backup_list = []
        retention_policy = {}
        backup_file_path = None

        fs_config_path = options.fs_config_path
        files_config_path = options.files_config_path
        backup_target = options.backup_target
        backup_option = options.backup_option
        prefix = options.prefix
        action = options.action
        retention_policy_path = options.retention_policy_path
        snapshot_tag = options.prefix
        catalog_type = options.catalog_type

        oss_bucket = inst_meta.default_bucket

        if not (backup_target and backup_option):
            message = "Both --storage-type and --backup-options need to be specified!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        # Get retention policy of this backup
        if retention_policy_path:
            if not os.path.isfile(retention_policy_path):
                message = "Invalid retention policy file provided by -p!"
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED
        else:
            retention_policy_path = globalvariables.RETENTION_POLICY_PATH_DEFAULT

        def post_exception():
            post_backup_metadata.create_backup_metadata(action, backup_type, backup_list, retention_days,
                               snapshot_tag,
                               catalog_type, "FAILED",log_file)
            sys.exit(1)

        # Do cleanup before backup.
        commonutils.cleanup_dir(globalvariables.BACKUP_FS_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_FS_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_OBJ_PATH)

        f = open(retention_policy_path, 'r')
        retention_policy = json.load(f)
        f.close()

        backup_type = backup_option + '_to_' + backup_target

        # Get retention days per backup type
        retention_days = retention_policy[backup_type]

        # Init the backup history table
        if osssdk.check_object_exist(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB) == True:
            out = osssdk.get_object(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        # If not set fs_config_path, will create one per the template.
        # Otherwise, will use the one specified by users.
        if not fs_config_path:
            fs_config_path = mt_backup.create_fs_list()
        else:
            if not os.path.isfile(fs_config_path):
                message = "Can not find the fs config file {0}!\n{1}".format(fs_config_path, sys.exc_info()[1:2])
                apscom.warn(message)
                post_exception()
                return globalvariables.BACKUP_FAILED

        # Backup files, the backup tarball is saved in /u01 file system.

        # cleanup older snapshots
        fsssdk.get_older_snapshots(fs_config_path, retention_days)

        # If backup destination is oss and backup type is full, only need to send the file system backup to oss.
        backup_file_path = backup_files(files_config_path, prefix)

        # Create file system snapshot
        snapshot_list = mt_backup.create_fs_snapshots(fs_config_path, prefix)

        # print backup_target, backup_type, oci_api.oss_namespace, oci_api.mtbk_oss_bucket
        if backup_target == "fss":
            for snapshot in snapshot_list:
                backup_list.append(snapshot["id"])

            backup_list.append(backup_file_path)

        # Create and save backup metadata
        backup_metadata = post_backup_metadata.create_backup_metadata(action, backup_type, backup_list, retention_days, snapshot_tag,
                                                 catalog_type, "ACTIVE",log_file)

        # Cleanup obsolete data after backup is finished.
        cleanup_per_backup_metadata(catalog_type)
        apscom.info("Cleanup old snapshots....")

        message = "Succeed to do {0} backup.".format(backup_type)
        apscom.info(message)

        message = json.dumps(backup_metadata, sort_keys=True, indent=4)
        apscom.info(message)
        f.close()
        # rpmupdates.verify_upgrade_rpm()
        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        if backup_file_path and os.path.isfile(backup_file_path):
            os.remove(backup_file_path)

        snapshot_ocid = []
        for snapshot in snapshot_list:
            snapshot_ocid.append(snapshot["id"])
        mt_backup.cleanup_snapshots(snapshot_ocid)

        commonutils.cleanup_dir(globalvariables.BACKUP_FS_PATH)
        post_exception()
        message = "Failed to do backup!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def get_snapshot_info(snapshot_list):
    try:
        snapshot_info_list = {}
        snapshot_pattern = ".*snapshot_(?P<fs_name>\S+).\d{4}-[0-1][0-9]-[0-3][0-9].[0-2][0-9][0-6][0-9][0-6][0-9]_\+\d{4}"
        component_type = inst_meta.component_type

        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)
        f.close()

        for snapshot in snapshot_list:
            matched = re.compile(snapshot_pattern).match(snapshot)
            if matched:
                fs_name = matched.group('fs_name')
            else:
                message = "Failed to get file systemname from snapshot {0}!".format(snapshot)
                apscom.warn(message)

                raise

            # Get mount point for each snapshot
            backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
            for mount_point in backup_dirs.keys():
                nfs_share = backup_dirs[mount_point]["nfs_share"]
                if nfs_share and nfs_share.rsplit("/", 1)[1] == fs_name:
                    snapshot_info_list[mount_point] = mount_point + "/.snapshot/" + snapshot
                    break

        return snapshot_info_list

    except Exception as e:
        message = "Failed to get snapshot information from snapshot list!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def fill_backup_metadata(backup_info):
    try:
        backup_metadata = {}

        backup_metadata["backup_id"] = backup_info[0]
        backup_metadata["backup_tool"] = backup_info[1]
        backup_metadata["btimestamp"] = backup_info[2]
        backup_metadata["etimestamp"] = backup_info[3]
        backup_metadata["backup_type"] = backup_info[4]
        backup_metadata["piece_name"] = backup_info[5]
        backup_metadata["retention_days"] = backup_info[6]
        backup_metadata["status"] = backup_info[7]
        backup_metadata["podname"] = backup_info[8]
        backup_metadata["hostname"] = backup_info[9]
        backup_metadata["client_type"] = backup_info[10]
        backup_metadata["client_name"] = backup_info[11]
        backup_metadata["log_file"] = backup_info[12]
        backup_metadata["tag"] = backup_info[13]

        return backup_metadata

    except Exception as e:
        message = "Failed to fill backup metadata!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def cleanup_backup_to_fss(backup_pieces):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS

        # Backup info [snap_ocid_1, ..., snap_ocid_n, files_path]
        backup_list = backup_pieces.split(",")

        # Remove the backup files
        if os.path.isfile(backup_list[-1]):
            os.remove(backup_list[-1])

        # Remove the item from backup list
        backup_list.remove(backup_list[-1])

        # All items in backup list are snapshot ocid
        ret_val = mt_backup.cleanup_snapshots(backup_list)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup obsolete backup data for backup to fss."
            apscom.info(message)
        else:
            message = "Failed to cleanup obsolete backup data for backup to fss!"
            apscom.warn(message)

        return ret_val

    except Exception as e:
        message = "Failed to do cleanup for backup to fss!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def cleanup_snapshot_pieces(backup_pieces):
    try:
        backup_list = backup_pieces.split(",")
        ret_val = mt_backup.cleanup_snapshots(backup_list)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup obsolete snapshot."
            apscom.info(message)
        else:
            message = "Failed to cleanup obsolete snapshot!"
            apscom.warn(message)

        return ret_val

    except Exception as e:
        message = "Failed to cleanup snapshot pieces!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def cleanup_snapshot_to_oss(backup_pieces):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        oss_namespace = osssdk.oss_namespace
        oss_bucket = inst_meta.default_bucket

        # Backup info [snap_ocid_1, ..., snap_ocid_n, files_obj_name]
        backup_list = backup_pieces.split(",")

        # Remove the object
        obj_deleted = osssdk.delete_object(oss_namespace, oss_bucket, backup_list[-1])
        if not obj_deleted:
            if osssdk.check_object_exist(oss_namespace, oss_bucket, backup_list[-1]):
                ret_val = globalvariables.BACKUP_FAILED
        else:
            message = "Succeed to delete object {0}!".format(backup_list[-1])
            apscom.info(message)

        # Remove the item from backup list no matter delete object succeed or not.
        backup_list.remove(backup_list[-1])

        # All items in backup list are snapshot ocid
        ret_val = mt_backup.cleanup_snapshots(backup_list)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup obsolete backup data for snapshot to oss backup."
            apscom.info(message)
        else:
            message = "Failed to cleanup obsolete backup data for snapshot to oss backup!"
            apscom.warn(message)

        return ret_val

    except Exception:
        message = "Failed to do cleanup for backup of snapshot_to_oss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise
def cleanup_full_to_oss(backup_pieces):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        oss_namespace = osssdk.oss_namespace
        oss_bucket =  inst_meta.default_bucket

        # Backup info [snap_obj_name_1, ..., snap_obj_name_n, files_path]
        backup_list = backup_pieces.split(",")

        # If only one item in the list, it is the object name. Need to remove.
        # Otherwise, the last one is the path of backup files. No need to remove.
        if len(backup_list) == 1:
            deleted = osssdk.delete_object(oss_namespace, oss_bucket, backup_list[-1])

            if not deleted:
                if osssdk.check_object_exist(oss_namespace, oss_bucket, backup_list[-1]):
                    ret_val = globalvariables.BACKUP_FAILED
            else:
                message = "Succeed to delete object {0}.".format(backup_list[-1])
                apscom.info(message)

            return ret_val

        # Remove the item from backup list no matter delete object succeed or not.
        backup_list.remove(backup_list[-1])

        # Remove the objects
        for object_name in backup_list:
            deleted = osssdk.delete_object(oss_namespace, oss_bucket, object_name)
            if not deleted:
                if osssdk.check_object_exist(oss_namespace, oss_bucket, object_name):
                    ret_val = globalvariables.BACKUP_FAILED
            else:
                message = "Succeed to delete object {0}.".format(object_name)
                apscom.info(message)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup obsolete backup data for full to oss backup."
            apscom.info(message)
        else:
            message = "Failed to cleanup obsolete backup data for full to oss backup!"
            apscom.warn(message)

        return ret_val

    except Exception:
        message = "Failed to do cleanup for backup of full_to_oss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise
CLEANUP_PER_BACKUP_TYPE = {
    "snapshot_to_fss": cleanup_backup_to_fss,
    "full_to_fss": cleanup_backup_to_fss,
    "create_snapshot": cleanup_snapshot_pieces,
    "snapshot_to_oss": cleanup_snapshot_to_oss,
    "full_to_oss": cleanup_full_to_oss
}


def cleanup_obsolete_backup_data(backup_metadata):
    try:
        backup_obsoleted = False

        backup_id = backup_metadata["backup_id"]
        backup_ts = backup_metadata["etimestamp"]
        backup_type = backup_metadata["backup_type"]
        backup_pieces = backup_metadata["piece_name"]
        retention_days = backup_metadata["retention_days"]

        backup_ts_epoch = calendar.timegm(time.strptime(backup_ts, "%Y-%m-%dT%H:%M:%SZ"))
        obsolete_ts_epoch = backup_ts_epoch + retention_days * globalvariables.SECONDS_PER_DAY
        current_ts_epoch = calendar.timegm(gmtime())

        if current_ts_epoch >= obsolete_ts_epoch:
            # Cleanup obsolete backup data
            ret_val = CLEANUP_PER_BACKUP_TYPE.get(backup_type)(backup_pieces)
            if ret_val == globalvariables.BACKUP_SUCCESS:
                backup_obsoleted = True
                obsolete_log_file = backup_metadata["log_file"]

                if obsolete_log_file and os.path.isfile(obsolete_log_file):
                    os.remove(obsolete_log_file)
            else:
                message = "Failed to cleanup obsolete backup data of backup id {0}!".format(backup_id)
                apscom.warn(message)

        return backup_obsoleted

    except Exception as e:
        message = "Failed to cleanup obsolete backup data!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.info(message)


def cleanup_per_backup_metadata(catalog_type):
    """ Cleanup obsolete backup data per backup metadata
    Args:
        catalog_type (str): Do cleanup per catalog type.
    Returns:
    Raises:
    """
    try:
        ret_val = globalvariables.BACKUP_SUCCESS

        # Do cleanup per local backup metadata.
        mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
        mt_backup_db.init_table(mt_backup_db, "backup_history_table_v2")

        db_tables = mt_backup_db.get_existing_tables()
        table_name = "backup_history_table_v2"
        if table_name not in db_tables:
            message = "Table {0} not created in local catalog DB.".format(table_name)
            apscom.warn(message)
            mt_backup_db.close()

            return globalvariables.BACKUP_FAILED
        else:
            sql_cmd = "SELECT * from " + table_name + " WHERE status = 'ACTIVE'"
            mt_backup_db.query(sql_cmd)
            backup_list = mt_backup_db.cursor.fetchall()

            for backup_info in backup_list:
                backup_metadata = fill_backup_metadata(backup_info)
                snapshot_tag = backup_metadata["tag"]

                backup_obsoleted = cleanup_obsolete_backup_data(backup_metadata)

                if backup_obsoleted:
                    backup_id = backup_metadata["backup_id"]
                    message = "Succeed to cleanup obsolete backup data of local backup id {0}.".format(backup_id)
                    apscom.info(message)

                    # Update status of this backup metadata to OBSOLETE
                    sql_cmd = "UPDATE " + table_name + " SET status = 'OBSOLETE' WHERE backup_id = " + str(
                        backup_id)
                    mt_backup_db.query(sql_cmd)

        mt_backup_db.close()

        # Send local backup db to oss.
        oss_bucket = inst_meta.default_bucket
        obj_created = osssdk.put_object_multipart(globalvariables.BACKUP_SQLDB_PATH, oss_bucket, globalvariables.OBJ_BACKUP_SQLDB)
        if not obj_created:
            ret_val = globalvariables.BACKUP_FAILED
            message = "Failed to upload backup db to oss!"
            apscom.warn(message)
        else:
            message = "Succeed to upload backup db to oss."
            apscom.info(message)

        return ret_val

    except Exception as e:
        message = "Failed to do cleanup per backup metadata!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.info(message)


def cleanup_snapshot_name_pattern(snapshot_name_pattern, snapshot_cleanup_threshold):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        component_type = inst_meta.component_type

        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)
        # snapshot_time_pattern = "\d{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-6][0-9]:[0-6][0-9].\d*[zZ]"
        snapshot_time_pattern = "\d{4}-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-6][0-9]:[0-6][0-9].\d*"

        # Only delete snapshot if "this" is true in fs_config_path
        backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
        for mount_point in backup_dirs.keys():
            if backup_dirs[mount_point]["this"]:
                fs_ocid = backup_dirs[mount_point]["id"]
                snapshot_list = fsssdk.list_fs_snapshots(fs_ocid)

                # Go through all snapshots created for this file system.
                for snapshot in snapshot_list:
                    snapshot_name = snapshot.name
                    # If snapshot name matched, delete this snapshot if it is obsolete.
                    if re.compile(snapshot_name_pattern).match(snapshot_name):
                        if not re.compile(snapshot_time_pattern).match(str(snapshot.time_created)):
                            ret_val = globalvariables.BACKUP_FAILED

                            message = "Unsupported time pattern of timeCreated {0} in snapshot metadata!".format(
                                str(snapshot.time_created))
                            apscom.warn(message)
                        else:
                            timestamp = str(snapshot.time_created)
                            created_ts_epoch = calendar.timegm(
                                time.strptime(timestamp.split(".")[0], "%Y-%m-%d %H:%M:%S"))
                            obsolete_ts_epoch = created_ts_epoch + snapshot_cleanup_threshold * globalvariables.SECONDS_PER_DAY
                            current_ts_epoch = calendar.timegm(gmtime())

                            if current_ts_epoch >= obsolete_ts_epoch:
                                # Cleanup obsolete snapshot
                                snapshot_ocid = snapshot.id
                                if ("DO_NOT_DELETE" not in snapshot.name):
                                    if fsssdk.delete_fs_snapshot(snapshot_ocid):
                                        message = "Succeed to delete snapshot {0}.".format(snapshot.name)
                                        apscom.info(message)
                                    else:
                                        if not mt_backup.check_snapshot_deleted(snapshot_ocid):
                                            ret_val = globalvariables.BACKUP_FAILED

                                            message = "Failed to delete snapshot {0}!".format(snapshot.name)
                                            apscom.warn(message)
        f.close()

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup snapshots per policy."
            apscom.info(message)
        else:
            message = "Failed to cleanup snapshots per policy."
            apscom.warn(message)

        return ret_val

    except Exception as e:
        message = "Failed to cleanup snapshot created {0} days ago with name pattern {1}!\n{2}{3}".format(
            snapshot_cleanup_threshold, snapshot_name_pattern, sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

    finally:
        if f:
            f.close()

def cleanup_object_name_pattern(object_name_pattern, object_cleanup_threshold):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        oss_bucket = inst_meta.default_bucket
        # object_time_pattern = "\d{4}-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-6][0-9]:[0-6][0-9].\d*[zZ]"
        object_time_pattern = "\d{4}-[0-1][0-9]-[0-3][0-9] [0-2][0-9]:[0-6][0-9]:[0-6][0-9].\d*"

        object_list = osssdk.list_objects(oss_bucket)

        for object_info in object_list:
            if re.compile(object_name_pattern).match(object_info.name):
                if not re.compile(object_time_pattern).match(str(object_info.time_created)):
                    ret_val = globalvariables.BACKUP_FAILED

                    message = "Unsupported time pattern of timeCreated {0} in object metadata!".format(
                        str(object_info.time_created))
                    apscom.warn(message)
                else:
                    timestamp = str(object_info.time_created)
                    created_ts_epoch = calendar.timegm(time.strptime(timestamp.split(".")[0], "%Y-%m-%d %H:%M:%S"))
                    obsolete_ts_epoch = created_ts_epoch + object_cleanup_threshold * globalvariables.SECONDS_PER_DAY
                    current_ts_epoch = calendar.timegm(gmtime())

                    if current_ts_epoch >= obsolete_ts_epoch:
                        # Cleanup obsolete object
                        deleted = osssdk.delete_object(oss_bucket, object_info.name)
                        if not deleted:
                            if osssdk.check_object_exist(oss_bucket, object_info.name):
                                ret_val = globalvariables.BACKUP_FAILED
                        else:
                            message = "Succeed to delete object {0}.".format(object_info.name)
                            apscom.info(message)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to cleanup objects per policy."
            apscom.info(message)
        else:
            message = "Failed to cleanup objects per policy."
            apscom.warn(message)

        return ret_val

    except Exception as e:
        message = "Failed to cleanup object created {0} days ago with name pattern {1}!\n{2}{3}".format(
            object_cleanup_threshold, object_name_pattern, sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def cleanup_per_policy(cleanup_policy_path):
    """ Cleanup obsolete backup data per cleanup policy
    Args:
        cleanup_policy_path (str): Path of cleanup policy file
    Returns:
    Raises:
    """
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        global fs_config_path

        fs_config_path = mt_backup.create_fs_list()

        if not os.path.isfile(cleanup_policy_path):
            message = "Invalid cleanup policy path provided by --cleanup-policy-file!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        f = open(cleanup_policy_path, 'r')
        cleanup_policy = json.load(f)

        snapshot_name_pattern = cleanup_policy["snapshot_name_pattern"]
        object_name_pattern = cleanup_policy["object_name_pattern"]
        snapshot_cleanup_threshold = cleanup_policy["snapshot_cleanup_threshold"]
        object_cleanup_threshold = cleanup_policy["object_cleanup_threshold"]

        if snapshot_name_pattern and snapshot_cleanup_threshold:
            cleanup_snapshot_name_pattern(snapshot_name_pattern, snapshot_cleanup_threshold)

        if object_name_pattern and object_cleanup_threshold:
            cleanup_object_name_pattern(object_name_pattern, object_cleanup_threshold)
        f.close()
    except Exception as e:
        message = "Failed to do cleanup per clean policy config file {0}!\n{1}{2}".format(cleanup_policy_path,
                                                                                       sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

    finally:
        if f:
            f.close()


def take_action_cleanup(options):
    """ Cleanup obsolete backup data
    Args:
        options: Program options
    Returns:
    Raises:
    """
    try:
        """
        If --cleanup-policy-file specified, do cleanup per policy of pattern in config file.
        If no --cleanup-policy-file specified, do cleanup per retention days of backup metadata.
        """
        global fs_config_path
        cleanup_policy_path = options.cleanup_policy_path
        catalog_type = options.catalog_type

        ret_val = globalvariables.BACKUP_SUCCESS

        # Create fs config file for cleanup
        fs_config_path = mt_backup.create_fs_list()
        retention_days = 60

        fsssdk.get_older_snapshots(fs_config_path, retention_days)

        if cleanup_policy_path:
            cleanup_per_policy(cleanup_policy_path)
        else:
            ret_val = cleanup_per_backup_metadata(catalog_type)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to do cleanup."
            apscom.info(message)
        else:
            message = "Failed to do cleanup!"
            apscom.warn(message)
        return ret_val

    except Exception as e:
        message = "Failed to cleanup obsolete backup data!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def take_action_schedule_enable(options):
    message = "Backup to cron job to be supported"
    apscom.info(message)

    return globalvariables.BACKUP_SUCCESS


def get_backup_list(database, table_name, backup_status):
    try:
        backup_list = []

        db_tables = database.get_existing_tables()
        if table_name not in db_tables:
            return backup_list

        if backup_status == "ALL":
            sql_cmd = "SELECT * from " + table_name
        else:
            sql_cmd = "SELECT * from " + table_name + " WHERE status = " + "'" + backup_status + "'"

        database.query(sql_cmd)
        backup_list = database.cursor.fetchall()

        return backup_list

    except Exception as e:
        message = "Failed to get backup list!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise

def take_action_list_backups(options):
    try:
        backup_history = {}

        oss_bucket = inst_meta.default_bucket

        backup_status = options.backup_status.upper()

        catalog_type = options.catalog_type

        # First download backup db from oss.
        if osssdk.check_object_exist(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
            out = osssdk.get_object(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        if not os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
            print("There is not any backup created.")
            return globalvariables.BACKUP_SUCCESS

        mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
        backup_list = get_backup_list(mt_backup_db, "backup_history_table_v2", backup_status)
        if not backup_list:
            print("There is not any backup created.")
            return globalvariables.BACKUP_SUCCESS

        for backup_info in backup_list:
            backup_metadata = fill_backup_metadata(backup_info)

            print(json.dumps(backup_metadata, sort_keys=True, indent=4))
            mt_backup_db.close()

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to list backup history!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise


def get_active_backup_tags(catalog_type):
    try:
        tag_list = []
        oss_bucket = inst_meta.default_bucket
        if osssdk.check_object_exist(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
            out = osssdk.get_object(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        if not os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
            return tag_list
        mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
        backup_list = get_backup_list(mt_backup_db, "backup_history_table_v2", "ACTIVE")
        for backup_info in backup_list:
            backup_metadata = fill_backup_metadata(backup_info)
            snapshot_tag = backup_metadata["tag"]
            if snapshot_tag != "ocifsbackup":
                tag_list.append(snapshot_tag)

        mt_backup_db.close()

        return tag_list

    except Exception as e:
        message = "Failed to get active backup tags!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise


def take_action_create_snapshot(options):
    try:
        global fs_config_path
        backup_list = []
        backup_metadata = {}

        retention_days = options.retention_days
        snapshot_tag = options.snapshot_tag
        if not snapshot_tag:
            message = "Need to provide snapshot tag by --snapshot-tag!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        catalog_type = options.catalog_type
        active_tag_list = get_active_backup_tags(catalog_type)
        if snapshot_tag in active_tag_list:
            message = "The snapshot with tag {0} is still active, please specify another tag!".format(snapshot_tag)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        # Only create snapshot on the backup host.
        component_type = inst_meta.component_type
        this = False

        if component_type in globalvariables.FA_COMPONENT_LIST:
            this = fsssdk.get_backup_host_fa()
        elif component_type in globalvariables.IDM_COMPONENT_LIST:
            this = fsssdk.get_backup_host_idm()
        elif component_type in globalvariables.OHS_COMPONENT_LIST:
            this = fsssdk.get_backup_host_ohs()
        else:
            message = "Unknown component type {0}!".format(component_type)
            apscom.warn(message)
            raise

        if this == False:
            message = "This VM is not the backup host. Snapshot is not created on this host."
            apscom.info(message)

            return globalvariables.BACKUP_SUCCESS

        # Create snapshot and fill backup_list for backup metadata.
        fs_config_path = mt_backup.create_fs_list()

        # For create snapshot, use snapshot_tag as prefix.
        # prefix = options.prefix
        prefix = snapshot_tag
        snapshot_list = mt_backup.create_fs_snapshots(fs_config_path, prefix)
        for snapshot in snapshot_list:
            backup_list.append(snapshot["id"])

        # Update backup metadata to central catalog DB.
        action = options.action
        backup_type = "create_snapshot"
        catalog_type = options.catalog_type
        post_backup_metadata.create_backup_metadata(action, backup_type, backup_list, retention_days, snapshot_tag, catalog_type, "ACTIVE",log_file)

        # Do cleanup after create snpashot
        cleanup_per_backup_metadata(catalog_type)

        message = "Succeed to create snapshot with tag {0}.".format(snapshot_tag)
        apscom.info(message)
        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to create snapshot!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def take_action_list_tags(options):
    try:
        catalog_type = options.catalog_type
        snapshot_tags = get_active_backup_tags(catalog_type)
        message = "Active snapshot tags: {0}".format(snapshot_tags)
        apscom.info(message)

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to list snapshot tags!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise


def get_metadata_from_tag(catalog_type, tag):
    try:
        backup_metadata = {}
        oss_bucket = inst_meta.default_bucket

        if osssdk.check_object_exist(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
            out = osssdk.get_object(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        if not os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
            return backup_metadata

        mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
        backup_list = get_backup_list(mt_backup_db, "backup_history_table_v2", "ACTIVE")
        for backup_info in backup_list:
            backup_metadata = fill_backup_metadata(backup_info)
            snapshot_tag = backup_metadata["tag"]
            if snapshot_tag == tag:
                mt_backup_db.close()
                return backup_metadata

            mt_backup_db.close()

        return backup_metadata

    except Exception as e:
        message = "Failed to get metadata with tag {0}!\n{1}{2}".format(tag, sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise


def take_action_list_snapshot(options):
    try:
        snapshot_tag = options.snapshot_tag
        catalog_type = options.catalog_type
        if not snapshot_tag:
            message = "Need to provide snapshot tag by --snapshot-tag!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        backup_metadata = get_metadata_from_tag(catalog_type, snapshot_tag)
        if backup_metadata:
            print(json.dumps(backup_metadata, sort_keys=True, indent=4))
        else:
            message = "There is not any active snapshot with tag {0}.".format(snapshot_tag)
            apscom.info(message)

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to list snapshot with tag{0}!\n{1}{2}".format(snapshot_tag, sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise

def take_action_restore_tag(options):
    try:
        global fs_config_path
        snapshot_list = []
        snapshot_tag = options.snapshot_tag

        if not snapshot_tag:
            message = "Need to provide snapshot tag by --snapshot-tag!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        catalog_type = options.catalog_type
        snapshot_tags = get_active_backup_tags(catalog_type)
        if snapshot_tag not in snapshot_tags:
            message = "{0} is not an active tag!".format(snapshot_tag)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        message = "Restoring from tag {0} ...".format(snapshot_tag)
        apscom.info(message)

        fs_config_path = mt_backup.create_fs_list()

        backup_metadata = get_metadata_from_tag(catalog_type, snapshot_tag)
        backup_pieces = backup_metadata["piece_name"]
        backup_list = backup_pieces.split(",")

        for backup in backup_list:
            snapshot_info = fsssdk.list_fs_snapshot(backup)
            if snapshot_info:
                snapshot_name = snapshot_info.name
                snapshot_list.append(snapshot_name)
            else:
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(backup)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

        # Restore snapshot
        snapshot_info_list = get_snapshot_info(snapshot_list)
        for mount_point in snapshot_info_list.keys():
            snapshot_path = snapshot_info_list[mount_point]
            if not os.path.isdir(snapshot_path):
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(
                    snapshot_path)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED
            else:
                message = "Restoring {0} from {1} ...".format(mount_point, snapshot_path)
                apscom.info(message)

                mount_point_stat = os.stat(mount_point)
                mount_point_perm = oct(mount_point_stat.st_mode)[-4:]

                if mount_point == "/u01":
                    exclude_list_f = open(globalvariables.RESTORE_EXCLUDE_LIST, 'w')
                    exclude_list_f.write("SRE")
                    exclude_list_f.close()

                    cmd = [CP_TOOL, "--delete", "--exclude-from={0}".format(globalvariables.RESTORE_EXCLUDE_LIST), snapshot_path,
                           mount_point]
                else:
                    cmd = [CP_TOOL, "--delete", snapshot_path, mount_point]

                process = Popen(cmd, stdout=PIPE)
                (out, err) = process.communicate()
                exit_code = process.wait()

                # Restore the perm of mount point in case it is changed during restore.
                os.chmod(mount_point,mount_point_perm)
                #cmd = ["chmod", mount_point_perm, mount_point]
                #out = apscom.run_cmd(cmd)

        message = "Succeed to restore from tag {0}.".format(snapshot_tag)
        apscom.info(message)

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to restore from tag!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

        raise


def get_orphan_snapshots(fs_config_list, active_backup_list, prefix):
    """ List orphan snapshots of each file system.
    Args:
         fs_config_list: Config list of each filesystem.
         active_backup_list: List of active backups.
         prefix: Prefix of snapshot name.
    Returns:
    Raises:
    """
    try:
        orphan_snapshots = {}

        component_type = inst_meta.component_type
        backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]

        for mount_point, fs_info in backup_dirs.items():
            snapshot_list = {}

            if fs_info["this"]:
                fs_name = fs_info["nfs_share"].split(":")[1].rsplit("/", 1)[1]
                snapshot_name_prefix = prefix + "_" + "snapshot" + "_" + fs_name + "."
                fs_ocid = fs_info["id"]

                fs_snapshots = fsssdk.list_fs_snapshots(fs_ocid)
                for snapshot in fs_snapshots:
                    snapshot_ocid = snapshot.id
                    snapshot_name = snapshot.name

                    if snapshot_name.startswith(snapshot_name_prefix) and (snapshot_ocid not in active_backup_list):
                        snapshot_list[snapshot_name] = snapshot_ocid

            if snapshot_list:
                orphan_snapshots[mount_point] = snapshot_list

        return orphan_snapshots

    except Exception as e:
        message = "Failed to list orphan snapshots!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def get_orphan_files(active_backup_list, prefix):
    """ List orphan backup files in FSS.
    Args:
         active_backup_list: List of active backups.
         prefix: Prefix of backup files.
    Returns:
    Raises:
    """
    try:
        orphan_files = []

        backup_prefix = prefix + "_" + globalvariables.LOCAL_HOST + "."
        backup_suffix = ".tgz"

        backup_files = os.listdir(globalvariables.BACKUP_FILES_PATH)
        for backup in backup_files:
            if backup.startswith(backup_prefix) and backup.endswith(backup_suffix):
                backup_path = globalvariables.BACKUP_FILES_PATH + "/" + backup

                if backup_path not in active_backup_list:
                    orphan_files.append(backup_path)

        return orphan_files

    except Exception as e:
        message = "Failed to list orphan files!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def get_orphan_objects(fs_config_list, active_backup_list, prefix):
    """ List orphan backup objects.
    Args:
         fs_config_list: Config list of each filesystem.
         active_backup_list: List of active backups.
         prefix: Prefix of object name.
    Returns:
    Raises:
    """
    try:
        orphan_objects = {}

        oss_bucket = inst_meta.default_bucket
        component_type = inst_meta.component_type
        fa_service = inst_meta.fa_service_name
        backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]

        for mount_point, fs_info in backup_dirs.items():
            obj_list = []

            if fs_info["this"]:
                fs_name = fs_info["nfs_share"].split(":")[1].rsplit("/", 1)[1]
                if fs_name.startswith(fa_service):
                    obj_name_prefix = prefix + "_" + fs_name + "."
                    obj_name_suffix = ".tgz"

                    fs_objects = osssdk.list_objects(oss_bucket, obj_name_prefix=obj_name_prefix)
                    for obj in fs_objects:
                        if obj.name.endswith(obj_name_suffix) and (obj.name not in active_backup_list):
                            obj_list.append(obj.name)

                if obj_list:
                    orphan_objects[mount_point] = obj_list

            else:
                # OS backup files only uploaded to OSS if not backup snapshot.
                # TODO: One bug for full to oss backup after fix of 29740242,
                # no os backups for host backup snapshots.
                obj_name_prefix = prefix + "_" + globalvariables.LOCAL_HOST + "."
                obj_name_suffix = ".tgz"
                backup_objects = osssdk.list_objects(oss_bucket, obj_name_prefix=obj_name_prefix)

                for obj in backup_objects:
                    if obj.name.endswith(obj_name_suffix) and (obj.name not in active_backup_list):
                        obj_list.append(obj.name)

                if obj_list:
                    orphan_objects["os_files"] = obj_list

                break

        return orphan_objects

    except Exception as e:
        message = "Failed to list orphan objects!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


def take_action_list_orphan(options):
    try:
        backup_pieces = []

        # Currently only local database is checked.
        oss_bucket = inst_meta.default_bucket
        prefix = options.prefix

        # Get all active backup components from local database.
        if osssdk.check_object_exist( oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
            out = osssdk.get_object( oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        if os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
            mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
            backup_list = get_backup_list(mt_backup_db, "backup_history_table_v2", "ACTIVE")

            for backup_info in backup_list:
                backup_metadata = fill_backup_metadata(backup_info)
                piece_name = backup_metadata["piece_name"]
                piece_list = piece_name.split(",")
                backup_pieces.extend(piece_name.split(","))

            mt_backup_db.close()

        # Update filesystem config list.
        fs_config_path = mt_backup.create_fs_list()
        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)

        # List orphan snapshots
        orphan_snapshots = get_orphan_snapshots(fs_config_list, backup_pieces, prefix)
        if orphan_snapshots:
            for mount_point, snapshot_list in orphan_snapshots.items():
                message = "The orphan snapshots created for {0} are:".format(mount_point)
                apscom.info(message)

                for snapshot_name in snapshot_list.keys():
                    apscom.info(" + {0}".format(snapshot_name))

        else:
            apscom.info("There is not any orphan snapshot.")

        # List orphan files
        orphan_files = get_orphan_files(backup_pieces, prefix)
        if orphan_files:
            apscom.info("The orphan os backup files in {0} of FSS are:".format(globalvariables.BACKUP_FILES_PATH))

            for backup_path in orphan_files:
                apscom.info(" + {0}".format(backup_path.rsplit("/", 2)[-1]))

        else:
            apscom.info("There is not any orphan os backup file in FSS.")

        # List orphan objects
        orphan_objects = get_orphan_objects(fs_config_list, backup_pieces, prefix)
        if orphan_objects:
            for backup_src, backup_info in orphan_objects.items():
                apscom.info("The orphan backup objects for {0} are:".format(backup_src))
                for backup in backup_info:
                    apscom.info(" + {0}".format(backup))
        else:
            apscom.info("There is not any orphan backup object.")
        f.close()
        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to list orphan backups!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def restore_backup_to_fss(backup_pieces, restore_os_files, exclude_list = None):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        snapshot_list = []

        message = "Restoring from backup to fss ..."
        apscom.info(message)

        # Backup info [snap_ocid_1, ..., snap_ocid_n, files_path]
        backup_list = backup_pieces.split(",")
        backup_files_path = backup_list[-1]
        backup_list.remove(backup_files_path)

        for backup in backup_list:
            snapshot_info = fsssdk.list_fs_snapshot(backup)
            if snapshot_info:
                snapshot_name = snapshot_info.name
                snapshot_list.append(snapshot_name)
            else:
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(backup)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

        snapshot_info_list = get_snapshot_info(snapshot_list)
        if "/u01" in snapshot_info_list.keys():
            u01_snapshot_path = snapshot_info_list["/u01"]
            backup_files_path = u01_snapshot_path + "/" + backup_files_path.split("/u01", 1)[1]

        # Verify the integrity of backup data
        if not os.path.isfile(backup_files_path):
            message = "Backup files {0} not exist, please verify the integrity of backup data!".format(backup_files_path)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        # Cleanup restore files path before restore
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)

        # Restore backup files first
        #tar.extractall(path=RESTORE_FILES_PATH)
        message = "Restoring os backup files to {0} ...".format(globalvariables.RESTORE_FILES_PATH)
        apscom.info(message)
        cmd = ["tar", "xzf", backup_files_path, '-C', globalvariables.RESTORE_FILES_PATH]
        out = apscom.run_cmd(cmd, timeout_secs=globalvariables.TAR_TIMEOUT)

        if restore_os_files:
            root_stat = os.stat("/")
            root_perm = oct(root_stat.st_mode)[-4:]

            if exclude_list:
                cmd = [CP_TOOL, "--exclude-from={0}".format(exclude_list), globalvariables.RESTORE_FILES_PATH, "/"]
            else:
                cmd = [CP_TOOL, globalvariables.RESTORE_FILES_PATH, "/"]

            message = "Restoring os files from {0} ...".format(globalvariables.RESTORE_FILES_PATH)
            apscom.info(message)
            process = Popen(cmd, stdout=PIPE)
            (out, err) = process.communicate()
            exit_code = process.wait()

            # Restore the perm of / in case it is changed during restore.
            cmd = ["chmod", root_perm, "/"]
            out = apscom.run_cmd(cmd)

        # Restore snapshot
        for mount_point in snapshot_info_list.keys():
            snapshot_path = snapshot_info_list[mount_point]
            if not os.path.isdir(snapshot_path):
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(snapshot_path)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED
            else:
                message = "Restoring {0} from {1} ...".format(mount_point, snapshot_path)
                apscom.info(message)

                mount_point_stat  = os.stat(mount_point)
                mount_point_perm = oct(mount_point_stat.st_mode)[-4:]

                if mount_point == "/u01":
                    exclude_list_f = open(globalvariables.RESTORE_EXCLUDE_LIST, 'w')
                    exclude_list_f.write("SRE")
                    exclude_list_f.close()

                    cmd = [CP_TOOL, "--delete", "--exclude-from={0}".format(globalvariables.RESTORE_EXCLUDE_LIST), snapshot_path, mount_point]
                else:
                    cmd = [CP_TOOL, "--delete", snapshot_path, mount_point]

                process = Popen(cmd, stdout=PIPE)
                (out, err) = process.communicate()
                exit_code = process.wait()

                # Restore the perm of mount point in case it is changed during restore.
                cmd = ["chmod", mount_point_perm, mount_point]
                out = apscom.run_cmd(cmd)

        if restore_os_files:
            commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)

        message = "Succeed to restore from backup to fss."
        apscom.info(message)

        return ret_val

    except Exception:
        message = "Failed to restore from backup to fss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


def restore_snapshot_to_oss(backup_pieces, restore_os_files, exclude_list=None):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        snapshot_list = []

        oss_namespace = osssdk.oss_namespace
        oss_bucket = inst_meta.default_bucket

        message = "Restoring from backup snapshot to oss ..."
        apscom.info(message)

        # Backup info [snap_ocid_1, ..., snap_ocid_n, files_obj_name]
        backup_list = backup_pieces.split(",")
        files_obj = backup_list[-1]
        backup_list.remove(files_obj)

        for backup in backup_list:
            snapshot_info = fsssdk.list_fs_snapshot(backup)
            if snapshot_info:
                snapshot_name = snapshot_info.name
                snapshot_list.append(snapshot_name)
            else:
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(backup)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

        # Cleanup restore path before restore
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_OBJ_PATH)

        # Verify the integrity of backup data
        if not osssdk.check_object_exist(oss_namespace, oss_bucket, files_obj):
            message = "Backup files object {0} not exist, please verify the integrity of backup data!".format(files_obj)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        # Download backup file object
        restore_path = globalvariables.RESTORE_OBJ_PATH + "/" + files_obj
        message = "Downloading object {0} to {1} ...".format(files_obj, restore_path)
        apscom.info(message)
        out = osssdk.get_object(oss_namespace, oss_bucket, files_obj, restore_path)

        # tar = tarfile.open(restore_path)
        # tar.extractall(path=RESTORE_FILES_PATH)
        # tar.close()
        message = "Restoring os backup files to {0} ...".format(globalvariables.RESTORE_FILES_PATH)
        apscom.info(message)
        cmd = ["tar", "xzf", restore_path, '-C', globalvariables.RESTORE_FILES_PATH]
        out = apscom.run_cmd(cmd, timeout_secs=globalvariables.TAR_TIMEOUT)

        if restore_os_files:
            root_stat = os.stat("/")
            root_perm = oct(root_stat.st_mode)[-4:]
            if exclude_list:
                cmd = [CP_TOOL, "--exclude-from={0}".format(exclude_list), globalvariables.RESTORE_FILES_PATH, "/"]
            else:
                cmd = [CP_TOOL, globalvariables.RESTORE_FILES_PATH, "/"]
            message = "Restoring os files from {0} ...".format(globalvariables.RESTORE_FILES_PATH)
            apscom.info(message)
            process = Popen(cmd, stdout=PIPE)
            (out, err) = process.communicate()
            exit_code = process.wait()

            # Restore the perm of / in case it is changed during restore.
            cmd = ["chmod", root_perm, "/"]
            out = apscom.run_cmd(cmd)

        # Restore snapshot
        snapshot_info_list = get_snapshot_info(snapshot_list)
        for mount_point in snapshot_info_list.keys():
            snapshot_path = snapshot_info_list[mount_point]
            if not os.path.isdir(snapshot_path):
                message = "Backup snapshot {0} not exist, please verify the integrity of backup data!".format(
                    snapshot_path)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED
            else:
                message = "Restoring {0} from {1} ...".format(mount_point, snapshot_path)
                apscom.info(message)

                mount_point_stat = os.stat(mount_point)
                mount_point_perm = oct(mount_point_stat.st_mode)[-4:]

                if mount_point == "/u01":
                    exclude_list_f = open(globalvariables.RESTORE_EXCLUDE_LIST, 'w')
                    exclude_list_f.write("SRE")
                    exclude_list_f.close()

                    cmd = [CP_TOOL, "--delete", "--exclude-from={0}".format(globalvariables.RESTORE_EXCLUDE_LIST), snapshot_path,
                           mount_point]
                else:
                    cmd = [CP_TOOL, "--delete", snapshot_path, mount_point]

                process = Popen(cmd, stdout=PIPE)
                (out, err) = process.communicate()
                exit_code = process.wait()

                # Restore the perm of mount point in case it is changed during restore.
                cmd = ["chmod", mount_point_perm, mount_point]
                out = apscom.run_cmd(cmd)

        if restore_os_files:
            commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_OBJ_PATH)

        message = "Succeed to restore from backup snapshot to oss."
        apscom.info(message)

        return ret_val

    except Exception:
        message = "Failed to restore from backup of snapshot_to_oss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


def restore_full_to_oss(backup_pieces, restore_os_files, exclude_list=None):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        oss_namespace = osssdk.oss_namespace
        oss_bucket = inst_meta.default_bucket

        message = "Restoring from backup full to oss ..."
        apscom.info(message)

        # Backup info [snap_obj_name_1, ..., snap_obj_name_n, files_path]
        backup_list = backup_pieces.split(",")

        # Cleanup restore files path before restore
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_OBJ_PATH)
        commonutils.cleanup_dir(globalvariables.RESTORE_FS_PATH)

        # If only one item in the list, it is the object name. Need to download.
        # Otherwise, the last one is the path of backup files. No need to download.
        if len(backup_list) == 1:
            # Download backup file object
            files_obj = backup_list[-1]
            restore_path = globalvariables.RESTORE_OBJ_PATH + "/" + files_obj

            if not osssdk.check_object_exist(oss_namespace, oss_bucket, files_obj):
                message = "Backup files object {0} not exist, please verify the integrity of backup data!".format(
                    files_obj)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

            message = "Downloading object {0} to {1} ...".format(files_obj, restore_path)
            apscom.info(message)
            out = osssdk.get_object(oss_namespace, oss_bucket, files_obj, restore_path)

            # tar = tarfile.open(restore_path)
            # tar.extractall(path=RESTORE_FILES_PATH)
            # tar.close()
            message = "Restoring os backup files to {0} ...".format(globalvariables.RESTORE_FILES_PATH)
            apscom.info(message)
            cmd = ["tar", "xzf", restore_path, '-C', globalvariables.RESTORE_FILES_PATH]
            out = apscom.run_cmd(cmd, timeout_secs=globalvariables.TAR_TIMEOUT)

            # Remove the object after untar
            os.remove(restore_path)

            if restore_os_files:
                root_stat = os.stat("/")
                root_perm = oct(root_stat.st_mode)[-4:]
                # Restore backup files
                if exclude_list:
                    cmd = [CP_TOOL, "--exclude-from={0}".format(exclude_list), globalvariables.RESTORE_FILES_PATH, "/"]
                else:
                    cmd = [CP_TOOL, globalvariables.RESTORE_FILES_PATH, "/"]

                message = "Restoring os files from {0} ...".format(globalvariables.RESTORE_FILES_PATH)
                apscom.info(message)

                process = Popen(cmd, stdout=PIPE)
                (out, err) = process.communicate()
                exit_code = process.wait()

                # Restore the perm of / in case it is changed during restore.
                cmd = ["chmod", root_perm, "/"]
                out = apscom.run_cmd(cmd)

                commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)

            message = "Succeed to restore from backup full to oss."
            apscom.info(message)

            return ret_val

        backup_files = backup_list[-1]
        backup_list.remove(backup_files)
        obj_pattern = "ocifsbackup_(?P<fs_name>\S+).\d{4}-[0-1][0-9]-[0-3][0-9].[0-2][0-9][0-6][0-9][0-6][0-9]_\+\d{4}.tgz"
        component_type = inst_meta.component_type

        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)
        f.close()

        for obj in backup_list:
            restore_path = globalvariables.RESTORE_OBJ_PATH + "/" + obj

            if not osssdk.check_object_exist(oss_namespace, oss_bucket, obj):
                message = "Backup files object {0} not exist, please verify the integrity of backup data!".format(obj)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

            message = "Downloading object {0} to {1} ...".format(obj, restore_path)
            apscom.info(message)
            out = osssdk.get_object(oss_namespace, oss_bucket, obj, restore_path)

            matched = re.compile(obj_pattern).match(obj)
            if matched:
                fs_name = matched.group('fs_name')
            else:
                message = "Failed to get file system name from object {0}!".format(obj)
                apscom.warn(message)

                raise

            # Get mount point for each snapshot
            backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
            for mount_point in backup_dirs.keys():
                nfs_share = backup_dirs[mount_point]["nfs_share"]
                if nfs_share and nfs_share.rsplit("/", 1)[1] == fs_name:
                    # Mount point is the target dir to do restore
                    tar = tarfile.open(restore_path)
                    tar.extractall(path=globalvariables.RESTORE_FS_PATH)
                    tar.close()

                    # Remove the object after untar
                    os.remove(restore_path)

                    if mount_point == "/u01":
                        # Verify the integrity of backup data
                        backup_files = globalvariables.RESTORE_FS_PATH + "/" + backup_files.split("/u01", 1)[1]
                        if not os.path.isfile(backup_files):
                            message = "OS backup files {0} not exist, skipping OS restore ...".format(backup_files)
                            apscom.warn(message)

                            ret_val = globalvariables.BACKUP_FAILED
                        else:
                            message = "Restoring os backup files to {0} ...".format(globalvariables.RESTORE_FILES_PATH)
                            apscom.info(message)
                            cmd = ["tar", "xzf", backup_files, '-C', globalvariables.RESTORE_FILES_PATH]
                            out = apscom.run_cmd(cmd, timeout_secs=globalvariables.TAR_TIMEOUT)

                            if restore_os_files:
                                root_stat = os.stat("/")
                                root_perm = oct(root_stat.st_mode)[-4:]
                                if exclude_list:
                                    cmd = [CP_TOOL, "--exclude-from={0}".format(exclude_list), globalvariables.RESTORE_FILES_PATH, "/"]
                                else:
                                    cmd = [CP_TOOL, restore_src, restore_dst]

                                message = "Restoring os files from {0} ...".format(globalvariables.RESTORE_FILES_PATH)
                                apscom.info(message)

                                process = Popen(cmd, stdout=PIPE)
                                (out, err) = process.communicate()
                                exit_code = process.wait()

                                # Restore the perm of / in case it is changed during restore.
                                cmd = ["chmod", root_perm, "/"]
                                out = apscom.run_cmd(cmd)

                                commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH)

                    message = "Restoring {0} from {1} ...".format(mount_point, globalvariables.RESTORE_FS_PATH)
                    apscom.info(message)

                    mount_point_stat = os.stat(mount_point)
                    mount_point_perm = oct(mount_point_stat.st_mode)[-4:]

                    if mount_point == "/u01":
                        exclude_list_f = open(globalvariables.RESTORE_EXCLUDE_LIST, 'w')
                        exclude_list_f.write("SRE")
                        exclude_list_f.close()

                        cmd = [CP_TOOL, "--delete", "--exclude-from={0}".format(globalvariables.RESTORE_EXCLUDE_LIST), globalvariables.RESTORE_FS_PATH,
                               mount_point]
                    else:
                        cmd = [CP_TOOL, "--delete", globalvariables.RESTORE_FS_PATH, mount_point]

                    process = Popen(cmd, stdout=PIPE)
                    (out, err) = process.communicate()
                    exit_code = process.wait()

                    # Restore the perm of mount point in case it is changed during restore.
                    cmd = ["chmod", mount_point_perm, mount_point]
                    out = apscom.run_cmd(cmd)

                    commonutils.cleanup_dir(globalvariables.RESTORE_FS_PATH)
                    break

        message = "Succeed to restore from backup full to oss."
        apscom.info(message)

        return ret_val

    except Exception:
        message = "Failed to do cleanup for backup of full_to_oss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


RESTORE_PER_BACKUP_TYPE = {
    "snapshot_to_fss": restore_backup_to_fss,
    "full_to_fss": restore_backup_to_fss,
    "snapshot_to_oss": restore_snapshot_to_oss,
    "full_to_oss": restore_full_to_oss
}
def take_action_restore(options):
    try:
        global fs_config_path
        backup_info = []
        backup_metadata = {}
        oss_namespace = osssdk.oss_namespace
        oss_bucket =  inst_meta.default_bucket

        backup_id = options.backup_id
        if not backup_id:
            message = "Backup id to be restored not specified by --backup-id!"
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        catalog_type = options.catalog_type
        exclude_list = options.exclude_list

        if catalog_type == "local":
            # First download backup db from oss.
            if osssdk.check_object_exist(oss_namespace, oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
                out = osssdk.get_object(oss_namespace, oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

            if not os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
                message = "Failed to restore from backup id {0}! There is not any backup created on this VM!".format(backup_id)
                apscom.warn(message)

                return globalvariables.BACKUP_FAILED

            mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
            if "backup_history_table_v2" in mt_backup_db.get_existing_tables():
                sql_cmd = "SELECT * from backup_history_table_v2 WHERE backup_id = " + str(backup_id)
                mt_backup_db.query(sql_cmd)
                backup_info = mt_backup_db.cursor.fetchone()
            mt_backup_db.close()

            if backup_info:
                backup_metadata = fill_backup_metadata(backup_info)

        if not backup_metadata:
            message = "Backup id {0} not found, need to specify a valid backup id by --backup-id!".format(backup_id)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        if backup_metadata["status"] != "ACTIVE":
            message = "Not an active backup id {0} specified by --backup-id!".format(backup_id)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        if backup_metadata["backup_type"] == "create_snapshot":
            message = "Please use --action restore-tag to restore this backup type."
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

        fs_config_path = mt_backup.create_fs_list()

        backup_type = backup_metadata["backup_type"]
        backup_pieces = backup_metadata["piece_name"]
        #print backup_type, backup_pieces, exclude_list
        exclude_list_f = open(globalvariables.RESTORE_EXCLUDE_LIST, 'w')
        if exclude_list:
            f = open(exclude_list, 'r')
            for line in f:
                exclude_list_f.write(line)
            f.close()

        default_f = open(globalvariables.RESTORE_EXCLUDE_DEFAULT, 'r')
        for line in default_f:
            exclude_list_f.write(line)
        default_f.close()

        exclude_list_f.close()

        restore_os_files = options.restore_os_files
        ret_val = RESTORE_PER_BACKUP_TYPE.get(backup_type)(backup_pieces, restore_os_files, globalvariables.RESTORE_EXCLUDE_LIST)

        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to restore from backup id {0}.".format(backup_id)
            apscom.info(message)

            return globalvariables.BACKUP_SUCCESS
        else:
            message = "Failed to restore from backup id {0}!".format(backup_id)
            apscom.warn(message)

            return globalvariables.BACKUP_FAILED

    except Exception:
        message = "Failed to do restore!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise
def take_action_cleanup_orphan(options):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        backup_pieces = []

        # Currently only local database is checked.
        oss_bucket = inst_meta.default_bucket
        prefix = options.prefix

        # Get all active backup components from local database.
        if osssdk.check_object_exist(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB):
            out = osssdk.get_object(oss_bucket, globalvariables.OBJ_BACKUP_SQLDB, globalvariables.BACKUP_SQLDB_PATH)

        if os.path.isfile(globalvariables.BACKUP_SQLDB_PATH):
            mt_backup_db = apssqldb.ApsSqldb(globalvariables.BACKUP_SQLDB_PATH)
            backup_list = get_backup_list(mt_backup_db, "backup_history_table_v2", "ACTIVE")

            for backup_info in backup_list:
                backup_metadata = fill_backup_metadata(backup_info)
                piece_name = backup_metadata["piece_name"]
                piece_list = piece_name.split(",")
                backup_pieces.extend(piece_name.split(","))

            mt_backup_db.close()

        # Update filesystem config list.
        fs_config_path = mt_backup.create_fs_list()
        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)

        # Get orphan snapshots
        orphan_snapshots = get_orphan_snapshots(fs_config_list, backup_pieces, prefix)
        snapshot_list = {}
        if orphan_snapshots:
            apscom.info("=== The following orphan snapshots will be deleted: ===")
            for mount_point, snapshots in orphan_snapshots.items():
                for snapshot_name, snapshot_ocid in snapshots.items():
                    snapshot_list[snapshot_name] = snapshot_ocid
                    apscom.info(" + {0}".format(snapshot_name))
        else:
            apscom.info("There is not any orphan snapshot to be cleaned up.")

        # Delete orphan snapshots
        for snapshot_name, snapshot_ocid in snapshot_list.items():
            if ("DO_NOT_DELETE" not in snapshot_name):
                if fsssdk.delete_fs_snapshot(snapshot_ocid):
                    message = "Succeed to delete snapshot {0}.".format(snapshot_name)
                    apscom.info(message)
                else:
                    if not mt_backup.check_snapshot_deleted(snapshot_ocid):
                        ret_val = globalvariables.BACKUP_FAILED

                        message = "Failed to delete snapshot {0}!".format(snapshot_name)
                        apscom.warn(message)
                    else:
                        message = "Snapshot {0} is already been deleted.".format(snapshot_name)
                        apscom.info(message)

        # Get orphan files
        orphan_files = get_orphan_files(backup_pieces, prefix)
        if orphan_files:
            apscom.info(
                "=== The following orphan backup files in {0} of FSS will be deleted: ===".format(globalvariables.BACKUP_FILES_PATH))
            for backup_path in orphan_files:
                apscom.info(" + {0}".format(backup_path.rsplit("/", 2)[-1]))

        else:
            apscom.info("There is not any orphan backup file in FSS to be cleaned up.")

        # Delete orphan files
        for backup_path in orphan_files:
            os.remove(backup_path)
            message = "Succeed to delete file {0}.".format(backup_path)
            apscom.info(message)

        # List orphan objects
        orphan_objects = get_orphan_objects(fs_config_list, backup_pieces, prefix)
        obj_list = []
        if orphan_objects:
            apscom.info("=== The following orphan backup objects will be deleted: ===")
            for backup_src, backup_info in orphan_objects.items():
                for obj in backup_info:
                    obj_list.append(obj)
                    apscom.info(" + {0}".format(obj))
        else:
            apscom.info("There is not any orphan backup object to be cleaned up.")

        # Delete orphan objects
        for obj in obj_list:
            obj_deleted = osssdk.delete_object(oss_bucket, obj)
            if not obj_deleted:
                if osssdk.check_object_exist(oss_bucket, obj):
                    apscom.warn("Failed to delete object {0}!".format(obj))
                    ret_val = globalvariables.BACKUP_FAILED
                else:
                    apscom.info("Object {0} is already been deleted.".format(obj))
            else:
                apscom.info("Succeed to delete object {0}.".format(obj))

        return ret_val

    except Exception as e:
        message = "Failed to list orphan backups!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise


TAKE_ACTION = {
    "backup": take_action_backup,
    "cleanup": take_action_cleanup,
    "update-fs-list": take_action_update_fs_list,
    "schedule-enable": take_action_schedule_enable,
    "list-backups": take_action_list_backups,
    "create-snapshot": take_action_create_snapshot,
    "list-snapshot-tags": take_action_list_tags,
    "list-tag": take_action_list_snapshot,
    "restore-tag": take_action_restore_tag,
    "list-orphan": take_action_list_orphan,
    "cleanup-orphan": take_action_cleanup_orphan,
    "restore": take_action_restore
}

usage_str = """
    ocifsbackup.py - Backup tool for OCI environment.

    # User Case 1: Update backup config file of file storage backup
    ocifsbackup.py --action update-fs-list -f <fs-config-file> 

    # User Case 2: Do backup action
    ocifsbackup.py --action backup -t <fss|oss> --backup-options <snaphot|full|incremental|differential> -p <retention-policy-file> --catalog-type <catalog_type>
        -t 
            fss - All backup data will be backup to file storage.
            oss - If oss, work with --backup-options.

        --backup-options
            snapshot - If snapshot and oss, only backup files in files-config-file will be sent to oss.
                       Snapshot of file storage will only backup in fss.
            full - If full and oss, all data will be backup to oss.
            incremental - To be supported.
            differential - To be supported.

        -p
            retention-policy-file - If not set, will use the default config-retention-policy_v2.json

        --catalog-type
            local - If set, backup metadata will be saved to local catalog DB.
            remote - Default type. When works in this mode, backup metadata will be send to central catalog DB.

    # User Case 3: Do restore action
    ocifsbackup.py --action restore --backup-id <backup_id> --catalog-type <catalog_type> --exclude-list <exclude_list>
        --backup-id
            Backup id of backups listed by "ocifsbackup.py --action list-backups"

        --catalog-type 
            local - If set, backup-id of local catalog db needs to be used.
            remote - Default type. When works in this mode, backup-id of central catalog db needs to be used.

        --exclude_list
            Path of file which includes files not to be restored.

    # User Case 4: Cleanup obsolete backup data
    ocifsbackup.py --action cleanup

    # User Case 5: Check the backup history
    ocifsbackup.py --action list-backups --catalog-type <catalog_type>

    # User Case 6: List orphan backup files, snapshots and objects.
    ocifsbackup_cleanup.py --action list-orphan

    # User Case 7: Cleanup all orphan backup files, snapshots and objects list in case 6.
    ocifsbackup_cleanup.py --action cleanup-orphan
    --debug_log         - Optional Use this oprion to enable logging as debug mode

"""


def parse_opts():
    try:
        """ Parse program options """
        parser = OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('--action', action='store', dest='action', choices=globalvariables.ACTION_SUPPORTED,
                          help='Specify action to do.')
        parser.add_option('-c', '--config-file', action='store', dest='oci_config_path',
                          default=globalvariables.MT_CONFIG_PATH_DEFAULT, type='string', help='Path of oci config file.')
        parser.add_option('-f', '--fs-config-file', action='store', dest='fs_config_path', type='string',
                          help='Path of file system backup config file. If not set, will generate one automatically.')
        parser.add_option('--files-config-file', action='store', dest='files_config_path', type='string',
                          default=FILE_PATTERN_PATH, help='Path of os files backup config file.')
        parser.add_option('-t', '--storage-type', action='store', dest='backup_target', choices=globalvariables.STORAGE_SUPPORTED,
                          help='Storage type of backup target.')
        parser.add_option('--backup-options', action='store', dest='backup_option', default='snapshot',
                          choices=globalvariables.OPTION_SUPPORTED, help='Backup Type.')
        parser.add_option('--prefix', action='store', dest='prefix', default='ocifsbackup', type='string',
                          help='Prefix of the backup name.')
        parser.add_option('-p', '--retention-policy-file', action='store', dest='retention_policy_path', type='string',
                          help='Path of retention policy config file.')
        parser.add_option('--snapshot-tag', action='store', dest='snapshot_tag', type='string',
                          help='Specify the unique tag of snapshot.')
        parser.add_option('--retention-days', action='store', dest='retention_days', default=7, type=int,
                          help='Set the retention days of snapshot created by create-snapshot action.')
        # Add hidden option for cleanup action in case misuse of this config file.
        parser.add_option('--cleanup-policy-file', action='store', dest='cleanup_policy_path', type='string',
                          help=optparse.SUPPRESS_HELP)
        parser.add_option('--backup-status', action='store', dest='backup_status', default='active',
                          choices=globalvariables.BACKUP_STATUS_SUPPORTED, help='List backup with backup-status.')
        parser.add_option('--backup-id', action='store', dest='backup_id', type='string',
                          help='Backup id of one backup.')
        parser.add_option('--catalog-type', action='store', dest='catalog_type', choices=globalvariables.CATALOG_DB_SUPPORTED,
                          default='remote', help='Source of catalog DB used for saving backup metadata.')
        parser.add_option('--exclude-list', action='store', dest='exclude_list', type='string',
                          help='Path of exclude list for restore.')
        parser.add_option('--restore-os-files', action='store', dest='restore_os_files', default=False,
                          help='Path of exclude list for restore.')
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log', default="no",help='Optional - Get logs in debug mode')                

        (opts, args) = parser.parse_args()
        return (opts, args)

    except Exception as e:
        message = "Failed to parse program options!\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

def main():
    try:
        global osssdk
        global log_file
        global inst_meta
        global fsssdk
        atexit.register(commonutils.backup_lock_exit)

        (options, args) = parse_opts()
        # oci_config_path = options.oci_config_path
        action = options.action

        if not action:
            message = "Need to provide action by --action!"
            print(message)
            sys.exit(1)
        
        if options.debug_log == "yes":
            import logging
            # Enable debug logging
            logging.getLogger('oci').setLevel(logging.DEBUG)
            # oci.base_client.is_http_log_enabled(True)
            # logging.basicConfig(filename='/tmp/test.log')
            log_file_path_for_debug = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
            if not os.path.exists(log_file_path_for_debug):
                os.makedirs(log_file_path_for_debug)
            filename_debug = log_file_path_for_debug+"/oci_debug" + \
                "_{0}_{1}.log".format(globalvariables.HOST_NAME,
                                    datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
            logging.basicConfig(filename=filename_debug)

        if not (action == 'list-backups' and options.catalog_type == 'remote'):
            try:
                os.umask(22)
                if not os.path.exists(globalvariables.BACKUP_FILES_PATH):
                    os.makedirs(globalvariables.BACKUP_FILES_PATH)

                if not os.path.exists(globalvariables.BACKUP_FS_PATH):
                    os.makedirs(globalvariables.BACKUP_FS_PATH)

                if not os.path.exists(globalvariables.BACKUP_LOG_PATH):
                    os.makedirs(globalvariables.BACKUP_LOG_PATH)

                if not os.path.exists(globalvariables.RESTORE_FILES_PATH):
                    os.makedirs(globalvariables.RESTORE_FILES_PATH)

                if not os.path.exists(globalvariables.RESTORE_FS_PATH):
                    os.makedirs(globalvariables.RESTORE_FS_PATH)

                if not os.path.exists(globalvariables.RESTORE_OBJ_PATH):
                    os.makedirs(globalvariables.RESTORE_OBJ_PATH)

            except Exception as e:
                message = "Failed to create backup directories!\n{0}{1}".format(sys.exc_info()[1:2],e)
                print(message)
                sys.exit(1)

            # Init logger
            log_file = apscom.init_logger(__file__, log_dir=globalvariables.BACKUP_LOG_PATH)

            ret_val = commonutils.backup_lock_enter()
            if ret_val == globalvariables.BACKUP_FAILED:
                message = "Failed to do {0}!".format(action)
                apscom.error(message)

        #osssdk = apsbkcom.Oci()
        osssdk=ociSDK.ociSDK()
        inst_meta = instance_metadata.ins_metadata()
        fsssdk=fssSDK.fssSDK()

        ret_val = TAKE_ACTION.get(action)(options)
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
