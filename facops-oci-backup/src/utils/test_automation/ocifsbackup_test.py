#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      ocifsbackup_test.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       09/30/20 - initial version (Test Automation)
"""
#### imports start here ##############################
import shlex
import shutil
import ssl
import sys
import os
import traceback
import json
import re
import urllib.request
from datetime import datetime
from time import strftime, gmtime
import requests
import subprocess
from zipfile import ZipFile
from requests.packages.urllib3.exceptions import InsecureRequestWarning
BASE_DIR = os.path.abspath(__file__ + "/../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables,commonutils,instance_metadata,post_backup_metadata
#### imports start here ##############################
test_results_list=[]
global system_type
global ct_path
ct_path = BASE_DIR + "/utils/test_automation"
inst_meta = instance_metadata.ins_metadata()
inst_metadata = inst_meta.get_inst_metadata()
if "dbSystemShape" in inst_metadata["metadata"]:
    system_type = "DB"
else:
    system_type = "MT"
def execute_test(test_name,script_name):
    try:
        #common_test_utils.TAKE_ACTION.get(script_name)
        script_path="{0}/utils/test_automation/{1}".format(BASE_DIR,script_name)
        os.chmod(script_path, 0o755)

        cmd = '{0}/utils/test_automation/{1} {2} {3} {4}'.format(BASE_DIR,script_name,test_name,test_log,dbname)
        #print(cmd)
        response=subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = response.communicate()
        schedule="auto"
        return_code =response.returncode
        output=re.sub(r"\s+$", "", stdout.decode('utf-8').strip(), flags=re.UNICODE)
        if output.isdigit() and int(output)==0:
            status="SUCCESS"
        else:
            status = "FAILED"
            with open(test_log, 'a') as file:
                file.write(stderr.decode('utf-8'))
        #print(test_name+'----------------'+status)
        get_results_dict(script_name,schedule,test_name,status)
    except Exception as e:
        traceback.print_exc()
        message = "Failed to execute test!\n{0},{1})".format(sys.exc_info()[1:2], e)
        apscom.error(message)
def get_results_dict(script_name,schedule,test_name,status):
    test_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    test_dict ={}
    test_dict["test_name"]= test_name
    test_dict["type"]= system_type
    test_dict["action"]= test_name
    test_dict["schedule"]= schedule
    test_dict["command"]= script_name
    test_dict["reported_by"]= "auto"
    test_dict["output_log"]= test_log
    test_dict["test_run_date"]= test_time
    test_dict["status"] =status
    test_results_list.append(test_dict)
def post_metadata():
    try:
        metadata_data={}
        json_file = "/opt/faops/spe/ocifabackup/utils/metadata.json"
        metadata_data["backup_test_results"] = test_results_list
        with open(json_file, 'w') as outfile:
            json.dump(metadata_data, outfile, indent=4, sort_keys=True)
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        print("{:<30} {:<30} {:<30}".format('test_name', 'status', 'test_run_date'))
        for data in test_results_list:
            test_name, status, test_run_date = data.get('test_name'), data.get('status'), data.get('test_run_date')
            print("{:<30} {:<30} {:<30}".format(test_name, status, test_run_date))
        # print(metadata_data["backup_test_results"])
        return metadata_data
    except Exception as e:
        message = "Failed to post metadata!\n{0},{1})".format(sys.exc_info()[1:2], e)
        apscom.error(message)

def main():
    try:
        global rpm_ver
        global test_log
        global dbname
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}".format("testresults")
        filename = log_file_path + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME, "test",
                                                                datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        test_log = apscom.init_logger(__file__ , log_dir=log_file_path, logfile=filename)

        #download_files()
        test_executed=False
        with open(ct_path+'/'+"faops_enable_test.json",'r') as test_config:
            temp_data = json.load(test_config)
            data = temp_data[0]["enable_tests"]
            for val in data:
                enable = "n"
                if globalvariables.HOST_NAME in val[system_type]["host"]:
                    enable = val[system_type]["enable"]
                if(enable=="Y"):
                    if globalvariables.HOST_NAME in val[system_type]["host"]:
                        if (system_type == "DB"):
                            dbname = val[system_type]['db_name']
                        else:
                            dbname=""
                        rpm_ver=val[system_type]['rpm_ver']
                        current_backup_version = commonutils.get_rpm_ver()
                        if (current_backup_version != rpm_ver):
                            message = "Current installed RPM version and testing RPM version is not same"
                            apscom.warn(message)
                            return False

                    with open(ct_path+'/'+"faops_backup_test.json",'r') as config:
                        data_config = json.load(config)
                        for val in data_config:
                            if val==system_type:
                                for test in (data_config[val]):
                                    #verify script enabled for testing
                                    #print(test, data_config[val][test]['script_name'], data_config[val][test]['enabled'], '$$$$$$$$$$$$$$$$$$$')
                                    if data_config[val][test]['enabled']=="y":
                                        execute_test(test,data_config[val][test]['script_name'])
                                        test_executed = True
        if not test_executed:
            message = "Test automation not enabled for {0}".format(globalvariables.HOST_NAME)
            apscom.warn(message)
            return False
        post_metadata()
        #cleanup_all_files()
        return True
    except Exception as e:
        traceback.print_exc()
        message="Failed to execute test!\n{0},{1})".format(sys.exc_info()[1:2],e)
        apscom.error(message)

def cleanup_all_files():
    try:
        #os.rmdir(BASE_DIR+"/utils/test_automation")
        shutil.rmtree(BASE_DIR+"/utils/test_automation")
    except Exception as e:
        traceback.print_exc()
        message = "Failed to cleanup files!\n{0},{1})".format(sys.exc_info()[1:2], e)
        apscom.error(message)

if __name__ == "__main__":
    main()