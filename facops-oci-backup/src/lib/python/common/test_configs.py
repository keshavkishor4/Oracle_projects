# source /opt/faops/spe/ocifabackup/lib/python/common/setpyenv.sh
# >/opt/faops/spe/ocifabackup/lib/python/common/test_wallet.py && vi /opt/faops/spe/ocifabackup/lib/python/common/test_wallet.py
# python test_wallet.py
# import paramiko
# import json
# import hashlib
# import sys
# import glob
# import os
# import shutil
# import sys
# import csv
# from datetime import datetime
# from pwd import getpwuid
# from operator import itemgetter

# 

# import oci
# from oci.exceptions import *
# from oci.object_storage.transfer.constants import MEBIBYTE
# from oci.object_storage import UploadManager
# from oci.retry import DEFAULT_RETRY_STRATEGY
# from Crypto.PublicKey import RSA
# from datetime import timedelta
# from cffi.backend_ctypes import xrange

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import ociSDK,apscom,commonutils,globalvariables,load_oci_config,post_backup_metadata,instance_metadata

import ociSDK

# from db import validate_sbt_test
# import json
# import traceback
# from paramiko import SSHClient
# import errno

# private_key_path=""
# #/u02/backup/log/epxa23-wbbhd1/exalogs/ldb_exec_states.csv
# ldb_txt_file_path = globalvariables.EXALOGS_PATH + "/ldb_exec_states.csv"

# def get_host():
#     with open(ldb_txt_file_path, newline="", encoding="utf-8") as file:
#         readData = [row for row in csv.DictReader(file)]
#     for i in range(0, len(readData)):
#         unique_list.append(readData[i]["host"])
#         unique_list = set(unique_list) 
#         return unique_list        

# # 
# #  three files
# # 1. /opt/faops/spe/ocifabackup/config/wallet/config-oci.json
# # 2. read 1, get private path and if it exists
# # 3. /opt/faops/spe/ocifabackup/config/db/sre_db.cfg
# def insert_char_every_n_chars(string, char='\n', every=64):
#     return char.join(
#         string[i:i + every] for i in xrange(0, len(string), every))

# def generate_fingerprint(private_key_path=None, key_file_obj=None,
#                                passphrase=None):
#     """
#     Returns the fingerprint of the public portion of an RSA key as a
#     47-character string (32 characters separated every 2 characters by a ':').
#     The fingerprint is computed using the MD5 (hex) digest of the DER-encoded
#     RSA public key.
#     """
#     try:
#         privkey = get_rsa_key(key_location=private_key_path, key_file_obj=key_file_obj,
#                               passphrase=passphrase, use_pycrypto=True)
#         pubkey = privkey.publickey()
#         md5digest = hashlib.md5(pubkey.exportKey('DER')).hexdigest()
#         fingerprint = insert_char_every_n_chars(md5digest, ':', 2)
#         return fingerprint
#     except Exception as e:
#         message = "Failed to generate fingerprint for {0}!\n{1}!\n{2}".format(private_key_path, sys.exc_info()[1:2], e)
#         print(message)

# def get_rsa_key(key_location=None, key_file_obj=None, passphrase=None,
#                 use_pycrypto=False):
#     key_fobj = key_file_obj or open(key_location)
#     try:
#         if use_pycrypto:
#             key = RSA.importKey(key_fobj.read())
#         else:
#             key = paramiko.RSAKey.from_private_key(key_fobj,
#                                                    password='')
#         return key
#     except Exception as e:
#         message = "Invalid RSA private key file or missing passphrase: {0}!\n{1}!\n{2}".format(key_location, sys.exc_info()[1:2], e)
#         print(message)

# def get_object_storage_config(oci_config_file):
#     try:
#         with open (oci_config_file, 'r') as config_file:
#             oci_config = json.load(config_file)
#         fingerprint = generate_fingerprint(oci_config["private_key_path"])
#         config = {
#             "user": oci_config["user_ocid"],
#             "key_file": oci_config["private_key_path"],
#             "fingerprint": fingerprint,
#             "tenancy": oci_config["tenancy_ocid"],
#             "region": oci_config["region"]
#         }
#         config_file.close()
#         return config
#     except Exception as e:
#         message = "Failed to generate config!\n{0}{1}".format(sys.exc_info()[1:2],e)
#         print(message)

# # data = get_object_storage_config('/opt/faops/spe/ocifabackup/config/wallet/config-oci.json')

# def get_tenancy_info():
#     try:
#         oci_data = {}
#         oci_wallet_config='/opt/faops/spe/ocifabackup/config/wallet/config-oci.json'
#         with open(oci_wallet_config, 'r') as f:
#             oci_config = json.load(f)
#             compartment_id = oci_config["tenancy_ocid"]
#             tenancy_ocid = oci_config["tenancy_ocid"]
    
#         config=get_object_storage_config(oci_wallet_config)
#         identity_client = oci.identity.IdentityClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
#         getTenancyInfo = identity_client.get_tenancy(tenancy_ocid).data
#         #print(getTenancyInfo)
#         # oss namespace
#         oss_client = oci.object_storage.ObjectStorageClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
#         oss_namespace = oss_client.get_namespace().data
#         if oss_namespace:
#             return True

#         oss_bucket="RMAN_WALLET_BUCKET"
#         #print("namespace: {0}".format(oss_namespace))

#         # prefix=".passwd"
#         # List_objects = oss_client.list_objects(namespace_name=oss_namespace, bucket_name=oss_bucket,prefix=prefix, retry_strategy=DEFAULT_RETRY_STRATEGY).data
#         # print(List_objects)
#     except Exception as e:
#         if e.errno != errno.ENOENT:
#                 # ignore "No such file or directory", but re-raise other errors
#                 message = "[get_tenancy_info]: Tenancy info is not correct\n{0}{1}".format(sys.exc_info()[1:2],e)
#                 apscom.warn(message)

# # 



ociSDK.get_tenancy_info()
#get_tenancy_info()