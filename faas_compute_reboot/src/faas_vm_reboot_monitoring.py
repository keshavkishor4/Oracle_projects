#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime, timedelta
import time
# from progress.bar import Bar
from prettytable import PrettyTable
BASE_DIR = os.path.abspath(__file__ + "/../..")
sys.path.append(BASE_DIR + "/src/lib/common")
import globalvariables
from globalvariables import print_info, print_warn, print_error
import commonutils
import ocisdk
oci_sdk = ocisdk.OciSdk()


# x = PrettyTable()
# x.field_names = ["POD_NAME", "Action Type", "Status", "WorkFlow Definition", "DevOPs Link"]


def get_work_req_id(scaleout_file_json):
    """Print work req details of given json file

    Args:
       param1 (str): scaleout/resize json file.

    Returns:
       None:  .
   """
    var_pod_region = ""
    var_opc_req_id = ""
    var_wf_id = ""
    var_wf_status = ""
    var_all_wf = []
    status_list = []
    final_status_list = []

    json_data_lst = []
    # x = PrettyTable()
    # x.field_names = ["POD_NAME", "Action Type", "Status", "WorkFlow Definition", "DevOPs Link"]
    try:
        with open(scaleout_file_json, 'r') as jsonf:
            jsondata_read = jsonf.read()
        jsondata = json.loads(jsondata_read)

        #Working code ================
        for var_pod_resized in jsondata:
            x = PrettyTable()
            # x.field_names = ["Action Type", "Status", "WorkFlow Definition", "DevOPs Link"]
            # x.field_names = [ "WorkFlow Definition", "Status", "DevOPs Link"]
            x.field_names = ["operationType","targetHostNameList","timeAccepted","timeStarted","timeFinished","percentComplete","status","completionCode","completionMessage"]
            var_pod_name = var_pod_resized.get("pod_name")
            var_pod_region = var_pod_resized.get("data_center")
            var_pdt_req_id = var_pod_resized.get("fusion_work_request_id")
            var_fusion_work_request_id = var_pod_resized.get("fusion_work_request_id")
            var_dt_req_id = var_pod_resized.get("fusion_work_request_id")
            # var_pdt_status = var_pod_resized.get("pdt_status")
            # var_dt_status = var_pod_resized.get("dt_status")
            # var_dt_sumitted = var_pod_resized.get("dt_submit_date")
            # var_pdt_submitted = var_pod_resized.get("pdt_submit_date")
            print_info("==================================")
            print_info("Pod Details :" + var_pod_name)
            print_info("Work Request Id :" + var_fusion_work_request_id)
            print_info("==================================")
            # if (var_pdt_req_id != ""):
            if (var_fusion_work_request_id != ""):
                # if (var_pdt_status == "SO_SUBMITTED" or (
                #         var_dt_status == "RESIZE_DT_READY" and var_pdt_status == "RESIZE_PDT_SUBMITTED")):
                #     timediff = check_timediff(var_pdt_submitted)
                #     if (timediff < 5 ):
                #         print_info("Scaleout/PDT just submitted, querying in 5 mins".format(timediff))
                #         with Bar('Sleeping', max=100) as bar:
                #             for i in range(100):
                #                 time.sleep(3)
                #                 bar.next()
                # var_pdt_all_wf = fetch_all_childWorkFlows(var_pod_region, var_pdt_req_id)
                var_pdt_all_wf = fetch_dt_worrkflow_detais(var_pod_region, var_pdt_req_id)
                # print ("var_pdt_all_wf : ",var_pdt_all_wf)
                

                var_dt_all_wf = fetch_all_childWorkFlows(var_pod_region, var_pdt_all_wf)
                # print ("var_dt_all_wf : ",var_dt_all_wf)

                status_list = print_details_as_table(var_pod_name, var_pod_region, var_dt_all_wf, x)
                # print ("status_list : ",status_list)

                final_status_list.extend(status_list)
                # elif (var_dt_req_id != "" and var_dt_status == "RESIZE_DT_SUBMITTED" and var_pdt_status == "RESIZE_PDT_SUBMITTED"):
                #     timediff = check_timediff(var_dt_sumitted)
                #     if(timediff < 5 ):
                #         print_info("Downtime just submitted, querying in 5 mins".format(timediff))
                #         with Bar('Sleeping', max=100) as bar:
                #             for i in range(100):
                #                 time.sleep(3)
                #                 bar.next()
                #     var_dt_wf_details = fetch_dt_worrkflow_detais(var_pod_region, var_dt_req_id)
                #     var_dt_all_wf = fetch_all_childWorkFlows(var_pod_region, var_dt_wf_details)
                #     status_list = print_details_as_table(var_pod_for_resize, var_pod_region, var_dt_all_wf, x)
                #     final_status_list.extend(status_list)
                # elif (var_dt_req_id != "" and var_dt_status == "RESIZE_DT_SCHEDULED" and var_pdt_status == "RESIZE_PDT_SUBMITTED"):
                #     print_info("Downtime scheduled as per input data")
                #     exit(0)
                print(x)

                # print ("jsondata : ",jsondata)
                for jdata in jsondata:
                    # print ("jdata------ :",jdata)
                    # print (type(jdata))
                    # print (type(var_dt_all_wf))
                    # print(len(var_dt_all_wf))
                    # print ("jdata------ :",jdata.get("pod_name"))
                    if (jdata.get("data_center") == var_pod_region and jdata.get("pod_name") == var_pod_name):
                        # print (jdata.get("request_start_time"))
                        # print (jdata.get("request_status"))
                        # print (jdata.get("request_end_time"))
                        # print (var_dt_all_wf)
                        for var_dt_each_wf in var_dt_all_wf:
                            # print ("in for loop")
                            jdata["timeAccepted"] = var_dt_each_wf[2]
                            jdata["timeStarted"] = var_dt_each_wf[3]
                            jdata["timeFinished"] = var_dt_each_wf[4]
                            jdata["percentComplete"] = var_dt_each_wf[1]
                            jdata["request_status"] = var_dt_each_wf[6]
                            jdata["completionCode"] = var_dt_each_wf[7]
                            jdata["completionMessage"] = var_dt_each_wf[8]

                            


                            print ("")
                            print ("")
                            # print ("-------",jdata)
                            json_data_lst.append(jdata)

                        
            else:
                print_error("No request id mentioned !!!! Please check!!")
                exit(1)
        # print ("LIST :: ",json_data_lst)
        print ("File to write : ",scaleout_file_json)
        print ("Writing the updated data back into the FILE.. ")
        with open(scaleout_file_json, 'w') as jsonf:
            jsonf.write(json.dumps(json_data_lst, indent=4))
        

        # Till here
        # print(x)
        # monitor_workflow(final_status_list,scaleout_file_json,var_pdt_status,var_dt_status)
        # monitor_workflow(final_status_list,scaleout_file_json,var_pdt_status,var_dt_status)
                
        # monitor_workflow(final_status_list,scaleout_file_json)
        
        # for status in final_status_list:
        #     if(status.strip() == "DELAYED" or status.strip() == "RUNNING"):
        #         print_info("Workflows still running ... Sleeping for 2 mins...")
        #         with Bar('Sleeping', max=100) as bar:
        #             for i in range(100):
        #                 time.sleep(1.2)
        #                 bar.next()
        #         print_info("Checking again...")
        #         get_work_req_id(scaleout_file_json)

            # if (status.strip() != "COMPLETE"):
            #     print_info("Workflows still running ... Sleeping for 2 mins...")
            #     with Bar('Sleeping', max=100) as bar:
            #         for i in range(100):
            #             time.sleep(1.2)
            #             bar.next()
            #     print_info("Checking again...")
            #     get_work_req_id(scaleout_file_json)
            # elif(status.strip() == "COMPLETE"):
            #     print_info("All Child workflow has been completed successfully!!!")
            #     # exit(0)
            # elif(status.strip() == "FAILED"):
            #     print_info("Some workflow failed, Please check!!!")
            #     exit(1)

    except Exception as e:
        message = "Exception in faas_resize_monitoring.get_work_req_id, unable to read scaleout_file_json JSONs {0}".format(e)
        print_error("{0}".format(message))

