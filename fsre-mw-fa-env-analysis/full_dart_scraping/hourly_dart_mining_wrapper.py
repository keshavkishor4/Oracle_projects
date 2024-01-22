#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from datetime import datetime,timedelta
from mining_dart_db_insert import *
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
def get_all_dates_dart_archive():
    """ Get all available dates from archive
    """
    try:
        now=datetime.now()
        delta=timedelta(hours=1)
        dt_string = now.strftime("%d-%m-%Y:%H")
        dart_date=now.strftime("%Y%m%d")
        start_time=datetime.strptime(dt_string,"%d-%m-%Y:%H") - delta
        file_date= start_time.strftime("%d%m%Y_%H")
        end_time=datetime.strptime(dt_string,"%d-%m-%Y:%H")
        print(start_time,end_time)
        base_url="https://dashboards.odin.oraclecloud.com/cgi-bin/dart_dashboard?"
        dict_data={}
        URL="{0}{1}".format(base_url,dart_date)
        print(URL)
        response=requests.get(URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        rows=soup.find(class_="sortable").find("tbody").find_all("tr")
        config_json=globalvariables.dart_config
        with open(config_json,'r') as code:
            j_data=json.loads(code.read())
        req_module=j_data["module"]
        
        for row in rows:
            data=row.find_all('a',href=True)
            if len(data) >0:
                POD=data[0].string
                #print("POD >", POD)
                Tenancy=row.find_all()[2].text                    
                module=row.find_all()[5].text.upper()
                
                if 'FAaaS' in Tenancy or  module not in req_module:                               
                    #print(f'SKIPPED Tenancy -> {Tenancy} Module -> {Module} POD -> {POD}')     
                    pass                      
                else:         
                    Tenancy=row.find_all()[2].text 
                    module=row.find_all()[5].text
                    time_string=row.find_all()[6].string[0:16].replace(' ','_')
                    # "2023-11-01_22:16"
                    date_time_string=datetime.strptime(time_string,"%Y-%m-%d_%H:%M")
                    if start_time < date_time_string < end_time:
                        if POD not in dict_data:
                            dict_data.update({POD:{"base_url":[],"time_array":[],"color_array":[],"date_value":file_date}})
                        dart_url="{0}{1}".format(globalvariables.odib_base_url,data[0]["href"])
                        dict_data[POD]["base_url"].append(dart_url)
                        dict_data[POD]["time_array"].append(time_string)
                        dict_data[POD]["color_array"].append("")
        
        dirpath="{0}/{1}".format(globalvariables.dart_data,dart_date)
        processed_dirpath="{0}/processed".format(dirpath)
        if not os.path.exists(dirpath):
            os.mkdir(dirpath)
        pod_info_file="{0}/pod_info_log.txt".format(dirpath)
        dart_pod_input=[]
        for pod_data,value in dict_data.items():
            d={}
            d.update({"podname":pod_data,"base_url":value["base_url"],"time_array":value["time_array"],"color_array":value["color_array"],"date_value":file_date})
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
            with ThreadPoolExecutor(max_workers=10) as executer:
                    result = executer.map(dict_dart.get_pod_dart_data,batch)
                    for res,pod_info in zip(result,batch):
                        podname=pod_info["podname"]
                        time_value=pod_info["date_value"]
                        # dart_json_file="{0}/{1}_pod_perf_data_{2}.json".format(dirpath,podname,time_value)
                        
                        db_art_json_file="{0}/{1}_db_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                        ess_art_json_file="{0}/{1}_ess_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                        bi_art_json_file="{0}/{1}_bi_art_perf_data_{2}.json".format(dirpath,podname,time_value)
                        mt_art_json_file="{0}/{1}_mt_art_perf_data_{2}.json".format(dirpath,podname,time_value)

                        processed_db_art_json_file="{0}/{1}_db_art_perf_data_{2}.json".format(processed_dirpath,podname,time_value)
                        processed_ess_art_json_file="{0}/{1}_ess_art_perf_data_{2}.json".format(processed_dirpath,podname,time_value)
                        processed_mt_art_json_file="{0}/{1}_mt_art_perf_data_{2}.json".format(processed_dirpath,podname,time_value)
                        processed_bi_art_json_file="{0}/{1}_bi_art_perf_data_{2}.json".format(processed_dirpath,podname,time_value)
                        
                        # if not os.path.exists(dart_json_file):
                        #     dict_dart.json_file_dump(r[0],dart_json_file,"","pod")
                        try:
                            if not os.path.exists(db_art_json_file) and not os.path.exists(processed_db_art_json_file) and res:
                                dict_dart.json_file_dump(res[1],db_art_json_file,"","pod")
                            if not os.path.exists(ess_art_json_file) and not os.path.exists(processed_ess_art_json_file) and res:
                                dict_dart.json_file_dump(res[2],ess_art_json_file,"","pod")
                            if not os.path.exists(bi_art_json_file) and not os.path.exists(processed_bi_art_json_file) and res:
                                dict_dart.json_file_dump(res[3],bi_art_json_file,"","pod")
                            if not os.path.exists(mt_art_json_file) and not os.path.exists(processed_mt_art_json_file) and res:
                                dict_dart.json_file_dump(res[4],mt_art_json_file,"","pod")
                        except Exception as e:
                            message="error in getting thread executer result"
                            print(message)
                        
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
    get_all_dates_dart_archive()
    now=datetime.now()
    dart_date=now.strftime("%Y%m%d")
    dir_path="{0}/{1}".format(globalvariables.dart_data,dart_date)
    get_db_art_file_list(dir_path)


if __name__ == "__main__":
    main()
