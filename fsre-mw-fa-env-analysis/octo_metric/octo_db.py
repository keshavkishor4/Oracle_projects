import requests
import urllib.parse
import json
from datetime import datetime,timedelta
import traceback
import os
import sys
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
from cloud_meta_data import  cloud_meta, cloud_meta_asyncio
from db_module import db_con
import time,asyncio
from statistics import mean 
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

session=requests.session()

def get_promql_query(query_name: str,inplace: str,lable: str) -> str:
    try:
        query=""
        with open(globalvariables.prom_file,'r') as promql_query_data:
            query_lines = promql_query_data.readlines()
        for line in query_lines:
                if line.split("##")[0] == query_name:
                    if line.split("##")[0] == "exadata_cpu" or line.split("##")[0] == "exadata_node_load" or line.split("##")[0] == "exadata_swap"  :
                        query= line.split("##")[1]
        prom_query=query.replace(inplace,lable)
        return prom_query
    except Exception as e:
        traceback.print_exc()
        message="error in getting query in func -get_promql_query {0}".format(e)
        print(message)

@globalvariables.timer
def get_octo_metric_data(query_string: str,start_time: str,end_time: str) -> list:
    try:
        #URL='https://api.octo.oraclecloud.com/fusion/query/{0}?start=2023-09-19T19:58:45.990Z&end=2023-09-20T20:58:45.988Z'.format(query_string)
        URL='https://api.octo.oraclecloud.com/fusion/query/{0}?start={1}Z&end={2}Z'.format(query_string,start_time,end_time)
        headers={"Content-Type":"application/json"}
        auth=('octo_fusion','saashealth')
        data=""
        with session.get(URL,headers=headers,auth=auth) as response:
            data=response.content
            j_data=json.loads(str(data.decode('utf8').replace("'", '"')))["data"]["result"]
        # print("\n{0}{1}\n".format(globalvariables.GREEN,URL))
        return j_data
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo metric in func -get_octo_metric_data {0}{1}".format(e.data)
        print(message)