# def monitor_workflow(final_status_list,scaleout_file_json,var_pdt_status,var_dt_status):
def monitor_workflow(final_status_list,scaleout_file_json):
    for status in final_status_list:
        if(status.strip() == "DELAYED" or status.strip() == "RUNNING" or status.strip() == "CREATED"):
            print_info("Workflows still running ... Sleeping for 2 mins...")
            oci_sdk.gen_token()
            with Bar('Sleeping', max=100) as bar:
                for i in range(100):
                    time.sleep(1.2)
                    bar.next()
            print_info("Checking again...")
            get_work_req_id(scaleout_file_json)

    # if(var_pdt_status == "SO_SUBMITTED"):
    #     with open(scaleout_file_json, 'r+') as jsonf:
    #         jsondata_read = jsonf.read()
    #         jsondata = json.loads(jsondata_read)
    #         print(len(jsondata))
    #         for k in jsondata:
    #             print(k)
    #             k['pdt_status'] = 'S0_SUCCESSFUL'
    #         jsonf.seek(0)
    #         jsonf.write(json.dumps(jsondata, indent=4))
    #         jsonf.truncate()

def check_timediff(var_dt_sumitted):
    try:
        #### Need to check if the DT got submitted before 5 mins, or else sleep for 5 mins
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        now1 = datetime.strptime(now,"%Y-%m-%d %H:%M:%S")
        dt_time = datetime.strptime(var_dt_sumitted,"%d-%b-%Y %H:%M:%S")
        # print(now1)
        # print(dt_time)
        delta = now1 - dt_time
        sec = delta.total_seconds()
        min = sec / 60
        return min
    except Exception as e:
        message = "Exception in faas_resize_monitoring.check_timediff, {0}".format(e)
        print_error("{0}".format(message))
