#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    NAME
      commonutils.py

    DESCRIPTION
      load global variables

    NOTES

    MODIFIED        (MM/DD/YY)

    Sachin Sirsi       12/06/22 - initial version (code refactoring)
    
"""
from datetime import datetime, timedelta
import sys
import oci
import json
import csv
import subprocess
from subprocess import check_output, STDOUT
import os
import traceback
import subprocess
from pprint import pprint
import globalvariables
# print(sys.path)
import apscom 
from apscom import print_info, print_warn, print_debug, print_error
from prettytable import PrettyTable
import validators
import ocisdk
oci_sdk = ocisdk.OciSdk()



# from globalvariables import print_info, print_warn, print_error, print_reset, print_info
# import ocisdk



def exec_api_cmd(cmd):
    try:
        # print ("In commonutils.exec_api_cmd", cmd)
        proc = subprocess.run(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode:
            # print('Issue reported, exit code {proc.returncode}, stderr:')
            print("error received exitting...")
            # print(proc.stderr)
            sys.exit(1)
        else:
            # print("in exec_api_cmd - proc.stdout : ", proc.stdout)
            return(proc.stdout)
    except Exception as e:
        message = "Exception in commonutils.exec_api_cmd, Unable to execute API {0} - {1} - {2}".format(cmd,e,traceback.print_exc())
        print_warn ("{0}".format(message))

def exec_api_cmd_with_status_output (cmd):
    try:
        # print ("In commonutils.exec_api_cmd", cmd)
        print ("cmd : ",cmd)
        proc = subprocess.run(cmd,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print ("proc : ",proc)
        
        if proc.returncode:
            # print('Issue reported, exit code {proc.returncode}, stderr:')
            print("error received exitting...")
            # print(proc.stderr)
            sys.exit(1)
        else:
            # print("in exec_api_cmd - proc.stdout : ", proc.stdout)
            # return(proc.stdout)

            var_cmd_output_utf8 = proc.stdout
            
            var_cmd_output_utf8_jsons = json.loads(var_cmd_output_utf8)

            print_info ("cmd_output_utf8_jsons : {0}".format(var_cmd_output_utf8_jsons))
            
            var_cmd_output_utf8_jsons_len = len(var_cmd_output_utf8_jsons)      

            var_req_data = {}
            var_req_status = ""
            var_req_header = {}
            var_opc_req_id = ""
            var_opc_wrk_req_id = ""
            var_opc_req_message = ""

            print ("var_cmd_output_utf8_jsons : ",var_cmd_output_utf8_jsons)
            
            if (var_cmd_output_utf8_jsons_len > 0):
                var_req_status = var_cmd_output_utf8_jsons.get("status")
                var_req_header = var_cmd_output_utf8_jsons.get("headers")
                var_req_data = var_cmd_output_utf8_jsons.get("data")
            
            print ( "var_req_status : ", var_req_status)
            
            if (var_req_status != '202 Accepted'):
                var_opc_req_id = var_req_header.get("opc-request-id")
                var_opc_req_message = var_req_data.get("message")

                # print ("var_opc_req_id if not 202 : ",var_opc_req_id)
                # print ("var_opc_req_message if not 202 : ",var_opc_req_message)
            elif (var_req_status == '202 Accepted'):
                var_opc_req_id = var_req_header.get("opc-request-id")
                var_opc_wrk_req_id = var_req_header.get("opc-work-request-id")
                


            print ("var_req_status : {0} , var_opc_req_id : {1} , var_opc_wrk_req_id : {2}, var_opc_req_message : {3} ".format(var_req_status,var_opc_req_id,var_opc_wrk_req_id,var_opc_req_message))

    except Exception as e:
        message = "Exception in commonutils.exec_api_cmd_with_status_output, Unable to execute API {0} - {1} - {2}".format(cmd,e,traceback.print_exc())
        print_warn ("{0}".format(message))


def write_to_file (var_filename, var_info_to_write):
    '''Procedure to WRITE Information into a FILE '''
    try :
        with open(var_filename, 'w') as jsonf:
            jsonf.write(json.dumps(var_info_to_write, indent=4))
    
    except Exception as e:
        message = "Exception in commonutils.write_to_file, : {0}".format(e)
        print_warn ("{0}".format(message))


def get_csv_entry_cnt (config_filename):
    '''Function to return the count of entries in a csv file (accepts csv file as argument) '''
    try :
        var_resize_pod_count = 0
        with open('%s'%(config_filename), 'r') as file: 
            reader = csv.DictReader(file, skipinitialspace=True)
            for row in reader:
                var_resize_pod_count +=1

        return (int(var_resize_pod_count))
    
    except Exception as e:
        message = "Exception in commonutils.get_csv_entry_cnt, : {0}".format(e)
        print_warn ("{0}".format(message))

def get_internalScheduleActivity_fliprt_template (var_pod_name, var_pod_ocid,var_pod_host_to_reboot):
    '''Function to TEMPLATIZE the internalScheduleActivity file that is used for POD VM Reboot accepts : 5 Parameters, returns : internalScheduleActivity Object with Values '''
    try :

        var_internalScheduleActivity = {}

        now = datetime.utcnow()
        # curr_ts = today_dt_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        var_maint_start_ts_next_2 = now + timedelta(minutes=2)
        var_maint_start_ts = var_maint_start_ts_next_2.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        globalvariables.glbl_maint_start_ts = var_maint_start_ts


        with open(globalvariables.glbl_cfg_env_internal_scheduled_activity_fliprt_file, 'r') as jsonf:
            var_internalScheduleActivity = json.load(jsonf)

        var_internalScheduleActivity["displayName"] = ("VM_reboot_activity_on_pod_{0}".format(var_pod_name))
        var_internalScheduleActivity["type"] = "MAINTENANCE"
        var_internalScheduleActivity["fusionEnvironmentId"] = var_pod_ocid

        var_jsondata_actions = var_internalScheduleActivity.get("actions")
        for var_jsondata_action in var_jsondata_actions:
            var_jsondata_action["targetHostNames"] = var_pod_host_to_reboot
            var_jsondata_action["actionType"] = globalvariables.glbl_action
            var_jsondata_action["mode"] = "COLD"
            var_jsondata_action["description"] = ("VM_reboot_activity_on_pod_{0}".format(var_pod_name))
            
        var_internalScheduleActivity["timeScheduledStart"] = var_maint_start_ts
        var_internalScheduleActivity["cmLink"] = globalvariables.glbl_fliprt_cm_jira
        
        if (var_internalScheduleActivity):
            return (var_internalScheduleActivity)

        print (" Will now proceed to SUBMIT the REBOOT of selected VMs for the POD .....")

    except Exception as e:
        message = "Exception in commonutils.get_internalScheduleActivity_fliprt_template while templatizing internalScheduledActivity, {0}".format(e)
        print_warn ("{0}".format(message))

# def get_pod_vm_reboot_info_fliprt_template (var_pod_name, var_pod_ocid,var_pod_host_to_reboot,var_vm_type,var_cmLink):
#     '''Function to TEMPLATIZE the internalScheduleActivity file that is used for POD VM Reboot accepts : 4 Parameters, returns : internalScheduleActivity Object with Values 
#         ALSO REFET TO --> globalvariables.glbl_fliprt_pod_vm_reboot_info
#     '''
#     try :
        
#         var_pod_vm_reboot_info = {}

#         with open(globalvariables.glbl_cfg_env_internal_scheduled_activity_file, 'r') as jsonf:
#             var_internalScheduleActivity = json.load(jsonf)

#         var_internalScheduleActivity["displayName"] = ("reboot_{0}_VM_on_pod_{1}".format(var_vm_type, var_pod_name))
#         var_internalScheduleActivity["type"] = "MAINTENANCE"
#         var_internalScheduleActivity["fusionEnvironmentId"] = var_pod_ocid

#         var_jsondata_actions = var_internalScheduleActivity.get("actions")
#         for var_jsondata_action in var_jsondata_actions:
#             var_jsondata_action["targetHostNames"] = var_pod_host_to_reboot
#             var_jsondata_action["actionType"] = "COMPUTE_REBOOT"
#             var_jsondata_action["mode"] = "COLD"
#             var_jsondata_action["description"] = ("VM_reboot_on_pod_{0}".format(var_pod_name))
            
#         var_internalScheduleActivity["timeScheduledStart"] = ""
#         var_internalScheduleActivity["cmLink"] = var_cmLink
        
#         print ("------>>>>>> var_internalScheduleActivity : {0}".format(var_internalScheduleActivity))

#         if (var_internalScheduleActivity):
#             return (var_internalScheduleActivity)


#     except Exception as e:
#         message = "Exception in commonutils.get_pod_vm_reboot_info_fliprt_template while templatizing internalScheduledActivity, {0}".format(e)
#         print_warn ("{0}".format(message))


def get_select_pod_vm_for_reboot (var_pod_region, var_pod_name, var_pod_ocid,var_pod_vms_inst_lst):
    '''This procedure is used to select the POD VM for REBOOTING '''
    try :

        var_selected_pod_vm_for_reboot = ""
        var_selected_pod_vms_for_reboot_list = []
        var_valid_VM = True

        print_info("{0}".format(""))
        # while (var_selected_pod_vm_for_reboot not in var_pod_vms_inst_lst):
        var_selected_pod_vm_for_reboot = input(
            "SELECT a POD VM to be REBOOTED or COMMA ',' seperated multiple VM list or ALL for all the PODs or EXIT to exit the Program : ")

        # print ("Select POD for scaleout is : ", var_get_geoRegion_pod_for_scaleout)
        if (var_selected_pod_vm_for_reboot.upper() == 'ALL'):
            print("All the POD VMs have been selected for REBOOTING...")
            var_selected_pod_vms_for_reboot_list = var_pod_vms_inst_lst

        elif (var_selected_pod_vm_for_reboot.upper() == 'EXIT'):
            print("Selected EXIT, exiting the program ....")
            exit(1)

        else:
            var_selected_pod_vms_for_reboot_list = var_selected_pod_vm_for_reboot.split(",")
        
        print ("----- Selected POD VMs for REBOOT : ----- ")
        for var_selected_pod_vm_for_reboot_list in var_selected_pod_vms_for_reboot_list:
            print (var_selected_pod_vm_for_reboot_list)

        print ("len : {0}".format(len(var_pod_vms_inst_lst)))
        print ("lenn : {0}".format(len(var_selected_pod_vms_for_reboot_list)))

        var_cmLink = "https://cm jira ticket"
        get_internalScheduleActivity_template (var_pod_name, var_pod_ocid,var_selected_pod_vms_for_reboot_list,var_cmLink)

    except Exception as e:
        message = "Exception in commonutils.get_select_pod_vm_for_reboot, checking for POD VM info {0}".format(e)
        print_warn ("{0}".format(message))

def get_pod_lifecycleinfo (var_pod_region, var_pod_name):
    '''This procedure is used to check lifecycleDetails and lifecycleState of a POD and return True or False '''
    try:

        print ("----- in get_pod_lifecycleinfo")
        var_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName={1}&lifecycleState="ACTIVE"'.format(var_pod_region,var_pod_name)
        # ocisdk1 = ocisdk.OciSdk("FAAAS_BOAT_PPD", None)
        var_pod_infos = oci_sdk.fetch_details_from_endpoint_url('GET',var_url) 

        if (var_pod_infos):
            print ("VALID POD in get_pod_lifecycleinfo")
            for var_pod_info in var_pod_infos:
                print ()
                var_pod_id = var_pod_info.get("id")
                var_pod_lifecycledetails = var_pod_info.get("lifecycleDetails")
                var_pod_lifecyclestate = var_pod_info.get("lifecycleState")
                
                
                if (var_pod_lifecycledetails == 'None' and var_pod_lifecyclestate == 'ACTIVE'):
                    print ("ACTIVE")
                    return (True, var_pod_lifecycledetails, var_pod_lifecyclestate, var_pod_id)
                else:
                    print ("INACTIVE")
                    return (False, var_pod_lifecycledetails, var_pod_lifecyclestate, var_pod_id)
        else:
            print_warn ("INVALID POD in get_pod_lifecycleinfo")
            return (False, var_pod_name, var_pod_region, "Invalid POD Name specified")

    except Exception as e:
        message = "Exception in commonutils.get_pod_lifecycleinfo, while checking POD lifecycleState {0}".format(e)
        print_warn ("{0}".format(message))

def get_pod_fliprt_lifecycleinfo (var_pod_region, var_pod_name,stack):
    '''This procedure is used to check lifecycleDetails and lifecycleState of a POD and return True or False '''
    try:
        # var_url = "{0}/fusionEnvironments?systemName={1}&lifecycleState=ACTIVE'.format(var_pod_region,var_pod_name)".format(faaas_api_url,)
        if stack == 'preprod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
        elif stack == 'prod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
        
        # print("faaas_api_url : ", faaas_api_url)
        var_url = "{0}internal/fusionEnvironments?systemName={1}".format(faaas_api_url,var_pod_name)
        
        # var_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName={1}&lifecycleState=ACTIVE'.format(var_pod_region,var_pod_name)
        # var_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName={1}'.format(var_pod_region,var_pod_name)
        # print ("--var_url",var_url)
        # ocisdk1 = ocisdk.OciSdk("FAAAS_BOAT_PPD", None)
        var_pod_infos = oci_sdk.fetch_details_from_endpoint_url('GET',var_url) 
        # print ("var_pod_infos : ",var_pod_infos)
        if (var_pod_infos):

            for var_pod_info1 in var_pod_infos:

                if (var_pod_info1.get("lifecycleState") == 'ACTIVE'):
                    return (True, var_pod_name, var_pod_region, var_pod_info1)
                    break;
                else:
                    print_warn ("INVALID POD lifecycleState in get_pod_fliprt_lifecycleinfo")
                    return (False, var_pod_name, var_pod_region, "Invalid POD lifecycleState")        
        else:
            print_warn ("INVALID POD in get_pod_fliprt_lifecycleinfo")
            return (False, var_pod_name, var_pod_region, "Invalid POD Name specified")

    except Exception as e:
        message = "Exception in commonutils.get_pod_fliprt_lifecycleinfo, while checking POD lifecycleState {0}".format(e)
        print_warn ("{0}".format(message))


def get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot):
    '''This procedure is used to get the POD VM info '''
    try :
        var_pod_vms_inst_lst=[]
        var_pod_vms_selected_inst_lst=[]
        vm_nums_lst = []
        vm_nums_int_lst = []
        user_vm_nums_int_input =[]

        var_host_found = False

        # print ("var_pod_host_to_reboot : ---- ",var_pod_host_to_reboot)
        if globalvariables.glbl_stack == 'preprod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
        elif globalvariables.glbl_stack == 'prod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)

        # https://prod-ops-fusionapps.us-ashburn-1.oci.oraclecloud.com/20191001/internal/fusionEnvironments/ocid1.fusionenvironment.oc1.iad.aaaaaaaaf26ydzqnms4bua343mlppk2cknyzdafw3o4vjahnd5c3ihdwmdta/podResourcesSummary
        var_pod_vm_url1='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments/{1}/podResourcesSummary'.format(var_pod_region,var_pod_ocid)
        var_pod_vm_url = '{0}internal/fusionEnvironments/{1}/podResourcesSummary'.format(faaas_api_url,var_pod_ocid)
        # print ("var_pod_vm_url1 : ",var_pod_vm_url1)
        # print ("var_pod_vm_url : ",var_pod_vm_url)
        
        # var_pod_vm_cmd="oci --profile oc1_facp_prd --auth security_token raw-request --http-method GET --target-uri '{0}'".format(var_pod_vm_url)
    
        var_pod_vm_infos = oci_sdk.fetch_details_from_endpoint_url('GET',var_pod_vm_url) 
        # print ("var_pod_vm_infos : {0}".format(var_pod_vm_infos))
        # print ("-->> len(var_pod_vm_infos) : {0}".format(len(var_pod_vm_infos)))
        
        if (var_pod_vm_infos):
            # print ("type(var_pod_vm_infos) : ",type(var_pod_vm_infos))
            # print ("VM_DISPLAYNAME ---- VM_RESOURCEID ---- VM_TIMECREATED ----- VM_STATE ")
            for var_pod_vm_info in var_pod_vm_infos:
                # print ("type(var_pod_vm_info) : ",type(var_pod_vm_info))
                if (var_pod_vm_info.get("resourceType") == 'node'):
                    # pprint (var_pod_vm_info)
                # if (var_pod_vm_info.get("resourceType") == 'node'):
                    # pprint (var_pod_vm_info.get("displayName"))

                    if (var_pod_vm_info.get("displayName") == var_pod_host_to_reboot):
                        var_host_found = True
                        # print ("-------------------- ",var_pod_vm_info.get("displayName"))
                        return (True, var_pod_vm_info)
                        # break; 
            
        # else:
        #     return (False, "INVALID POD provided")
        

    except Exception as e:
        message = "Exception in commonutils.get_pod_vm_fliprt_info, checking for POD VM info {0}".format(e)
        print_warn ("{0}".format(message))



def get_pod_info (var_pod_region, var_pod_name):
    '''This procedure is used to check if the POD Names in the csv file are VALID or NOT '''
    try :
        if globalvariables.glbl_stack == 'preprod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
        elif globalvariables.glbl_stack == 'prod':
            faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
            # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)

        var_pod_url='{0}/internal/fusionEnvironments?systemName={1}&&lifecycleState=ACTIVE'.format(faaas_api_url,var_pod_name)
        # var_pod_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName={1}&&lifecycleState=ACTIVE'.format(var_pod_region,var_pod_name)
        # oci --profile oc1_facp_prd --auth security_token raw-request --http-method GET --target-uri var_url
        # var_pod_url_cmd="oci --profile oc1_facp_prd --auth security_token raw-request --http-method GET --target-uri '{0}'".format(var_pod_url)
        var_pod_info_jsons = oci_sdk.fetch_details_from_endpoint_url('GET',var_pod_url)
        # print ("type(var_pod_info_jsons) : {0}".format(type(var_pod_info_jsons)))
        # print ("var_pod_info_jsons : {0}".format(var_pod_info_jsons))
        if (var_pod_info_jsons):
            var_pod_data = var_pod_info_jsons[0]
            # print ("var_pod_data : {0}".format(var_pod_data))  
            print ("-- VALID POD_Name : {0}".format(var_pod_name))
            # print ("-- get the POD OCID")
            var_pod_ocid = var_pod_data.get("id")
            print ("-- POD OCID is : {0}".format(var_pod_ocid))
            # print ("-- call the procedure to get the POD VMs List")
            return (True, var_pod_region,var_pod_name,var_pod_ocid)
            # get_pod_vm_info (var_pod_region,var_pod_name,var_pod_ocid)
        else:
            
            return (False, var_pod_region,var_pod_name,"INVALID POD Name")

    except Exception as e:
        message = "Exception in commonutils.get_pod_info, checking for POD info {0}".format(e)
        print_warn ("{0}".format(message))


def get_pod_name_from_csv (config_filename):
    '''This procedure is used to DISPLY POD_NAMEs from the csv file  '''
    '''This procedure also calls another procedure to check the validity of PODs'''
    try :
        with open('%s'%(config_filename),'r') as f:
            DictReader_obj = csv.DictReader(f)
            # print ("opened the file")
            failed_status_ctr = 0
            for item in DictReader_obj:
                print ("Pod Name is : {0} in Region : {1}".format(item["system_name"],item["pod_region"]))
                print ("Calling the procedure to check if the POD is VALID")

                var_pod_lifecycleinfo = get_pod_lifecycleinfo (item["pod_region"],item["system_name"])

                if (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[1] != item["system_name"]):
                    print ("This is a valid POD")
                    print ("Current POD lifecycleDetails : {0} and lifecycleState is : {1}".format(var_pod_lifecycleinfo[1],var_pod_lifecycleinfo[2]))
                    print ("We are GOOD to proceed with the Reboot Activity...")
                    var_pod_region = item["pod_region"]
                    var_pod_name = item["system_name"]
                    var_pod_lifecycledetails = var_pod_lifecycleinfo[1]
                    var_pod_lifecyclestate = var_pod_lifecycleinfo[2]
                    var_pod_ocid = var_pod_lifecycleinfo[3]

                    print ("POD REGION & NAME : {0} & {1} -- POD_OCID : {2}".format(var_pod_region,var_pod_name,var_pod_ocid))
                    get_pod_vm_info (var_pod_region, var_pod_name, var_pod_ocid)
                    

                elif (not var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[1] != item["system_name"]):
                    print_warn ("Current POD lifecycleDetails : {0} and lifecycleState is : {1}".format(var_pod_lifecycleinfo[1],var_pod_lifecycleinfo[2]))
                    print_warn ("We are NOT GOOD to proceed with the Reboot Activity...")

                elif (not var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[1] == item["system_name"]):
                    print_warn ("This is NOT a valid POD")

                # x = input ("asdasdasdasdasd")

                print ("-----------------------------------------------------------------")
    except Exception as e:
        message = "Exception in commonutils.get_pod_name_from_csv, checking for POD info {0}".format(e)
        print_warn ("{0}".format(message))

def convert_csv_to_dict (var_input_flip_rt_csv_file):
   
    maindict = dict()
    count = 0
    with open (var_input_flip_rt_csv_file) as csv_file:
        next(csv_file)

        for line in csv_file:
            vmname = line.split(",")[0]
            pod_name = line.split(",")[2]
            region = line.split(",")[3]
            # print(vmname)
            # print(pod_name)
            # print(region)
            if pod_name in maindict:
                maindict[pod_name]['vm_list'].append(vmname)
                # print(maindict)
                # input()
            else:
                vmlist = []
                maindict[pod_name] = dict()
                maindict[pod_name]['region'] = region
                vmlist.append(vmname)
                maindict[pod_name]['vm_list'] = vmlist
                # print(maindict)
                # input()
    # pprint(maindict)
    return (maindict)

def get_pod_info_from_fliprt_csv (config_filename,stack):
    '''This procedure is used to DISPLY POD_NAMEs from the csv file  '''
    '''This procedure also calls another procedure to check the validity of PODs'''
    try :
        
        var_valid_pod_vm_infos_for_reboot_lst = []
        var_invalid_pod_vm_infos_for_reboot_lst = []

        var_valid_pod_vm = True



        # var_fliprt_valid_pod_vm_reboot_info = {
        #                     "incident_jira" : "",
        #                     "data_center" : "",
        #                     "pod_name": "",
        #                     "pod_ocid" : "",
        #                     "pod_lifecyclestate" : "",
        #                     "host_name" :"",
        #                     "vm_type" : "",
        #                     "host_id" : "",
        #                     "host_state" : "",
        #                     "cm_jira" : "",
        #                     "maint_file_name" : "",
        #                     "maint_cmd" : "",
        #                     "submit_time" : "",
        #                     "submitter" : "",
        #                     "opc_request_id" : "",
        #                     "fusion_work_request_id" : "",
        #                     "request_start_time" : "",
        #                     "request_status" : "",
        #                     "request_end_time" : ""
        #                     }
                
        # var_fliprt_invalid_pod_vm_reboot_info = {
        #                     "incident_jira" : "",
        #                     "data_center" : "",
        #                     "pod_name": "",
        #                     "pod_ocid" : "",
        #                     "pod_lifecyclestate" : "",
        #                     "host_name" :"",
        #                     "vm_type" : "",
        #                     "host_id" : "",
        #                     "host_state" : "",
        #                     "cm_jira" : "",
        #                     "maint_file_name" : "",
        #                     "maint_cmd" : "",
        #                     "submit_time" : "",
        #                     "submitter" : "",
        #                     "opc_request_id" : "",
        #                     "request_code" : "",
        #                     "request_nessage" : "",
        #                     }
        
        print ("************** initialized **************")
        var_pod_info_dict = convert_csv_to_dict (config_filename)

        
        # with open('%s'%(config_filename),'r') as f:
        # with open(config_filename, mode="r", encoding="utf-8-sig") as f:
        #     DictReader_obj = csv.DictReader(f)
        #     # print ("opened the file")

        for pod, value in var_pod_info_dict.items():
            
            # print (type(pod))
            print ("POD is : ",pod)
            # print ("value is : ",value)

            var_fliprt_valid_pod_vm_reboot_info = {
                                "incident_jira" : "",
                                "data_center" : "",
                                "pod_name": "",
                                "pod_ocid" : "",
                                "pod_lifecyclestate" : "",
                                "host_name" :[],
                                "vm_type" : "",
                                "host_id" : "",
                                "host_state" : "",
                                "cm_jira" : "",
                                "maint_file_name" : "",
                                "maint_cmd" : "",
                                "submit_time" : "",
                                "submitter" : "",
                                "opc_request_id" : "",
                                "fusion_work_request_id" : "",
                                "timeAccepted" : "",
                                "timeStarted" : "",
                                "timeFinished" : "",
                                "percentComplete" : "",
                                "completionCode" : "",
                                "completionMessage" : "",
                                }
                    
                    
            var_fliprt_invalid_pod_vm_reboot_info = {
                        "incident_jira" : "",
                        "data_center" : "",
                        "pod_name": "",
                        "pod_lifecyclestate" : "",
                        "host_name" :[],
                        "cm_jira" : "",
                        "reason" : ""
                        }
            
            tmp_pod_valid_hosts_lst = []
            tmp_pod_invalid_hosts_lst =[]

            # print (value.get("region"))
            # print (value.get("vm_list"))
            var_pod_name = pod
            var_pod_region = value.get("region")
            var_pod_hosts_to_reboot = value.get("vm_list")
            print ("Pod Name is : {0} in Region : {1}".format(var_pod_name, var_pod_region))
            print ("Calling the procedure to check if the POD is VALID")


            globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))
            globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_invalid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))

            var_pod_lifecycleinfo = get_pod_fliprt_lifecycleinfo (var_pod_region,var_pod_name,globalvariables.glbl_stack)
            # print ("returned pod lifecycle : ",var_pod_lifecycleinfo)
            # var_pod_region = item["Datacenter"]
            # var_pod_name = item["POD"]
            # var_pod_host_to_reboot = item["Host_Name"]

            if (var_pod_lifecycleinfo[0]):
                var_valid_pod = True
                print ("POD is VALID & ACTIVE, proceed with the rest of activities")
                var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
                var_pod_lifecyclestate = var_pod_lifecycleinfo[3].get("lifecycleState")
                var_pod_lifecycledetails = var_pod_lifecycleinfo[3].get("lifecycleDetails")
                if (var_pod_lifecycleinfo[3].get("lifecycleDetails") == 'None'):
                    var_valid_pod = True
                    # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails = None, proceed with the rest of activities")
                    # pprint (var_pod_lifecycleinfo[3])
                    var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
                    var_pod_lifecyclestate = var_pod_lifecycleinfo[3].get("lifecycleState")
                    var_pod_lifecycledetails = var_pod_lifecycleinfo[3].get("lifecycleDetails")
                    # print ("var_pod_ocid : ",var_pod_ocid)
                    for var_pod_host_to_reboot in var_pod_hosts_to_reboot:
                        print_info ("----- calling to validate host : {0}".format(var_pod_host_to_reboot))
                        var_pod_vm_fliprt_info = get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)  
                        # print ("------------------------")
                        # print (var_pod_vm_fliprt_info)
                        # print ("------------------------")

                        if (var_pod_vm_fliprt_info):
                            var_valid_pod = True
                            # print ("HOST Name provided is VALID")
                            # print (var_pod_vm_fliprt_info[1].get("displayName"))

                            var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                            var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_region
                            var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_name
                            var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_ocid
                            var_fliprt_valid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
                            tmp_pod_valid_hosts_lst.append(var_pod_host_to_reboot)

                            var_vm_displayname = var_pod_vm_fliprt_info[1].get("displayName")
                            var_host_id = var_pod_vm_fliprt_info[1].get("displayName")
                            # initializing substrings
                            sub1 = ".node-"
                            sub2 = ".node-"
                            
                            var_vm_displayname_oper = var_vm_displayname
                            var_vm_displayname_oper=var_vm_displayname_oper.replace(sub1,"*")
                            var_vm_displayname_oper=var_vm_displayname_oper.replace(sub2,"*")
                            re=var_vm_displayname_oper.split("*")
                            var_vm_type=re[1]
                            
                            var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_vm_type
                            var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_pod_vm_fliprt_info[1].get("resourceId")
                            var_fliprt_valid_pod_vm_reboot_info["host_state"]= var_pod_vm_fliprt_info[1].get("state")
                            var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira

                            # print ("var_fliprt_valid_pod_vm_reboot_info ----> ",var_fliprt_valid_pod_vm_reboot_info)
                            # var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)
                            # print ("VALID POD List : ----> ",var_valid_pod_vm_infos_for_reboot_lst)
                    
                        else:
                            var_valid_pod = False
                            # print ("HOST Name provided is INVALID")
                            # # print (var_pod_vm_fliprt_info[1])
                            print ("Populate the INVALID POD Object and update the INVALID_LIST file 1")
                            var_reason = "HOST Name provided is INVALID"
                            tmp_pod_invalid_hosts_lst.append(var_pod_host_to_reboot)
                            print (var_reason)
                            var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                            var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                            var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                            var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
                            # var_fliprt_invalid_pod_vm_reboot_info["host_name"].append(var_pod_host_to_reboot)
                            var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
                            var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason
                            
                    
                    # print ("")
                    # print ("------- tmp_pod_valid_hosts_lst -----",tmp_pod_valid_hosts_lst)
                    for i in range(0,len(tmp_pod_valid_hosts_lst)):
                        var_fliprt_valid_pod_vm_reboot_info["host_name"].append(tmp_pod_valid_hosts_lst[i])
                    # print ("")
                    # # print (" ---------- POD VALID Dictionary is --------- : ", var_fliprt_valid_pod_vm_reboot_info)
                    # print ("")

                    if (var_fliprt_valid_pod_vm_reboot_info.get("incident_jira")):
                        # print ("infor for VALID POD ",var_fliprt_valid_pod_vm_reboot_info.get("incident_jira"))
                        var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)

                else:
                    var_valid_pod = False
                    # print (var_pod_vm_fliprt_info[1])
                    # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails is NOT None, CANNOT proceed with the rest of activities")
                    print ("Populate the INVALID POD Object and update the INVALID_LIST file 2")
                    var_reason = "lifecycleDetails  is {0}, cannot proceed !!!".format (var_pod_lifecycledetails)
                    print (var_reason)
                    var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                    var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                    var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                    var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
                    var_fliprt_invalid_pod_vm_reboot_info["host_name"] = var_pod_hosts_to_reboot
                    var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
                    var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason
                
            else:
                var_valid_pod = False
                # print ("POD is NOT GOOD & NOT VALID, CANNOT proceed with the rest of activities")
                print ("Populate the INVALID POD Object and update the INVALID_LIST file 3")
                var_reason = "POD Name is INVALID"
                print (var_reason)
                var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
                var_fliprt_invalid_pod_vm_reboot_info["host_name"]= var_pod_hosts_to_reboot
                var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
                var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason
                
            

            # if (not var_valid_pod) :
                
            #     # print ("in the false")
            #     # print (var_pod_vm_fliprt_info[1])
            #     # print (var_pod_vm_fliprt_info[1])
            #     # print ("------+++++++")
            #     # if (var_pod_vm_fliprt_info[1]):
            #     #     var_reason = var_pod_vm_fliprt_info[1]
            #     # elif (var_pod_vm_fliprt_info[1]):
            #     #     var_reason = var_pod_vm_fliprt_info[1]
            #     # else:
            #     # var_reason = "POD is NOT GOOD & NOT VALID & HOST Name is INVALID, CANNOT proceed with the rest of activities"

            #     # print ("all INVALID Info has been provided")

            #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
            #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
            #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
            #     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
            #     var_fliprt_invalid_pod_vm_reboot_info["host_name"].append(var_pod_host_to_reboot)
            #     var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
            #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason
                

            print ("")
            # print ("------- tmp_pod_invalid_hosts_lst -----",tmp_pod_invalid_hosts_lst)
            for i in range (0,len(tmp_pod_invalid_hosts_lst)):
                var_fliprt_invalid_pod_vm_reboot_info["host_name"].append(tmp_pod_invalid_hosts_lst[i])
                # print ("var_fliprt_invalid_pod_vm_reboot_info *******",var_fliprt_invalid_pod_vm_reboot_info)
            # print ("")
            # print (" ---------- POD INVALID Dictionary is --------- : ", var_fliprt_invalid_pod_vm_reboot_info)
            # print ("")


            if (var_fliprt_invalid_pod_vm_reboot_info.get("incident_jira")):
                var_invalid_pod_vm_infos_for_reboot_lst.append(var_fliprt_invalid_pod_vm_reboot_info)
                                
            # else:
            #     print ("")
            #     # pprint (var_fliprt_valid_pod_vm_reboot_info)

        # sach = input ("check and proceed...")
        # # print ("VALID POD List : ",var_valid_pod_vm_infos_for_reboot_lst)

        # globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))
        # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
        write_to_file (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file, var_valid_pod_vm_infos_for_reboot_lst)


        # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
        write_to_file (globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file, var_invalid_pod_vm_infos_for_reboot_lst)

        print (" ---------------------------- ALL PODs Processing END ---------------------------- ")

            #########################################
            # for item in DictReader_obj:
            #     print ("-------------------------------------------------------------------------------------------------------")

                
            #     var_pod_lifecycleinfo = get_pod_fliprt_lifecycleinfo (item["Datacenter"],item["POD"],stack)
            #     # print ("returned as : ",var_pod_lifecycleinfo )
            #     # print ("returned back")
            #     # # print (var_pod_lifecycleinfo.get("systemName"))
            #     # print ("returned back1")
            #     # ======================================================================================================
            #     if (var_pod_lifecycleinfo[0]):
            #         print ("POD is VALID & ACTIVE, proceed with the rest of activities")
            #         if (var_pod_lifecycleinfo[3].get("lifecycleDetails") == 'None'):
            #             # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails = None, proceed with the rest of activities")
            #             # pprint (var_pod_lifecycleinfo[3])
            #             var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
            #             var_pod_lifecyclestate = var_pod_lifecycleinfo[3].get("lifecycleState")

            #             var_pod_vm_fliprt_info = get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
            #             # print ("var_pod_vm_fliprt_info ***",var_pod_vm_fliprt_info)

            #             if (var_pod_vm_fliprt_info):
            #                 var_valid_pod = True
            #                 # print ("HOST Name provided is VALID")
            #                 # print (var_pod_vm_fliprt_info[1].get("displayName"))

            #                 var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
            #                 var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_region
            #                 var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_name
            #                 var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_ocid
            #                 var_fliprt_valid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
            #                 var_fliprt_valid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot

            #                 var_vm_displayname = var_pod_vm_fliprt_info[1].get("displayName")
            #                 var_host_id = var_pod_vm_fliprt_info[1].get("displayName")
            #                 # initializing substrings
            #                 sub1 = ".node-"
            #                 sub2 = ".node-"
                            
            #                 var_vm_displayname_oper = var_vm_displayname
            #                 var_vm_displayname_oper=var_vm_displayname_oper.replace(sub1,"*")
            #                 var_vm_displayname_oper=var_vm_displayname_oper.replace(sub2,"*")
            #                 re=var_vm_displayname_oper.split("*")
            #                 var_vm_type=re[1]
                            
            #                 var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_vm_type
            #                 var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_pod_vm_fliprt_info[1].get("resourceId")
            #                 var_fliprt_valid_pod_vm_reboot_info["host_state"] = var_pod_vm_fliprt_info[1].get("state")
            #                 var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira

                            
            #                 var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)
            #                 # print ("VALID POD List : ",var_valid_pod_vm_infos_for_reboot_lst)
                            
            #             else:
            #                 var_valid_pod = False
            #                 # print ("HOST Name provided is INVALID")
            #                 # # print (var_pod_vm_fliprt_info[1])
            #                 # print ("Populate the INVALID POD Object and update the INVALID_LIST file 1")
            #                 var_reason = "HOST Name provided is INVALID"

            #         else:
            #             var_valid_pod = False
            #             # print (var_pod_vm_fliprt_info[1])
            #             # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails is NOT None, CANNOT proceed with the rest of activities")
            #             # print ("Populate the INVALID POD Object and update the INVALID_LIST file 2")
            #             var_reason = "lifecycleDetails  is INVALID"
                
            #     else:
            #         var_valid_pod = False
            #         # print ("POD is NOT GOOD & NOT VALID, CANNOT proceed with the rest of activities")
            #         # print ("Populate the INVALID POD Object and update the INVALID_LIST file 3")
            #         var_reason = "POD Name is INVALID"
                
            #     if (not var_valid_pod) :
                    
            #         # print ("in the false")
            #         # print (var_pod_vm_fliprt_info[1])
            #         # print (var_pod_vm_fliprt_info[1])
            #         # print ("------+++++++")
            #         # if (var_pod_vm_fliprt_info[1]):
            #         #     var_reason = var_pod_vm_fliprt_info[1]
            #         # elif (var_pod_vm_fliprt_info[1]):
            #         #     var_reason = var_pod_vm_fliprt_info[1]
            #         # else:
            #         # var_reason = "POD is NOT GOOD & NOT VALID & HOST Name is INVALID, CANNOT proceed with the rest of activities"

            #         # print ("all INVALID Info has been provided")

            #         var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
            #         var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
            #         var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
            #         var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
            #         var_fliprt_invalid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot
            #         var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
            #         var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason

            #         # print ("var_fliprt_invalid_pod_vm_reboot_info *******",var_fliprt_invalid_pod_vm_reboot_info)
            #         var_invalid_pod_vm_infos_for_reboot_lst.append(var_fliprt_invalid_pod_vm_reboot_info)
                            
            #     else:
            #         print ("")
            #         # pprint (var_fliprt_valid_pod_vm_reboot_info)

            # sach = input ("check and proceed...")
            # # print ("VALID POD List : ",var_valid_pod_vm_infos_for_reboot_lst)

            # globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))
            # # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
            # write_to_file (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file, var_valid_pod_vm_infos_for_reboot_lst)


            # # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
            # write_to_file (globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file, var_invalid_pod_vm_infos_for_reboot_lst)

        # return (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file,globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file)




                # ======================================================================================================
                # if (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] != item["POD"]):
                #     print_warn ("------- INVALID POD Name specified ------- ")
                #     print_warn ("------- Cannot proceed with VM Reboot ------")

                #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
                
                #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID POD Name specified"

                #     var_valid_pod_vm = False
                #     # break;
                
                # elif (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] == item["POD"] and var_pod_lifecycleinfo[3].get("lifecycleState") != 'ACTIVE'):
                #     print_warn ("------- INVALID lifecycleState, some LCM Activity inProgress on POD")
                #     print_warn ("------- Cannot proceed with VM Reboot ------")
                #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecycleinfo.get("lifecycleDetails")
                #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID lifecycleDetails, some LCM Activity inProgress on POD"

                #     var_valid_pod_vm = False
                #     # break;

                # elif (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] == item["POD"] and var_pod_lifecycleinfo[3].get("lifecycleDetails") != 'None'):
                #     print_warn ("------- INVALID lifecycleDetails, some LCM Activity inProgress on POD")
                #     print_warn ("------- Cannot proceed with VM Reboot ------")
                #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
                #     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecycleinfo.get("lifecycleDetails")
                #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID lifecycleDetails, some LCM Activity inProgress on POD"

                #     var_valid_pod_vm = False
                #     # break;

                # elif (var_pod_lifecycleinfo):
                #     print ("POD is VALID, lifecycleState is AVAILABLE and lifecycleDetails is None ")
                #     print ("We can proceed to get the VM Related information")
                    
                #     var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
                #     var_pod_vm_fliprt_info = get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
                #     # var_pod_resource_digest = get_pod_resource_digest (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
                #     # saaa = input ("SACHINSSSS")
                #     # print ("---- var_pod_vm_fliprt_info ",var_pod_vm_fliprt_info)

                #     if (not var_pod_vm_fliprt_info):
                #         print_warn ("------- INVALID POD HOST Name specified -------")
                #         print_warn ("------- Cannot proceed with VM Reboot ------")
                #         var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                #         var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
                #         var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
                #         var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
                #         var_fliprt_invalid_pod_vm_reboot_info["host_name"] = "var_pod_host_to_reboot"
                #         var_fliprt_invalid_pod_vm_reboot_info["vm_type"] = "var_vm_type"
                #         var_fliprt_invalid_pod_vm_reboot_info["host_id"] = "var_host_id"
                #         var_fliprt_invalid_pod_vm_reboot_info["host_state"] = "host_state"
                #         var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID POD HOST Name specified"

                #         var_valid_pod_vm = False


                #         # var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = var_cmLink
                #         # var_fliprt_invalid_pod_vm_reboot_info["maint_file_name"] = "var_filename"
                #         # var_fliprt_invalid_pod_vm_reboot_info["maint_cmd"] = "var_exec_cmd"
                #         # var_fliprt_invalid_pod_vm_reboot_info["submit_time"] = "submit_time"
                #         # var_fliprt_invalid_pod_vm_reboot_info["submitter"] = ""

                #         # break;

                #     else:
                #         print ("POD & POD VM are in VALID State")
                #         print ("We can proceed to REBOOT the VM")
                #         var_vm_resource_id = var_pod_vm_fliprt_info.get("resourceId")
                #         var_vm_timecreated = var_pod_vm_fliprt_info.get("timeCreated")
                #         var_vm_displayname = var_pod_vm_fliprt_info.get("displayName")
                #         var_host_id = var_pod_vm_fliprt_info.get("resourceId")
                #         # initializing substrings
                #         sub1 = ".node-"
                #         sub2 = ".instance-"
                        
                #         var_vm_displayname_oper = var_vm_displayname
                #         var_vm_displayname_oper=var_vm_displayname_oper.replace(sub1,"*")
                #         var_vm_displayname_oper=var_vm_displayname_oper.replace(sub2,"*")
                #         re=var_vm_displayname_oper.split("*")
                #         var_vm_type=re[1]

                #         var_cmLink = 'https://jira-sd.mc1.oracleiaas.com/browse/CHANGE-0'
                #         print (" ------------- passing var_vm_displayname  -------------  : ",var_vm_displayname)
                #         var_internalScheduleActivity = get_internalScheduleActivity_fliprt_template (var_pod_name, var_pod_ocid,var_vm_displayname,var_vm_type,var_cmLink)

                #         # print ("var_internalScheduleActivity : {0}".format(var_internalScheduleActivity))
                #         # print ("Creating the internalScheduleActivity json file")

                #         var_filename = ("{}incident_{}_{}_{}_reboot.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira,var_pod_name,var_vm_type))
                #         print ("var_filename : {0}".format(var_filename))

                #         write_to_file (var_filename, var_internalScheduleActivity)
                #         print ("Created the internalScheduleActivity json file")

                #         print ("COMMAND to execute")
                #         if globalvariables.glbl_stack == 'preprod':
                #             faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
                #             # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
                #         elif globalvariables.glbl_stack == 'prod':
                #             faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
                #             # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)

                #         # oci --profile oc1_facp_prd --auth security_token raw-request --http-method POST --request-body file:///Users/ssirsi/schedule_reboot.json --target-uri 'https://prod-ops-fusionapps.us-ashburn-1.oci.oraclecloud.com/20191001/internalScheduledActivities'
                #         var_exec_cmd = ("oci --profile resize_oci_config --auth security_token raw-request --http-method POST --request-body file://{0} --target-uri '{1}/internalScheduledActivities'".format(var_filename, faaas_api_url))

                #         # print ("---- VM Info : ",var_pod_vm_fliprt_info)
                #         # print ("Collecting the VALID POD Info")
                        
                #         print ("")

                #         var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
                #         var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_region
                #         var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_name
                #         var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_ocid
                #         var_fliprt_valid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot
                #         var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_vm_type
                #         var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_host_id
                #         var_fliprt_valid_pod_vm_reboot_info["host_state"] = var_pod_vm_fliprt_info.get("state")
                #         var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = var_cmLink
                #         var_fliprt_valid_pod_vm_reboot_info["maint_file_name"] = var_filename
                #         var_fliprt_valid_pod_vm_reboot_info["maint_cmd"] = var_exec_cmd
                #         var_fliprt_valid_pod_vm_reboot_info["submit_time"] = globalvariables.glbl_maint_start_ts
                #         var_fliprt_valid_pod_vm_reboot_info["submitter"] = ""

                #         # print ("Done assigning the values")
                        
                #         var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)

                # if (var_valid_pod_vm == False) :
                #     var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = 'https://jira-sd.mc1.oracleiaas.com/browse/CHANGE-0'
                #     var_fliprt_invalid_pod_vm_reboot_info["maint_file_name"] = "var_filename"
                #     var_fliprt_invalid_pod_vm_reboot_info["maint_cmd"] = "var_exec_cmd"
                #     var_fliprt_invalid_pod_vm_reboot_info["submit_time"] = "submit_time"
                #     var_fliprt_invalid_pod_vm_reboot_info["submitter"] = ""

                #     # print ("====var_fliprt_invalid_pod_vm_reboot_info : ",var_fliprt_invalid_pod_vm_reboot_info)
                #     var_invalid_pod_vm_infos_for_reboot_lst.append(var_fliprt_invalid_pod_vm_reboot_info)

                    
                
            

        # print ("-------------------------------------------------------------------------------------------------------")
                
        # print_info ("--------------------- var_valid_pod_vm_infos_for_reboot {0}".format(var_valid_pod_vm_infos_for_reboot_lst))

      
        # print ("-----------------------------------------------------------------")
    except Exception as e:
        message = "Exception in commonutils.get_pod_info_from_fliprt_csv, checking for POD info {0}".format(e)
        print_warn ("{0}".format(message))



# # def get_pod_info_from_fliprt_csv (config_filename,stack):
#     '''This procedure is used to DISPLY POD_NAMEs from the csv file  '''
#     '''This procedure also calls another procedure to check the validity of PODs'''
#     try :
        
#         var_valid_pod_vm_infos_for_reboot_lst = []
#         var_invalid_pod_vm_infos_for_reboot_lst = []

#         var_valid_pod_vm = True



#         # var_fliprt_valid_pod_vm_reboot_info = {
#         #                     "incident_jira" : "",
#         #                     "data_center" : "",
#         #                     "pod_name": "",
#         #                     "pod_ocid" : "",
#         #                     "pod_lifecyclestate" : "",
#         #                     "host_name" :"",
#         #                     "vm_type" : "",
#         #                     "host_id" : "",
#         #                     "host_state" : "",
#         #                     "cm_jira" : "",
#         #                     "maint_file_name" : "",
#         #                     "maint_cmd" : "",
#         #                     "submit_time" : "",
#         #                     "submitter" : "",
#         #                     "opc_request_id" : "",
#         #                     "fusion_work_request_id" : "",
#         #                     "request_start_time" : "",
#         #                     "request_status" : "",
#         #                     "request_end_time" : ""
#         #                     }
                
#         # var_fliprt_invalid_pod_vm_reboot_info = {
#         #                     "incident_jira" : "",
#         #                     "data_center" : "",
#         #                     "pod_name": "",
#         #                     "pod_ocid" : "",
#         #                     "pod_lifecyclestate" : "",
#         #                     "host_name" :"",
#         #                     "vm_type" : "",
#         #                     "host_id" : "",
#         #                     "host_state" : "",
#         #                     "cm_jira" : "",
#         #                     "maint_file_name" : "",
#         #                     "maint_cmd" : "",
#         #                     "submit_time" : "",
#         #                     "submitter" : "",
#         #                     "opc_request_id" : "",
#         #                     "request_code" : "",
#         #                     "request_nessage" : "",
#         #                     }
        
#         print ("************** initialized **************")
#         # with open('%s'%(config_filename),'r') as f:
#         with open(config_filename, mode="r", encoding="utf-8-sig") as f:
#             DictReader_obj = csv.DictReader(f)
#             # print ("opened the file")
#             for item in DictReader_obj:
#                 print ("-------------------------------------------------------------------------------------------------------")

#                 var_fliprt_valid_pod_vm_reboot_info = {
#                             "incident_jira" : "",
#                             "data_center" : "",
#                             "pod_name": "",
#                             "pod_ocid" : "",
#                             "pod_lifecyclestate" : "",
#                             "host_name" :"",
#                             "vm_type" : "",
#                             "host_id" : "",
#                             "host_state" : "",
#                             "cm_jira" : "",
#                             "maint_file_name" : "",
#                             "maint_cmd" : "",
#                             "submit_time" : "",
#                             "submitter" : "",
#                             "opc_request_id" : "",
#                             "fusion_work_request_id" : "",
#                             "timeAccepted" : "",
#                             "timeStarted" : "",
#                             "timeFinished" : "",
#                             "percentComplete" : "",
#                             "completionCode" : "",
#                             "completionMessage" : "",
#                             }
                
                
#                 var_fliprt_invalid_pod_vm_reboot_info = {
#                             "incident_jira" : "",
#                             "data_center" : "",
#                             "pod_name": "",
#                             "pod_lifecyclestate" : "",
#                             "host_name" :"",
#                             "cm_jira" : "",
#                             "reason" : ""
#                             }
                
#                 print ("Pod Name is : {0} in Region : {1}".format(item["POD"],item["Datacenter"]))
#                 print ("Calling the procedure to check if the POD is VALID")

#                 # var_pod_lifecycleinfo = get_pod_lifecycleinfo (item["Datacenter"],item["POD"])
#                 # print (item)
#                 var_pod_region = item["Datacenter"]
#                 var_pod_name = item["POD"]
#                 var_pod_host_to_reboot = item["Host_Name"]

#                 globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))
#                 globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_invalid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))

                
#                 var_pod_lifecycleinfo = get_pod_fliprt_lifecycleinfo (item["Datacenter"],item["POD"],stack)
#                 # print ("returned as : ",var_pod_lifecycleinfo )
#                 # print ("returned back")
#                 # # print (var_pod_lifecycleinfo.get("systemName"))
#                 # print ("returned back1")
#                 # ======================================================================================================
#                 if (var_pod_lifecycleinfo[0]):
#                     print ("POD is VALID & ACTIVE, proceed with the rest of activities")
#                     if (var_pod_lifecycleinfo[3].get("lifecycleDetails") == 'None'):
#                         # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails = None, proceed with the rest of activities")
#                         # pprint (var_pod_lifecycleinfo[3])
#                         var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
#                         var_pod_lifecyclestate = var_pod_lifecycleinfo[3].get("lifecycleState")

#                         var_pod_vm_fliprt_info = get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
#                         # print ("var_pod_vm_fliprt_info ***",var_pod_vm_fliprt_info)

#                         if (var_pod_vm_fliprt_info):
#                             var_valid_pod = True
#                             # print ("HOST Name provided is VALID")
#                             # print (var_pod_vm_fliprt_info[1].get("displayName"))

#                             var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                             var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_region
#                             var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                             var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_ocid
#                             var_fliprt_valid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
#                             var_fliprt_valid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot

#                             var_vm_displayname = var_pod_vm_fliprt_info[1].get("displayName")
#                             var_host_id = var_pod_vm_fliprt_info[1].get("displayName")
#                             # initializing substrings
#                             sub1 = ".node-"
#                             sub2 = ".node-"
                            
#                             var_vm_displayname_oper = var_vm_displayname
#                             var_vm_displayname_oper=var_vm_displayname_oper.replace(sub1,"*")
#                             var_vm_displayname_oper=var_vm_displayname_oper.replace(sub2,"*")
#                             re=var_vm_displayname_oper.split("*")
#                             var_vm_type=re[1]
                            
#                             var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_vm_type
#                             var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_pod_vm_fliprt_info[1].get("resourceId")
#                             var_fliprt_valid_pod_vm_reboot_info["host_state"] = var_pod_vm_fliprt_info[1].get("state")
#                             var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira

                            
#                             var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)
#                             # print ("VALID POD List : ",var_valid_pod_vm_infos_for_reboot_lst)
                            
#                         else:
#                             var_valid_pod = False
#                             # print ("HOST Name provided is INVALID")
#                             # # print (var_pod_vm_fliprt_info[1])
#                             # print ("Populate the INVALID POD Object and update the INVALID_LIST file 1")
#                             var_reason = "HOST Name provided is INVALID"

#                     else:
#                         var_valid_pod = False
#                         # print (var_pod_vm_fliprt_info[1])
#                         # print ("POD is VALID & lifecycleState = ACTIVE & lifecycleDetails is NOT None, CANNOT proceed with the rest of activities")
#                         # print ("Populate the INVALID POD Object and update the INVALID_LIST file 2")
#                         var_reason = "lifecycleDetails  is INVALID"
                
#                 else:
#                     var_valid_pod = False
#                     # print ("POD is NOT GOOD & NOT VALID, CANNOT proceed with the rest of activities")
#                     # print ("Populate the INVALID POD Object and update the INVALID_LIST file 3")
#                     var_reason = "POD Name is INVALID"
                
#                 if (not var_valid_pod) :
                    
#                     # print ("in the false")
#                     # print (var_pod_vm_fliprt_info[1])
#                     # print (var_pod_vm_fliprt_info[1])
#                     # print ("------+++++++")
#                     # if (var_pod_vm_fliprt_info[1]):
#                     #     var_reason = var_pod_vm_fliprt_info[1]
#                     # elif (var_pod_vm_fliprt_info[1]):
#                     #     var_reason = var_pod_vm_fliprt_info[1]
#                     # else:
#                     # var_reason = "POD is NOT GOOD & NOT VALID & HOST Name is INVALID, CANNOT proceed with the rest of activities"

#                     # print ("all INVALID Info has been provided")

#                     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
#                     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecyclestate
#                     var_fliprt_invalid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot
#                     var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = globalvariables.glbl_fliprt_cm_jira
#                     var_fliprt_invalid_pod_vm_reboot_info["reason"] = var_reason

#                     # print ("var_fliprt_invalid_pod_vm_reboot_info *******",var_fliprt_invalid_pod_vm_reboot_info)
#                     var_invalid_pod_vm_infos_for_reboot_lst.append(var_fliprt_invalid_pod_vm_reboot_info)
                            
#                 else:
#                     print ("")
#                     # pprint (var_fliprt_valid_pod_vm_reboot_info)

#             sach = input ("check and proceed...")
#             # print ("VALID POD List : ",var_valid_pod_vm_infos_for_reboot_lst)

#             globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file = ("{0}incident_{1}_valid_pod_vms_for_reboot_list.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira))
#             # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
#             write_to_file (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file, var_valid_pod_vm_infos_for_reboot_lst)


#             # print ("----- var_valid_pod_vm_reboot_info_file : {0}".format(globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file))
#             write_to_file (globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file, var_invalid_pod_vm_infos_for_reboot_lst)

#         # return (globalvariables.var_valid_fliprt_pod_vm_infos_for_reboot_file,globalvariables.var_invalid_fliprt_pod_vm_infos_for_reboot_file)




#                 # ======================================================================================================
#                 # if (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] != item["POD"]):
#                 #     print_warn ("------- INVALID POD Name specified ------- ")
#                 #     print_warn ("------- Cannot proceed with VM Reboot ------")

#                 #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                 #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
                
#                 #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID POD Name specified"

#                 #     var_valid_pod_vm = False
#                 #     # break;
                
#                 # elif (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] == item["POD"] and var_pod_lifecycleinfo[3].get("lifecycleState") != 'ACTIVE'):
#                 #     print_warn ("------- INVALID lifecycleState, some LCM Activity inProgress on POD")
#                 #     print_warn ("------- Cannot proceed with VM Reboot ------")
#                 #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                 #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecycleinfo.get("lifecycleDetails")
#                 #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID lifecycleDetails, some LCM Activity inProgress on POD"

#                 #     var_valid_pod_vm = False
#                 #     # break;

#                 # elif (var_pod_lifecycleinfo[0] and var_pod_lifecycleinfo[2] == item["POD"] and var_pod_lifecycleinfo[3].get("lifecycleDetails") != 'None'):
#                 #     print_warn ("------- INVALID lifecycleDetails, some LCM Activity inProgress on POD")
#                 #     print_warn ("------- Cannot proceed with VM Reboot ------")
#                 #     var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                 #     var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
#                 #     var_fliprt_invalid_pod_vm_reboot_info["pod_lifecyclestate"] = var_pod_lifecycleinfo.get("lifecycleDetails")
#                 #     var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID lifecycleDetails, some LCM Activity inProgress on POD"

#                 #     var_valid_pod_vm = False
#                 #     # break;

#                 # elif (var_pod_lifecycleinfo):
#                 #     print ("POD is VALID, lifecycleState is AVAILABLE and lifecycleDetails is None ")
#                 #     print ("We can proceed to get the VM Related information")
                    
#                 #     var_pod_ocid = var_pod_lifecycleinfo[3].get("id")
#                 #     var_pod_vm_fliprt_info = get_pod_vm_fliprt_info (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
#                 #     # var_pod_resource_digest = get_pod_resource_digest (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot)
#                 #     # saaa = input ("SACHINSSSS")
#                 #     # print ("---- var_pod_vm_fliprt_info ",var_pod_vm_fliprt_info)

#                 #     if (not var_pod_vm_fliprt_info):
#                 #         print_warn ("------- INVALID POD HOST Name specified -------")
#                 #         print_warn ("------- Cannot proceed with VM Reboot ------")
#                 #         var_fliprt_invalid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                 #         var_fliprt_invalid_pod_vm_reboot_info["data_center"] = var_pod_region
#                 #         var_fliprt_invalid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                 #         var_fliprt_invalid_pod_vm_reboot_info["pod_ocid"] = "var_pod_ocid"
#                 #         var_fliprt_invalid_pod_vm_reboot_info["host_name"] = "var_pod_host_to_reboot"
#                 #         var_fliprt_invalid_pod_vm_reboot_info["vm_type"] = "var_vm_type"
#                 #         var_fliprt_invalid_pod_vm_reboot_info["host_id"] = "var_host_id"
#                 #         var_fliprt_invalid_pod_vm_reboot_info["host_state"] = "host_state"
#                 #         var_fliprt_invalid_pod_vm_reboot_info["reason"] = "INVALID POD HOST Name specified"

#                 #         var_valid_pod_vm = False


#                 #         # var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = var_cmLink
#                 #         # var_fliprt_invalid_pod_vm_reboot_info["maint_file_name"] = "var_filename"
#                 #         # var_fliprt_invalid_pod_vm_reboot_info["maint_cmd"] = "var_exec_cmd"
#                 #         # var_fliprt_invalid_pod_vm_reboot_info["submit_time"] = "submit_time"
#                 #         # var_fliprt_invalid_pod_vm_reboot_info["submitter"] = ""

#                 #         # break;

#                 #     else:
#                 #         print ("POD & POD VM are in VALID State")
#                 #         print ("We can proceed to REBOOT the VM")
#                 #         var_vm_resource_id = var_pod_vm_fliprt_info.get("resourceId")
#                 #         var_vm_timecreated = var_pod_vm_fliprt_info.get("timeCreated")
#                 #         var_vm_displayname = var_pod_vm_fliprt_info.get("displayName")
#                 #         var_host_id = var_pod_vm_fliprt_info.get("resourceId")
#                 #         # initializing substrings
#                 #         sub1 = ".node-"
#                 #         sub2 = ".instance-"
                        
#                 #         var_vm_displayname_oper = var_vm_displayname
#                 #         var_vm_displayname_oper=var_vm_displayname_oper.replace(sub1,"*")
#                 #         var_vm_displayname_oper=var_vm_displayname_oper.replace(sub2,"*")
#                 #         re=var_vm_displayname_oper.split("*")
#                 #         var_vm_type=re[1]

#                 #         var_cmLink = 'https://jira-sd.mc1.oracleiaas.com/browse/CHANGE-0'
#                 #         print (" ------------- passing var_vm_displayname  -------------  : ",var_vm_displayname)
#                 #         var_internalScheduleActivity = get_internalScheduleActivity_fliprt_template (var_pod_name, var_pod_ocid,var_vm_displayname,var_vm_type,var_cmLink)

#                 #         # print ("var_internalScheduleActivity : {0}".format(var_internalScheduleActivity))
#                 #         # print ("Creating the internalScheduleActivity json file")

#                 #         var_filename = ("{}incident_{}_{}_{}_reboot.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira,var_pod_name,var_vm_type))
#                 #         print ("var_filename : {0}".format(var_filename))

#                 #         write_to_file (var_filename, var_internalScheduleActivity)
#                 #         print ("Created the internalScheduleActivity json file")

#                 #         print ("COMMAND to execute")
#                 #         if globalvariables.glbl_stack == 'preprod':
#                 #             faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
#                 #             # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
#                 #         elif globalvariables.glbl_stack == 'prod':
#                 #             faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
#                 #             # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)

#                 #         # oci --profile oc1_facp_prd --auth security_token raw-request --http-method POST --request-body file:///Users/ssirsi/schedule_reboot.json --target-uri 'https://prod-ops-fusionapps.us-ashburn-1.oci.oraclecloud.com/20191001/internalScheduledActivities'
#                 #         var_exec_cmd = ("oci --profile resize_oci_config --auth security_token raw-request --http-method POST --request-body file://{0} --target-uri '{1}/internalScheduledActivities'".format(var_filename, faaas_api_url))

#                 #         # print ("---- VM Info : ",var_pod_vm_fliprt_info)
#                 #         # print ("Collecting the VALID POD Info")
                        
#                 #         print ("")

#                 #         var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = globalvariables.glbl_fliprt_incident_jira
#                 #         var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_region
#                 #         var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_name
#                 #         var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_ocid
#                 #         var_fliprt_valid_pod_vm_reboot_info["host_name"] = var_pod_host_to_reboot
#                 #         var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_vm_type
#                 #         var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_host_id
#                 #         var_fliprt_valid_pod_vm_reboot_info["host_state"] = var_pod_vm_fliprt_info.get("state")
#                 #         var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = var_cmLink
#                 #         var_fliprt_valid_pod_vm_reboot_info["maint_file_name"] = var_filename
#                 #         var_fliprt_valid_pod_vm_reboot_info["maint_cmd"] = var_exec_cmd
#                 #         var_fliprt_valid_pod_vm_reboot_info["submit_time"] = globalvariables.glbl_maint_start_ts
#                 #         var_fliprt_valid_pod_vm_reboot_info["submitter"] = ""

#                 #         # print ("Done assigning the values")
                        
#                 #         var_valid_pod_vm_infos_for_reboot_lst.append(var_fliprt_valid_pod_vm_reboot_info)

#                 # if (var_valid_pod_vm == False) :
#                 #     var_fliprt_invalid_pod_vm_reboot_info["cm_jira"] = 'https://jira-sd.mc1.oracleiaas.com/browse/CHANGE-0'
#                 #     var_fliprt_invalid_pod_vm_reboot_info["maint_file_name"] = "var_filename"
#                 #     var_fliprt_invalid_pod_vm_reboot_info["maint_cmd"] = "var_exec_cmd"
#                 #     var_fliprt_invalid_pod_vm_reboot_info["submit_time"] = "submit_time"
#                 #     var_fliprt_invalid_pod_vm_reboot_info["submitter"] = ""

#                 #     # print ("====var_fliprt_invalid_pod_vm_reboot_info : ",var_fliprt_invalid_pod_vm_reboot_info)
#                 #     var_invalid_pod_vm_infos_for_reboot_lst.append(var_fliprt_invalid_pod_vm_reboot_info)

                    
                
            

#         # print ("-------------------------------------------------------------------------------------------------------")
                
#         # print_info ("--------------------- var_valid_pod_vm_infos_for_reboot {0}".format(var_valid_pod_vm_infos_for_reboot_lst))

      
#         print ("-----------------------------------------------------------------")
#     except Exception as e:
#         message = "Exception in commonutils.get_pod_info_from_fliprt_csv, checking for POD info {0}".format(e)
#         print_warn ("{0}".format(message))



def disp_fliprt_valid_pod_vms_for_reboot (var_file):
    try:
        with open(var_file, 'r') as jsonf:
            var_pod_vms_for_reboot = json.load(jsonf)
        
        # print ("**********************",var_pod_vms_for_reboot)
        
        mytable= PrettyTable(['jira', 'data_center', 'pod_name', 'host_name', 'vm_type', 'host_state','submit_time'])

        for var_pod_vm_for_reboot in var_pod_vms_for_reboot:
            # print ("var_pod_vms_for_reboot --> {0}".format(var_pod_vm_for_reboot))
            var_jira = var_pod_vm_for_reboot.get("incident_jira")
            var_region = var_pod_vm_for_reboot.get("data_center")
            var_pod = var_pod_vm_for_reboot.get("pod_name")
            var_host = var_pod_vm_for_reboot.get("host_name")
            var_vmtype = var_pod_vm_for_reboot.get("vm_type")
            print_info ("{0} -- {1} -- {2} -- {3} -- {4}".format(var_jira, var_region, var_pod, var_host, var_vmtype))
    
        
        
        print (mytable)        

    except Exception as e:
        message = "Exception in commonutils.disp_fliprt_pod_vms_for_reboot, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))


# def disp_fliprt_submit_pod_vms_for_reboot (var_file):
def submit_fliprt_pod_vms_for_reboot (var_file):
    try:


        var_fliprt_valid_pod_vm_reboot_info_lst = []

        var_req_data = {}
        var_req_status = ""
        var_req_header = {}
        var_opc_req_id = ""
        var_code = ""
        var_message = ""
        var_opc_work_req_id = ""


        with open(var_file, 'r') as jsonf:
            var_pod_vms_for_reboot = json.load(jsonf)

        for var_pod_vm_for_reboot in var_pod_vms_for_reboot:

            # print ("var_pod_vm_for_reboot : {0}".format(var_pod_vm_for_reboot))
            var_pod = var_pod_vm_for_reboot.get("pod_name")
            var_host = var_pod_vm_for_reboot.get("host_name")
            
            var_reboot_cmd = var_pod_vm_for_reboot.get("maint_cmd")
            
            print ("var_reboot_cmd :",var_reboot_cmd)
            print_info ("Submitting REBOOT for VM : {0} on the POD : {1} ".format(var_host, var_pod))
            # sdsd = input ("Press any Key to continue ......")
            var_pod_vm_pod_reboot_utf8 = exec_api_cmd(var_reboot_cmd)
            
            var_pod_vm_pod_reboot_utf8_jsons = json.loads(var_pod_vm_pod_reboot_utf8)
            # print ("var_pod_vm_pod_reboot_utf8_jsons ------")
            # pprint (var_pod_vm_pod_reboot_utf8_jsons)
            # print ("var_pod_vm_pod_reboot_utf8_jsons : ",var_pod_vm_pod_reboot_utf8_jsons)
            var_pod_vm_pod_reboot_utf8_jsons_len = len(var_pod_vm_pod_reboot_utf8_jsons)

            var_req_data = {}
            var_req_status = ""
            var_req_header = {}

            var_fliprt_valid_pod_vm_reboot_info = {
                            "incident_jira" : "",
                            "data_center" : "",
                            "pod_name": "",
                            "pod_ocid" : "",
                            "pod_lifecyclestate" : "",
                            "host_name" :"",
                            "vm_type" : "",
                            "host_id" : "",
                            "host_state" : "",
                            "cm_jira" : "",
                            "maint_file_name" : "",
                            "maint_cmd" : "",
                            "submit_time" : "",
                            "submitter" : "",
                            "opc_request_id" : "",
                            "fusion_work_request_id" : "",
                            "timeAccepted" : "",
                            "timeStarted" : "",
                            "timeFinished" : "",
                            "percentComplete" : "",
                            "completionCode" : "",
                            "completionMessage" : "",
                            }
            
            if (var_pod_vm_pod_reboot_utf8_jsons_len > 0):

                var_req_status = var_pod_vm_pod_reboot_utf8_jsons.get("status")
                # print ("var_req_status : {0}".format(var_req_status))
                print ("")
                print ("")
            if (var_req_status != '202 Accepted'):
                print_warn ("Unable to submit the REQUEST on POD : {0}".format(var_pod))
                var_req_header = var_pod_vm_pod_reboot_utf8_jsons.get("headers")
                var_opc_req_id = var_req_header.get("opc-request-id")
                var_code = var_req_data.get("code")
                var_message = var_req_data.get("message")
                print_warn ("Reason : {0}".format(var_message))

            elif (var_req_status == '202 Accepted'):
                print_info ("Submitted the REQUEST on POD : {0}".format(var_pod))
                var_req_header = var_pod_vm_pod_reboot_utf8_jsons.get("headers")
                var_req_data = var_pod_vm_pod_reboot_utf8_jsons.get("data")
                var_opc_req_id = var_req_header.get("opc-request-id")
                var_opc_work_req_id = var_req_header.get("opc-work-request-id")
                print ("var_opc_req_id : {0}".format(var_opc_req_id))
                print ("var_opc_work_req_id : {0}".format(var_opc_work_req_id))

                
        
            var_fliprt_valid_pod_vm_reboot_info["incident_jira"] = var_pod_vm_for_reboot.get("incident_jira")
            var_fliprt_valid_pod_vm_reboot_info["data_center"] = var_pod_vm_for_reboot.get("data_center")
            var_fliprt_valid_pod_vm_reboot_info["pod_name"] = var_pod_vm_for_reboot.get("pod_name")
            var_fliprt_valid_pod_vm_reboot_info["pod_ocid"] = var_pod_vm_for_reboot.get("pod_ocid")
            var_fliprt_valid_pod_vm_reboot_info["host_name"] = var_pod_vm_for_reboot.get("host_name")
            var_fliprt_valid_pod_vm_reboot_info["vm_type"] = var_pod_vm_for_reboot.get("vm_type")
            var_fliprt_valid_pod_vm_reboot_info["host_id"] = var_pod_vm_for_reboot.get("host_id")
            var_fliprt_valid_pod_vm_reboot_info["host_state"] = var_pod_vm_for_reboot.get("host_state")
            var_fliprt_valid_pod_vm_reboot_info["cm_jira"] = var_pod_vm_for_reboot.get("cm_jira")
            var_fliprt_valid_pod_vm_reboot_info["maint_file_name"] = var_pod_vm_for_reboot.get("maint_file_name")
            var_fliprt_valid_pod_vm_reboot_info["maint_cmd"] = var_pod_vm_for_reboot.get("maint_cmd")
            var_fliprt_valid_pod_vm_reboot_info["submit_time"] = var_pod_vm_for_reboot.get("submit_time")
            var_fliprt_valid_pod_vm_reboot_info["submitter"] = var_pod_vm_for_reboot.get("submitter")
            var_fliprt_valid_pod_vm_reboot_info["opc_request_id"] = var_opc_req_id
            var_fliprt_valid_pod_vm_reboot_info["fusion_work_request_id"] = var_opc_work_req_id
            var_fliprt_valid_pod_vm_reboot_info["timeAccepted"] = ""
            var_fliprt_valid_pod_vm_reboot_info["timeStarted"] = ""
            var_fliprt_valid_pod_vm_reboot_info["timeFinished"] = ""
            var_fliprt_valid_pod_vm_reboot_info["percentComplete"] = ""
            var_fliprt_valid_pod_vm_reboot_info["completionCode"] = ""
            var_fliprt_valid_pod_vm_reboot_info["completionMessage"] = ""



            # print ("After populating the info : {0}".format(var_fliprt_valid_pod_vm_reboot_info))

            var_fliprt_valid_pod_vm_reboot_info_lst.append(var_fliprt_valid_pod_vm_reboot_info)

        # print ("List with all the info : {0}".format(var_fliprt_valid_pod_vm_reboot_info_lst))
        # print ()
        # print ("Writing the info back into the file.. {0}".format(var_file))
        with open(var_file, 'w') as jsonf:
            jsonf.write(json.dumps(var_fliprt_valid_pod_vm_reboot_info_lst, indent=4))


    except Exception as e:
        message = "Exception in commonutils.submit_fliprt_pod_vms_for_reboot, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))



def get_fliprt_count_pod_vms_for_reboot_from_file (var_file):
    try:
        
        with open(var_file, 'r') as jsonf:
            var_pod_vms_for_reboot = json.load(jsonf)
        
        ctr = 0;
        for var_pod_vm_for_reboot in var_pod_vms_for_reboot:
            if (var_pod_vm_for_reboot):
                ctr += 1

        return (ctr)
    
    except Exception as e:
        message = "Exception in commonutils.get_fliprt_count_pod_vms_for_reboot_from_file, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))    


def get_pod_resource_digest (var_pod_region, var_pod_name, var_pod_ocid, var_pod_host_to_reboot):
    '''This procedure is used to get the POD VM info '''
    try :
        var_pod_vms_inst_lst=[]
        var_pod_vms_selected_inst_lst=[]
        vm_nums_lst = []
        vm_nums_int_lst = []
        user_vm_nums_int_input =[]

        var_host_found = False

        var_pod_host_to_reboot='IBOGJB-DEV1-OPT3.ibogjbd11.mdt01iad01prd.oraclevcn.com'
        print ("var_pod_host_to_reboot : ---- ",var_pod_host_to_reboot)
        
        # https://prod-ops-fusionapps.us-ashburn-1.oci.oraclecloud.com/20191001/internal/fusionEnvironments/ocid1.fusionenvironment.oc1.iad.aaaaaaaaf26ydzqnms4bua343mlppk2cknyzdafw3o4vjahnd5c3ihdwmdta/podResourcesSummary
        var_pod_vm_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments/{1}/podResourceDigest'.format(var_pod_region,var_pod_ocid)
        # var_pod_vm_cmd="oci --profile oc1_facp_prd --auth security_token raw-request --http-method GET --target-uri '{0}'".format(var_pod_vm_url)
    
        var_pod_resource_digest = oci_sdk.fetch_details_from_endpoint_url('GET',var_pod_vm_url) 
        # print ("var_pod_resource_digest : {0}".format(var_pod_resource_digest))
        # print ("-->> len(var_pod_vm_infos) : {0}".format(len(var_pod_vm_infos)))
        var_node_diget_coll_lst = var_pod_resource_digest.get("nodeDigestCollection")
        # print ("var_node_diget_coll_lst : ",var_node_diget_coll_lst)
        var_node_found = False
        for var_each_node_diget_coll_lst in var_node_diget_coll_lst:
            print ("var_each_node_diget_coll_lst - : ",var_each_node_diget_coll_lst)
            if (var_pod_host_to_reboot == var_each_node_diget_coll_lst.get("fqdn")):
                var_node_found = True
                print ("Node Found")
                var_vm_fqdn = var_each_node_diget_coll_lst.get("fqdn")
                var_vm_name = var_each_node_diget_coll_lst.get("name")
                var_vm_nodetype = var_each_node_diget_coll_lst.get("nodeType")
                var_pod_vm_url='https://prod-ops-fusionapps.{0}.oci.oraclecloud.com/20191001/internal/fusionEnvironments/{1}/podResourcesSummary'.format(var_pod_region,var_pod_ocid)
                # var_pod_vm_cmd="oci --profile oc1_facp_prd --auth security_token raw-request --http-method GET --target-uri '{0}'".format(var_pod_vm_url)
    
                var_pod_resource_summary = oci_sdk.fetch_details_from_endpoint_url('GET',var_pod_vm_url) 
                # print (var_pod_resource_summary)
                if (var_pod_resource_summary):
                    for var_pod_each_resource_summary in var_pod_resource_summary:
                        
                        if (var_pod_each_resource_summary.get("resourceType") == 'instance'):
                            if (var_vm_name == var_pod_each_resource_summary.get("displayName")):
                                var_pod_resourceid = var_pod_each_resource_summary.get(resourceId)
                                print ("var_pod_resourceid : ",var_pod_resourceid)
                            # print ("var_pod_each_resource_summary : ",var_pod_each_resource_summary)
                            
                        if (var_pod_each_resource_summary.get("resourceType") == 'node'):
                        
                            if (var_vm_name == var_pod_each_resource_summary.get("displayName")):
                                print ("var_vm_name : ",var_vm_name)
                                print ("displayName : ",var_pod_each_resource_summary.get("displayName") )
                                print (var_pod_each_resource_summary.get("resourceId"))
                                print (var_pod_each_resource_summary.get("state"))

                            # if (var_pod_each_resource_summary.get("displayName") == var_pod_host_to_reboot):
                        
                # print ("{0} - {1} - {2}".format(var_each_node_diget_coll_lst.get("fqdn"),
                #                                 var_each_node_diget_coll_lst.get("name"),
                #                                 var_each_node_diget_coll_lst.get("nodeType")))
                
        # var_pod_resource_digest_data


    except Exception as e:
        message = "Exception in commonutils.get_fliprt_count_pod_vms_for_reboot_from_file, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))   


def consolidate_fliprt_pod_vms_for_reboot (var_file):
    '''This procedure is used to get the POD VM info '''
    try :
        
        var_pod_vms = {
                        "incident_jira" : "",
                        "data_center" : "",
                        "pod_name": "",
                        "pod_ocid" : "",
                        "pod_lifecyclestate" : "",
                        "host_name" :[],
                        "vm_type" : "",
                        "host_id" : "",
                        "host_state" : "",
                        "cm_jira" : "",
                        "maint_file_name" : "",
                        "maint_cmd" : "",
                        "submit_time" : "",
                        "submitter" : "",
                        "opc_request_id" : "",
                        "fusion_work_request_id" : "",
                        "timeAccepted" : "",
                        "timeStarted" : "",
                        "timeFinished" : "",
                        "percentComplete" : "",
                        "completionCode" : "",
                        "completionMessage" : "",
                        } #redefine this with hostname as an ARRY

        with open(var_file, 'r') as jsonf:
            var_pod_vms_for_reboot = json.load(jsonf)
        
        for var_pod_vm_for_reboot in var_pod_vms_for_reboot:

            print (var_pod_vm_for_reboot.get("pod_name"))
            if (not var_pod_vms.get("pod_name")):
                print ("dict is empty so assigning the first record")
                var_pod_vms = var_pod_vm_for_reboot

                print ("==== First Record : ",var_pod_vms)
            else:
                print ("dict is NOT empty")
                print ("loop through the local dictonary for the POD Name")
                print ("local dict : ",var_pod_vms)
                print ("type(var_pod_vms) : ",type(var_pod_vms))
                print ("{0} -- {1}".format( var_pod_vm_for_reboot.get("pod_name"),  var_pod_vm_for_reboot.get("host_name")))

                for var_pod_vm in var_pod_vms:
                    print ("in the for")
                    print (var_pod_vm)
                    if (var_pod_vm("pod_name") == var_pod_vm_for_reboot.get("pod_name")):
                        print ("Duplicate POD Name found")
                        print ("Need to add this as in ARRAY {0} -- {1}".format( var_pod_vm_for_reboot.get("pod_name"),  var_pod_vm_for_reboot.get("host_name")))


                        # assign individual values and append to the hostname
                        # var_pod_vm[""] = var_pod_vm_for_reboot.get()

        sirsi = input ("CANCEL Here......")

    except Exception as e:
        message = "Exception in commonutils.consolidate_fliprt_pod_vms_for_reboot, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))   


# def read_pod_from_dict (var_pod_info_dict):
    
    # get_pod_fliprt_lifecycleinfo (var_pod_region, var_pod_name,stack):

def create_payload_json_file (var_filename):
    try :
        with open(var_filename, 'r') as jsonf:
                var_pod_vms_for_reboot = json.load(jsonf)

        var_pod_vm_lst = []
        
        for var_pod_vm_for_reboot in var_pod_vms_for_reboot:
            var_pod_region = var_pod_vm_for_reboot.get("data_center")
            var_pod_name = var_pod_vm_for_reboot.get("pod_name")
            var_pod_ocid = var_pod_vm_for_reboot.get("pod_ocid")
            
            var_pod_vms_for_reboot = var_pod_vm_for_reboot.get("host_name")
            
            var_payload_info = get_internalScheduleActivity_fliprt_template (var_pod_name, var_pod_ocid,var_pod_vms_for_reboot)

            # print ("var_payload_info : ------------------ ")
            # pprint(var_payload_info)

            var_maint_file_name = ("{}incident_{}_{}_reboot.json".format(globalvariables.output_dir, globalvariables.glbl_fliprt_incident_jira,var_pod_name))
            # print ("var_maint_file_name : ",var_maint_file_name)

            write_to_file (var_maint_file_name, var_payload_info)

            if globalvariables.glbl_stack == 'preprod':
                faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["ppd"],var_pod_region,globalvariables.glbl_env_api_suffix)
                # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)
            elif globalvariables.glbl_stack == 'prod':
                faaas_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_facp_url_prefixs["prd"],var_pod_region,globalvariables.glbl_env_api_suffix)
                # adp_api_url = "https://{0}.{1}.{2}".format(globalvariables.glbl_env_adp_url_prefixs["prd"],globalvariables.glbl_env_api_suffix)

            # oci --profile oc1_facp_prd --auth security_token raw-request --http-method POST --request-body file:///Users/ssirsi/schedule_reboot.json --target-uri 'https://prod-ops-fusionapps.us-ashburn-1.oci.oraclecloud.com/20191001/internalScheduledActivities'
            var_exec_cmd = ("oci --profile resize_oci_config --auth security_token raw-request --http-method POST --request-body file://{0} --target-uri '{1}internalScheduledActivities'".format(var_maint_file_name, faaas_api_url))
            print ("")
            print ("---------- execution command : ---------",var_exec_cmd)
            print ("")
            # print ("---- VM Info : ",var_pod_vm_fliprt_info)
            var_pod_vm_for_reboot["maint_file_name"] = var_maint_file_name
            var_pod_vm_for_reboot["maint_cmd"] = var_exec_cmd

            var_pod_vm_lst.append(var_pod_vm_for_reboot)
        

        with open(var_filename, 'w') as jsonf:
            jsonf.write(json.dumps(var_pod_vm_lst, indent=4))



    except Exception as e:
        message = "Exception in commonutils.create_payload_json_file, Error while displaying the info {0}".format(e)
        print_warn ("{0}".format(message))  