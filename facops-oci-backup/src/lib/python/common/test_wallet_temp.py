#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
from pkgutil import get_data
import sys
import oci 
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import globalvariables, test_configs

def wallet_files_checks():
    wallet_config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
    #wallet_config_file="/opt/faops/spe/ocifabackup/config/wallet/config-oci-template.json"
    if os.path.exists(wallet_config_file):
        try:
            with open(wallet_config_file) as f:
                wallet_config_data = json.load(f)
            #
            private_key_path = wallet_config_data["private_key_path"]
            if private_key_path != "":
                #check private key path exists
                if os.path.exists(private_key_path):
                    status = test_configs.get_tenancy_info()
                    if status:
                        return True,'Good'
                    if not status:
                        file_push = "config_key"
                        return False,file_push
                else:
                    with open(wallet_config_file, "r") as config_file:
                        data = json.load(config_file)
                        data["private_key_path"] = "/opt/faops/spe/ocifabackup/config/wallet/oci_api_key.pem"
                    with open(wallet_config_file, "w") as config_file:
                        json.dump(data, config_file)
                        file_push = "Private_file"
                        return False,file_push
            else:
                file_push = "config_file"
                return False,file_push
        except Exception as e:
            print(e)
    else:
        file_push = "config_file"
        return False,file_push

status,File=wallet_files_checks()
print ("{0}:{1}".format(status,File,end=''))


import json
import os
import oci
from urllib.error import HTTPError as ServiceError

def list_objects():
    try:
        object_info = "/u04/tmp/fra_mt_backup_bucket_info.json"
        #object_info = "/u04/tmp/object_info.json"
        signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
        object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer)
        oss_namespace = object_storage.get_namespace().data
        # objects = object_storage.list_objects(oss_namespace, 'MT_BACKUP').data.objects
        get_data = oci.pagination.list_call_get_all_results(object_storage.list_objects, oss_namespace, 'MT_BACKUP').data
        #print(type(objects))
        #print(objects)
        with open(object_info, "w") as object_info:
            for element in get_data:
                object_info.write(str(element))

    except ServiceError as e:
        message = "Failed to list objects!\n{0}{1}".format(sys.exc_info()[1:2],e)
        # apscom.warn(message)
        raise
    
list_objects()