def get_exa_parameter_details(exa: str ,st_time: str,ed_time: str) -> dict:
    try:
        # exadetails=cloud_meta.get_exadata_details(podname)
        # pod_exa=[]
        exajson_details={}
        # file_name="{0}/{1}_pod_perf_data.json".format(globalvariables.exa_octo_data,podname)
        if exa:
            exajson_details.update({exa:{}})
            exa_st_time=st_time.split(":")[0].replace("T",":")
            exa_et_time=ed_time.split(":")[0].replace("T",":")
            exajson_details[exa].update({"start_time":exa_st_time})
            exajson_details[exa].update({"end_time":exa_et_time})
            # file_name="{0}/{1}_pod_perf_data.json".format(globalvariables.exa_octo_data,exa)
            exajson_details_cpu=getexadata_cpu_details(exa,st_time,ed_time)
            if exajson_details_cpu:
                exajson_details[exa].update({"exa_high_cpu_spikes":exajson_details_cpu})
            else:
                exajson_details[exa].update({"exa_high_cpu_spikes":[]})
            exaload_details=getexadata_load_details(exa,st_time,ed_time)
            exaswap_details=getexadata_swap_details(exa,st_time,ed_time)
            exacpu_details=getexadata_cpu_no_spike(exa,st_time,ed_time)
            db_perf_details=get_db_perf_metric(exa,st_time,ed_time)
            if exaload_details:
                avg_load=exaload_details[exa]["avg_load"]
                max_load=exaload_details[exa]["max_load"]
                exajson_details[exa].update({"avg_load":avg_load})
                exajson_details[exa].update({"max_load":max_load})
            else:
                message="error in getting exa load details"
                print(message)
            if exaswap_details:
                avg_swap=exaswap_details[exa]["avg_swap"]
                max_swap=exaswap_details[exa]["max_swap"]
                exajson_details[exa].update({"avg_swap":avg_swap})
                exajson_details[exa].update({"max_swap":max_swap})
            else:
                message="error in getting exa swap details"
                print(message)
            if exacpu_details:
                avg_cpu=exacpu_details[exa]["avg_cpu"]
                max_cpu=exacpu_details[exa]["max_cpu"]
                exajson_details[exa].update({"avg_cpu":avg_cpu})
                exajson_details[exa].update({"max_cpu":max_cpu})
            else:
                message="error in getting exa cpu details"
                print(message)
            if db_perf_details:
                exajson_details[exa].update({"databases":db_perf_details})
            
            exajson_details[exa].update({"collection_time_stamp":datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        return exajson_details
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo metric in func -get_octo_metric_data {0}".format(e)
        print(message)

def get_db_perf_metric(exadata: str,st_time: str,ed_time: str)  -> list:
        try:
            databases_perf_metric=[]
            pods=cloud_meta.get_pod_details(exadata)
            pod_size=asyncio.run(cloud_meta_asyncio.get_pods_size(pods))
            for pod in pods:
                pod_metric={}
                as_data=getdb_nodes_active_session_details(pod,exadata,st_time,ed_time)
                db_cpu=getdb_nodes_cpu_details(pod,exadata,st_time,ed_time)
                pod_size_value=""
                pod_size_value=[pod_size_dict[pod] for pod_size_dict in pod_size if pod in pod_size_dict][0]
                sga_data=getdb_nodes_sga_details(pod,exadata,st_time,ed_time)
                pod_metric.update({"pod_name":pod,"dbname":sga_data.get("dbname",pod),"sid":sga_data.get("sid"),"pod_size":pod_size_value,"avg_sga":sga_data.get("avg_sga"),"max_sga":sga_data.get("max_sga")})
                if db_cpu:
                    pod_metric.update(db_cpu)
                else:
                    pod_metric.update({"avg_db_cpu":None,"max_db_cpu":None})
                if as_data:
                    pod_metric.update(as_data)
                else:
                    pod_metric.update({"avg_cpu_active_session":None,"max_cpu_active_session":None})
                databases_perf_metric.append(pod_metric)
            return databases_perf_metric
        except Exception as e:
            traceback.print_exc()
            message = "{0}Error in db perf metric for func - get_db_perf_metric for exa {1},{0}".format(e,exadata)
            print(message,file=sys.stderr)

def exa_json_file_dump(json_data: list,file_name: str) -> None:
    try:
        json_object = json.dumps(json_data, indent=4)
        if not os.path.exists(globalvariables.exa_octo_data):
                    os.makedirs(globalvariables.exa_octo_data)   
        with open(file_name,'w') as dart_data:
                dart_data.write(json_object)
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in writing json data in file - {1},{2}".format(globalvariables.RED,file_name,e)
        print(message)

def get_query_list(exadata: str) -> list:
    query_list=["exadata_cpu","exadata_node_load","exadata_swap","sgadata"]
    urls=[]
    for query in query_list:
        urls.append(get_promql_query(query,"exadata_instance",exadata))
    return urls

def getexadata_cpu_details(exadata: str,st_time: str,ed_time: str) -> list:
    try:
        exa_cpu=[]
        query=get_promql_query("exadata_cpu","exadata_instance",exadata)
        if query:
            j_data=get_octo_metric_data(query,st_time,ed_time)
            if j_data:
                print(f'calling hourly analysis')
                exa_cpu=getexa_cpu_hourly_analysis(exadata,j_data[0]['values'])
                # print(exa_cpu)
            else:
                message="error in getting exa cpu octo metric details"
                print(message)
        else:
            message="error in getting prom query details"
            print(message)
        return exa_cpu
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo cpu metric in func -getexadata_cpu_details {0}".format(e)
        print(message)

@globalvariables.timer
def getexa_cpu_hourly_analysis(exadata: str,metric_data: list) -> list:
    try:
        delta=timedelta(hours=1)
        data =[{"date_time":datetime.fromtimestamp(x[0]),"cpu_uses":float(x[1])} for x in metric_data]
        df=pd.DataFrame(data)
        # print(df)
        df['date_time']=df["date_time"].dt.strftime('%Y-%m-%d:%H')
        # df.to_json("test2.json")
        dt=df.groupby("date_time")
        # print(dt)
        mean_value=dt.mean()
        max_value=dt.max()
        # print(mean_value)
        # mean_value.to_json("test2.json")
        #count no of max peak  globalvariables.exa_cpu_peak every hour 
        max_cpu=dt["cpu_uses"].apply(lambda x: ((x>globalvariables.exa_cpu_peak).sum())).reset_index(name="count")
        # print(max_cpu)
        #find the date hour where max peak count greater than globalvariables.per_hour_count
        dates=list(max_cpu[max_cpu["count"] > globalvariables.per_hour_count]["date_time"])
        # print(dates)
        #Below logic to get data if max peak count continue for 3 hrs 
        start_Date=""
        start_point=[]
        end_point=[]
        cpu_cont=[]
        count=1
        for date in dates:
            dt_time=datetime.strptime(date,"%Y-%m-%d:%H")
            if dt_time == start_Date:
                count+=1
                if count > 2:
                    if count ==3:
                        prev_val=dt_time - delta
                        cpu_cont.append(datetime.strftime(prev_val,"%Y-%m-%d:%H"))
                        start_time=prev_val - delta
                        cpu_cont_start_index=cpu_cont.index(datetime.strftime(prev_val,"%Y-%m-%d:%H"))
                        start_point.append(datetime.strftime(start_time,"%Y-%m-%d:%H"))
                        if cpu_cont_start_index != 0:
                            end_point_index = cpu_cont_start_index - 1
                            end_value_time_obj=datetime.strptime(cpu_cont[end_point_index],"%Y-%m-%d:%H") + delta
                            end_point.append(datetime.strftime(end_value_time_obj,"%Y-%m-%d:%H"))
                    else:
                        prev_val=dt_time - delta
                        cpu_cont.append(datetime.strftime(prev_val,"%Y-%m-%d:%H"))
            else:
                count=1
                start_Date = dt_time
            start_Date=dt_time + delta
        if cpu_cont:
            end_point.append(cpu_cont[-1])
        cpu_throttling=[]
        for ind in range(0,len(start_point)):
            series={}
            mean_cpu,max_cpu=get_exa_cpu_mean_max(start_point[ind],end_point[ind],mean_value,max_value)
            series.update({"start_time":start_point[ind],"end_time":end_point[ind],"avg_cpu":round(mean_cpu,2),"max_cpu":round(max_cpu,2)})
            # "2023-09-29T00:00:45"
            db_start_time="{0}:00:05".format(start_point[ind].replace(":","T"))
            db_end_time="{0}:00:05".format(end_point[ind].replace(":","T"))
            db_perf_metric=get_db_perf_metric(exadata,db_start_time,db_end_time)
            series.update({"database":db_perf_metric})
            cpu_throttling.append(series)
        return cpu_throttling
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo per hour cpu throttling - func - getexa_cpu_hourly_analysis {0}".format(e)
        print(message)

def get_exa_cpu_mean_max(st_date: str,ed_date: str,mean_data: list,max_data: list)-> str:
    # start_date="2023-09-29:09"
    # end_date="2023-09-29:12"
    start_date=datetime.strptime(st_date,"%Y-%m-%d:%H")
    end_date=datetime.strptime(ed_date,"%Y-%m-%d:%H")
    dt_list=[]
    max_list=[]
    delta=timedelta(hours=1)

    while start_date < end_date :
        start_date=start_date + delta
        value=datetime.strftime(start_date,"%Y-%m-%d:%H")
        dt_list.append(mean_data["cpu_uses"][value])
        max_list.append(max_data["cpu_uses"][value])
    return mean(dt_list),max(max_list)


@globalvariables.timer
def getexadata_cpu_computation(metric_data: list) -> list:
    try:
        # print(metric_data)
        today=datetime.now()
        delta=timedelta(days=7)
        mid_week=today - delta
        first_week=[]
        second_week=[]
        for val in metric_data:
            # print(f"{val} and {type(val)}")
            dt_time=datetime.fromtimestamp(val[0])
            if dt_time < mid_week:
                first_week.append(val)
            else:
                second_week.append(val)
        first_week_start_date=f"{datetime.fromtimestamp(first_week[0][0]).strftime('%d%m%Y')}"
        second_week_start_date=f"{datetime.fromtimestamp(second_week[0][0]).strftime('%d%m%Y')}"
        first_avg_value=mean(float(x[1]) for x in first_week)
        second_week_avg_value=mean(float(x[1]) for x in second_week)
        # print(first_week)
        first_week_max_list=list(filter(lambda x:float(x[1])>95,first_week))
        second_week_max_list=list(filter(lambda x:float(x[1])>95,second_week))
        if first_week_max_list:
            first_max_value=max(first_week_max_list,key=lambda x:float(x[1]))[1]
            first_max_count=len(first_week_max_list)
        else:
            first_max_value=max(first_week,key=lambda x:float(x[1]))[1]
            first_max_count=0
        # print(first_w_start_date)
        # data={"1st_w_start_date" : [{"maxcount":""},{"avg_value":""},{"max_value":""}]}
        
        if second_week_max_list:
            second_week_max_value=max(second_week_max_list,key=lambda x:float(x[1]))[1]
            second_week_max_count=len(second_week_max_list)
        else:
            second_week_max_value=max(second_week,key=lambda x:float(x[1]))[1]
            second_week_max_count=0

        data=[{first_week_start_date : [{"maxcount":first_max_count},{"avg_value":first_avg_value},{"max_value":first_max_value}]},
            {second_week_start_date:[{"maxcount":second_week_max_count},{"avg_value":second_week_avg_value},{"max_value":second_week_max_value}]}]

        return data
    except Exception as e:
        traceback.print_exc()
        message="error in computing cpu func - getexadata_cpu_computation {0} {1}".format(e,metric_data)
        print(message)

def getexadata_load_details(exadata: str,st_time: str,ed_time: str) -> dict:
    try:
        exadata_json={}
        query=get_promql_query("exadata_node_load","exadata_instance",exadata)
        if query:
            j_data=get_octo_metric_data(query,st_time,ed_time)
            for metric in j_data:
                load=[]
                for tm in metric['values']:
                    load.append(round(float(tm[1]),2))
                # pods=cloud_meta.get_pod_details(exadata) #getting associated pods with exadata
                avg=round(sum(load)/len(load),2)
                exa_details={exadata:{"avg_load":avg,"max_load":max(load)}}
                exadata_json.update(exa_details)
        else:
            message="error in getting prom query details"
            print(message)
        return exadata_json
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo loadmetric in func - getexadata_load_details {0}".format(e)
        print(message)

def getexadata_swap_details(exadata: str,st_time: str,ed_time: str) -> dict:
    try:
        exadata_json={}
        query=get_promql_query("exadata_swap","exadata_instance",exadata)
        if query:
            j_data=get_octo_metric_data(query,st_time,ed_time)
            #print(j_data)
            for metric in j_data:
                swap=[]
                for tm in metric['values']:
                    swap.append(round(float(tm[1]),2))
                avg=round(sum(swap)/len(swap),2)
                exa_details={exadata:{"avg_swap":avg,"max_swap":max(swap)}}
                exadata_json.update(exa_details)
        else:
            message="error in getting prom query details"
            print(message)
        return exadata_json
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo loadmetric in func - getexadata_swap_details {0}".format(e)
        print(message)

def getexadata_cpu_no_spike(exadata: str,st_time: str,ed_time: str) -> dict:
    try:
        exadata_json={}
        query=get_promql_query("exadata_cpu","exadata_instance",exadata)
        if query:
            j_data=get_octo_metric_data(query,st_time,ed_time)
            #print(j_data)
            for metric in j_data:
                cpu=[]
                for tm in metric['values']:
                    cpu.append(round(float(tm[1]),2))
                avg=round(sum(cpu)/len(cpu),2)
                exa_details={exadata:{"avg_cpu":avg,"max_cpu":max(cpu)}}
                exadata_json.update(exa_details)
        else:
            message="error in getting prom query details"
            print(message)
        return exadata_json
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo exa cpu no spike in func - getexadata_cpu_no_spike {0}".format(e)
        print(message)

@globalvariables.timer
def getdb_nodes_sga_details(podname: str,exadata: str,st_time: str,ed_time: str)  -> dict:
    try:
        query=""
        with open(globalvariables.prom_file,'r') as promql_query_data:
            query_lines = promql_query_data.readlines()
        for line in query_lines:
                if line.split("##")[0] == "sgadata":
                    query= line.split("##")[1].strip()
        query_new = query.replace("pod_name",podname.lower().replace("-","_")).replace("exadata_instance",exadata)
        encoded_query=urllib.parse.quote(query_new,safe="")
        query_new="(({0}))*100".format(encoded_query)
        j_data=get_octo_metric_data(query_new,st_time,ed_time)
        sga=[]
        metric_data={}
        if j_data:
            for tm in j_data[0]['values']:
                sga.append(round(float(tm[1]),2))
            avg=round(sum(sga)/len(sga),2)
            metric_data.update({"dbname":j_data[0]["metric"]["dbname"],"sid":j_data[0]["metric"]["instance_name"],"avg_sga":avg,"max_sga":max(sga)})
        else:
            message=f"getting Null for sga details for start time{st_time} and end time  {ed_time}"
            print(message)
        return metric_data
    except Exception as e:
        traceback.print_exc()
        message="error in getting octo sga metric in func - getdb_nodes_sga_details {0}".format(e)
        print(message)

def getdb_nodes_active_session_details(podname: str,exadata: str,st_time: str,ed_time: str) -> dict: 
    try:
        query=""
        with open(globalvariables.prom_file,'r') as promql_query_data:
            query_lines = promql_query_data.readlines()
        for line in query_lines:
                if line.split("##")[0] == "cpu_used_pct":
                    query= line.split("##")[1].strip()
        query_new = query.replace("pod_name",podname.lower().replace("-","_")).replace("exadata_instance",exadata)
        encoded_query=urllib.parse.quote(query_new,safe="")
        query_new="(({0}))".format(encoded_query)
        j_data=get_octo_metric_data(query_new,st_time,ed_time)
        cpu_io_wait_pct=[]
        metric_data={}
        if j_data:
            for tm in j_data[0]['values']:
                cpu_io_wait_pct.append(round(float(tm[1]),2))
            avg_io_wait_pct=round(sum(cpu_io_wait_pct)/len(cpu_io_wait_pct),2)
            metric_data.update({"avg_cpu_active_session":avg_io_wait_pct,"max_cpu_active_session":max(cpu_io_wait_pct)})
        else:
            message=f"getting Null for active session details for start time{st_time} and end time  {ed_time}"
            print(message)

        return metric_data
    except Exception as e:
        traceback.print_exc()
        message="error in getting db node active session cpu uses func - getdb_nodes_active_session_details {0}".format(e)
        print(message)

def getdb_nodes_cpu_details(podname: str,exadata: str,st_time: str,ed_time: str) -> dict: 
    try:
        query=""
        with open(globalvariables.prom_file,'r') as promql_query_data:
            query_lines = promql_query_data.readlines()
            #print(query_lines)
        for line in query_lines:
                if line.split("##")[0] == "cpu_utilization":
                    query= line.split("##")[1].strip()
        query_new = query.replace("pod_name",podname.lower().replace("-","_")).replace("exadata_instance",exadata)
        encoded_query=urllib.parse.quote(query_new,safe="")
        query_new="(({0}))".format(encoded_query)
        j_data=get_octo_metric_data(query_new,st_time,ed_time)
        cpu=[]
        metric_data={}
        if j_data:
            for tm in j_data[0]['values']:
                cpu.append(round(float(round(float(tm[1]),2)/100),2))
            avg=round(sum(cpu)/len(cpu),2)
            metric_data.update({"avg_db_cpu":avg,"max_db_cpu":max(cpu)})
        else:
            message=f"getting Null for node cpu details for start time{st_time} and end time  {ed_time}"
            print(message)
        return metric_data
    except Exception as e:
        traceback.print_exc()
        message="error in getting db cpu uses func - getdb_nodes_cpu_details {0}".format(e)
        print(message)

def pod_octo_metric(pod: str,st: str,et: str)->dict:
    """ Fetch the POD octo metric for all the associated exanodes using multi threading.  
    Args:
        podname (str): podname
        st (str): start time 
        et (str): end time 
    Returns:
        json_object (json): exa metric in json form.
        exa_list (array): return array  for all the exa nodes
    Raises:
        Exception: value error  
    """
    try:
        exa_list=cloud_meta.get_exadata_details(pod)
        file_name="{0}/{1}_pod_perf_data.json".format(globalvariables.exa_octo_data,pod)
        json_object={}
        if exa_list:
            with ThreadPoolExecutor() as executer:
                st_list=[st for i in range(len(exa_list))]
                et_list=[et for i in range(len(exa_list))]
                results=executer.map(get_exa_parameter_details, exa_list,st_list,et_list)
                for i in results:
                    json_object.update(i)
        exa_json_file_dump(json_object,file_name)  
        
        return json_object,exa_list      
    except Exception as e:
        traceback.print_exc()
        message="error in getting pod octo data func - pod_octo_metric {0}".format(e)
        print(message)

def main():
    start=time.time()
    pod_octo_metric("EINO-TEST","2023-11-26T00:00:45","2023-11-27T05:40:45")
    end=time.time()
    print(end-start)
    # print(exa_details)

if __name__ == "__main__":
    main()