def print_details_as_table(var_pod_for_resize,var_pod_region,var_all_wf,x):
    """Print the given details as table format

    Args:
       param1 (str): pod name.
       param2 (str): region name.
       param3 (str): All workflow details.

    Returns:
       Table: Print as table format.
   """
    var_wf_status_list = []
    for var_wf in var_all_wf:
        var_wf_id = var_wf[0]
        var_workreq_id = var_wf[2]
        var_wf_status = var_wf[3]
        var_id = var_wf[4]

        var_1 = var_wf[0]
        var_2 = var_wf[5]
        var_3 = var_wf[2]
        var_4 = var_wf[3]
        var_5 = var_wf[4]
        var_6 = var_wf[1]
        var_7 = var_wf[6]
        var_8 = var_wf[7]
        var_9 = var_wf[8]
        # var_10 = var_wf[9]


        var_devops_link = create_devops_link(var_pod_region, var_id)
        # x.add_row([var_workreq_id, var_wf_status, var_wf_id, var_devops_link])
        x.add_row([var_1, var_2, var_3,var_4,var_5,var_6,var_7,var_8,var_9])
        var_wf_status_list.append(var_wf_status)
    return var_wf_status_list

def fetch_all_childWorkFlows(var_pod_region, var_opc_req_id):
    """This procedure will fetch all the childWorkFlows for input workflow
    Args:
       param1 (str): region name.
       param2 (str): workflow request id .

    Returns:
       List: List all workflow details.
    """
    var_ch_wkflows_list = []
    try:
        # print ("aaa", 'prod-ops-fusionapps')
        # print ("aaa", var_pod_region)
        # print ("aaa", var_opc_req_id)
        target_url = 'https://{}.{}.oci.oraclecloud.com/20191001/internalWorkRequests/{}'.format('prod-ops-fusionapps',
            var_pod_region, var_opc_req_id)
        # print_info("target_url : {0}".format(target_url))
        pod_work_req_details = oci_sdk.fetch_details_from_endpoint_url("GET", target_url)

        # print ("pod_work_req_details********* :",pod_work_req_details)

        var_oper_type = pod_work_req_details["operationType"]
        var_percentComplete = pod_work_req_details["percentComplete"]
        var_timeAccepted = pod_work_req_details["timeAccepted"]
        var_timeStarted = pod_work_req_details["timeStarted"]
        var_timeFinished = pod_work_req_details["timeFinished"]
        # var_status = pod_work_req_details['status']
        var_resources = pod_work_req_details['resources']
        var_resources_wfs = pod_work_req_details['workflows']
        # print ("var_resources_wfs ----****---- ",var_resources_wfs)

        for var_resources_wf in var_resources_wfs:
            var_resources_wf_args = json.loads(var_resources_wf['arguments'])
        # print ("var_resources_wf_args : ",var_resources_wf_args)
        # print (type(var_resources_wf_args))
        var_resources_wf_args_resType =  var_resources_wf_args.get("resourceType")
        # print (var_resources_wf_args_resType)
        var_resources_wf_args_hosts =  var_resources_wf_args.get("targetHostNameList")
        # print (var_resources_wf_args_hosts)
        # var_resources_wf_args_timecreated = var_resources_wf.get("timeCreated")
        # var_resources_wf_args_timecompleted = var_resources_wf.get("timeCompleted")
        var_resources_wf_args_status = var_resources_wf.get("status")
        var_resources_wf_args_completionCode = var_resources_wf.get("completionCode")
        var_resources_wf_args_completionMessage = var_resources_wf.get("completionMessage")
        var_resource_wkflow_lst=[]
        var_resource_wkflow_lst.append(var_oper_type)
        var_resource_wkflow_lst.append(var_percentComplete)
        var_resource_wkflow_lst.append(var_timeAccepted)
        var_resource_wkflow_lst.append(var_timeStarted)
        var_resource_wkflow_lst.append(var_timeFinished)
        var_resource_wkflow_lst.append(var_resources_wf_args_hosts)
        # var_resource_wkflow_lst.append(var_resources_wf_args_timecreated)
        # var_resource_wkflow_lst.append(var_resources_wf_args_timecompleted)
        var_resource_wkflow_lst.append(var_resources_wf_args_status)
        var_resource_wkflow_lst.append(var_resources_wf_args_completionCode)
        var_resource_wkflow_lst.append(var_resources_wf_args_completionMessage)
        var_ch_wkflows_list.append(var_resource_wkflow_lst)
        # var_resource_wkflow_lst.append()
        

        # print ("var_status ---- ",var_resource_wkflow_lst)
        # for resource in pod_work_req_details['workflows']:
            # var_workreq_id = resource['surrogateKey']
            # var_status = resource['status']
            # var_completionCode = resource['completionCode']
            # var_id = resource['id']
            # var_def = resource['workflowDefinitionId']
            # var_def_name = var_def["name"]
            # var_ch_wkflow = []
            # var_ch_wkflow.append(var_def_name)
            # var_ch_wkflow.append(var_completionCode)
            # var_ch_wkflow.append(var_workreq_id)
            # var_ch_wkflow.append(var_status)
            # var_ch_wkflow.append(var_id)
            # var_ch_wkflows_list.append(var_ch_wkflow)

        return var_ch_wkflows_list
    except Exception as e:
        message = "Exception in faas_resize_monitoring.fetch_all_childWorkFlows, unable to fetch action_details {0}. " \
                  "Either your OCI session authentication has been interrupted. Or some issue while monitoring. Please resume your monitring script.".format(
            e)
        print_error("{0}".format(message))


