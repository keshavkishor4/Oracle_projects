#!/usr/bin/env python
# -*- coding: utf-8 -*-

#### imports start here ##############################
import os
import sys
import socket
import getpass
# import colorama
import json#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      gloablvariables.py

    DESCRIPTION
      load global variables

    NOTES

    MODIFIED        (MM/DD/YY)

    Sachin Sirsi       12/06/22 - initial version (code refactoring)
    
"""
#### imports start here ##############################
import os
import sys
import socket
import getpass
import colorama
import json
from colorama import Fore, Back, Style

from datetime import datetime
from datetime import timezone
# from setenv import ROOT_DIR, LIB_DIR


sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# print(sys.path)
import apscom
# import commonutils
from pathlib import Path

def get_project_root() -> Path:
    project_path = Path(__file__).parent.parent.parent.parent
    # print(project_path)
    return project_path
def get_lib_dir() -> Path:
    return Path(__file__)

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))




# INIT Variables (POD related MT/FACP Related)

glbl_jc_oc1_url=""
glbl_jc_oc4_url=""

####  https://prod-ops-fusionapps.ap-mumbai-1.oci.oraclecloud.com/20191001/internal/fusionEnvironments
####  https://preprod-ops-fusionapps.ap-mumbai-1.oci.oraclecloud.com/20191001/internal/fusionEnvironments

# Confluence for defining the Naming conventions of Files being uploaded to BUCKET for horizon
#### https://confluence.oraclecorp.com/confluence/display/FusionSRE/POC+for+OCI+Backup+on+Horizon#POCforOCIBackuponHorizon-References

glbl_config_profile="resize_oci_config"
# glbl_config_profile="oc1"
glbl_csv_fileName = ""
glbl_lock_fileName = ""
glbl_stack = ""
glbl_action = ""
glbl_fliprt_incident_jira=""
glbl_fliprt_cm_jira=""


glbl_maint_start_ts = ""

glbl_env_facp_url_prefixs={ "preprod" : "preprod-ops-fusionapps",
                            "prod": "prod-ops-fusionapps",
                            "prd": "prod-ops-fusionapps",
                            "prd-ukg": "prod-ops-fusionapps",
                            "prd-eura": "prod-ops-fusionapps",
                            "prd-usg" : "prod-ops-fusionapps"
                            }
glbl_env_facp_url_prefix=""

glbl_env_adp_url_prefixs={ "preprod" : "preprod-adp-ops",
                           "prod" : "prod-adp-ops"
                           }
glbl_env_adp_url_prefix=""

glbl_env_api_suffix="oci.oraclecloud.com/20191001/"

glbl_env_api_suffix_list={
    "oc1": "oci.oraclecloud.com/20191001/internal",
    "oc4": "oci.oraclecloud.com/20191001/internal",
    "oc8": "oci.oraclecloud.com/20191001/internal",
    "oc9": "oci.oraclecloud.com/20191001/internal"
}



glbl_fliprt_invalid_pod_vm_info = {
"incident_jira" : "",
"data_center" : "",
"pod_name": "",
"pod_ocid" : "",
"host_name" :"",
"vm_type" : "",
"host_id" : "",
"host_state" : "",
"cm_jira" : "",
"reason" : ""
}



var_valid_fliprt_pod_vm_infos_for_reboot_file=""
var_invalid_fliprt_pod_vm_infos_for_reboot_file=""





########## directory location definitions
# print ("---------------------- dir definitions ----------------------")

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
src_dir=BASE_PATH+"/../.."

def get_exec_time ():
    try :
        today_dt = datetime.now()
        exec_time=today_dt.strftime("%d%b%Y%H%M%S")
        # print ("Execution Time (exec_time) -----> : {0}".format(exec_time))
        return exec_time
    except Exception as e:
        message = "Exception in commonutils.get_exec_time, : {0}".format(e)
        print (message) 

glbl_exec_time = get_exec_time()


###### remote user/host info
glbl_uid=getpass.getuser()
# os.getenv("HOME")
glbl_user_home_dir="/Users/{0}/".format(glbl_uid)
glbl_user_name=getpass.getuser()
glbl_user_host = os.uname()[1]
######

########## directory location definitions
# print ("---------------------- dir definitions ----------------------")

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
src_dir=BASE_PATH+"/../.."

# print ("---------------------- log dir ----------------------")
log_dir=src_dir+"/log/"

# log_dir=resize_variables.src_dir+"/log/"
# print ("log dir : log_dir : ", log_dir)

is_log_dir_exists=os.path.exists(log_dir)
if (is_log_dir_exists):
    # print("log dir exists..", is_log_dir_exists)
    print ("")
else:
    # print ("creating the log dir..")
    # log_path=os.path.join(resize_variables.src_dir, "log")
    os.mkdir(log_dir)
    print ("log dir created..")
    print ("Listing log dir")
    dir_list=os.listdir(log_dir)
    # print("Log dir listing : ", dir_list)

f_allpodsinfo=log_dir + "all_pod_info.json"
# print("File 1 location : ", f_allpodsinfo)
# print ("--------------------------------------------------------")


def init_apscom ():
    ###############
    glbl_log_file_path=output_dir
    glbl_log_file_path=log_dir
    glbl_log_filename = "{0}/{1}_{2}_run_{3}.log".format(glbl_log_file_path,glbl_user_name,glbl_user_host,glbl_exec_time)

    apscom.init_logger(__file__, log_dir=glbl_log_file_path, logfile=glbl_log_filename)
    ###############


##### PRINT Colour Codes
# def print_info (data):
#     print (Fore.GREEN + data + Style.NORMAL)
#     # init_apscom ()
#     # apscom.info(data)
    
# def print_error (data):
#     print (Fore.RED + data + Style.NORMAL)
#     # init_apscom ()
#     # apscom.error(data)
    
# def print_warn (data):
#     print (Fore.YELLOW + data + Style.NORMAL)
#     # init_apscom ()
#     # apscom.warn(data)

# def print_reset (data):
#     print (Style.RESET_ALL)

# def print_normal (data):
#     print (Fore.WHITE + data + Style.NORMAL)

######
# glbl_log_file_path=output_dir
# glbl_log_filename = "{0}/{1}_{2}_test.log".format(glbl_log_file_path,glbl_user_name,glbl_user_host)

# apscom.init_logger(__file__, log_dir=glbl_log_file_path, logfile=glbl_log_filename)

##### PRINT Colour Codes
def print_info (data):
    # print (Fore.GREEN + data + Style.NORMAL)
    init_apscom ()
    apscom.info(data)
    
def print_error (data):
    # print (Fore.RED + data + Style.NORMAL)
    init_apscom ()
    apscom.error(data)
    
def print_warn (data):
    # print (Fore.YELLOW + data + Style.NORMAL)
    init_apscom ()
    apscom.warn(data)

def print_reset (data):
    print (Style.RESET_ALL)

def print_normal (data):
    print (Fore.WHITE + data + Style.NORMAL)
######

print ("---------------------- output dir ----------------------")
output_dir=src_dir+"/output/"
# output_dir=src_dir+"/output/"
# print ("output dir : ", output_dir)
# define the output dir --> src_dir + output
# output_path=os.path.join(resize_variables.src_dir, "output")

is_output_dir_exists=os.path.exists(output_dir)
if (is_output_dir_exists):
    init_apscom ()
    # print_info ("output dir already exists.. {0}".format(is_output_dir_exists) )
    
else:
    print ("output dir does not exist, creating the dir .. {0}".format(output_dir) )    
    os.mkdir(output_dir)
    init_apscom ()
    print_info ("{0}".format("output dir created.."))

dir_list=os.listdir(output_dir)

###############
###############




# print ("--------------------------------------------------------")


# print ("-----------------CONFIG related information------------------------")

# print ("--------------------------------------------------------")

cfg_dir = ""
cfg_dir=src_dir+"/config/"
if (os.path.exists(cfg_dir)):
    # print ("config directory EXISTS, we can proceed further...")
    print ("")
else:
    print ("Creating the config directory ...")
    os.mkdir (cfg_dir)


glbl_cfg_env_region_pod_input_csv_file = cfg_dir+"cfg_env_region_pod_input_csv_file.csv"
# print ("glbl_cfg_env_region_pod_input_csv_file : {0}".format(glbl_cfg_env_region_pod_input_csv_file))


glbl_cfg_env_internal_scheduled_activity_fliprt_file = cfg_dir+"cfg_env_internal_scheduled_activity.json"
# print ("glbl_cfg_env_internal_scheduled_activity_fliprt_file : {0}".format(glbl_cfg_env_internal_scheduled_activity_fliprt_file))



# print ("---------------------- log dir ----------------------")
log_dir=src_dir+"/log/"

# log_dir=resize_variables.src_dir+"/log/"
# print ("log dir : log_dir : ", log_dir)

is_log_dir_exists=os.path.exists(log_dir)
if (is_log_dir_exists):
    # print("log dir exists..", is_log_dir_exists)
    print ("")
else:
    # print ("creating the log dir..")
    # log_path=os.path.join(resize_variables.src_dir, "log")
    os.mkdir(log_dir)
    print ("log dir created..")
    print ("Listing log dir")
    dir_list=os.listdir(log_dir)
    # print("Log dir listing : ", dir_list)

f_allpodsinfo=log_dir + "all_pod_info.json"
# print("File 1 location : ", f_allpodsinfo)
# print ("--------------------------------------------------------")

# jsonConfigInValidFilePath --> invalid_pods_file
# invalid_pods_file = resize_variables.output_dir + "invalid_pods_"+resize_variables.get_exec_time()+".json"
# invalid_pods_file = ("{0}invalid_pods_{1}.json".format(output_dir,commonutils.get_exec_time()))
print_info ("glbl_exec_time : {0}".format(glbl_exec_time))


from datetime import datetime
from datetime import timezone
# from setenv import ROOT_DIR, LIB_DIR

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
src_dir=BASE_PATH+"/../.."

# # print ("---------------------- output dir ----------------------")
# output_dir=src_dir+"/output/"

# # print ("---------------------- config dir ----------------------")
# cfg_dir=src_dir+"/config/"






