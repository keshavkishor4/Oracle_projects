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
"""
#### imports start here ##############################
import os
import sys
import json
from datetime import date
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import instance_metadata
import globalvariables
try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError

import apscom
import backoff

#### imports end here ################################
class fssSDK(object):
    def __init__(self, cn=None, oss_bucket=None, timeout_secs=10):
        global inst_meta
        try:
            inst_meta = instance_metadata.ins_metadata()
            retry_strategy_via_constructor = oci.retry.RetryStrategyBuilder(
                max_attempts_check=True,
                max_attempts=5,
                total_elapsed_time_check=True,
                total_elapsed_time_seconds=3600,
                retry_max_wait_between_calls_seconds=600,
                retry_base_sleep_time_seconds=30,
                service_error_check=True,
                service_error_retry_on_any_5xx=True,
                service_error_retry_config={
                    400: ['QuotaExceeded', 'LimitExceeded'],
                    429: []
                },
                backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
            ).get_retry_strategy()
            self.retry_strategy = retry_strategy_via_constructor
            # Load up OCI config

        except Exception as e:
            message = "Failed to init ociSDk!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def get_fs_list(self, compart_ocid, disp_name=""):
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            file_storage_client = oci.file_storage.FileStorageClient(config={}, signer=signer, timeout=600,
                                                                          retry_strategy=self.retry_strategy)
            if disp_name:
                file_systems = file_storage_client.list_file_systems(compartment_id=compart_ocid,
                                                                     availability_domain=inst_meta.availability_domain,
                                                                     display_name=disp_name).data
            else:
                file_systems = file_storage_client.list_file_systems(compartment_id=compart_ocid,
                                                                     availability_domain=inst_meta.availability_domain).data
            return file_systems
        except ServiceError as e:
            message = "Failed to get file system list!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def list_fs_snapshots(self, filesystem_ocid, limit=None):
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            file_storage_client = oci.file_storage.FileStorageClient(config={}, signer=signer, timeout=600,
                                                                          retry_strategy=self.retry_strategy)
            fs_snapshots = file_storage_client.list_snapshots(file_system_id=filesystem_ocid, limit=limit,
                                                              sort_order="ASC").data
            return fs_snapshots

        except ServiceError as e:
            message = "Failed to list snapshots of the file system!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def create_fs_snapshot(self, snapshot_name, fs_ocid):
        """ Create snapshot of file system.
        Args:
            snapshot_name (str): Snapshot name to be created.
            fs_ocid (str): OCID of the file system.
        Returns:
            out (str): The info of snapshot created.
        """
        try:
            # Do sanity check before create and delete the snapshot with the same name.
            snapshot_list = self.list_fs_snapshots(fs_ocid)
            for snapshot in snapshot_list:
                fs_snapshot_name = snapshot.name
                if fs_snapshot_name == snapshot_name:
                    snapshot_ocid = snapshot.id
                    self.delete_fs_snapshot(snapshot_ocid)
                    break
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            file_storage_client = oci.file_storage.FileStorageClient(config={}, signer=signer, timeout=600,
                                                                          retry_strategy=self.retry_strategy)

            # Snapshot created one by one only on one vm for each component.
            create_snapshot_details = oci.file_storage.models.CreateSnapshotDetails(file_system_id=fs_ocid,
                                                                                    name=snapshot_name)
            fs_snapshot = file_storage_client.create_snapshot(create_snapshot_details=create_snapshot_details).data

            return fs_snapshot

        except ServiceError as e:
            message = "Failed to create snapshot of the file system!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def list_fs_snapshot(self, snapshot_ocid):
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            file_storage_client = oci.file_storage.FileStorageClient(config={}, signer=signer, timeout=600,
                                                                     retry_strategy=self.retry_strategy)
            fs_snapshot = file_storage_client.get_snapshot(snapshot_id=snapshot_ocid).data
            return fs_snapshot
        except ServiceError as e:
                message = "Failed to list snapshot!\n{0}{1}".format(sys.exc_info()[1:2],e)
                apscom.warn(message)
                raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def delete_fs_snapshot(self, snapshot_ocid):
        """ Delete the snapshot with snapshot_ocid.
        Args:
            snapshot_ocid (str): OCID of the snapshot to be deleted.
        Returns:
            deleted (bool): Set to True if snapshot_ocid is deleted or not exist.
        """
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            file_storage_client = oci.file_storage.FileStorageClient(config={}, signer=signer, timeout=600,
                                                                     retry_strategy=self.retry_strategy)
            resp = file_storage_client.delete_snapshot(snapshot_id=snapshot_ocid)

            if resp.status == 204:
                "Status: 204 - The snapshot is being deleted."
                return True
            else:
                return False

        except ServiceError as e:
                message = "Failed to delete snapshot!\n{0}{1}".format(sys.exc_info()[1:2],e)
                apscom.warn(message)
                # raise
    def fill_fs_config_list_shares(self,fs_config_list):
        try:
            f = None
            component_type = inst_meta.component_type
            system_type = inst_meta.system_type

            # Update nfs_share to each mount point.
            f = open(globalvariables.MONUT_TAB, "r")
            for mount_point in fs_config_list["backup_component"][component_type]["backup_dir"].keys():
                f.seek(0)
                for line in f:
                    if line.split()[1] == mount_point:
                        nfs_share = line.split()[0]
                        fs_config_list["backup_component"][component_type]["backup_dir"][mount_point][
                            "nfs_share"] = nfs_share
                        break
            return fs_config_list

        except Exception as e:
            message = "Failed to fill nfs shares information to config list!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

        finally:
            if f:
                f.close()

    def fill_fs_config_list_this(self,fs_config_list):
        try:
            component_type = inst_meta.component_type
            this = False

            if component_type in globalvariables.FA_COMPONENT_LIST:
                this = self.get_backup_host_fa()
            elif component_type in globalvariables.IDM_COMPONENT_LIST:
                this = self.get_backup_host_idm()
            elif component_type in globalvariables.OHS_COMPONENT_LIST:
                this = self.get_backup_host_ohs()
            else:
                message = "Unknown component type {0}!".format(component_type)
                apscom.warn(message)
                raise

            for mount_point in fs_config_list["backup_component"][component_type]["backup_dir"].keys():
                fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["this"] = this

                # The POD level sharing file system will be backup in FA component with ADMIN role.
                mount_info = fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]
                if ("ALL" in mount_info["sharing_type"]) and (component_type not in globalvariables.FA_COMPONENT_LIST):
                    fs_config_list["backup_component"][component_type]["backup_dir"][mount_point]["this"] = False

            return fs_config_list

        except Exception as e:
            message = "Failed to fill backup host information to config list!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    def get_backup_host_fa(self):
        """ Get the backup host of FA component.
            For FA, only do backup from FA component with role "ADMIN".
        Args:
        Returns:
            this (bool): If True, will do backup form this host.
        """
        try:
            this = False

            vm_list = inst_meta.inst_metadata["metadata"]["serviceVM"]
            for vm_num in vm_list.keys():
                vm = vm_list[vm_num]
                if "this" in vm.keys() and vm["this"] and vm["role"] == "ADMIN":
                    return True

            return this

        except Exception as e:
            message = "Failed to get backup host of FA component!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    def get_backup_host_idm(self):
        """ Get the backup host of IDM component.
            For IDM, only do backup from IDM hosts having the minimum vm number.
        Args:
        Returns:
            this (bool): If True, will do backup form this host.
        """
        try:
            this = False
            vm_num_list = []

            # Get vm num of all IDM components.
            vm_list = inst_meta.inst_metadata["metadata"]["serviceVM"]
            for vm_num in vm_list.keys():
                if vm_list[vm_num]["component"] in globalvariables.IDM_COMPONENT_LIST:
                    vm_num_list.append(int(vm_num))

            vm_num_min = min(vm_num_list)
            backup_vm = vm_list[str(vm_num_min)]
            if "this" in backup_vm.keys() and backup_vm["this"]:
                return True

            return this

        except Exception as e:
            message = "Failed to get backup host of IDM component!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    def get_backup_host_ohs(self):
        """ Get the backup host of OHS component.
            For OHS, only do backup from OHS hosts having the minimum vm number.
        Args:

        Returns:
            this (bool): If True, will do backup form this host.
        """
        try:
            this = False
            vm_num_list = []

            # Get vm num of all OHS components.
            vm_list = inst_meta.inst_metadata["metadata"]["serviceVM"]
            for vm_num in vm_list.keys():
                if vm_list[vm_num]["component"] in globalvariables.OHS_COMPONENT_LIST:
                    vm_num_list.append(int(vm_num))

            vm_num_min = min(vm_num_list)
            backup_vm = vm_list[str(vm_num_min)]
            if "this" in backup_vm.keys() and backup_vm["this"]:
                return True

            return this

        except Exception as e:
            message = "Failed to get backup host of OHS component!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise


    def get_older_snapshots(self, fs_config_path, retention_days):
        """ List older snapshots to delete.
            Args:
                fs_config_path (str): fs_config_path
                retention_days (str): retention days to delete
        """
        try:
            component_type = inst_meta.component_type
            f = open(fs_config_path, 'r')
            fs_config_list = json.load(f)
            f.close()
            block_enabled = inst_meta.block_enabled
            backup_dirs = fs_config_list["backup_component"][component_type]["backup_dir"]
            if block_enabled == "true":
                mount_point = "/u04"
                if os.path.exists(mount_point + "/.snapshot"):
                    message = "Clearing snapshots... {0}".format(mount_point)
                    apscom.info(message)
                    filesystem_ocid = backup_dirs[mount_point]["id"]
                    self.delete_older_snapshots(filesystem_ocid, retention_days)
            else:
                for mount_point in backup_dirs.keys():
                    if os.path.exists(mount_point + "/.snapshot"):
                        message = "Clearing snapshots... {0}".format(mount_point)
                        apscom.info(message)
                        filesystem_ocid = backup_dirs[mount_point]["id"]
                        self.delete_older_snapshots(filesystem_ocid,retention_days)
        except Exception as e:
            message = "Failed to get older snapshot details\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
    def delete_older_snapshots(self, filesystem_ocid, retention_days):
        """ List and delete older snapshots.
           Args:
               filesystem_ocid (str): fs_config_path
               retention_days (str): retention days to delete
        """
        try:
            delete_older_snap = False
            current_time = date.today()
            snapshot_list = self.list_fs_snapshots(filesystem_ocid,10)
            for snapshot in snapshot_list:
                created_time = snapshot.time_created
                snapshot_ocid = snapshot.id
                snapshot_name = snapshot.name
                snapshot_date = date(created_time.year, created_time.month, created_time.day)
                current_date = date(current_time.year, current_time.month, current_time.day)
                delta = current_date - snapshot_date
                if("DO_NOT_DELETE" not in snapshot_name):
                    if (delta.days > retention_days):
                        #print("printing older than ", delta.days, snapshot.name)
                        delete_older_snap = True
                        self.delete_fs_snapshot(snapshot_ocid)
                        message = "Successfully deleted {0} ...".format(snapshot_name)
                        apscom.info(message)
            if (delete_older_snap):
                self.delete_older_snapshots(filesystem_ocid, retention_days)
        except Exception as e:
            message = "Failed to delete older snapshots\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
