#!/usr/bin/env python3

import os
import sys
import argparse
import faas_vm_reboot_monitoring
BASE_DIR = os.path.abspath(__file__ + "/../..")
sys.path.append(BASE_DIR + "/src/lib/common")
import globalvariables
from globalvariables import print_info, print_warn, print_error

import commonutils

import ocisdk
oci_sdk = ocisdk.OciSdk()

def arg_parse():
    parser = argparse.ArgumentParser(description='Resize Monitoring')
    parser.add_argument('--incident_jira', type=str, help='enter the MI JIRA', required=True)
    parser.add_argument('--region', type=str, help='enter the REGION', required=True)
    parser.add_argument('--stack', type=str, default='prod' , help='enter the REALM (Preprod --> preprod or Production --> prod)', required=False)
    parser.add_argument('--action', type=str, default='COMPUTE_REBOOT' , help='enter the action that needs to Performed ', required=False)
    parser.add_argument('--cm_jira', type=str, default='CHANGE-0' , help='enter the Change Mgmt JIRA for REBOOT)', required=False)

    # print("parser.parse_args : ", parser.parse_args())

    return parser.parse_args()


def main():
    args = arg_parse()
    var_incident_jira = args.incident_jira
    var_region = args.region
    var_stack = args.stack
    var_action = args.action
    var_stack = args.stack
    # type = args.type
    # resize_branch = commonutils.get_next_Friday(var_branch.strip())
    # globalvariables.glbl_stack = stack
    # if type.upper() == "TEST":
    #     globalvariables.glbl_file_prefix = globalvariables.glbl_test_file_prefix

    # incident_FA-1234_valid_pod_vms_for_reboot_list.json
    fileName = "{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, var_incident_jira)
    var_input_filepath = fileName
    # filepath = "{}{}".format(globalvariables.output_dir,var_region)
    # var_input_filepath = filepath+"/"+fileName
    # print(var_input_filepath)
    
    # file_location = input("Want to fetch json file to monitor your run from local or remote -  local/remote : - ")
    # if (file_location.upper().strip() == "LOCAL"):
    #     if os.path.exists(var_input_filepath):
    #         faas_resize_monitoring.get_work_req_id(var_input_filepath)
    #     else:
    #         oci_sdk.download_file_from_objectstore(fileName, filepath)
    # else:
    #     oci_sdk.download_file_from_objectstore(fileName, filepath)
    # print_info("#################Monitoring getting started ####################")
    faas_vm_reboot_monitoring.get_work_req_id(var_input_filepath)


if __name__ == "__main__":
    main()
