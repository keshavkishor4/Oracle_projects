#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      load_oci_config.py
    DESCRIPTION
      Used to generate oci configuration.
    NOTES
    MODIFIED        (MM/DD/YY)
    Saritha Gireddy       16/10/20 - initial version (code refactoring)
"""
#### imports start here ##############################
import shutil
import sys
import json
import os
import socket
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,instance_metadata,globalvariables,commonutils,ociSDK
from db import database_config 
try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError

# 
# Test existing config
def test_config(config_file,config_key,region):
    with open(config_file, 'r') as config_file_new:
        # print("trying --->"+config_file)
        oci_config = json.load(config_file_new)
        private_key_path=config_key
        try:
            fingerprint = commonutils.generate_fingerprint(private_key_path)
            config = {
                "user": oci_config["user_ocid"],
                "key_file": config_key,
                "fingerprint": fingerprint,
                "tenancy": oci_config["tenancy_ocid"],
                "region": region
            }

            try:
                config_tenancy_id = config["tenancy"]
                # testing oci
                try:
                    identity = oci.identity.IdentityClient(config)
                    tenancy_data = identity.get_tenancy(config_tenancy_id).data
                    tenancy_name = tenancy_data.name
                    return True
                except Exception as e:
                    message = "{2}config does not look correct for  !\n{0} or {1}".format(config_file,config_key,globalvariables.RED)
                    apscom.warn(message)
                    return False
                    pass
            except Exception as e:
                message = "Failed to generate config for !\n{0}".format(e)
                apscom.warn(message)
        except Exception as e:
            print(e)
            message = "problem generating fingerprint for !\n{0} or {1}".format(config_file,config_key)
            apscom.info(message)

def process_new_config(config_file,region):
    # config file
    cmd = "{0} --file {1}".format(globalvariables.DECRYPT_TOOL,config_file)
    commonutils.execute_shell(cmd)
    # # pem key
    # cmd = "{0} --file {1}".format(globalvariables.DECRYPT_TOOL, config_key)
    # commonutils.execute_shell(cmd)
    # decrypt files
    # dec_config_key=config_key+".decrypt"
    dec_config_file=config_file+".decrypt"
    # 
    # result = test_config(dec_config_file,region)
    result=True
    if(result):
        # print("success")
        # shutil.copy(dec_config_key,"{0}/config/wallet/oci_api_key.pem".format(BASE_DIR))
        shutil.copy(dec_config_file, "{0}/config/wallet/config-oci.json".format(BASE_DIR))
        update_json(region)
        # os.remove(dec_config_key)
        os.remove(dec_config_file)
    else:
        message = "Failed to load oci-config!"
        apscom.warn(message)
        sys.exit(1)

def check_files(region):
    try:
        config_file=""
        config_key=""
        fqdn = socket.getfqdn()
        ns=get_namespace_from_sre()
        print("Value of ns is:-",ns)
        # test existing files if present 
        if os.path.exists("{0}/config/wallet/config-oci.json".format(BASE_DIR)) and os.path.exists("{0}/config/wallet/oci_api_key.pem".format(BASE_DIR)):
           result = test_config("{0}/config/wallet/config-oci.json".format(BASE_DIR),"{0}/config/wallet/oci_api_key.pem".format(BASE_DIR),region)
           if (result):
               print("success")
               return 0
        #
        # ukgov
        if ns == "axqqulwjr5ll":
            config_file = "{0}/config/wallet/.oci/config-oci-saasfaukgovprod1.json.crypt".format(BASE_DIR)
            # config_key = "{0}/config/wallet/.oci/oci_api_key_saasfaukgovprod1.pem.enc".format(BASE_DIR)
        # ppd
        elif ns == "p1-saasfapreprod1":
            config_file = "{0}/config/wallet/.oci/config-oci-p1-saasfapreprod1.json.crypt".format(BASE_DIR)
            print("Confi file value is:-",config_file)
            # config_key = "{0}/config/wallet/.oci/oci_api_key_p1-saasfapreprod1.pem.enc".format(BASE_DIR)
        elif ns == "saasfaprod1":
            config_file = "{0}/config/wallet/.oci/config-oci-saasfaprod1.json.crypt".format(BASE_DIR)
            # config_key = "{0}/config/wallet/.oci/oci_api_key_saasfaprod1.pem.enc".format(BASE_DIR)
        else:
            message ="config-oci.json restore not supported for this namespace/tenancy"
            apscom.warn("{0}".format(message))
        #
        # print(config_file,config_key,region)
        process_new_config(config_file,region)

    except Exception as e:
        message = "Failed to generate config, tenancy not supported !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        pass

def get_namespace_from_sre():
    try:
        namespace = ''
        inst_meta = instance_metadata.ins_metadata()
        sytem_cata = inst_meta.system_category
        if sytem_cata == 'Exadata':
            if not os.path.exists("{0}/sre_db.cfg".format(globalvariables.DB_CONFIG_PATH)):
                database_config.gen_sre_db_config()

            with open(globalvariables.DB_CONFIG_PATH + '/sre_db.cfg', 'r') as fp:
                lines = fp.readlines()
                for line in lines:
                    if "swiftobjectstorage" in line:
                        namespace = line.split("=")[1].split("/")[-2]
        else:
            signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
            object_storage = oci.object_storage.ObjectStorageClient(config={}, signer=signer, timeout=600)
            namespace = object_storage.get_namespace().data
        return namespace
    except Exception as e:
        message = "Failed to get namespace , check entries in {0} are correct, exception: {1}".format(globalvariables.DB_CONFIG_PATH + '/sre_db.cfg',e)
        apscom.warn(message)
        raise

def main():
    region=instance_metadata.ins_metadata().region
    print(region)
    check_files(region)
    
def update_json(region):
    try:
        with open(globalvariables.DB_CONFIG_PATH_DEFAULT, "r") as config_file:
            config_object = json.load(config_file)
        config_object["region"] = region
        config_object["private_key_path"] = globalvariables.WALLET_CONFIG_PATH+"/oci_api_key.pem"
        with open(globalvariables.DB_CONFIG_PATH_DEFAULT, "w") as outfile:
            json.dump(config_object, outfile, indent=4, sort_keys=True)
    except Exception as e:
        message = "Failed to update config !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.info(message)
        pass

if __name__ == "__main__":
    main()