def create_devops_link(var_pod_region, var_wf_id):
    """This procedure will prepare the devops links to share while monitoring the progress of the run
    Args:
       param1 (str): region name.
       param2 (str): workflow request id .

    Returns:
       str: direct debops/DOPE link of the work request.
    """
    var_devops_link = "https://devops.oci.oraclecorp.com/fusion-apps/workflows/{}?isFacp=true&stack={}&region={}&realm=OC1".format(
        var_wf_id, globalvariables.glbl_stack.capitalize(), var_pod_region)
    # [[http: // example.net / | example site]]
    # var_hlink = [["https://devops.oci.oraclecorp.com/fusion-apps/workflows/{0}?isFacp=true&stack=Prod&region={1}&realm=OC1".format(var_action_id,var_pod_region)| "Text"]]
    # print(var_hlink)
    # https://devops.oci.oraclecorp.com/fusion-apps/workflows/<workflow_id>?isFacp=true&stack=Prod&region=<region>&realm=OC1
    # hyperlink_format = '<a href="{link}">{text}</a>'
    # var_hlink=hyperlink_format.format(link=var_devops_link, text=var_action_id)
    # var_hlink = pd.DataFrame(data)
    # var_hlink = var_hlink.style.format({'location': var_devops_link})
    # print(var_devops_link)
    return var_devops_link

def fetch_dt_worrkflow_detais(var_pod_region, var_dt_req_id):
    identifier =""
    try:
        target_url = 'https://{}.{}.oci.oraclecloud.com/20191001/internalWorkRequests/{}'.format('prod-ops-fusionapps',
        var_pod_region, var_dt_req_id)
        pod_req_details = oci_sdk.fetch_details_from_endpoint_url("GET", target_url)
        for resource in pod_req_details['resources']:
            # print(resource['identifier'])
            identifier = resource['identifier']
            workreqid = fetch_dt_wrok_req_id(var_pod_region,identifier)
            return workreqid
    except Exception as e:
        message = "Exception in faas_resize_monitoring.fetch_dt_worrkflow_detais, unable to fetch internalWorkRequests {0}".format(e)
        print_error("{0}".format(message))

def fetch_dt_wrok_req_id(var_pod_region,identifier):
    internal_work_req_state = ""
    internal_work_req_id = ""
    try:
        target_url = 'https://{}.{}.oci.oraclecloud.com/20191001/internalScheduledActivities/{}'.format('prod-ops-fusionapps',
            var_pod_region, identifier)
        pod_identifier_details = oci_sdk.fetch_details_from_endpoint_url("GET", target_url)
        for resource in pod_identifier_details['actions']:
            # print(resource['state'])
            # print(resource['workRequestId'])
            # internal_work_req_state = resource['state']
            internal_work_req_id = resource['workRequestId']
            return internal_work_req_id
    except Exception as e:
        message = "Exception in faas_resize_monitoring.fetch_dt_wrok_req_id, unable to fetch action_details {0}".format(
            e)
        print_error("{0}".format(message))
# var_scaleout_georegion_json="/Users/tatsarka/Downloads/AMER_RESIZE_19May2023_scaleout.json"
# get_work_req_id(var_scaleout_georegion_json)

