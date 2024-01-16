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
import subprocess
import sys
import os
import json
import traceback
from datetime import datetime

BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables,commonutils,instance_metadata

#### imports start here ##############################
def execute_test(test_name,script_name):
    try:
        print("this is test execution")
        #common_test_utils.TAKE_ACTION.get(script_name)
        cmd = '{0}/bin/validate_rpm.sh {1}'.format(BASE_DIR,script_name)
        output, ret_code = execute_shell(cmd)
    except Exception as e:
        message = "Failed to execute test!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.error(message)
def execute_shell(command):
    try:
        com_list = command.split('|')
        lstPopen = []

        for i in range (0,len(com_list)):
            if i == 0:
                lstPopen = [subprocess.run(shlex.split(com_list[0]), stdout=subprocess.PIPE, stderr=subprocess.PIPE)]
            else:
                lstPopen.append(subprocess.run(shlex.split(com_list[i]), input=lstPopen[i-1].stdout, stdout=subprocess.PIPE))

        str_process_info = lstPopen[-1].stdout.decode('utf-8')
        return str_process_info.rstrip(),lstPopen[-1].returncode
    except Exception as e:
        message = "Could not run execute_shell !\n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise
def main():
    try:
        global rpm_ver
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}".format("testresults")
        filename = log_file_path + "{0}_{1}_{2}_{3}.log".format(globalvariables.HOST_NAME, "test",
                                                                os.path.basename(__file__).split(".")[0],
                                                                datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        rman_main_log = apscom.init_logger(__file__ , log_dir=log_file_path, logfile=filename)
        inst_meta = instance_metadata.ins_metadata()
        inst_metadata = inst_meta.get_inst_metadata()
        region = inst_meta.region
        if "dbSystemShape" in inst_metadata["metadata"]:
            system_type = "DB"
        else:
            system_type = "MT"
        with open(globalvariables.CONFIG_PATH+'/'+"faops_test_main.json",'r') as test_config:
            temp_data = json.load(test_config)
            rpm_ver=temp_data[system_type]['rpm_ver']
            #verify host details for testing
            if(globalvariables.HOST_NAME in temp_data[system_type]['host']):
                #opening test json
                current_backup_version = commonutils.get_rpm_ver()
                if (current_backup_version != rpm_ver):
                    message = "Current installed RPM version and testing RPM version is not same"
                    apscom.error(message)
                with open(globalvariables.CONFIG_PATH+'/'+"faops_backup_test.json",'r') as config:
                    data = json.load(config)
                    for val in data:
                        if val==system_type:
                            for test in (data[val]):
                                #verify script enabled for testing
                                if data[val][test]['enabled']=="y":
                                    execute_test(test,data[val][test]['script_name'])
    except Exception as e:
        traceback.print_exc()
        message="Failed to execute test!\n{0},{1})".format(sys.exc_info()[1:2],e)
        apscom.error(message)

if __name__ == "__main__":
    main()