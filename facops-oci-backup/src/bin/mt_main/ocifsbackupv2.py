#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    NAME
      ocifsbackupv2.py

    DESCRIPTION
      moving to ocifsbackupv2 for BV requirement
      to backup files only part of include list

    NOTES

    MODIFIED        (MM/DD/YY)
    Zakki Ahmed        01/20/20 - Initial version


"""

from __future__ import absolute_import, print_function

__version__ = "2.0.0.0.200120"

import os
import re
import sys
from optparse import OptionParser
import glob
import atexit
# Added for v2
import ssl
import urllib
import urllib.request
import urllib.parse
import json
from datetime import datetime
import tarfile
# For PROD deployment
from subprocess import Popen, PIPE
from time import strftime, gmtime

BASE_DIR = os.path.abspath(__file__ + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import ociSDK, commonutils, post_backup_metadata
from mt import mt_backup
from common import instance_metadata, apscom, globalvariables, fssSDK

# For Development only
# BASE_DIR = os.path.abspath(os.getcwd() + "/../")
# sys.path.append(BASE_DIR + "/lib/python")

# Move CB funcitons and etc to different folders
#
# Only for PROD -- required for restores
if not os.path.isfile("/usr/bin/parcp"):
    print("[ERROR] The dependent package fss-parallel-tools is not installed!")
    sys.exit(1)
else:
    CP_TOOL = "/usr/bin/parcp"

################Global Variables#################
#
# Use uniq name for each vm in case conflicts between vms of the same component.
log_file = ""

# Take Actions tasks
inst_metadata = instance_metadata.ins_metadata().post_inst_metadata
component_type = instance_metadata.ins_metadata().component_type
def take_action_backup(options):
    """ Action of Backup
    Args:
         options: Program options
    Returns:
    Raises:
    """
    try:
        inst_metadata = instance_metadata.ins_metadata().post_inst_metadata
        component_type = instance_metadata.ins_metadata().component_type
        global fs_config_path
        fs_config_path = options.fs_config_path
        backup_list = []
        retention_policy = {}
        backup_file_path = None
        # files_config_path = options.files_config_path
        backup_target = options.backup_target
        # backup_option = options.backup_option
        prefix = options.prefix
        action = options.action
        tag=options.tag
        retention_days=options.retention_days
        # retention_policy_path = options.retention_policy_path
        catalog_type = "local"
        if not tag:
            tag = "ocifsbackup_v2"

        retention_policy_path = globalvariables.RETENTION_POLICY_PATH_DEFAULT
        if component_type == "OHS":
            if not os.path.exists(globalvariables.BACKUP_FILES_PATH_V2):
                os.makedirs(globalvariables.BACKUP_FILES_PATH_V2)
        def post_exception():
            post_backup_metadata.create_backup_metadata(action, backup_type, backup_list, retention_days, tag,
                                                        catalog_type, "FAILED", log_file)
            sys.exit(1)

        # Do cleanup before backup.
        commonutils.cleanup_dir(globalvariables.BACKUP_FS_PATH_V2)
        commonutils.cleanup_dir(globalvariables.BACKUP_FILES_PATH_V1)
        commonutils.cleanup_dir(globalvariables.BACKUP_FILES_PATH_V2)
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH_V1)
        commonutils.cleanup_dir(globalvariables.RESTORE_FILES_PATH_V2)
        commonutils.cleanup_dir(globalvariables.RESTORE_FS_PATH_V2)
        commonutils.cleanup_dir(globalvariables.RESTORE_OBJ_PATH_V2)
        backup_type = 'backup_to_' + backup_target
        if not retention_days:
            f = open(retention_policy_path, 'r')
            retention_policy = json.load(f)
            f.close()
            # Get retention days per backup type
            retention_days = retention_policy[backup_type]
            snapshot_retention_days = retention_policy['snapshot_to_fss']

        #if component_type == "OHS":
         #   take_action_backup_for_ohs()
        #else:
            

        # Backup files, the backup tarball is saved in /u01 file system.
        # If backup destination is oss and backup type is full, only need to send the file system backup to oss.
        # backup_file_path = backup_files_v2(files_config_path, prefix)

        # Added for BV
        # backup_list = backup_files_v2()
        if not backup_target:
            message = "Backup target not specified"
            apscom.warn(message)
            post_exception()
            return globalvariables.BACKUP_FAILED

        # print backup_target, backup_type, oci_api.oss_namespace, oci_api.mtbk_oss_bucket
        # /u04 backup
        if component_type != "OHS":
            if not fs_config_path:
                fs_config_path = mt_backup.create_fs_list()
            f = open(fs_config_path, 'r')
            fs_config_list = json.load(f)

            # cleanup older snapshots
        # 
        
            fssSDK.fssSDK().get_older_snapshots(fs_config_path, snapshot_retention_days)
            snapshot_info = {}
            snapshot_list = []
            backup_dirs = fs_config_list["backup_component"][inst_meta.component_type]["backup_dir"]
            if backup_dirs["/u04"]["nfs_share"]:
                fs_name = backup_dirs["/u04"]["nfs_share"].split(":")[1].rsplit("/", 1)[1]
                fs_ocid = backup_dirs["/u04"]["id"]
                snapshot_name = prefix + "_" + "snapshot" + "_" + fs_name + "." + strftime("%Y-%m-%d.%H%M%S",
                                                                                        gmtime())
                fs_snapshot = fssSDK.fssSDK().create_fs_snapshot(snapshot_name, fs_ocid)
                snapshot_info["fileSystemId"] = fs_snapshot.file_system_id
                snapshot_info["id"] = fs_snapshot.id
                snapshot_info["name"] = fs_snapshot.name
                snapshot_info["mount_point"] = "/u04"
                snapshot_list.append(snapshot_info)
                message = "Succeed to do {0} snap shot backup.".format(snapshot_name)
                apscom.info(message)
        # 
        if backup_target == "local":
            if component_type == "OHS":
                backup_list = mt_backup.ohs_backup_files_v2(tag,retention_days)
            else:
                backup_list = mt_backup.backup_files_v2(tag,retention_days)
            if component_type != "OHS":
                for snapshot in snapshot_list:
                    backup_list.append(snapshot["id"])

        elif backup_target == "oss":
            # clean up OSS objects 
            # backup_type = 'backup_to_' + backup_target
            splitlist = '-'.join(globalvariables.LOCAL_HOST.split('-')[:2]), '-'.join(globalvariables.LOCAL_HOST.split('-')[2:])
            podname = str(list(splitlist)[0])
            backup_config_files = glob.glob(globalvariables.BACKUP_CONFIG_PATH + "*.json")
            for file in backup_config_files:
                with open(file, 'r') as f:
                    backup_list = json.load(f)
                    f.close()
                    for (k, v) in backup_list.items():
                        prefix = k + "_" + tag + "_" +str(retention_days) + "_"  + podname
                        # ociapi.delete_obj(backup_target)
                        ociapi.delete_from_oss(prefix, backup_type)
            # cleanup for oss backup
            # ociapi.cleanup_oss_objects(backup_type)
            if component_type == "OHS":
                backup_list = mt_backup.ohs_backup_files_v2(tag,retention_days)
            else:
                backup_list = mt_backup.backup_files_v2(tag,retention_days)  # change this to include empty/none if none, throw exception and fail the backup, refer err format, add exception e

            for backup_file in backup_list:
                message = "Uploading file {0} to oss ...".format(backup_file)
                ociapi.upload_backups_to_oss(backup_file)
                apscom.info(message)
            if component_type != "OHS":
                for snapshot in snapshot_list:
                    backup_list.append(snapshot["id"])

        # Create and save backup metadata
        backup_metadata = post_backup_metadata.create_backup_metadata(action, backup_type, backup_list, retention_days,
                                                                    tag, catalog_type, "ACTIVE", log_file)

        message = "Succeed to do {0} backup.".format(backup_type)
        apscom.info(message)

        message = json.dumps(backup_metadata, sort_keys=True, indent=4)
        apscom.info(message)
        f.close()
        # rpmupdates.verify_upgrade_rpm()

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        commonutils.cleanup_dir(globalvariables.BACKUP_FS_PATH_V2)
        post_exception()
        message = "Failed to do backup!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise
    # finally:
    #     rpmupdates.verify_upgrade_rpm()

def take_action_post_metadata(options):
    action = options.action
    inst_metadata = inst_meta.post_inst_metadata
    region = inst_meta.region
    try:
        #
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        # Post Instance Metadata
        params = json.dumps(inst_metadata).encode('utf8')
        # req = urllib.request.Request(inst_metadata_url, data=params, headers={'content-type': 'application/json'})
        # with urllib.request.urlopen(req, context=ctx) as res:
        #     message = "Backup metadata {0}".format(res.read().decode('utf-8'))
        #     print(message)
        #     apscom.info(message)

    except Exception as e:
        msg = "Failed to post instance metadata!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(msg)
        raise


def take_action_list_backups(options):
    action = options.action
    try:
        tag = options.tag
        #
        backup_target = options.backup_target
        if not backup_target:
            message = "Backup target not specified, with fetch for local backups"
            apscom.warn(message)
            backup_target = "local"
        backup_type = 'backup_to_' + backup_target

        if backup_target == "oss":
            backup_list = ociapi.list_oss_backups(backup_type,component_type,tag)
            print("Listing backups:")
            print("========================================")
            for val in backup_list:
                print(val)
        elif backup_target == "local":
            fss_list=os.listdir(globalvariables.BACKUP_FILES_PATH_V2)
            for obj in fss_list:
                print(globalvariables.BACKUP_FILES_PATH_V2 + "/" + obj)
            if component_type != "OHS":
                list_fss_backups()
    except Exception as e:
        message = "Failed to list Backup files {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise



def take_action_download_mt_backups(options):
    action = options.action
    try:
        mtname = options.mt_name
        download_dir = options.download_loc
        backup_target = options.backup_target
        if not backup_target:
            message = "Backup target not specified, with fetch for local backups"
            apscom.warn(message)
            backup_target = "local"
        backup_type = 'backup_to_' + backup_target
        ociapi.download_mt_backup(mtname, download_dir)
        message = "Downloaded {0} to {1}".format(mtname, download_dir)
        apscom.info(message)
    except Exception as e:
        message = "Failed to download file {0} ...{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

def list_fss_backups():
    try:
        fs_config_path = mt_backup.create_fs_list()
        f = open(fs_config_path, 'r')
        fs_config_list = json.load(f)
        component_type = inst_meta.component_type
        backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
        snapshot_list = []
        for mount_point in backup_dirs.keys():
            if backup_dirs[mount_point]["this"]:
                fs_ocid = backup_dirs[mount_point]["id"]
                if fs_ocid:
                    snapshot_list = fssSDK.fssSDK().list_fs_snapshots(fs_ocid)
                    print("\n listing snapshot .......\n")
                    for obj in snapshot_list:
                        print(json.loads(str(obj))["name"])
        return snapshot_list
    except Exception as e:
        message = "Failed to list backup history!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)


def get_snapshot_info(snapshot_list):
    try:
        snapshot_info_list = {}
        snapshot_pattern = ".*snapshot_(?P<fs_name>\S+).\d{4}-[0-1][0-9]-[0-3][0-9].[0-2][0-9][0-6][0-9][0-6][0-9]_\+\d{4}"
        component_type = inst_meta.component_type
        fs_config_path = mt_backup.create_fs_list()
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
        message = "Failed to get snapshot information from snapshot list!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


def restore_backup_to_fss(snapshot):
    try:
        ret_val = globalvariables.BACKUP_SUCCESS
        snapshot_list = []
        snapshot_list.append(snapshot)
        message = "Restoring from backup to fss ..."
        apscom.info(message)
        snapshot_info_list = get_snapshot_info(snapshot_list)
        print(snapshot_info_list)
        # Restore snapshot
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

                    cmd = [CP_TOOL, "--delete", "--exclude-from={0}".format(globalvariables.RESTORE_EXCLUDE_LIST),
                           snapshot_path, mount_point]
                else:
                    cmd = [CP_TOOL, "--delete", snapshot_path, mount_point]

                process = Popen(cmd, stdout=PIPE)
                (out, err) = process.communicate()
                exit_code = process.wait()

                # Restore the perm of mount point in case it is changed during restore.
                cmd = ["chmod", mount_point_perm, mount_point]
                out = apscom.run_cmd(cmd)

        message = "Succeed to restore from backup to fss."
        apscom.info(message)

        return ret_val

    except Exception:
        message = "Failed to restore from backup to fss!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


RESTORE_PER_BACKUP_TYPE = {
    "snapshot_to_fss": restore_backup_to_fss,
}


def take_action_restore(options):
    try:
        global fs_config_path
        backup_piece = options.backup_name
        target = options.backup_target
        if target == 'oss':
            wiki = 'https://confluence.oci.oraclecorp.com/display/FAOCIBKP/MT+-+FA+on+OCI+Backup+Contents'
            message = "this will take care of restore, not implemented yet..., refer to wiki {0}!".format(wiki)
            apscom.warn(message)
            return globalvariables.BACKUP_FAILED
        if not backup_piece:
            message = "Backup id to be restored not specified by --backup-id!"
            apscom.warn(message)
            return globalvariables.BACKUP_FAILED
        backup_type = "snapshot_to_fss"

        # restore_os_files = options.restore_os_files
        ret_val = RESTORE_PER_BACKUP_TYPE.get(backup_type)(backup_piece)
        if ret_val == globalvariables.BACKUP_SUCCESS:
            message = "Succeed to restore from backup id {0}.".format(backup_piece)
            apscom.info(message)
            return globalvariables.BACKUP_SUCCESS
        else:
            message = "Failed to restore from backup id {0}!".format(backup_piece)
            apscom.warn(message)
            return globalvariables.BACKUP_FAILED

    except Exception:
        message = "Failed to do restore!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise


def take_action_cleanup(options):
    try:
        action = options.action
        backup_target = options.backup_target
        tag = "ocifsbackup_v2"
        backup_type = 'backup_to_' + backup_target
        retention_policy_path=globalvariables.RETENTION_POLICY_PATH_DEFAULT
        with open(retention_policy_path, 'r') as f:
            retention_policy = json.load(f)
            f.close()
            # Get retention days per backup type
            retention_days = retention_policy[backup_type]

        if backup_target == "oss":
            backup_type = 'backup_to_' + backup_target
            splitlist = '-'.join(globalvariables.LOCAL_HOST.split('-')[:2]), '-'.join(globalvariables.LOCAL_HOST.split('-')[2:])
            podname = str(list(splitlist)[0])
            if component_type == "OHS":
                backup_config_files = glob.glob(globalvariables.OHS_BACKUP_CONFIG_PATH + "*.json")
            else:
                backup_config_files = glob.glob(globalvariables.BACKUP_CONFIG_PATH + "*.json")
            for file in backup_config_files:
                with open(file, 'r') as f:
                    backup_list = json.load(f)
                    f.close()
                    for (k, v) in backup_list.items():
                        prefix = k + "_" +tag + "_" +str(retention_days) + "_"  + podname
                        # ociapi.delete_obj(backup_target)
                        ociapi.delete_from_oss(prefix, backup_type)
        elif backup_target == "fss":
            fs_config_path=None
            if not fs_config_path:
                fs_config_path = mt_backup.create_fs_list()
            f = open(fs_config_path, 'r')
            fs_config_list = json.load(f)

            # cleanup older snapshots
            retention_days=7
            fssSDK.fssSDK().get_older_snapshots(fs_config_path, retention_days)
            snapshot_info = {}
            snapshot_list = []
    except Exception as e:
        message = "Failed to do {0} {1}!".format(action,e)
        apscom.warn(message)
        raise


def parse_opts():
    try:
        """ Parse program options """
        parser = OptionParser(version="%prog 1.0")
        parser.add_option('--action', action='store', dest='action', choices=globalvariables.ACTION_SUPPORTED,
                          help='Specify action to do. backup, restore, list-backups, download-mt')
        parser.add_option('-t', '--target', action='store', dest='backup_target',
                          choices=globalvariables.STORAGE_SUPPORTED, help='Storage type of backup target.')
        parser.add_option('-f', '--fs-config-file', action='store', dest='fs_config_path', type='string',
                          help='Path of file system backup config file. If not set, will generate one automatically.')
        parser.add_option('--prefix', action='store', dest='prefix', default='ocifsbackup', type='string',
                          help='Prefix of the backup name.')
        parser.add_option('--backup-name', action='store', dest='backup_name', type='string',
                          help='Backup id of one backup.')
        parser.add_option('--mt-name', action='store', dest='mt_name', type='string',
                          help='MT Name to be downloaded')
        parser.add_option('--download_dir', action='store', dest='download_loc', default='./',
                          help='Specify the directory in which to download mt')
        #fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1035
        parser.add_option('--retention-days', action='store', dest='retention_days', type=int,
                          help='Set the retention days of snapshot created by create-snapshot action.')
        parser.add_option('--tag', action='store', dest='tag', default=None)
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log', default="no",help='Optional - Get logs in debug mode')
        (opts, args) = parser.parse_args()
        return (opts, args)

    except Exception as e:
        message = "Failed to parse program options!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


# Take Actions
TAKE_ACTION = {
    "backup": take_action_backup,
    "restore": take_action_restore,
    "cleanup": take_action_cleanup,
    "download-mt": take_action_download_mt_backups,
    "list-backups": take_action_list_backups,
    "post-metadata": take_action_post_metadata
}


def main():
    try:
        global ociapi
        global log_file
        global inst_meta
        global ret_days
        global tag

        atexit.register(commonutils.backup_lock_exit)

        (options, args) = parse_opts()
        # oci_config_path = options.oci_config_path
        action = options.action
        ret_days=options.retention_days
        tag = options.tag

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

        if not (action == 'list-backups'):
            try:
                os.umask(22)
                if not os.path.exists(globalvariables.BACKUP_FILES_PATH_V2):
                    os.makedirs(globalvariables.BACKUP_FILES_PATH_V2)

                if not os.path.exists(globalvariables.BACKUP_FS_PATH_V2):
                    os.makedirs(globalvariables.BACKUP_FS_PATH_V2)

                if not os.path.exists(globalvariables.BACKUP_LOG_PATH):
                    os.makedirs(globalvariables.BACKUP_LOG_PATH)

                if not os.path.exists(globalvariables.RESTORE_FILES_PATH_V2):
                    os.makedirs(globalvariables.RESTORE_FILES_PATH_V2)

                if not os.path.exists(globalvariables.RESTORE_FS_PATH_V2):
                    os.makedirs(globalvariables.RESTORE_FS_PATH_V2)

                if not os.path.exists(globalvariables.RESTORE_OBJ_PATH_V2):
                    os.makedirs(globalvariables.RESTORE_OBJ_PATH_V2)

            except Exception:
                message = "Failed to create backup directories!\n{0}".format(sys.exc_info()[1:2])
                print(message)
                sys.exit(1)

            # Init logger
            log_file = apscom.init_logger(__file__, log_dir=globalvariables.BACKUP_LOG_PATH)
            ret_val = commonutils.backup_lock_enter()
            if ret_val == globalvariables.BACKUP_FAILED:
                message = "Failed to do {0}!".format(action)
                apscom.error(message)
        # Load up OCI
        ociapi = ociSDK.ociSDK()
        inst_meta = instance_metadata.ins_metadata()
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