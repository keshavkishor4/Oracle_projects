#!/usr/bin/env python
# -*- coding: utf-8 -*-


from datetime import timedelta
from Crypto.PublicKey import RSA
import commonutils
import globalvariables
import json
import instance_metadata
from requests.auth import HTTPBasicAuth
import sys
import requests
import os
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime, timedelta
from cffi.backend_ctypes import xrange
from requests.adapters import HTTPAdapter
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def bucket_validate(bucket_name,obj_name):
    try:
        region = instance_metadata.ins_metadata().region
        with open(globalvariables.DB_CONFIG_PATH_DEFAULT, 'r') as oci_config_file:
            oci_config = json.load(oci_config_file)
        oss_namespace = oci_config["oss_namespace"]
        #download_passwd_file()
        cred_f = "/tmp/.passwd.json"
        with open(cred_f, 'r') as f:
            data = json.load(f)
            user = list(data[oss_namespace].keys())[0]
            bucket_oss_passwd = data[oss_namespace][user]
        cmd = "{0} --key {1}".format(globalvariables.DECRYPT_TOOL,
                                    bucket_oss_passwd)
        [output, ret_code, stderror] = commonutils.execute_shell(cmd)
        password = output

        retry_strategy= Retry(total=5, backoff_factor=1, status_forcelist=[502,503,504,500,429])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.session()
        http.mount('https://', adapter)
        http.mount('http://', adapter)
        if not "uk-gov-" in region:
            URL='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
        else:
            URL='https://swiftobjectstorage.{0}.oraclegovcloud.uk/v1/{1}/{2}/'.format(region,oss_namespace,bucket_name)

        #removing new line character from URL string#
        URL = URL.strip()
        URL = URL + obj_name
        response = http.put(URL, auth=HTTPBasicAuth(user, password))
        # print(response.status_code,URL)
        if response.status_code == 204:
            return True
        else:
            return False
    except Exception as e:
        message = "Bucket validate got failed with status False"
        print(message,e)


bucket_validate("RMAN_BACKUP", "test.txt")

