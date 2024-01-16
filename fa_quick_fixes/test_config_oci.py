#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import paramiko
import sys
import oci
import errno
BASE_DIR = "/opt/faops/spe/ocifabackup/"
sys.path.append(BASE_DIR + "/lib/python/")
from common import globalvariables, apscom, commonutils

wallet_config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
private_key_path = globalvariables.PRIVATE_KEY_PATH_FILES
python_path = globalvariables.BASE_DIR+"/utils/python3/el7/bin/python"
script_path = globalvariables.BASE_DIR + "/lib/python/common/test_wallet_temp.py"
myhost = globalvariables.HOST_NAME


def get_tenancy_info():
    try:
        oci_data = {}
        oci_wallet_config='/opt/faops/spe/ocifabackup/config/wallet/config-oci.json'
        with open(oci_wallet_config, 'r') as f:
            oci_config = json.load(f)
            compartment_id = oci_config["tenancy_ocid"]
            tenancy_ocid = oci_config["tenancy_ocid"]

        #config=get_object_storage_config(oci_wallet_config)
        config = commonutils.get_object_storage_config(oci_wallet_config)
        identity_client = oci.identity.IdentityClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        getTenancyInfo = identity_client.get_tenancy(tenancy_ocid).data
        #print(getTenancyInfo)
        # oss namespace
        oss_client = oci.object_storage.ObjectStorageClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
        oss_namespace = oss_client.get_namespace().data
        if oss_namespace:
            return True
    except Exception as e:
        if e.errno != errno.ENOENT:
            # ignore "No such file or directory", but re-raise other errors
            message = "[get_tenancy_info]: Tenancy info is not correct\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            
def wallet_files_checks():
    #wallet_config_file="/opt/faops/spe/ocifabackup/config/wallet/config-oci-template.json"
    try:
        if os.path.exists(wallet_config_file):
            try:
                with open(wallet_config_file) as f:
                    wallet_config_data = json.load(f)
                #
                private_key_path = wallet_config_data["private_key_path"]
                if private_key_path != "":
                    #check private key path exists
                    if os.path.exists(private_key_path):
                        status = get_tenancy_info()
                        if status:
                            return True,'Good'
                        if not status:
                            file_push = "corrupted_key"
                            return False,file_push
                    else:
                        return False,private_key_path
                else:
                    file_push = "config_file"
                    return False,file_push
            except Exception as e:
                print(e) 
        else:
            file_push = "config_file not present"
            return False,file_push
    except Exception as e:
        apscom.warn(e)
    
def main():
    status,File=wallet_files_checks()
    if status==True:
        print(status)
    else:
        print(status,File)

if __name__ == "__main__":
    main()
