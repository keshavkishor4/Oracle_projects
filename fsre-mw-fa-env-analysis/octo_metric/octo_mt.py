import requests
import json
import traceback
import os
import sys
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
from statistics import mean 
import pandas as pd

@globalvariables.timer
def mt_perf_metric_details(pod: str,st_time: str,ed_time: str)-> None:
    try:
        file_name="{0}/{1}_pod_mt_octo_perf_data.json".format(globalvariables.exa_octo_data,pod)
        mt_details={}
        #jvm_heap=[]
        mt_details.update({pod:{}})
        jvm_heap=jvm_heapusage_details(pod,st_time,ed_time)
        #print(jvm_heap)
        mt_stuckthread=mt_stuckthread_details(pod,st_time,ed_time)
        Ds_active_count=ds_connection_details(pod,st_time,ed_time)
        jvm_restart_detail= jvm_restart_details(pod,st_time,ed_time)
        mt_details[pod].update({"jvm_heap_uses":jvm_heap})
        mt_details[pod].update({"jvm_stuck_thread":mt_stuckthread})
        mt_details[pod].update({"datasource_connection_count":Ds_active_count})
        mt_details[pod].update({"jvm_restart_details":jvm_restart_detail})
        json_object = json.dumps(mt_details, indent=4)
        with open(file_name,'w') as dart_data:
            dart_data.write(json_object)     
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting query fa mt metric details - mt_perf_metric_details {0}".format(e,globalvariables.RED)
        print(message)

def get_octo_metric_data(query_string: str,start_time: str,end_time: str)-> dict:
    try:
        #URL='https://api.octo.oraclecloud.com/fusion/query/{0}?start=2023-09-19T19:58:45.990Z&end=2023-09-20T20:58:45.988Z'.format(query_string)
        URL='https://api.octo.oraclecloud.com/fusion/query/{0}?start={1}Z&end={2}Z'.format(query_string,start_time,end_time)
        #print (URL)
        headers={"Content-Type":"application/json"}
        auth=('octo_fusion', 'saashealth')
        response=requests.get(URL,headers=headers,auth=auth,verify=True)
        #print(response.status_code)
        j_data=json.loads(str(response.content.decode('utf8').replace("'", '"')))["data"]["result"]
        return j_data
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting mt metric data - get_octo_metric_data {0}".format(e,globalvariables.RED)
        print(message)

def get_promql_query(query_name: str,inplace: str,lable: str)-> str:
    try:
        query=""
        with open(globalvariables.prom_file,'r') as promql_query_data:
            query_lines = promql_query_data.readlines()
        for line in query_lines:
                if line.split("##")[0] == query_name:
                    query= line.split("##")[1]
        prom_query=query.replace(inplace,lable)
        return prom_query
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting query in func - get_promql_query {0}".format(e,globalvariables.RED)
        print(message)

def jvm_restart_details(pod: str,st_time: str,ed_time: str)-> dict:
    """ jvm_restart_details
        Args:
            pod (str): pod name to get jvm restart details 
            st_time (str): start time for time window of octo. 
            ed_time (str): end time for time window of octo.
        Returns:
            jvm restart details (dict): restart details for all the jvms present in the given pod.
        Raises:
            Exception: octo metric error
        """
    try:
        query=get_promql_query("wls_restart","pod_name",pod)
        j_data=get_octo_metric_data(query,st_time,ed_time)
        restart={}
        for i in j_data:
            valu_arr=[int(stk[1]) for stk in i["values"]]
            restart.update({i["metric"]["wls"]:sum(valu_arr)})
        return restart
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting jvm restart details - jvm_restart_details {0}".format(e,globalvariables.RED)
        print(message)

def jvm_heapusage_details(pod: str,st_time: str,ed_time: str)-> dict:
    try:
        query=get_promql_query("mt_heap_usage","pod_name",pod)
        j_data=get_octo_metric_data(query,st_time,ed_time)
        jvm_heap_uses=[]
        for i in j_data:
            heap_uses={}
            # heap=round(round(float(i["values"][0][1]),2))
            valu_arr=[float(stk[1]) for stk in i["values"] ]
            if valu_arr:
                avg_heap=mean(valu_arr)
                max_heap=max(valu_arr)
                if avg_heap > 60:
                    heap_uses.update({"jvm_name":i["metric"]["wls"],"avg_heap":round(avg_heap,0),"max_heap":round(max_heap,0)})
                    jvm_heap_uses.append(heap_uses)
            # if heap > 90:
            #     restart.update({i["metric"]["wls"]:heap})
            #     main_data={"pod_name":pod,"server_heap_usage":restart}
        return jvm_heap_uses
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting jvp heap details - jvm_heapusage_details {0}".format(e,globalvariables.RED)
        print(message)

def mt_stuckthread_details(pod: str,st_time: str,ed_time: str)-> list:
    try:
        query=get_promql_query("mt_stuck_thread","pod_name",pod)
        j_data=get_octo_metric_data(query,st_time,ed_time)
        jvm_stuck_thread=[]
        for i in j_data:
            stuck_thread={}
            valu_arr=[int(stk[1]) for stk in i["values"] if int(stk[1]) > 4]
            if valu_arr:
                avg_stuck=mean(valu_arr)
                max_stuck=max(valu_arr)
                if avg_stuck > 10:
                    stuck_thread.update({"jvm_name":i["metric"]["wls"],"avg_stuck_thread":round(avg_stuck,0),"max_stuck_thread":max_stuck})
                    jvm_stuck_thread.append(stuck_thread)
        # print(jvm_stuck_thread)
        return jvm_stuck_thread
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting jvm stuck thread details- mt_stuckthread_details {0}".format(e,globalvariables.RED)
        print(message)

def ds_connection_details(pod: str,st_time: str,ed_time: str)-> dict:
    try:
        query=get_promql_query("DS_active_connection_count","pod_name",pod)
        #print(query)
        j_data=get_octo_metric_data(query,st_time,ed_time)
        #print(j_data)
        restart={}
        main_data_f={}
        connection_count_details=[]
        for i in j_data:
            connection_count={}
            # print(i["metric"])
            valu_arr=[int(stk[1]) for stk in i["values"] if int(stk[1]) > 30 ]
            if valu_arr:
                avg_connection=mean(valu_arr)
                max_connection=max(valu_arr)
                if avg_connection > 100:
                    connection_count.update({"jvm_name":i["metric"]["wls"],"datasource":i["metric"]["datasource"],"avg_connection_count":round(avg_connection,0),"max_connection_count":max_connection})
                    connection_count_details.append(connection_count)

            #server=i["metric"]["wls"]
            #print(server)
            #nm_restart=i["values"][0][1]
            # ds_active_connection_count=int(i["values"][0][1])
            # #print(stuck)
            # if ds_active_connection_count > 10:
            #     restart.update({i["metric"]["datasource"]:ds_active_connection_count})
            #     main_data={"pod_name":pod,"datasource_connection_count":restart}
                #main_data_f=main_data({1})
        #print(main_data)
        return connection_count_details
    except Exception as e:
        traceback.print_exc
        message="{1}Error in getting data source connection count details - ds_connection_details {0}".format(e,globalvariables.RED)
        print(message)



def main():
    mt_perf_metric_details("eino","2023-10-06T19:58:45","2023-10-10T20:58:45")

if __name__ == "__main__":
    main()
