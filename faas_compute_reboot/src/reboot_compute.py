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
from datetime import datetime, timedelta, time
import getpass
import glob
import shutil
import argparse
import shutil

import reboot_compute_main

BASE_DIR = os.path.abspath(__file__ + "/../..")
print ("BASE_DIR : {0}".format(BASE_DIR))
sys.path.append(BASE_DIR + "/src/lib/common")

# print ("asasdasd : {0}".format(sys.path.append(BASE_DIR + "/src/lib/common")))
print ("BASE_DIR after append : {0}".format(BASE_DIR))
import globalvariables
import commonutils

def get_args():
    parser = argparse.ArgumentParser(description='FAaaS Reboot Compute')
    parser.add_argument('--incident_jira', type=str, help='enter the MI JIRA', required=True)
    parser.add_argument('--input_file', type=str, help='enter the FLIP RT Input csv file', required=True)
    parser.add_argument('--stack', type=str, default='prod' , help='enter the REALM (Preprod --> preprod or Production --> prod)', required=False)
    parser.add_argument('--action', type=str, default='COMPUTE_REBOOT' , help='enter the action that needs to Performed ', required=False)
    parser.add_argument('--cm_jira', type=str, default='https://jira-sd.mc1.oracleiaas.com/browse/CHANGE-0' , help='enter the Change Mgmt JIRA for REBOOT)', required=False)

    return parser.parse_args()


# git add -A . && git commit -m "updates as of $(date) FUSIONSRE-25491" && git push origin

# https://confluence.oraclecorp.com/confluence/display/FusionSRE/FAOCI+-+FAaaS+VM+Reboot+-+DSO

def main():
    args = get_args()
    stack = args.stack

    globalvariables.glbl_fliprt_incident_jira=args.incident_jira.strip()
    var_csv_input_file = args.input_file.strip()
    globalvariables.glbl_fliprt_cm_jira=args.cm_jira.strip()
    globalvariables.glbl_stack=args.stack
    globalvariables.glbl_action=args.action


    # print ("input file is : {0}".format(var_csv_input_file))
    reboot_compute_main.get_pod_name_info (var_csv_input_file,globalvariables.glbl_stack.strip())

    print ("Submitting the Requests for Reboot....")
    


if __name__ == "__main__":
    main()