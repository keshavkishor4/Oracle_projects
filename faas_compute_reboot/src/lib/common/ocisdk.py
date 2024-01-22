#!/usr/bin/env python3
import json
import multiprocessing
import subprocess
import os
import sys
import requests
import jsonpickle
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/common")
import backoff
import time
import datetime
import commonutils
import globalvariables
from globalvariables import print_info, print_warn, print_error
import re

BASE_PATH=globalvariables.get_project_root()
base_path=BASE_PATH
# print("Base_path:" + str(base_path))
home_dir=os.path.expanduser("~")

# import commonutils

try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError

namespace = "axxyy35wuycx"
bucket_name = "fsremw_dso_resize"


dotenv_path="{0}/creds/.env".format(home_dir)
env_temp="{0}/creds/env_temp".format(home_dir)


class OciSdk():
   def __init__(self,oci_region=None,oci_tenancy=None):
      self.profile = globalvariables.glbl_config_profile
      self.region = "us-phoenix-1"
      self.auth_token = "security_token"
      self.gen_token()
      self.config = oci.config.from_file(profile_name=self.profile)
      self.token_file = self.config['security_token_file']
      self.private_key = oci.signer.load_private_key_from_file(self.config['key_file'])
      # self.signer = oci.auth.signers.SecurityTokenSigner(self.token, self.private_key)
      self.signer = self.get_signer()


      self.client = oci.identity.IdentityClient({'region': self.config['region']}, signer=self.signer)
      result = self.client.list_region_subscriptions(self.config['tenancy'])

   def fetch_tenancy_from_env(self, tenancy):
      with open(dotenv_path, "r") as ifile:
         for line in ifile:
            if line.endswith(tenancy):
               print(next(ifile, '').strip())

   def __get_oci_auth_signer(self, oci_config):
      """Generating the signer from given config file

       Args:
           param1 (str): oci config file path.

       Returns:
           str: The return value. The signer details .
       """
      # key_file_loc = "../creds/{0}".format(oci_config.get('key_file'))
      # key_file_loc = "{0}/creds/{1}".format(base_path, oci_config.get('key_file'))
      key_file_loc = oci_config.get('key_file')
      # if oci_region is None and oci_tenancy is None :
      signer = oci.Signer(tenancy=oci_config.get('tenancy'), user=oci_config.get('user'),
                          fingerprint=oci_config.get('fingerprint'),
                          # private_key_file_location=oci_config.get('key_file'),
                          private_key_file_location=key_file_loc,
                          pass_phrase=oci_config.get('pass_phrase'))

      return signer

   def oci_session_refresh(self):
      time_hour = 72
      for i in range(time_hour):
         cmd = "oci session authenticate --profile-name {0} --region {1} --tenancy-name bmc_operator_access".format(
            self.profile, self.region)
         os.system(cmd)
         time.sleep(120)

   def gen_token(self):
      base_path = os.path.dirname(os.getcwd())
      tokenfile = "{0}/creds/apitoken.txt".format(base_path)
      if os.path.exists(tokenfile):
         with open(tokenfile) as f:
            data = f.readline().split("|")
            value = data[0]
            format = '%Y-%m-%d %H:%M:%S.%f'
            then = datetime.datetime.strptime(value, format)
            now = datetime.datetime.now()
            difference = now - then
            seconds_in_day = 24 * 60 * 60
            total_minutes = divmod(difference.days * seconds_in_day + difference.seconds, 60)[0]
            # print_info("Checking OCI authentication status. Last auth done {0} Minutes before...".format(total_minutes))
            if total_minutes > 45 or data[1] is None:
               with open(tokenfile, "w") as k:
                  result = self.get_token__()
                  k.write("{0}|{1}".format(datetime.datetime.now(), result))
      else:
         with open(tokenfile, "w") as f:
            result = self.get_token__()
            f.write("{0}|{1}".format(datetime.datetime.now(), result))

   def get_token(self):
      self.gen_token()
      # print(self.token_file)
      self.token = None
      with open(self.token_file, 'r') as f:
         self.token = f.read()

      return self.token
   def get_token__(self):
      try:
         print_info("Re-Generating the OCI session authentication, as session authentication not valid...")
         cmd = "oci session authenticate --profile-name {0} --region {1} --tenancy-name bmc_operator_access".format(self.profile,self.region)
         os.system(cmd)
      except Exception as e:
         print_error(e)

   def get_tenancy(self):
      config = self.config
      # print(config.get('tenancy'))
      return config.get('tenancy')

   def get_config(self):
      return self.config

   def get_signer(self):
      return oci.auth.signers.SecurityTokenSigner(self.get_token(), self.private_key)

   def __get_oci_auth_signer_custom(self, oci_config, oci_tenancy):
      """Generating the signer from given config file

       Args:
           param1 (str): oci config file path.

       Returns:
           str: The return value. The signer details .
       """
      key_file_loc = oci_config.get('key_file')
      if (oci_tenancy == "faaasrkadam1") :
         tenancy = os.getenv("oci_oc1_frk1_tenancy_ocid")
      elif (oci_tenancy == "faaasrkadam") :
         tenancy = os.getenv("oci_oc1_frk1_tenancy_ocid")

      signer = oci.Signer(tenancy=tenancy, user=oci_config.get('user'),
                             fingerprint=oci_config.get('fingerprint'),
                             # private_key_file_location=oci_config.get('key_file'),
                             private_key_file_location=key_file_loc,
                             pass_phrase=oci_config.get('pass_phrase'))

      return signer
   def __get_oci_config(self, config_file, profile):
      config = oci.config.from_file(config_file, profile)
      return config

   @backoff.on_exception(backoff.expo, ServiceError, max_tries=2)
   def fetch_details_from_endpoint_url(self, reqtype, endpoint):
      """Execute GET requset and return details in json format

       Args:
           param1 (str): Request Type "GET".
           param2 (str): Endpoint url to execute GET request

       Returns:
           str: The return value. response in json format.
       """
      self.reqtype = reqtype
      self.endpoint = endpoint
      if self.reqtype == "GET":
         try:
            response = requests.get(self.endpoint, auth=self.signer)
            return response.json()
         except Exception as e:
            message = "Exception in OCI request,  {0}".format(e)
            print(message)

   def execute_requests(self, reqtype, body, endpoint, tenancy=None):
      """Execute requset and return response value

       Args:
           param1 (str): Request Type "POST/PUT/DELETE".
           param2 (str): Request body
           param3 (str): Endpoint url to execute GET request

       Returns:
           str: The return value. response in json format.
       """
      try:
         self.reqtype = reqtype
         self.endpoint = endpoint
         print(self.reqtype)
         print(self.endpoint)
         print(body)
         input("Wait")
         if self.reqtype == "DELETE":
            response = requests.delete(self.endpoint, auth=self.signer)
            # return response.json()
         elif self.reqtype == "POST":
            # url = 'https://api.example.com/api/dir/v1/accounts/9999999/orders'
            headers = {'Authorization': self.signer, 'Accept': 'application/json', 'Content-Type': 'application/json'}
            response = requests.post(endpoint, data=open(body, 'rb'), headers=headers)
            # response = requests.post(self.endpoint, json=body, auth=self.signer)
            response.raise_for_status()
         elif self.reqtype == "PUT":
            response = requests.put(self.endpoint, auth=self.signer)
         else:
            message = "Not supported request type in OCI request,  {0}".format(self.reqtype)
            print(message)

         return response.json()
      except Exception as e:
         message = "Exception in OCI request,  {0}".format(e)
         print(message)

   def get_capacity_reservatrion_id(self,instance_id, core_client):
      """Fetch Capacity Reservation ID for a given instance ID

       Args:
           param1 (str): Instance ID .
           param2 (str): oci core compute client info


       Returns:
           str: The return value. Capacity Reservation id of the Instance.
       """
      try:
         insDetails = core_client.get_instance(instance_id).data
         insJSON = jsonpickle.encode(insDetails, unpicklable=False)
         instanceJSONData = json.dumps(insJSON, indent=4)
         InstanceJSON = jsonpickle.decode(instanceJSONData)
         instanceJSON = json.loads(InstanceJSON)
         print(instanceJSON['_capacity_reservation_id'])
         return instanceJSON['_capacity_reservation_id']
      except Exception as e:
         message = "Exception in get_capacity_reservatrion_id, Error to get Capacity Reservation id {0}".format(e)
         print(message)


   def get_capacity_reservation(self, cap_resrv_id=None, instance_id=None, region=None):
      """Fetch Capacity Reservation info for a given instance ID of a region

       Args:
           param1 (str): Capacity reservation ID .
           param2 (str): Instance ID
           param3 (str): region name


       Returns:
           str: The return value. Capacity Reservation info of the Instance.
       """
      if region == None and cap_resrv_id == None:
         core_client = oci.core.ComputeClient(self.config)
         cap_resrv_id = self.get_capacity_reservatrion_id(instance_id,core_client)
         try:
            return core_client.get_compute_capacity_reservation(cap_resrv_id).data
         except Exception as e:
            message = "Exception in ocisdk.get_capacity_reservation. With region " +region + ". Error to get Capacity Reservation details {0}".format(e)
            print(message)
      if cap_resrv_id == None and instance_id == None:
         sys.exit(1)
      if region != None and cap_resrv_id == None:
         self.config['region'] = region
         core_client = oci.core.ComputeClient(self.config)
         cap_resrv_id = self.get_capacity_reservatrion_id(instance_id, core_client)
         try:
            return core_client.get_compute_capacity_reservation(cap_resrv_id).data
         except Exception as e:
            message = "Exception in ocisdk.get_capacity_reservation. With region " +region + ". Error to get Capacity Reservation details {0}".format(
               e)
            print(message)

   def progress_callback(self, bytes_uploaded):
      print("{} additional bytes uploaded".format(bytes_uploaded))
   def upload_file_to_objectstore(self, fileName):
      """Upload a given file to the object store

       Args:
           param1 (str): File name

       Returns:
           None: Upload the file to OSS bucket.
       """
      object_name = fileName.split("/")[-1]
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config,signer=self.signer)
      print_info("uploading {}".format(object_name))

      # upload manager will automatically use mutlipart uploads if the part size is less than the file size
      #=================
      part_size = 2 * MEBIBYTE  # part size (in bytes)
      upload_manager = UploadManager(object_storage, allow_parallel_uploads=True, parallel_process_count=3)
      try:
         response = upload_manager.upload_file(namespace, bucket_name, object_name, fileName, part_size=part_size, progress_callback=self.progress_callback)
      except Exception as e:
         message = "Error: upload manager failed with {0}{1}".format(sys.exc_info()[1:2], e)
         print_warn(message)
         raise
      #==========================
      # To force single part uploads, set "allow_multipart_uploads=False" when creating the UploadManager.
      # upload_manager = UploadManager(object_storage, allow_multipart_uploads=False)
      # response = upload_manager.upload_file(
      #    namespace, bucket_name, object_name, filename, part_size=part_size, progress_callback=progress_callback)

   def download_file_from_objectstore(self, fileName, download_dir):
      """Download a given file from the object store to a given directory

       Args:
           param1 (str): File name
           param2 (str): Target directory name

       Returns:
           None: Download the file from OSS bucket to given directory.
       """
      print_info("{}----{}".format(fileName,download_dir))
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config, signer=self.signer)
      try:
         get_obj = object_storage.get_object(namespace, bucket_name, fileName)
         with open(download_dir + '/' + fileName, 'wb') as f:
            for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
               f.write(chunk)
         print_info(f'downloaded "{fileName}" in "{download_dir}" from bucket "{bucket_name}"')
         subprocess.call(['chmod', '0755', download_dir+"/"+fileName])
         return download_dir+"/"+fileName
      except Exception as e:
         message = "Failed to download {0}!{1}.... {2}".format(fileName, sys.exc_info()[1:2], e)
         print_warn(message)
         raise

   def check_file_in_ossbucket(self,filename,filepath):
      """Fetch file name from oss_bucket for given region and branch

       Args:
           param1 (str): Region name
           param2 (str): Branch Name
           param3 (str): Action Type


       Returns:
           List : List of similar filenames available in oss bucket
       """
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config, signer=self.signer)
      next_starts_with = None
      try:
         response = object_storage.list_objects(namespace, bucket_name, start=next_starts_with, prefix=filename,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
         next_starts_with = response.data.next_start_with
         if(response.data.objects):
            for object_file in response.data.objects:
               print(object_file.name)
               self.download_file_from_objectstore(filename,filepath)
               # oss_filename_list.append(object_file.name)
         else:
            print_info("No files available in OSS with name {0}".format(filename))
         # return oss_filename_list
      except Exception as e:
         message = "Failed to fetch files starts with {0} from oss_bucket {1} with exception {2}!".format(filename,bucket_name,e)
         print_warn(message)
         raise

   def list_oss_fileName(self, file_prefix, resize_branch):
      """Fetch file name from oss_bucket for given region and branch

       Args:
           param1 (str): Region name
           param2 (str): Branch Name
           param3 (str): Action Type


       Returns:
           List : List of similar filenames available in oss bucket
       """
      oss_filename_list = []
      # if(fileType == "json"):
      #    var_oss_file = "{0}_{1}_{2}_{3}".format(globalvariables.glbl_file_prefix,var_region, var_branch, var_action.lower())
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config, signer=self.signer)
      next_starts_with = None
      try:
         response = object_storage.list_objects(namespace, bucket_name, start=next_starts_with, prefix=file_prefix,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
         next_starts_with = response.data.next_start_with
         print_info(resize_branch)
         # input()
         if(response.data.objects):
            for object_file in response.data.objects:
               if resize_branch in object_file.name:
                  print(object_file.name)
                  oss_filename_list.append(object_file.name)
         else:
            print_info("No files available in OSS with name starts with {0}".format(file_prefix))
         return oss_filename_list
      except Exception as e:
         message = "Failed to fetch files starts with {0} from oss_bucket {1} with exception {2}!".format(file_prefix,bucket_name,e)
         print_warn(message)
         raise

   def check_if_file_available_in_bucket(self,csvFile, lockFile):
      """Fetch file name from oss_bucket for given region and branch

       Args:
           param1 (str): Region name
           param2 (str): Branch Name
           param3 (str): Action Type


       Returns:
           List : List of similar filenames available in oss bucket
       """
      # lockFile= fileName+".lck"
      # csvFile = fileName+".csv"
      # print(filePath)
      # print(" lockFile "+ lockFile)
      fileName = csvFile.split(".")[0]
      filePath = globalvariables.cfg_dir
      fileList = []
      status = False
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config, signer=self.signer)
      next_starts_with = None
      try:
         response = object_storage.list_objects(namespace, bucket_name, start=next_starts_with, prefix=fileName,retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
         next_starts_with = response.data.next_start_with
         if(response.data.objects):
            for object_file in response.data.objects:
               print("object_file.name " +object_file.name)
               fileList.append(object_file.name)

            if lockFile in fileList:
               self.download_file_from_objectstore(lockFile, filePath)
               with open(filePath + "/" + lockFile) as f:
                  userName = f.readline().strip()
                  filetime = f.readline().strip()
               print_warn(
                  "A file with {0} file is available in the bucket and user is {2}, meaning {2} using the {1}. Checking the lock file timestamp for more info".format(
                     lockFile, csvFile, userName))

               stat,timediff = commonutils.get_lockfile_timediff(filetime)
               if stat:
                  self.delete_file(filePath + "/" + lockFile)
                  print_info("The lock file is 60 mins old. Unblocking your run!!!")
                  status = True
               else:
                  os.remove(filePath + "/" + lockFile)
                  print_warn("Please wait until the lock file get removed. Or by default try after {0} mins to unblock your run ".format(str(timediff)))
                  exit(1)
            elif((lockFile not in fileList) and (csvFile in fileList)):
               print_info("Config file {0} is already available in the bucket, downloading it ".format(csvFile))
               status = True
            else:
               print_info("Config file {0} not available in bucket, continue to create it".format(csvFile))
               status = False
         else:
            print("No files available in OSS with name starts with {0}".format(fileName))
            status = False
         return status
      except Exception as e:
         message = "Failed to fetch files starts with {0} from oss_bucket {1} with exception {2}!".format(fileName,bucket_name,e)
         print_warn(message)
         raise

   def delete_file(self, configfile):
      """Fetch file name from oss_bucket for given region and branch

       Args:
           param1 (str): Region name
           param2 (str): Branch Name
           param3 (str): Action Type


       Returns:
           List : List of similar filenames available in oss bucket
       """
      # print(configfile)
      configFileName=os.path.basename(configfile).split('/')[-1]
      # print(configFileName)
      lockFile=configFileName.split(".")[0]+".lck"
      # print(lockFile)
      object_storage = oci.object_storage.ObjectStorageClient(config=self.config, signer=self.signer)
      next_starts_with = None
      try:
         # print(lockFile)
         response1 = object_storage.list_objects(namespace, bucket_name, start=next_starts_with, prefix=lockFile,
                                                retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)

         next_starts_with = response1.data.next_start_with
         if (response1.data.objects):
            for object_file in response1.data.objects:
               print_info("object_file.name " +object_file.name)
               if lockFile in object_file.name:
                  response = object_storage.delete_object(namespace, bucket_name, lockFile)
                  print_info(response.status)
                  print_info(response.data)
         else:
            print_info("No lock file to delete. ")

      except Exception as e:
         message = "Failed to delete file {0} from oss_bucket {1} with exception {2}!".format(lockFile,bucket_name,e)
         print_warn(message)
         raise

   def fetch_userid(self):
      filename = "../../creds/.env"
      userid = ""
      try:
         with open(filename, 'r') as file:
            for line in file:
               if re.search("JC_COMM_USER_NAME=", line):
                  # print(line)
                  userid = line.split("=")[1].strip()
         return userid
      except Exception as e:
         message = "Failed to open file {0}  with exception {1}!".format(filename, e)
         print_warn(message)
         raise
   def create_lockfile(self,fileName):
      try:
         with open(fileName, 'w') as fp:
            # fp.write(globalvariables.glbl_user_name+"\n")
            fp.write(self.fetch_userid()+"\n")
            fp.write(globalvariables.glbl_utc_str_time)
      except Exception as e:
         message = "Failed to create file {0}  with exception {1}!".format(fileName, e)
         print_warn(message)
         raise

   def prepare_local_env(self, file_prefix, resize_branch, csv_fileName, lock_fileName):
      filedir = ""
      try:
         isAvailable = self.check_if_file_available_in_bucket(csv_fileName, lock_fileName)
         # lock_fileName = csv_fileName + ".lck"
         self.create_lockfile(lock_fileName)
         self.upload_file_to_objectstore(lock_fileName)
         os.remove(lock_fileName)
         if isAvailable == True:
            oss_filename_list_all = self.list_oss_fileName(file_prefix, resize_branch)
            # print(oss_filename_list_all)
            oss_filename_list = [i for i in oss_filename_list_all if 'lck' not in i]
            # print(oss_filename_list)
            for file in oss_filename_list:
               filedir = ""
               if file.endswith(".csv"):
                  filedir = globalvariables.cfg_dir
               elif file.endswith(".json") or file.endswith(".cmd"):
                  res = [ele for ele in globalvariables.glbl_regions if (ele in file)]
                  if bool(res):
                     # print(res[0])
                     # print(file)
                     filedir = globalvariables.output_dir+res[0]+"/"
                  else:
                     filedir = globalvariables.output_dir
               # else:
               #    filedir = globalvariables.output_dir
               self.download_file_from_objectstore(file, filedir)
               time.sleep(10)
         else:
            print_info("No file available for {} branch to download . Please continue ...".format(resize_branch))
      except Exception as e:
         message = "Failed to get file {0}  with exception {1}!".format(file_prefix, e)
         print_warn(message)
         raise

   def upload_all_required_files_oss(self, file_prefix, resize_branch):
      dirlist = [globalvariables.output_dir, globalvariables.cfg_dir]
      for region in globalvariables.glbl_regions:
         dirlist.append(globalvariables.output_dir+region+"/")
      try:
         for dir in dirlist:
            for file in os.listdir(dir):
               if file.startswith(file_prefix) and re.search(resize_branch, file):
                  print_info(dir+file)
                  self.upload_file_to_objectstore(dir+file)
                  time.sleep(20)

      except Exception as e:
         message = "Failed to fetch files starts with {0} and with branch name as {1} with exception {2}!".format(file_prefix,resize_branch,e)
         print_warn(message)
         raise


# Confluence for defining the Naming conventions of Files being uploaded to BUCKET for horizon
#### https://confluence.oraclecorp.com/confluence/display/FusionSRE/POC+for+OCI+Backup+on+Horizon#POCforOCIBackuponHorizon-References
# def put_file_into_bucket_for_horizon():



