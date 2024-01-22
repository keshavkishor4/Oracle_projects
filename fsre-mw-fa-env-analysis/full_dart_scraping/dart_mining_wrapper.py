#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from datetime import datetime,timedelta
import os
import sys
import json
import time
from concurrent.futures import ThreadPoolExecutor
import traceback
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
import dict_dart

config_json=globalvariables.dart_config
with open(config_json,'r') as code:
    j_data=json.loads(code.read())
Module=j_data["module"]
#print(f'MODULE => {Module}')

#def get_all_dates_dart_archive()
def get_all_dates_dart_archive(user_srt_date: str, user_end_date: str, PODS: list=[], max_incident: str=0, Threads: str=10):
    """ Get all available dates from archive
    """
    try:
        start_time=datetime.strptime(user_srt_date,"%Y-%m-%d") 
        end_time=datetime.strptime(user_end_date,"%Y-%m-%d") 
        
        print("DURATION:  START %s, END %s" % (user_srt_date, user_end_date))
        dates=dict_dart.get_date_time_list(start_time,end_time)
        print("DATES:", dates)
        
        base_url="https://dashboards.odin.oraclecloud.com/cgi-bin/dart_dashboard?"
        for count,date in enumerate(dates):
            dict_data={}
            skipped_pods=[]
            All_pod_inc_row = []
            URL="{0}{1}".format(base_url,date)
            response=requests.get(URL)
            soup = BeautifulSoup(response.text, 'html.parser')
            rows=soup.find(class_="sortable").find("tbody").find_all("tr")
            All_pod_inc_row.extend(rows)
                
            for row in All_pod_inc_row:
                data=row.find_all('a',href=True)
                config_json=globalvariables.dart_config
                with open(config_json,'r') as code:
                    j_data=json.loads(code.read())
                MODULE=j_data["module"]

                if len(data) >0:
                    POD=data[0].string
                    #print("POD >", POD)
                    Tenancy=row.find_all()[2].text                    
                    Module=row.find_all()[5].text.upper()
                    
                    if 'FAaaS' in Tenancy or  Module not in MODULE:                               
                        #print(f'SKIPPED Tenancy -> {Tenancy} Module -> {Module} POD -> {POD}')     
                        skipped_pods.append(f'{Tenancy} {Module} {POD}')                      
                    else:         
                        Tenancy=row.find_all()[2].text                    
                        Module=row.find_all()[5].text
                        
                        if (PODS and POD in PODS) or (not PODS):
                            if POD not in dict_data:
                                dict_data.update({POD:{"base_url":[],"time_array":[],"color_array":[],"date_value":date}})
                            time_string=row.find_all()[6].string[0:16].replace(' ','_')
                            art_url="{0}{1}".format(globalvariables.odib_base_url,data[0]["href"])
                            if (max_incident == 0) or (len(dict_data[POD]["base_url"]) < max_incident):
                                dict_data[POD]["base_url"].append(art_url)
                                dict_data[POD]["time_array"].append(time_string)
                                dict_data[POD]["color_array"].append("")
            
            dirpath="{0}/{1}".format(globalvariables.dart_data,date)
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            pod_info_file="{0}/pod_info_log.txt".format(dirpath)
            dart_pod_input=[]
            for pod_data,value in dict_data.items():
                d={}
                d.update({"podname":pod_data,"base_url":value["base_url"],"time_array":value["time_array"],"color_array":value["color_array"],"date_value":date})
                if not value["base_url"]:
                    print(f'url not available for POD - {pod_data}')
                else:
                    url=value["base_url"][0]
                    length=len(value["base_url"])
                    with open(pod_info_file,'a') as pod_details:
                         pod_details.write(f'{pod_data}:{url}:{length}\n')
                dart_pod_input.append(d)
            
            
            t_batch=int(len(dart_pod_input)/10) + 1
            print(f'Total Batches={t_batch}')
            batch_start=0
            batch_size=10
            for batch_no in range(t_batch):
                print(f'Batch started => {batch_no}')
                batch=dart_pod_input[batch_start:batch_size]
                batch_start=batch_size
                batch_size+=10
            
                print("Total no of pods",len(dart_pod_input))
                with ThreadPoolExecutor(max_workers=Threads) as executer:
                        result = executer.map(dict_dart.get_pod_dart_data,batch)
                        for res,pod_info in zip(result,batch):
                            podname=pod_info["podname"]
                            time_value=pod_info["date_value"]
                            dart_json_file="{0}/{1}_pod_perf_data_{2}.json".format(dirpath,podname,time_value)
                            db_art_json_file="{0}/{1}_db_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                            ess_art_json_file="{0}/{1}_ess_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                            bi_art_json_file="{0}/{1}_bi_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                            mt_art_json_file="{0}/{1}_mt_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                            # if not os.path.exists(dart_json_file):
                            #     dict_dart.json_file_dump(r[0],dart_json_file,"","pod")
                            try:
                                if not os.path.exists(db_art_json_file) and res:
                                    dict_dart.json_file_dump(res[1],db_art_json_file,"","pod")
                                if not os.path.exists(ess_art_json_file) and res:
                                    dict_dart.json_file_dump(res[2],ess_art_json_file,"","pod")
                                if not os.path.exists(bi_art_json_file) and res:
                                    dict_dart.json_file_dump(res[3],bi_art_json_file,"","pod")
                                if not os.path.exists(mt_art_json_file) and res:
                                    dict_dart.json_file_dump(res[4],mt_art_json_file,"","pod")
                            except Exception as e:
                                message="error in getting thread executer result"
                                print(message)
            if len(dates)>1 and count<len(dates)-1:
                time.sleep(900)
                            
    except Exception as e:
        traceback.print_exc()
        message = "Error in mining data - get_all_dates_dart_archive {0},{1}".format(globalvariables.RED,e)
        print(message)

def main():
    #get_pod_dart_data(pdoname,starttime,endtime)
    #get_all_dates_dart_archive('2023-12-08:00','2023-12-09:00',['DDDD','HCRI'],3,1)
    #get_all_dates_dart_archive('2023-12-08:05','2023-12-10:13',['HCRI','HDIU'],5,2)
    #get_all_dates_dart_archive('2023-12-08:10','2023-12-08:15',[],2,5)
    #get_all_dates_dart_archive('2023-10-30:01','2023-10-30:23')
    #get_all_dates_dart_archive(sys.argv[1],sys.argv[2],sys.argv[3])
    get_all_dates_dart_archive(sys.argv[1],sys.argv[2])

if __name__ == "__main__":
    main()
