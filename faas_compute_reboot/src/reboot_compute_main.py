#!/usr/bin/env python3

# from turtle import resizemode

from urllib import response
from datetime import datetime
# import faperf_client

import csv
import json
import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
import time
from pprint import pprint
import getpass
import glob
import shutil
import argparse
import shutil

BASE_DIR = os.path.abspath(__file__ + "/../..")
print ("BASE_DIR : {0}".format(BASE_DIR))
sys.path.append(BASE_DIR + "/src/lib/common")

print ("asasdasd : {0}".format(sys.path.append(BASE_DIR + "/src/lib/common")))
print ("BASE_DIR after append : {0}".format(BASE_DIR))
import globalvariables
import commonutils
from apscom import print_info, print_warn, print_debug, print_error
import pretty

from prettytable import PrettyTable









def get_pod_name_info (var_input_flip_rt_csv_file,stack):

    # print ("Calling the Function to convert the csv file to DICT")
    # var_pod_info_dict = convert_csv_to_dict (var_input_flip_rt_csv_file)
    # pprint (var_pod_info_dict)

    # commonutils.read_pod_from_dict (var_pod_info_dict)


    # kkk = input ("stop here....")
    # print ("in the main......")
    var_pod_entries_in_csv_file=commonutils.get_csv_entry_cnt (var_input_flip_rt_csv_file)
    print ("============ Count of entries in csv file is : {0}".format(var_pod_entries_in_csv_file))

    # commonutils.get_pod_name_from_csv (var_input_flip_rt_csv_file)
    # scan_input_to_output_files = commonutils.get_pod_info_from_fliprt_csv (var_input_flip_rt_csv_file,stack)
    commonutils.get_pod_info_from_fliprt_csv (var_input_flip_rt_csv_file,stack)

    # print ("scan_input_to_output_files : ",scan_input_to_output_files)
    # print ("COMPLETED SCANNING THE PODS provided as Input ...")
    # if (scan_input_to_output_files):
    #     valid_fliprt_pod_vm_infos_for_reboot_file = scan_input_to_output_files[0]
    #     invalid_fliprt_pod_vm_infos_for_reboot_file = scan_input_to_output_files[1]

    if (os.path.exists(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)):
        var_valid_pod_vms_for_reboot_cnt = commonutils.get_fliprt_count_pod_vms_for_reboot_from_file (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)
    else:
        var_valid_pod_vms_for_reboot_cnt = 0

    if (os.path.exists(globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file)):
        var_invalid_pod_vms_for_reboot_cnt = commonutils.get_fliprt_count_pod_vms_for_reboot_from_file (globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file)
    else:
        var_invalid_pod_vms_for_reboot_cnt = 0
        

    if (var_invalid_pod_vms_for_reboot_cnt > 0):
        print_warn ("There are {0} INVALID Entries in the input csv file ".format(var_invalid_pod_vms_for_reboot_cnt))
        pretty.print_invalid_info_pretty_table(globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file)

    if (var_valid_pod_vms_for_reboot_cnt > 0):
        print_info ("There are {0} VALID ENTRIES in the input file".format(var_valid_pod_vms_for_reboot_cnt))
        print ("Following POD VMs will be REBOOTED.... ")
        # print ("File to be read is : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
        # commonutils.disp_fliprt_valid_pod_vms_for_reboot (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)
        pretty.print_valid_info_pretty_table(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)

        # commonutils.consolidate_fliprt_pod_vms_for_reboot (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)

        sss = input ("Wait and check here...")
        var_proceed_to_reboot_options = ["Y","N"]
        var_proceed_to_reboot = ""
        
        while (var_proceed_to_reboot.upper() not in var_proceed_to_reboot_options):
            var_proceed_to_reboot = input(
                "Proceed to REBOOT the listed VMs (Y/N) : ")
        
        if (var_proceed_to_reboot.upper() == 'Y'):

            commonutils.create_payload_json_file ((globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))

            ss = input ("Press Ctrl + C to terminate last chance ....")

            # commonutils.disp_fliprt_submit_pod_vms_for_reboot (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)
            commonutils.submit_fliprt_pod_vms_for_reboot (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file)

            print_info ("Submitting the Requests, waiting for the Acceptance...")
            time.sleep (200)
            print_info ("Requests submitted, these can be Monitored via the Monitoring script...")

    elif (var_valid_pod_vms_for_reboot_cnt == 0 ):
        print_warn ("There are {0} VALID ENTRIES in the input file".format(var_valid_pod_vms_for_reboot_cnt))




