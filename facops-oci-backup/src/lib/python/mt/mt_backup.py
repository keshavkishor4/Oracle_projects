#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      ociSDK.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
    Vipin Azad            12/04/22 - fa_release_check added as part of Jira - FSRE-57
    Vipin Azad            02/01/23 - fill_fs_config_list_metadata changed and removed the dependency on block_enabled instance metadata - FUSIONSRE-580
"""
#### imports start here ##############################
import os
import sys
import json
import tarfile
from time import gmtime, strftime

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python")
import glob
from common import apscom,fssSDK,instance_metadata,globalvariables,commonutils
try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError
#### imports end here ################################
fsssdk = fssSDK.fssSDK()
inst_meta = instance_metadata.ins_metadata()
# Looks into mt/config/backup_config dir for backups to perform
def backup_files_v2(tag=None,retention_days=0):
   # Check if include files present and in right format
   try:
      full_backup_names = []
      backup_include_files = glob.glob(globalvariables.BACKUP_CONFIG_PATH + "/*.json")
      
      for file in backup_include_files:
         if fa_release_check() :
            if "bv_backup.json" in file:
               backup_include_files.remove(file)
         else:
            if "non_fs_backup.json" in file:
                backup_include_files.remove(file)
      
      message = ("{0}".format(backup_include_files))
      apscom.info(message)
      for file in backup_include_files:
         try:
            with open(file, 'r') as f:
               backup_list = json.load(f)
               for backup_key in backup_list.keys():
                  backup_list_loc = backup_list[backup_key]
                  if not backup_list_loc:
                     message = "Warn: {0} value is empty, skipping backup for {0}".format(backup_list_loc)
                     apscom.warn(message)
                     continue
                  startname=''
                  if tag:
                     startname=tag
                  if retention_days>0:
                     if startname:
                        startname=startname+'_'+str(retention_days)
                     else:
                        startname=str(retention_days)
                  if startname:
                     adhoc_backup_name = '{0}/{1}_{2}_{3}_{4}.tgz'.format(globalvariables.BACKUP_FILES_PATH_V2,backup_key,startname,
                                                                      globalvariables.LOCAL_HOST, strftime(
                           "%Y-%m-%d.%H%M%S"))
                  else:
                      adhoc_backup_name='{0}/{1}_{2}_{3}.tgz'.format(globalvariables.BACKUP_FILES_PATH_V2,backup_key,globalvariables.LOCAL_HOST,strftime(
                     "%Y-%m-%d.%H%M%S"))

                 # adhoc_backup_name = globalvariables.BACKUP_FILES_PATH_V2 + "/" + backup_key + "_" + globalvariables.LOCAL_HOST + "." + strftime(
                  #   "%Y-%m-%d.%H%M%S") + ".tgz"
                  with tarfile.open(adhoc_backup_name, "w:gz") as tar:
                     # Perform adhoc backups
                     for name in backup_list_loc:
                        # check if file or directory exists
                        if os.path.exists(name):
                           message = "Backing up file {0} ...".format(name)
                           apscom.info(message)
                           tar.add(name)
                        else:
                           message = "file or directory {0} does not exist , skipping...".format(name)
                           apscom.warn(message)
                           pass
                     message = "Successfully created {0} backup file".format(adhoc_backup_name)
                     apscom.info(message)
                     full_backup_names.append(adhoc_backup_name)
                     apscom.info(message)
            f.close()

         except Exception as e:
            message = "Failed to backup files in {0}!\n{1}{2}".format(globalvariables.BACKUP_CONFIG_PATH,
                                                                   sys.exc_info()[1:2],e)
            apscom.warn(message)
            # return full_backup_names so ocifsbackup.py line 125 catches the exception
            raise
      message=("{0}".format(full_backup_names))
      apscom.info(message)
      return full_backup_names
   except Exception as e:
      message = "Error: No backup include files present or format not correct {0}".format(e)
      apscom.warn(message)
      # return full_backup_names so ocifsbackup.py line 125 catches the exception
      raise

def ohs_backup_files_v2(tag=None,retention_days=0):
   # Check if include files present and in right format
   try:
      full_backup_names = []
      backup_include_files = glob.glob(globalvariables.OHS_BACKUP_CONFIG_PATH + "/*.json")
      for file in backup_include_files:
         try:
            with open(file, 'r') as f:
               # print(file)
               backup_list = json.load(f)
               for backup_key in backup_list.keys():
                  if "ohs_backup" in backup_key:
                     if "ohs1" in globalvariables.LOCAL_HOST:
                        backup_list_loc = backup_list[backup_key]["OHS"]
                     else:
                        backup_list_loc = backup_list[backup_key]["OHS-HA"]
                  else:
                     backup_list_loc = backup_list[backup_key]
                  # print("Backup list loc is:-",backup_list_loc)
                  if not backup_list_loc:
                     message = "Warn: {0} value is empty, skipping backup for {0}".format(backup_list_loc)
                     apscom.warn(message)
                     continue
                  startname=''
                  if tag:
                     startname=tag
                  if retention_days>0:
                     if startname:
                        startname=startname+'_'+str(retention_days)
                     else:
                        startname=str(retention_days)
                  if startname:
                     adhoc_backup_name = '{0}/{1}_{2}_{3}_{4}.tgz'.format(globalvariables.BACKUP_FILES_PATH_V2,backup_key,startname,
                                                                      globalvariables.LOCAL_HOST, strftime(
                           "%Y-%m-%d.%H%M%S"))
                  else:
                     adhoc_backup_name='{0}/{1}_{2}_{3}.tgz'.format(globalvariables.BACKUP_FILES_PATH_V2,backup_key,globalvariables.LOCAL_HOST,strftime(
                     "%Y-%m-%d.%H%M%S"))
                  with tarfile.open(adhoc_backup_name, "w:gz") as tar:
                     # Perform adhoc backups
                     for name in backup_list_loc:
                        # check if file or directory exists
                        if os.path.exists(name):
                           message = "Backing up file {0} ...".format(name)
                           apscom.info(message)
                           tar.add(name)
                        else:
                           message = "file or directory {0} does not exist , skipping...".format(name)
                           apscom.warn(message)
                           pass
                     message = "Successfully created {0} backup file".format(adhoc_backup_name)
                     full_backup_names.append(adhoc_backup_name)
                     apscom.info(message)
            f.close()

         except Exception as e:
            message = "Failed to backup files in {0}!\n{1}{2}".format(globalvariables.BACKUP_CONFIG_PATH,
                                                                   sys.exc_info()[1:2],e)
            apscom.warn(message)
            # return full_backup_names so ocifsbackup.py line 125 catches the exception
            raise
      return full_backup_names
   except Exception as e:
      message = "Error: No backup include files present or format not correct {0}".format(e)
      apscom.warn(message)
      # return full_backup_names so ocifsbackup.py line 125 catches the exception
      raise

#cat /u01/APPLTOP/instance/lcm/metadata/pod.properties
#podSize=XS0,GRC=1,VCP=1,ES=0,BIP=1
#maintenance_level=11.13.22.10.0_12.0.00
#stamp_prev=XS0,VCP=1,BIP=1,GRC=1,ES=0

#Below function added as part of Jira - FSRE-57
def fa_release_check():
    with open (globalvariables.POD_REL_INFO,'r') as file:
        lines=file.readlines()
    rel_list=[line.split('=')[1].split('.') for line in lines if line.split('=')[0]== "maintenance_level"][0]
    
    pod_fa_rel = {
        "rel_base_0" : int(rel_list[0]),
        "rel_base_1" : int(rel_list[1]),
        "rel_base_2" : int(rel_list[2]),
        "rel_base_3" : int(rel_list[3])
    }

    pod_req_rel = {
        "rel_base_0" : 11,
        "rel_base_1" : 13,
        "rel_base_2" : 22,
        "rel_base_3" : 1
    }
    flag = 0
    for i in pod_fa_rel:
        if pod_fa_rel.get(i) >= pod_req_rel.get(i):
            pass
        else:
            flag = 1
            
    if flag == 1 :
        return False
    else:
        return True

def bi_backup():
    """To run BI Backup - Bug 33805599

    Raises:
        Exception: backup_script_run Error
    """
    try:
      #  check existin path of script
      script_path=None
      old_path="/u01/APPLTOP/fusionapps/bi/bifoundation/facade/backuprestore/scripts/"
      new_path="/u01/APPLTOP/fmw/otbi/facade/backuprestore/"
      script_file="bi_backup_restore.sh"
      if os.path.exists(new_path+script_file):
         script_path=new_path
      elif os.path.exists(old_path+script_file):
         script_path = old_path
      else:
         script_path=None

      if script_path != None:
         lines = ["#BI Oracle Home", "biprov.bi_home.dir=/u01/APPLTOP/fusionapps/bi"]
         script_path = "/u01/APPLTOP/fusionapps/bi/bifoundation/facade/backuprestore/scripts/bi_backup_restore.sh"
         input_text_path = "/u01/APPLTOP/fusionapps/bi/bifoundation/facade/backuprestore/scripts/"
         if os.path.exists(script_path):
            if os.path.exists(input_text_path):
               cmd = script_path + " " + "BACKUP" + input_text_path
               output = commonutils.execute_shell(cmd)
               apscom.info(output)
            else:
               with open(input_text_path, 'w') as f:
                     for line in lines:
                        f.write(line)
                        f.write('\n')
               cmd = script_path + " " + "BACKUP" + input_text_path
               output = commonutils.execute_shell(cmd)
               print(output)
         else:
            print("bi_backup_restore.sh script is not availabale in desired location")
    except Exception as e:
      message = "Could not run backup_script_run !\n{0}{1}".format(sys.exc_info()[1:2],e)
      apscom.warn(message)
      # raise Exception(message)
 

def create_fs_list(fs_list=globalvariables.FS_LIST_PATH):
   """ Create and update the fs config path
   Args:
       fs_list (str): Path of fs config list
   Returns:
   Raises:
   """
   try:
      fs_config_path = fs_list

      # Load json format from template.
      fs_config_list = json.load(open(globalvariables.FS_LIST_TEMPLATE))

      # Fill nfs shares of the host per mtab.
      fs_config_list = fsssdk.fill_fs_config_list_shares(fs_config_list)

      # Fill if this is the nfs backup host.
      fs_config_list = fsssdk.fill_fs_config_list_this(fs_config_list)

      # Fill metadata of each file system.
      fs_config_list = fill_fs_config_list_metadata(fs_config_list)

      f = open(fs_config_path, 'w')
      json.dump(fs_config_list, f, indent=4, sort_keys=True)
      f.close()

      return fs_config_path

   except Exception as e:
      message = "Failed to create file system list {0}!\n{1}{2}".format(fs_config_path, sys.exc_info()[1:2], e)
      apscom.warn(message)
      raise

def fill_fs_config_list_metadata(fs_config_list):
   try:
      component_type = inst_meta.component_type
      fs_compart_ocid = inst_meta.app_compart_ocid
      fa_service_name = inst_meta.fa_service_name
      fs_list = []
      mount_point="/u04"
      nfs_share = fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["nfs_share"]
      if nfs_share and (len(nfs_share.split(":"))>1):
         export_path = nfs_share.split(":")[1]
         display_name = "FS:{0}:{1}".format(fa_service_name, export_path)

         fs_list = fsssdk.get_fs_list(fs_compart_ocid, display_name)
         if len(fs_list) != 1:
            message = "Too many file systems found for {0}!".format(display_name)
            apscom.warn(message)
            raise

         fs = fs_list[0]
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
            "availabilityDomain"] = fs.availability_domain
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
            "compartmentId"] = fs.compartment_id
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
            "displayName"] = fs.display_name
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["id"] = fs.id
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
            "lifecycleState"] = fs.lifecycle_state
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
            "meteredBytes"] = fs.metered_bytes
         fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["timeCreated"] = str(
            fs.time_created)
      else:
         if fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["this"] :
               fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["this"] = False
               message = "File system {0} configed in backup list is not active or not mounted in current VM, will not backup it!".format(
                  mount_point)
               apscom.warn(message)

      return fs_config_list

   except Exception as e:
      message = "Failed to fill metadata of file system to config list!\n{0}{1}".format(sys.exc_info()[1:2], e)
      apscom.warn(message)
      raise


def create_fs_snapshots(fs_config_path, prefix):
   """ Create snapshots for configured file systems.
       Args:
           fs_config_path (str): Path of backup file systems list.
           prefix (str): Prefix of snapshot name or orbject name if to oss.
       Returns:
           snapshot_list (list): List of snapshot info
   """
   try:
      snapshot_list = []

      component_type = inst_meta.component_type

      if not os.path.isfile(fs_config_path):
         message = "Not a valid configuration file!"
         apscom.warn(message)
         return
      f = open(fs_config_path, 'r')
      fs_config_list = json.load(f)
      # Create snapshot if "this" is true.
      backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
      for mount_point in backup_dirs.keys():
         if backup_dirs[mount_point]["this"]:
            snapshot_info = {}
            if (len(backup_dirs[mount_point]["nfs_share"].split(":"))>1):
               fs_name = backup_dirs[mount_point]["nfs_share"].split(":")[1].rsplit("/", 1)[1]
               fs_ocid = backup_dirs[mount_point]["id"]
               snapshot_name = prefix + "_" + "snapshot" + "_" + fs_name + "." + strftime("%Y-%m-%d.%H%M%S",
                                                                                          gmtime())
               # print snapshot_name, fs_ocid

               # Create snapshot for each file system
               message = "Creating snapshot {0} ...".format(snapshot_name)
               apscom.info(message)

               fs_snapshot = fsssdk.create_fs_snapshot(snapshot_name, fs_ocid)
               snapshot_info["fileSystemId"] = fs_snapshot.file_system_id
               snapshot_info["id"] = fs_snapshot.id
               snapshot_info["name"] = fs_snapshot.name
               snapshot_info["mount_point"] = mount_point
               snapshot_list.append(snapshot_info)
      f.close()
      return snapshot_list

   except Exception as e:
      snapshot_ocid = []
      for snapshot in snapshot_list:
         snapshot_ocid.append(snapshot["id"])
      cleanup_snapshots(snapshot_ocid)

      message = "Failed to create snapshot of file systems!\n{0}{1}".format(sys.exc_info()[1:2], e)
      apscom.warn(message)
      raise



def cleanup_snapshots(snapshot_list):
   """ Cleanup snapshots in snapshot list
   Args:
       snapshot_list (list): List of snapshot ocid
   Returns:
   Raises:
   """
   try:
      ret_val = globalvariables.BACKUP_SUCCESS
      for snapshot_ocid in snapshot_list:
         snapshot_info = fsssdk.list_fs_snapshot(snapshot_ocid)
         if snapshot_info and snapshot_info.lifecycle_state == "ACTIVE":
            if "DO_NOT_DELETE" not in snapshot_info.name:
               deleted = fsssdk.delete_fs_snapshot(snapshot_ocid)
               if deleted:
                  message = "Succeed to delete snapshot {0}.".format(snapshot_info.name)
                  apscom.info(message)
               else:
                  if not check_snapshot_deleted(snapshot_ocid):
                     ret_val = globalvariables.BACKUP_FAILED
                     message = "Failed to delete snapshot {0}!".format(snapshot_info.name)
                     apscom.warn(message)

      return ret_val

   except Exception as e:
      message = "Failed to cleanup snapshots!\n{0}{1}".format(sys.exc_info()[1:2], e)
      apscom.warn(message)
      raise


def check_snapshot_deleted(snapshot_ocid):
    try:
        snapshot_info = fsssdk.list_fs_snapshot(snapshot_ocid)

        if (not snapshot_info) \
                or (snapshot_info.lifecycle_state == "DELETING") \
                or (snapshot_info.lifecycle_state == "DELETED"):

            message = "Snapshot {0} is already deleted.".format(snapshot_info.name)
            apscom.info(message)

            return True
        else:
            message = "Snapshot {0} not deleted.".format(snapshot_info.name)
            apscom.info(message)

            return False

    except Exception as e:
        message = "Failed to check if snapshot {0} is already deleted!\n{1}{2}".format(snapshot_ocid, sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

