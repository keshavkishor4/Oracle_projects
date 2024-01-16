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

import multiprocessing
from email import message
import os
import socket
import sys
import json
from datetime import datetime, timedelta
import glob
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import apscom
import commonutils
import backoff
import globalvariables
import instance_metadata

try:
    import oci
    from oci.exceptions import *
    from oci.object_storage.transfer.constants import MEBIBYTE
    from oci.object_storage import UploadManager
    from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
    from urllib.error import HTTPError as ServiceError

#### imports end here ################################


class ociSDK(object):
    def __init__(self, oci_config_path=None):
        """_summary_

        Args:
            oci_config_path (str, optional): Path of oci configuration file. Defaults to None.
        """
        global inst_meta
        try:
            commonutils.cert_check()
            inst_meta = instance_metadata.ins_metadata()
            if oci_config_path:
                self.object_storage_config = commonutils.get_object_storage_config(
                    oci_config_path)
            else:
                self.object_storage_config = None

            if os.path.exists(globalvariables.RETRY_INFO):
                with open(globalvariables.RETRY_INFO, 'r') as f:
                    data = json.load(f)
                    retry_value = data["oci_oss_total_retries"]

            retry_strategy_via_constructor = oci.retry.RetryStrategyBuilder(
                max_attempts_check=True,
                max_attempts=retry_value,
                total_elapsed_time_check=True,
                total_elapsed_time_seconds=3600,
                retry_max_wait_between_calls_seconds=60,
                retry_base_sleep_time_seconds=30,
                retry_exponential_growth_factor=2,
                service_error_check=True,
                service_error_retry_on_any_5xx=True,
                service_error_retry_config={
                    400: ['QuotaExceeded', 'LimitExceeded'],
                    429: [],
                    503: []
                },
                backoff_type=oci.retry.BACKOFF_FULL_JITTER_EQUAL_ON_THROTTLE_VALUE
            ).get_retry_strategy()
            self.retry_strategy = retry_strategy_via_constructor
            # Load up OCI config
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                config={}, signer=signer, timeout=30, retry_strategy=self.retry_strategy)
            self.oss_namespace = object_storage.get_namespace().data

        except Exception as e:
            message = "Failed to init ociSDk!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise
        
    #Return true false as per exception status code condition define here to give up retry in backoff decorator.
    def fatal_code(e):
        return 404 == e.status

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def upload_backups_to_oss(self, backup_name):
        """ Upload backups file to oss bucket
        Args:
            backup_name (str): Name of the backup file which needs to upload into oss.
        Raises:
            Exception: upload_backups_to_oss error
        """
        bc_ocid, bc_bn = commonutils.load_oci_config()
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600,
                                                                retry_strategy=self.retry_strategy)
        oss_namespace = object_storage.get_namespace().data
        upload_manager = UploadManager(object_storage, allow_parallel_uploads=True, parallel_process_count=3,
                                       retry_strategy=self.retry_strategy)
        # 2MB upload
        part_size = 2 * MEBIBYTE
        object_name = backup_name.split("/")[-1]
        filename = backup_name
        try:
            response = upload_manager.upload_file(oss_namespace, bc_bn, object_name, filename, part_size=part_size,
                                                  progress_callback=self.progress_callback)
        except Exception as e:
            message = "Error: upload manager failed with {0}{1}".format(sys.exc_info()[
                                                                        1:2], e)
            apscom.warn(message)
            raise

    def progress_callback(self, bytes_uploaded):
        message = "{} additional bytes uploaded".format(bytes_uploaded)
        apscom.info(message)

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def list_objects(self, oss_bucket, obj_name_prefix=None, oss_namespace=None):
        """ List objects in the bucket
        Args:
            oss_namespace (str): object namespace
            oss_bucket (str): object bucket
        Returns:
            objects (list): list of objects
        Raises:
            Exception: list_objects error
        """
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)

            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            if obj_name_prefix:
                objects = object_storage.list_objects(oss_namespace, oss_bucket, retry_strategy=self.retry_strategy, prefix=obj_name_prefix,
                                                      fields="name,timeCreated").data.objects
            else:
                objects = object_storage.list_objects(
                    oss_namespace, oss_bucket, retry_strategy=self.retry_strategy, fields="name,timeCreated").data.objects

            return objects

        except ServiceError as e:
            message = "Failed to list objects!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    def list_object_passwdjson(self, oss_bucket, oss_namespace=None):
        try:

            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            data1 = object_storage.list_objects(
                oss_namespace, oss_bucket, prefix=".passwd.json", fields="name,timeCreated,size").data.objects
            j_data = json.loads(str(data1))
            sort_d = json.dumps(j_data, sort_keys=True)
            j_d = json.loads(sort_d)
            # print(data1)
            return sort_d
        except Exception as e:
            message = "File {0} not found. {1}".format(".passwd.json", e)
            apscom.warn(message)

    def upload_file_passwdjson(self, File_path, File_name, oss_bucket, oss_namespace=None):
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            with open(File_path, 'rb') as f:
                obj = object_storage.put_object(
                    oss_namespace, oss_bucket, File_name, f)
                if obj:
                    message = "File  {0} uploaded successfully".format(
                        File_name)
                    apscom.info(message)
        except Exception as e:
            message = "Password json file is not uploaded successfully on bucket {0}. {1}".format(
                oss_bucket, e)
            apscom.warn(message)

    def delete_object_OSS_passwdjson(self, File_name, oss_bucket, oss_namespace=None):
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            obj = object_storage.delete_object(
                oss_namespace, oss_bucket, File_name)
            if obj:
                message = "File name {0} deleted".format(File_name)
                apscom.warn(message)
        except Exception as e:
            message = "FIle {0} is not deleted successfully. {1}".format(
                File_name, e)
            apscom.warn(message)

    def get_object_lock_passwdjson(self, File_name, oss_bucket, oss_namespace=None):
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            status = object_storage.get_object(
                oss_namespace, oss_bucket, File_name)
            return status
        except oci.exceptions.ServiceError as e:
            #print("Status is :- ",e.status)
            if e.status == 304:
                # Object exists but has not been modified (based on the etag value)
                return e.status
                pass
            else:
                message = "Failed to get object!\n{0}{1}".format(
                    sys.exc_info()[1:2], e)
                apscom.warn(message)
                return e.status

    def download_file_passwdjson(self, oss_bucket, oss_namespace=None):
        try:
            oci_wallet_config = globalvariables.DB_CONFIG_PATH_DEFAULT
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                with open(oci_wallet_config, 'r') as oci_config_file:
                    oci_config = json.load(oci_config_file)
                oss_namespace = oci_config["oss_namespace"]
            filenames = ".passwd.json"
            retrieve_files_loc = "/tmp"
            get_obj = object_storage.get_object(
                oss_namespace, oss_bucket, filenames)
            with open(retrieve_files_loc+'/'+filenames, 'wb') as f:
                for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
                    f.write(chunk)
                message = "File  name {0} downloaded successfully".format(
                    filenames)
                apscom.info(message)
        except Exception as e:
            message = "File name {0} not downloaded successfully. {1}".format(
                filenames, e)
            apscom.warn(message)

    def update_passwdjson(self, password_file_path, password_file_name, oss_bucket):
        try:
            self.list_object_passwdjson(oss_bucket)
            self.download_file_passwdjson(oss_bucket)
            self.delete_object_OSS_passwdjson(password_file_name, oss_bucket)
            self.upload_file_passwdjson(
                password_file_path, password_file_name, oss_bucket)
            self.list_object_passwdjson(oss_bucket)
        except Exception as e:
            message = "Password file did not uploaded properly. {0}".format(e)
            apscom.warn(message)

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def get_object(self, oss_bucket, oss_object_name, restore_path=None, oss_namespace=None):
        """ Get body of an object and metadata
        Args:
            oss_object_name (str): object name
            restore_path (str): (default=None) file path to be written
        Returns:
            obj: object content or None if restore_path
        Raises:
            Exception: get_object error
        """
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            obj = object_storage.get_object(
                oss_namespace, oss_bucket, oss_object_name, retry_strategy=self.retry_strategy).data

            # streaming it into file in 1 MB chunks
            if restore_path:
                with open(restore_path, 'wb') as f:
                    for chunk in obj.raw.stream(1024 * 1024, decode_content=False):
                        f.write(chunk)
                f.close()
                return None
            else:
                return obj.content

        except ServiceError as e:
            message = "Failed to get object!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100,giveup=fatal_code)
    def delete_object(self, oss_bucket, oss_object_name, oss_namespace=None):
        """ Delete the object.
        Args:
            oss_object_name (str): object name to be deleted.
        Returns:
            deleted (bool): Set to True if object is deleted or not exist.
        """
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            resp = object_storage.delete_object(
                oss_namespace, oss_bucket, oss_object_name, retry_strategy=self.retry_strategy)

            " Status: 204 - The object was successfully deleted. "
            if resp.status == 204:
                return True
            else:
                return False

        except ServiceError as e:
            message = "Failed to delete object!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def check_object_exist(self, oss_bucket, object_name, oss_namespace=None):
        """Check for a particular object exists or not in oss

        Args:
            oss_bucket (str): Name of oss bucket
            object_name (str): Name of object
            oss_namespace (str, optional): Namespace. Defaults to None.

        Returns:
            Boolean: Response of object
        """
        try:
            if not self.object_storage_config:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
            else:
                config = self.object_storage_config
                object_storage = oci.object_storage.ObjectStorageClient(config)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            try:
                resp = object_storage.head_object(
                    oss_namespace, oss_bucket, object_name, retry_strategy=self.retry_strategy)
            except Exception as e:
                return False

            if resp.status == 200:
                return True
            else:
                return False
        except Exception as e:
            message = "Failed to get object head!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            return False

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def list_oss_backups(self, backuptype,component_type=None, tag=None):
        """ List backup objects in the bucket
           Returns:
               objects (list): list of backup objects from oss
           Raises:progress_callback
               Exception: list_objects error
           """
        try:
            bkp_object_list = []
            splitlist = '-'.join(globalvariables.LOCAL_HOST.split('-')
                                 [:2]), '-'.join(globalvariables.LOCAL_HOST.split('-')[2:])
            podname = str(list(splitlist)[0])
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                {}, signer=signer, retry_strategy=self.retry_strategy)
            nameSpace = object_storage.get_namespace().data
            backup_config_files = glob.glob(
                globalvariables.BACKUP_CONFIG_PATH + "*.json")
            bucketname = inst_meta.default_bucket
            if component_type == "OHS":
                prefixes = ["ohs_backup","ohs_os_backup"]
            else:
                prefixes = ["bv_backup","bv_os_backup"]
            if not tag:
               tag = "_ocifsbackup_v2_60_"
            for prefix in prefixes:
                fix = str(prefix) + str(tag) + podname
                print("Fix : ",fix)
                List_objects = object_storage.list_objects(namespace_name=nameSpace, bucket_name=bucketname, prefix=fix, retry_strategy=self.retry_strategy).data
                bkp_objects = List_objects.objects
                for obj in bkp_objects:
                    if podname in obj.name:
                       bkp_object_list.append(obj.name)            
            # for file in backup_config_files:
            #     with open(file, 'r') as f:
            #         backup_list = json.load(f)
            #         f.close()
            #         for (k, v) in backup_list.items():
            #             if tag:
            #                 prefix = k + "_" + tag
            #             else:
            #                 prefix = k + "_" + podname
            #             List_objects = object_storage.list_objects(
            #                 namespace_name=nameSpace, bucket_name=bucketname, prefix=prefix, retry_strategy=self.retry_strategy).data
            #             bkp_objects = List_objects.objects
            #             for obj in bkp_objects:
            #                 if podname in obj.name:
            #                     bkp_object_list.append(obj.name)
            return bkp_object_list
        except Exception as e:
            message = "Failed to List the objects..{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    # filter the object data based on retention policy
    def list_ret_obj(self, obj_list, backup_type):
        """ List objects in the bucket based on retention policy
           Args:
               obj_list: list of backup objects from oss
               backup_type (str): backup type
           Returns:
               objects (list): list of objects from oss to cleanup
           Raises:
               Exception: list_objects error
           """
        try:
            obj_list_new = list(obj_list)
            f = open(globalvariables.RETENTION_POLICY_PATH_DEFAULT, 'r')
            retention_policy = json.load(f)
            f.close()
            retention_days = retention_policy[backup_type]
            dateList = []
            for x in range(0, retention_days):
                date1 = datetime.now() - timedelta(days=x)
                strdate = date1.strftime('%Y-%m-%d')
                dateList.append(strdate)
            for obj in obj_list:
                for cdate in dateList:
                    if cdate in obj:
                        obj_list_new.remove(obj)
            return obj_list_new
        except Exception as e:
            message = "Failed to do {0}{1}!".format(sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    # delete the object based on retention policy
    def delete_obj(self, backup_target):
        """ delete the object based on retention policy
               Args:
                   backup_target (str): backup target type
               Raises:
                   Exception: list_objects error
               """
        try:
            backup_type = 'backup_to_' + backup_target
            if (backup_target == "oss"):
                self.delete_from_oss("", backup_type)
            else:
                print("")  # add logic to delete in local
        except Exception as e:
            message = "Failed to delete the objects{0}".format(e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def delete_from_oss(self, prefix, backup_type):
        """ delete the object based on retention policy
           Args:
               prefix (str): prefix of object
           Raises:
               Exception: list_objects error
           """
        try:
            dateList = []
            bkp_objects_new = []
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                {}, signer=signer, retry_strategy=self.retry_strategy)
            bucketname = inst_meta.default_bucket
            oss_namespace = object_storage.get_namespace().data
            f = open(globalvariables.RETENTION_POLICY_PATH_DEFAULT, 'r')
            retention_policy = json.load(f)
            f.close()
            retention_days = retention_policy[backup_type]
            for x in range(0, retention_days):
                date1 = datetime.now() - timedelta(days=x)
                strdate = date1.strftime('%Y-%m-%d')
                dateList.append(strdate)
            List_objects = object_storage.list_objects(namespace_name=oss_namespace, bucket_name=bucketname,
                                                       prefix=prefix, retry_strategy=self.retry_strategy,
                                                       limit=300).data
            bkp_objects = List_objects.objects
            bkp_objects_new = list(bkp_objects)
            for obj in bkp_objects:
                for cdate in dateList:
                    if cdate in obj.name:
                        bkp_objects_new.remove(obj)
            if(len(bkp_objects_new) > 0):
                for objname in bkp_objects_new:
                    object_storage.delete_object(
                        namespace_name=oss_namespace, bucket_name=bucketname, object_name=objname.name, retry_strategy=self.retry_strategy)
                    message = "Deleting {0}!".format(objname.name)
                    apscom.info(message)
                self.delete_from_oss(prefix, backup_type)
        except Exception as e:
            message = "Failed to delete the objects from oss{0}{1}".format(sys.exc_info()[
                                                                           1:2], e)
            apscom.warn(message)

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def put_object(self, file_path, oss_namespace, oss_bucket, oss_object_name, overwrite=True):
        """ Create a new object or overwrites an existing one
        Args:
            file_path (str): Path of file to upload
            oss_namespace (str): Namespace of object storage
            oss_bucket (str): Bucket name of object storage
            oss_object_name (str): Object name
            overwrite (bool): (default=True) overwrite if True
        Returns:
            bool: True if succeeded
        Raises:
            Exception: put_object error
        """
        try:
            object_created = False
            if not apscom.file_exists(file_path):
                raise ValueError(
                    "Upload file {0} is not found!".format(file_path))
            else:
                with open(file_path, 'rb') as f:
                    if not self.object_storage_config:
                        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                        object_storage = oci.object_storage.ObjectStorageClient(
                            config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
                    else:
                        config = self.object_storage_config
                        object_storage = oci.object_storage.ObjectStorageClient(
                            config)
                    if overwrite:
                        resp = object_storage.put_object(
                            oss_namespace, oss_bucket, oss_object_name, f, retry_strategy=self.retry_strategy)
                    else:
                        resp = object_storage.put_object(
                            oss_namespace, oss_bucket, oss_object_name, f, timeout=600, retry_strategy=self.retry_strategy, if_none_match='*')

                    " Status: 200 - The object was successfully created. "

                    if resp.status == 200:
                        object_created = True
                f.close()

            return object_created
        except ServiceError as e:
            message = "Failed to put {0} to object storage!\n{1}{2}".format(
                file_path, sys.exc_info()[1:2], e)
            apscom.warn(message)
            # raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def put_object_multipart(self, file_path, oss_bucket, oss_object_name, overwrite=True, oss_namespace=None):
        """Upload large objects into multipart

        Args:
            file_path (str): Name of object in local
            oss_bucket (str): Name of oss bucket
            oss_object_name (str): Name of object in oss
            overwrite (bool, optional): _description_. Defaults to True.
            oss_namespace (str, optional): Namespace. Defaults to None.

        Returns:
            _type_: _description_
        """
        try:
            upload_id = None
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600,
                                                                    retry_strategy=self.retry_strategy)
            if not oss_namespace:
                oss_namespace = object_storage.get_namespace().data
            # Split files to multiparts.
            split_file_list = commonutils.split_files(
                file_path, oss_object_name)

            # Initiate an upload
            upload_id = self.create_multipart_upload_id(
                oss_namespace, oss_bucket, oss_object_name, overwrite)

            # Upload object parts
            ret_val = []
            part_list = enumerate(split_file_list)

            p = multiprocessing.Pool(multiprocessing.cpu_count())
            for part_num, part in part_list:
                ret_val.append(p.apply_async(self.upload_part, (part, oss_namespace,
                               oss_bucket, oss_object_name, upload_id, part_num + 1,)))
            p.close()
            p.join()

            for ret in ret_val:
                result = ret.get()
                if not result:
                    message = "Failed to upload object! Aborting this upload ..."
                    apscom.warn(message)

                    object_storage.abort_multipart_upload(
                        oss_namespace, oss_bucket, oss_object_name, upload_id)

                    for split_file in split_file_list:
                        if os.path.isfile(split_file):
                            os.remove(split_file)

                    return False

            # Commit the upload
            self.commit_multipart_upload(
                oss_namespace, oss_bucket, oss_object_name, upload_id)

            # Cleanup the Split files.
            for split_file in split_file_list:
                if os.path.isfile(split_file):
                    os.remove(split_file)

            return True

        except ServiceError as e:

            message = "Failed to put object by multipart upload! Aborting this upload ...\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            if upload_id:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage_clinet = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
                object_storage_clinet.abort_multipart_upload(
                    oss_namespace, oss_bucket, oss_object_name, upload_id)

            for split_file in split_file_list:
                if os.path.isfile(split_file):
                    os.remove(split_file)

            raise

        except Exception as e:
            message = "Failed to put object by multipart upload! Aborting this upload ...\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
            if upload_id:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage_clinet = oci.object_storage.ObjectStorageClient(
                    config={}, signer=signer, timeout=600, retry_strategy=self.retry_strategy)
                object_storage_clinet.abort_multipart_upload(
                    oss_namespace, oss_bucket, oss_object_name, upload_id)

            for split_file in split_file_list:
                if os.path.isfile(split_file):
                    os.remove(split_file)

            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def commit_multipart_upload(self, oss_namespace, oss_bucket, oss_object_name, upload_id):
        """_summary_

        Args:
            oss_namespace (str): _description_
            oss_bucket (str): _description_
            oss_object_name (str): _description_
            upload_id (str): _description_
        """
        try:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage_clinet = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600,
                                                                           retry_strategy=self.retry_strategy)
            commit_parts = object_storage_clinet.list_multipart_upload_parts(oss_namespace, oss_bucket, oss_object_name,
                                                                             upload_id).data

            commit_multipart_details_list = []
            for commit_part in commit_parts:
                part_num = commit_part.part_number
                etag = commit_part.etag
                commit_multipart_details = oci.object_storage.models.CommitMultipartUploadPartDetails(part_num=part_num,
                                                                                                      etag=etag)
                commit_multipart_details_list.append(commit_multipart_details)

            commit_multipart_upload_details = oci.object_storage.models.CommitMultipartUploadDetails(
                parts_to_commit=commit_multipart_details_list)
            object_storage_clinet.commit_multipart_upload(oss_namespace, oss_bucket, oss_object_name, upload_id,
                                                          commit_multipart_upload_details)

        except ServiceError as e:
            message = "Failed to commit multipart upload!\n{0}{1}".format(sys.exc_info()[
                                                                          1:2], e)
            apscom.warn(message)
            raise

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def upload_part(self, file_part, oss_namespace, oss_bucket, oss_object_name, upload_id, part_num):
        try:
            with open(file_part, 'rb') as f:
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                object_storage_clinet = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=3600,
                                                                               retry_strategy=self.retry_strategy)
                object_storage_clinet.upload_part(
                    oss_namespace, oss_bucket, oss_object_name, upload_id, part_num, f)

                return True
        except ServiceError as e:
            message = "Failed to upload part!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)

            return False
        finally:
            if f:
                f.close()

    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def create_multipart_upload_id(self, oss_namespace, oss_bucket, oss_object_name, overwrite=True):
        """Create upload id for each part of object which gets uploaded to OSS

        Args:
            oss_namespace (str): Name of namespace
            oss_bucket (str): Name of bucket
            oss_object_name (str): Name of object
            overwrite (bool, optional): . Defaults to True.

        Returns:
            upload_id: _description_
        """
        try:
            multipart_details = oci.object_storage.models.CreateMultipartUploadDetails(
                object=oss_object_name)

            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage_clinet = oci.object_storage.ObjectStorageClient(
                config={}, signer=signer, timeout=600)
            if overwrite:
                create_resp = object_storage_clinet.create_multipart_upload(oss_namespace, oss_bucket,
                                                                            multipart_details, retry_strategy=self.retry_strategy)
            else:
                create_resp = object_storage_clinet.create_multipart_upload(oss_namespace, oss_bucket,
                                                                            multipart_details, retry_strategy=self.retry_strategy, if_none_match='*')

            upload_id = create_resp.data.upload_id

            return upload_id

        except ServiceError as e:
            message = "Failed to create multipart upload!\n{0}{1}".format(sys.exc_info()[
                                                                          1:2], e)
            apscom.warn(message)
            raise

    # fix for 31130133 ENABLE FEATURE TO DOWNLOAD DB_WALLET FROM OSS
    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def download_wallet_backup(self, walletname, download_dir, oci_wallet_config,oss_bucket):
        """ download the object from  bucket
        Args:
            walletname (str): object name
            download_dir (str): download directory location
            oci_wallet_config(str):config file to authenticate
        Raises:
            Exception: download_objects error
        """
        try:
            try:
                with open(oci_wallet_config, 'r') as oci_config_file:
                    oci_config = json.load(oci_config_file)
                oss_namespace = oci_config["oss_namespace"]
            except Exception as e:
                message = "Failed to load config file {0}!{1} ... {2}".format(
                    walletname, sys.exc_info()[1:2], e)
                apscom.warn(message)
                raise
            try:
                config = commonutils.get_object_storage_config(
                    oci_wallet_config)
                object_storage = oci.object_storage.ObjectStorageClient(config)
                obj = object_storage.get_object(oss_namespace, oss_bucket, walletname,
                                                retry_strategy=self.retry_strategy).data
            except Exception as e:
                message = "Failed to download {0}!{1}.... {2}".format(
                    walletname, sys.exc_info()[1:2], e)
                apscom.warn(message)
                raise
            # streaming it into file in 1 MB chunks
            commonutils.validateJSON(obj)
            oci_config_file.close()
            if download_dir:
                restore_path = download_dir + "/" + walletname
                with open(restore_path, 'wb') as f:
                    for chunk in obj.raw.stream(1024 * 1024, decode_content=False):
                        f.write(chunk)
                f.close()
                return None
            else:
                return obj.content
        except Exception as e:
            message = "Failed to download file {0}{1}.... {2}...".format(
                walletname, sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise
    
    @backoff.on_exception(backoff.expo, ServiceError, max_tries=100)
    def download_mt_backup(self, mtname, download_dir):
        """ download the object from  bucket
        Args:
            walletname (str): object name
            download_dir (str): download directory location
            oci_wallet_config(str):config file to authenticate
        Raises:
            Exception: download_objects error
        """
        try:
            bkp_object_list = []
            splitlist = '-'.join(globalvariables.LOCAL_HOST.split('-')
                                    [:2]), '-'.join(globalvariables.LOCAL_HOST.split('-')[2:])
            podname = str(list(splitlist)[0])
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(
                {}, signer=signer, retry_strategy=self.retry_strategy)
            nameSpace = object_storage.get_namespace().data
            backup_config_files = glob.glob(
                globalvariables.BACKUP_CONFIG_PATH + "*.json")
            bucketname = inst_meta.default_bucket
            obj = object_storage.get_object(nameSpace, bucketname, mtname,
                                                retry_strategy=self.retry_strategy).data

            # streaming it into file in 1 MB chunks
            commonutils.validateJSON(obj)
            if download_dir:
                restore_path = download_dir + "/" + mtname
                with open(restore_path, 'wb') as f:
                    for chunk in obj.raw.stream(1024 * 1024, decode_content=False):
                        f.write(chunk)
                f.close()
                return None
            else:
                return obj.content
        except Exception as e:
            message = "Failed to download file {0}{1}.... {2}...".format(
                mtname, sys.exc_info()[1:2], e)
            apscom.warn(message)
            raise

    def list_wallet_backup(self, dbname, prefix, oci_wallet_config, retention_days):
        """List wallet objects from 

        Args:
            dbname (_type_): _description_
            prefix (_type_): _description_
            oci_wallet_config (_type_): _description_

        Returns:
            bkp_object_list: List of files which is older than 60 days
            comp_bkp_object_list: Complete list of files excluded bkp_object_list
        """
        bkp_object_list = []
        wallet_list = []
        dateList = []
        comp_bkp_object_list = []
        try:
            prefix = prefix + '_' + dbname
            oci_config_file = open(oci_wallet_config, 'r')
            oci_config = json.load(oci_config_file)
            oci_config_file.close()
            oss_namespace = oci_config["oss_namespace"]
            oss_bucket = commonutils.get_bucket_details(dbname,oss_namespace)
            config = self.object_storage_config
            object_storage = oci.object_storage.ObjectStorageClient(config)
            List_objects = object_storage.list_objects(namespace_name=oss_namespace, bucket_name=oss_bucket,
                                                       prefix=prefix, retry_strategy=self.retry_strategy).data
            for obj in List_objects.objects:
                wallet_list.append(obj.name)
            for x in range(0, retention_days):
                date1 = datetime.now() - timedelta(days=x)
                strdate = date1.strftime('%Y-%m-%d')
                dateList.append(strdate)
            for obj in wallet_list:
                if dbname not in "all":
                    if (dbname in obj):
                        comp_bkp_object_list.append(obj)
                        for d in dateList:
                            if d in obj:
                                bkp_object_list.append(obj)
                else:
                    comp_bkp_object_list.append(obj)
                    for d in dateList:
                        if d in obj:
                            bkp_object_list.append(obj)
            return bkp_object_list, comp_bkp_object_list, oss_bucket

        except Exception as e:
            message = "Error occurred while listing{0}{1} ".format(sys.exc_info()[
                                                                   1:2], e)
            apscom.error(message)

    def get_oci_metrics(self, oci_wallet_config):
        # cd /opt/faops/spe/ocifabackup/lib/python/common
        # import ociSDK
        # oci_sdk=ociSDK.ociSDK('/opt/faops/spe/ocifabackup/config/wallet/config-oci.json')
        # oci_sdk.get_oci_metrics('/opt/faops/spe/ocifabackup/config/wallet/config-oci.json')
        try:
            # fetch compartment
            comp_name = ""
            comp_id = ""
            env_types = ['dev', 'ppd', 'prd']
            fqdn_split = socket.getfqdn().split('.')
            #
            FA_ENV = commonutils.get_region_env()
            comp_name = "{0}_fa_lcm_network".format(FA_ENV)
            oci_config_file = open(oci_wallet_config, 'r')
            oci_config = json.load(oci_config_file)
            oci_config_file.close()
            compartment_id = oci_config["tenancy_ocid"]
            config = self.object_storage_config
            identity_client = oci.identity.IdentityClient(
                config, retry_strategy=self.retry_strategy)
            getCompartments = identity_client.list_compartments(
                compartment_id).data
            for compartment in getCompartments:
                if compartment.name == comp_name:
                    comp_id = compartment.id
            #
            # comp_id="ocid1.compartment.oc1..aaaaaaaaswaecutmhfgkhdqvescmvguqpnngw3mysxb5jzag4nse5wq3phrq"
            sgw_query_pfs = "packetsFromService[1m].sum()"
            sgw_query_pts = "packetsToService[1m].sum()"
            #
            sgw_query_pdfs = 'sgwDropsFromService[1m].sum()'
            sgw_query_pdts = "sgwDropsToService[1m].sum()"
            ns = "oci_service_gateway"
            config = self.object_storage_config
            object_storage = oci.object_storage.ObjectStorageClient(config)
            mon_client = oci.monitoring.MonitoringClient(config)
            # Packets to-fro
            sum_data_res_pfs = mon_client.summarize_metrics_data(
                compartment_id=comp_id, summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(namespace=ns, query=sgw_query_pfs))
            sum_data_res_pfs_data = sum_data_res_pfs.data[0].aggregated_datapoints
            #
            sum_data_res_pts = mon_client.summarize_metrics_data(
                compartment_id=comp_id, summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(namespace=ns, query=sgw_query_pts))
            sum_data_res_pts_data = sum_data_res_pts.data[0].aggregated_datapoints
            # Drops
            sum_data_res_pdfs = mon_client.summarize_metrics_data(
                compartment_id=comp_id, summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(namespace=ns, query=sgw_query_pdfs))
            sum_data_res_pdfs_data = sum_data_res_pdfs.data[0].aggregated_datapoints
            #
            sum_data_res_pdts = mon_client.summarize_metrics_data(
                compartment_id=comp_id, summarize_metrics_data_details=oci.monitoring.models.SummarizeMetricsDataDetails(namespace=ns, query=sgw_query_pdts))
            sum_data_res_pdts_data = sum_data_res_pdts.data[0].aggregated_datapoints
            #
            # packets to-fro sgw
            pfs_data = []
            pts_data = []
            #

            # capture metric for last 5 minutes, metric sample 1m.
            for val in sum_data_res_pfs_data:
                #ts = datetime.strptime(val.timestamp, '%Y-%m-%d %H+%M+%S')
                tz_info = val.timestamp.tzinfo
                now = datetime.now(tz_info)
                diff = now - val.timestamp
                if diff.total_seconds() < 300:
                    # print(str(diff)+"--"+str(val.value))
                    pfs_data.append(val.value)
            #
            for val in sum_data_res_pts_data:
                #ts = datetime.strptime(val.timestamp, '%Y-%m-%d %H+%M+%S')
                tz_info = val.timestamp.tzinfo
                now = datetime.now(tz_info)
                diff = now - val.timestamp
                if diff.total_seconds() < 300:
                    # print(str(diff)+"--"+str(val.value))
                    pts_data.append(val.value)
            pts_total_usage_mpps = (int(max(pts_data)) * 60/1000000)
            pfs_total_usage_mpps = (int(max(pfs_data)) * 60/1000000)
            sum_total_usage_per_seconds = (
                pts_total_usage_mpps+pfs_total_usage_mpps)
            apscom.info(
                "Max Total mmps to SGW in last 5 minutes - {0}".format(pts_total_usage_mpps))
            apscom.info(
                "Max Total mmps from SGW n last 5 minutes- {0}".format(pfs_total_usage_mpps))
            apscom.info(
                "Total to-n-fro Usage {0}".format(sum_total_usage_per_seconds))
            # Capture packet drops and sum
            pdfs_data = []
            pdts_data = []
            # capture metric for last 5 minutes, metric sample 1m.
            for val in sum_data_res_pdfs_data:
                #ts = datetime.strptime(val.timestamp, '%Y-%m-%d %H+%M+%S')
                tz_info = val.timestamp.tzinfo
                now = datetime.now(tz_info)
                diff = now - val.timestamp
                if diff.total_seconds() < 300:
                    # print(str(diff)+"--"+str(val.value))
                    pdfs_data.append(val.value)
            #
            for val in sum_data_res_pdts_data:
                #ts = datetime.strptime(val.timestamp, '%Y-%m-%d %H+%M+%S')
                tz_info = val.timestamp.tzinfo
                now = datetime.now(tz_info)
                diff = now - val.timestamp
                if diff.total_seconds() < 300:
                    # print(str(diff)+"--"+str(val.value))
                    pdts_data.append(val.value)
            pdts_total_usage_mpps = (int(max(pdts_data)) * 60/1000000)
            pdfs_total_usage_mpps = (int(max(pdfs_data)) * 60/1000000)
            sum_total_drops_usage_per_seconds = (
                pdts_total_usage_mpps+pdfs_total_usage_mpps)
            # Calculate ratio drops to sum of usage -- %
            apscom.info(
                "Max Total Drops mmps to SGW in last 5 minutes - {0}".format(pdts_total_usage_mpps))
            apscom.info(
                "Max Total Drops mmps to SGW in last 5 minutes - {0}".format(pdts_total_usage_mpps))
            apscom.info(
                "Max Total Drops mmps from SGW in last 5 minutes - {0}".format(pdfs_total_usage_mpps))
            apscom.info(
                "Total Drops to-n-fro Usage  {0}".format(sum_total_drops_usage_per_seconds))
            apscom.info("Ratio Total Drops to Total Packets Sen/Received: {0}".format(
                sum_total_drops_usage_per_seconds/sum_total_usage_per_seconds))
        except Exception as e:
            message = "Error in running get_oci_metric, check policies are in place{0}{1} ".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)

    # change the logic to pick up locally and run only once
    def get_tenancy_info(self, oci_wallet_config):
        try:
            oci_data = {}
            OCI_SDK_META_FILE = globalvariables.OCI_SDK_META_FILE
            LOCAL_HOST = socket.getfqdn()
            HOST_NAME = LOCAL_HOST.split(".")[0]
            OCI_TENANCY_META_FILE = "{0}/config/{1}_tenancy_md.json".format(
                BASE_DIR, HOST_NAME)
            OCI_TENANCY_OSS_META_FILE = "{0}/config/{1}_tenancy_oss_md.json".format(
                BASE_DIR, HOST_NAME)
            OCI_SDK_META_FILE = globalvariables.OCI_SDK_META_FILE
            if os.path.exists(OCI_SDK_META_FILE):
                status = commonutils.is_file_older_than(
                    OCI_SDK_META_FILE, timedelta(seconds=86400))
                if status:
                    apscom.info("refreshing {0}".format(OCI_SDK_META_FILE))
                    with open(oci_wallet_config, 'r') as f:
                        oci_config = json.load(f)
                        compartment_id = oci_config["tenancy_ocid"]
                        tenancy_ocid = oci_config["tenancy_ocid"]
                    config = self.object_storage_config
                    # tenancy name
                    identity_client = oci.identity.IdentityClient(
                        config, retry_strategy=self.retry_strategy)
                    getTenancyData = identity_client.get_tenancy(
                        tenancy_ocid).data

                    #
                    # oss namespace
                    oss_client = oci.object_storage.ObjectStorageClient(
                        config, retry_strategy=self.retry_strategy)
                    ns = oss_client.get_namespace().data
                    #
                    oci_data["tenancy_name"] = getTenancyData.name
                    oci_data["ns"] = ns
                    #

                    # create md file
                    try:
                        with open(OCI_SDK_META_FILE, 'w') as f:
                            json.dump(
                                oci_data, f, ensure_ascii=False, indent=4)
                    except Exception as e:
                        message = "failed to generate tenancy oss metadata from file {2} \n{0}{1}".format(
                            sys.exc_info()[1:2], e, OCI_SDK_META_FILE)
                        apscom.warn(message)

            else:
                apscom.info("creating sdk meta file {0}".format(
                    OCI_SDK_META_FILE))
                with open(oci_wallet_config, 'r') as f:
                    oci_config = json.load(f)
                    compartment_id = oci_config["tenancy_ocid"]
                    tenancy_ocid = oci_config["tenancy_ocid"]
                config = self.object_storage_config
                # tenancy name
                identity_client = oci.identity.IdentityClient(
                    config, retry_strategy=self.retry_strategy)
                getTenancyData = identity_client.get_tenancy(tenancy_ocid).data

                #
                # oss namespace
                oss_client = oci.object_storage.ObjectStorageClient(
                    config, retry_strategy=self.retry_strategy)
                ns = oss_client.get_namespace().data
                #
                oci_data["tenancy_name"] = getTenancyData.name
                oci_data["ns"] = ns
                #

                # create md file
                try:
                    with open(OCI_SDK_META_FILE, 'w') as f:
                        json.dump(oci_data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    message = "failed to generate tenancy oss metadata from file {2} \n{0}{1}".format(
                        sys.exc_info()[1:2], e, OCI_SDK_META_FILE)
                    apscom.warn(message)

            # # out = json.dumps(oci_data)
            # # print(oci_data)
            # if os.path.exists(OCI_SDK_META_FILE):
            #     status = status=commonutils.is_file_older_than(OCI_SDK_META_FILE,timedelta(seconds=86400))
            #     if status:
            #         with open(oci_wallet_config, 'r') as f:
            #             oci_config = json.load(f)
            #             compartment_id = oci_config["tenancy_ocid"]
            #             tenancy_ocid = oci_config["tenancy_ocid"]
            #         config=self.object_storage_config
            #         # tenancy name
            #         identity_client = oci.identity.IdentityClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            #         getTenancyInfo = identity_client.get_tenancy(tenancy_ocid).data
            #         oci_data["tenancy_name"]=getTenancyInfo.name
            #         # oss namespace
            #         oss_client = oci.object_storage.ObjectStorageClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            #         ns = oss_client.get_namespace().data
            #         oci_data["ns"]=ns
            #         with open(OCI_SDK_META_FILE,'w+') as f:
            #             data = json.dumps(oci_data)
            #             json.dump(json.loads(data), f, ensure_ascii=False, indent=4)
            # else:
            #     with open(oci_wallet_config, 'r') as f:
            #         oci_config = json.load(f)
            #         compartment_id = oci_config["tenancy_ocid"]
            #         tenancy_ocid = oci_config["tenancy_ocid"]
            #     config=self.object_storage_config
            #     # tenancy name
            #     identity_client = oci.identity.IdentityClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            #     getTenancyInfo = identity_client.get_tenancy(tenancy_ocid).data
            #     oci_data["tenancy_name"]=getTenancyInfo.name
            #     # oss namespace
            #     oss_client = oci.object_storage.ObjectStorageClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
            #     ns = oss_client.get_namespace().data
            #     oci_data["ns"]=ns
            #     with open(OCI_SDK_META_FILE,'w+') as f:
            #         data = json.dumps(oci_data)
            #         json.dump(json.loads(data), f, ensure_ascii=False, indent=4)

        except Exception as e:
            message = "Error in running get_tenancy_info, check policies are in place{0}{1} ".format(
                sys.exc_info()[1:2], e)
            apscom.warn(message)
