#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from datetime import datetime,timedelta
import os
import json
import unittest
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables,commonutils
from db_module import db_con
from dart_scraping import db_art,ess_dart,bi_dart,mt_dart

config_json=globalvariables.dart_config
with open(config_json,'r') as code:
    j_data=json.loads(code.read())
color=j_data["color"]
module=j_data["module"]

@globalvariables.timer
def get_pod_dart_data(podname: str,start_time: str,end_time: str)-> list:
    """ Implemented the multi threading and write the scrapped json data to given file and to database
        Args:
            podname (str): podname for which dart needs to be scrap
            start_time (str): dart scrap duration start time
            end_time (str):dart scrap duration end time
        Returns:
            all_files (list): return all dart type files location
        Raises:
            Exception: tag error 
        """
    try:
        delta=timedelta(hours=1)
        sd_time_obj=datetime.strptime(start_time,"%Y-%m-%d:%H") 
        sd_time_obj=sd_time_obj - delta
        ed_time_obj=datetime.strptime(end_time,"%Y-%m-%d:%H") 
        ed_time_obj=ed_time_obj + delta
        end_time_string=datetime.strftime(ed_time_obj,"%Y-%m-%d:%H")
        dart_pod,all_db_art,all_ess_art,all_bi_art,all_mt_art=[],[],[],[],[]
        dart_json_file="{0}/{1}_pod_perf_data_{2}.json".format(globalvariables.dart_data,podname,end_time_string)
        db_art_json_file="{0}/{1}_db_art_perf_data_{2}.json".format(globalvariables.dart_data,podname,end_time_string)
        ess_art_json_file="{0}/{1}_ess_art_perf_data_{2}.json".format(globalvariables.dart_data,podname,end_time_string)
        bi_art_json_file="{0}/{1}_bi_art_perf_data_{2}.json".format(globalvariables.dart_data,podname,end_time_string)
        mt_art_json_file="{0}/{1}_mt_art_perf_data_{2}.json".format(globalvariables.dart_data,podname,end_time_string)
        #sample=    ://dashboards.odin.oraclecloud.com/cgi-bin/dart_dashboard?20230920
        date_list=get_date_time_list(sd_time_obj,ed_time_obj)
        sd_array=[sd_time_obj for i in range(len(date_list))]
        pod_array=[podname for i in range(len(date_list))]
        ed_array=[ed_time_obj for i in range(len(date_list))]
        # print(sd_array,pod_array,ed_array)
        #Implemented multithreading as below 
        with ThreadPoolExecutor() as executer:
            result = executer.map(dart_multi_module_data, pod_array,date_list,sd_array,ed_array)
            for i in result:
                dart_pod.append(i[0]),all_db_art.append(i[1]),all_ess_art.append(i[2]),all_bi_art.append(i[3]),all_mt_art.append(i[4])
        #writing dart data to json file 
        json_file_dump(dart_pod,dart_json_file,podname,"pod")
        #writing db_art data to json file 
        json_file_dump(all_db_art,db_art_json_file,podname,"db")
        #writing ess_art data to json file
        json_file_dump(all_ess_art,ess_art_json_file,podname,"ess")
        #writing ess_art data to json file
        json_file_dump(all_bi_art,bi_art_json_file,podname,"bi")
        #writing ess_art data to json file
        json_file_dump(all_mt_art,mt_art_json_file,podname,"mt")
        return [ dart_json_file,db_art_json_file,ess_art_json_file,bi_art_json_file,mt_art_json_file ]
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting dart data for pod func - get_pod_dart_data {0},{1}".format(globalvariables.RED,podname,e)
        print(message)

#json_file_dump -> this function with write the scrapped json data to given file and to database. 
def json_file_dump(json_data: dict,file_name: str,podname: str,comp_type: str)->None:
    """ write the scrapped json data to given file and to database
        Args:
            json_data (json): scrapped dart data in json format
            file_name (str): filename to save json in file
            podname (str): pod name
            comp_type (str): dart type "pod,db,ess,bi,mt" for db table
        Returns:
            None
        Raises:
            Exception: db connection error 
        """
    try:
        # final_json={}
        # final_json.update({podname:json_data})
        # print(type(json.loads(str(json_data))))
        json_object = json.dumps(json_data, indent=4)
        if not os.path.exists(globalvariables.dart_data):
                    os.makedirs(globalvariables.dart_data)   
        with open(file_name,'w') as dart_data:
                dart_data.write(json_object)
        # print(str(json_data))
        #writing json files to db 
        # if json_data:
        #     print("{0}writing the given json to db {1}".format(globalvariables.GREEN,file_name))
        #     db_con.dml_operation(str(json_data),podname,comp_type)
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in writing json data in file - {1},{2}".format(globalvariables.RED,file_name,e)
        print(message)

def dart_bi_multithread(mt_dart_array: list)-> list:
    """ implemented the multi threading to parse bi dart data
        Args:
            mt_dart_array (list): array to get the bi dart url to scrap the data
        Returns:
            bi_dart_array (list): return scrapped bi dart array
        Raises:
            Exception: tag error 
        """
    try:
        bi_dart_array=[]
        for value in mt_dart_array:
            if "biart_summary" in value["dict_data"] and value["dict_data"]["biart_summary"]:
                bi_url=value["url"].replace("ART_Summary.html","bi_art.html")
                bi_dart_array.append(value)
                ind=bi_dart_array.index(value)
                bi_dart_array[ind].update({"bi_url":bi_url})
            else:
                bi_dart_array.append(value)
                ind=bi_dart_array.index(value)
                bi_dart_array[ind].update({"bi_url":None})
        bi_urls=[]
        for data in  bi_dart_array:
            bi_urls.append(data["bi_url"])   
        bi_results=odin_dart_threading(bi_dart.get_dart_html_data, bi_urls)
        for count, _ in enumerate(bi_urls):
            bi_dart_array[count].update({"bi_dart_dict":next(bi_results)})

        return bi_dart_array
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting ess dart data fun dart_mt_multithread - {1}".format(globalvariables.RED,e)
        print(message)

def dart_mt_multithread(ess_dart_array: list)-> list:
    """ implemented the multi threading to parse mt dart data
        Args:
            ess_dart_array (list): array to get the mt dart url to scrap the data
        Returns:
            mt_dart_array (list): return scrapped mt dart array
        Raises:
            Exception: tag error 
        """
    try:
        mt_dart_array=[]
        for value in ess_dart_array:
            if "middle_tier_servers_summary" in value["dict_data"] and value["dict_data"]["middle_tier_servers_summary"]:
                mt_url=value["url"].replace("ART_Summary.html","MTArt.html")
                mt_dart_array.append(value)
                ind=mt_dart_array.index(value)
                mt_dart_array[ind].update({"mt_url":mt_url})
            else:
                mt_dart_array.append(value)
                ind=mt_dart_array.index(value)
                mt_dart_array[ind].update({"mt_url":None})
        mt_urls=[]
        for data in  mt_dart_array:
            mt_urls.append(data["mt_url"])   
        mt_results=odin_dart_threading(mt_dart.get_dart_html_data, mt_urls)
        for count, _ in enumerate(mt_urls):
            mt_dart_array[count].update({"mt_dart_dict":next(mt_results)})

        return mt_dart_array
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting ess dart data fun dart_mt_multithread - {1}".format(globalvariables.RED,e)
        print(message)

def dart_ess_multithread(db_dart_array: list)-> list:
    """ implemented the multi threading to parse ess dart data
        Args:
            db_dart_array (list): array to get the ess dart url to scrap the data
        Returns:
            ess_dart_array (list): return scrapped ess dart array
        Raises:
            Exception: tag error 
        """
    try:
        ess_dart_array=[]
        for value in db_dart_array:
            if value["dict_data"]["essart_summary"]:
                uri=[ url["uri"] for url in value["dict_data"]["essart_summary"] if type(url) == dict ]
                if uri:
                    uri="{0}/ess_art.html".format(uri[0])
                    ess_url=value["url"].replace("ART_Summary.html",uri)
                else:
                    ess_url=value["url"].replace("ART_Summary.html","ess_art.html")
                print(f'essurl -> {ess_url}')
                ess_dart_array.append(value)
                ind=ess_dart_array.index(value)
                ess_dart_array[ind].update({"ess_url":ess_url})
            else:
                ess_dart_array.append(value)
                ind=ess_dart_array.index(value)
                ess_dart_array[ind].update({"ess_url":None})
        ess_urls=[]
        for data in  ess_dart_array:
            ess_urls.append(data["ess_url"])   
        ess_results=odin_dart_threading(ess_dart.get_dart_html_data, ess_urls)
        for count, _ in enumerate(ess_urls):
            ess_dart_array[count].update({"ess_dart_dict":next(ess_results)})

        return ess_dart_array
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting ess dart data fun dart_ess_multithread - {1}".format(globalvariables.RED,e)
        print(message)

def dart_db_multithread(results: list,time_array: list,url_array: list)-> list:
    """ implemented the multi threading to parse db dart data
        Args:
            dart parsed result from multithread func (generator): array to get the scrapped pod data and db dart url to scrap the db dart
        Returns:
            bi_dart_array (list): return scrapped db dart array
        Raises:
            Exception: tag error 
        """
    try:
        dart_array=[]
        for count,t_key in enumerate(time_array):
            pod_perf_metric={}
            pod_perf_metric.update({"time":t_key,"url":url_array[count],"dict_data":next(results)})
            dart_array.append(pod_perf_metric)
        db_dart_array=[]
        for value in dart_array:
            # print(value,"\n")
            if "db_performance" in value["dict_data"] and value["dict_data"]["db_performance"]:
                db_url=value["url"].replace("ART_Summary.html",value["dict_data"]["db_art_url"])
                db_dart_array.append(value)
                ind=db_dart_array.index(value)
                db_dart_array[ind].update({"db_url":db_url})
            else:
                db_dart_array.append(value)
                ind=db_dart_array.index(value)
                db_dart_array[ind].update({"db_url":None})
                # print(f'URLK -> {value["url"]}')
            
        db_urls=[]
        for data in  db_dart_array:
            db_urls.append(data["db_url"])   
        db_results=odin_dart_threading(db_art.get_dart_html_data, db_urls)
        for count, _ in enumerate(db_urls):
            db_dart_array[count].update({"db_dart_dict":next(db_results)})
        return db_dart_array
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting db dart data for fun dart_db_multithread - {1}".format(globalvariables.RED,e)
        print(message)

@globalvariables.timer
def odin_dart_threading(func: str,*arg: list)-> list:
    """ Implemented  multithreading for given function
        Args:
            func (function): function needs to be call in multithreading
        Returns:
            result (list): return scrapped dart array
        Raises:
            Exception: tag error 
        """
    try:
        with ThreadPoolExecutor() as executer:
            results=executer.map(func, *arg)
        return results
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting dart data for fun odin_dart_threading - {1}".format(globalvariables.RED,e)
        print(message)

def get_date_time_list(start_time: str,end_time: str)-> list:
    """ generate the list of dates present in given duration
        Args:
            start_time (str): duration start time
            end_time (str): duration end time
        Returns:
            dates (list): return list of dates present in given duration
        Raises:
            Exception: tag error 
        """
    try:
        dates=[]
        # sd=datetime.strptime(start_time,"%Y-%m-%d:%H") 
        # ed=datetime.strptime(end_time,"%Y-%m-%d:%H") 
        delta=timedelta(days=1)
        while start_time <= end_time:
            str_sd=datetime.strftime(start_time,"%Y%m%d")
            dates.append(str_sd)
            start_time+=delta
        return dates
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in get_date_time_list - {1}".format(globalvariables.RED,e)
        print(message)

def pod_dart_url_json(pod: str,html_data: str,sd_time_obj: object,ed_time_obj: object)-> list:
    """ generate the list of dates present in given duration
        Args:
            pod (str): podname to filter pod specific data
            html_data (str): html data needs to be parse
            sd_time_obj (time object): duration start time in time object
            ed_time_obj (time object): duration end time in time object
        Returns:
            time_array (list): return list of time array for parsing 
            url_array (list): return list of urls needs to parsed 
            color_array (list): return list of color code to filter data

        Raises:
            Exception: tag error 
        """ 
    try:
        time_array=[]
        url_array=[]
        color_array=[]
        soup = BeautifulSoup(html_data, 'html.parser')
        rows=soup.find(class_="sortable").find("tbody").find_all("tr")
        for row in rows:
            data=row.find_all('a',href=True)
            # print(data[0]["href"])
            if len(data) >0 and data[0].string == pod and row.find_all()[5].text.upper() in module:
                time_string=row.find_all()[6].string[0:16].replace(' ','_')
                if data[0]["href"] and time_string:
                    URL ="{0}{1}".format(globalvariables.odib_base_url,data[0]["href"])
                    # print(URL)
                    conv_dt=datetime.strptime(time_string,"%Y-%m-%d_%H:%M")
                    if sd_time_obj < conv_dt < ed_time_obj:
                        # print(URL)
                        # pod_url.update({time_string:URL})
                        time_array.append(time_string)
                        url_array.append(URL)
                        color_array.append(color)
                    # else:
                    #     print(f'time -> {conv_dt} URL -> {URL} string -> {time_string}')
                # print(row.find_all()[6].string[0:13].replace(' ',':'))
        # print( /len(pod_url))
        return url_array,time_array,color_array
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in pod_dart_url_json for pod  - {1}{2}".format(globalvariables.RED.pod,e)
        print(message)

def get_pod_perf_metric(URL: str,time_key: str,color: str)-> dict:
    """ scrapped the pod perf metric for give arguments 
        Args:
            URL (str): url needs to parse
            time_key (str):time key for collected time stamp in json
            color (str): color code to filter the data
        Returns:
            dart_dic (dict): scrapped json for given pod and time duration. 
        Raises:
            Exception: tag error 
        """
    try:
        # print(f'dart url ->{URL}')
        response=commonutils.get_request_data(URL)
        soup = BeautifulSoup(response.text, 'html.parser')
        tables=soup.find_all('table')[-1].find_all(['td','th'])
        dart_dic={}
        t_header=""
        for tr in tables:
            if tr.name != 'th':
                if color:
                    if tr.text and tr.find('font') and tr.find('font')["color"] == color:
                        dart_dic[t_header].append(tr.text.strip().lower().replace(" ","_"))
                else:
                    dart_dic[t_header].append(tr.text.strip().lower().replace(" ","_"))
                if tr.find_all('a') and tr.find('a').string == "DBArt report":
                    dart_dic.update({"db_art_url":tr.find('a')['href']})
            else:
                if tr.text.strip().split()[0] == "ESS":
                    uri_no=tr.text.strip().split()[1]
                else:
                    uri_no=None
                t_header=tr.text.strip().lower().replace(" ","_")
                t_header = ''.join([i for i in t_header if not i.isdigit()]).replace("__","")
                # print(f'dart url tables ->{t_header} url -> {URL}')
                dart_dic.update({t_header:[]})
                if uri_no:
                    uri={"uri":uri_no}
                    dart_dic[t_header].append(uri)

        dart_dic.update({"URL":URL,"Collected_time":time_key})
        # if "ess_20332118_art_summary" in dart_dic:
        #     print(f'dart url tables ->{dart_dic}')
        return dart_dic
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in getting get_pod_perf_metric  for URL {1}{2}".format(globalvariables.RED,URL,e)
        print(message)

class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_pod_dart_url(self):
        actual = get_pod_dart_data("EINO")
        expected = 8
        self.assertEqual(actual, expected)


def dart_multi_module_data(podname: str,dd: str,sd_time_obj: str,ed_time_obj: str)-> dict:
    """ get the dart data for all the module (DB,MT,BI,ESS) 
        Args:
            podname (str): podname for which dart needs to be scrap
            dd (str): date for which scraping needs to be done
            sd_time_obj (date time obj): dart scrap duration start time
            ed_time_obj (date time obj):dart scrap duration end time
        Returns:
            dart_pod, all_db_art, all_ess_art, all_bi_art, all_mt_art (dict): json data for all the modules
        Raises:
            Exception: tag error 
        """
    try:
        dart_pod,all_db_art,all_ess_art,all_bi_art,all_mt_art={},{},{},{},{}
        if dd:
            URL="{0}{1}".format(globalvariables.dart_base_url,dd)
            response=commonutils.get_request_data(URL)
            url_array,time_array,color_array=pod_dart_url_json(podname,response.text,sd_time_obj,ed_time_obj)
            results=odin_dart_threading(get_pod_perf_metric,url_array,time_array,color_array)
            db_dart_array=dart_db_multithread(results,time_array,url_array)
            ess_dart_array=dart_ess_multithread(db_dart_array)
            mt_dart_array=dart_mt_multithread(ess_dart_array)
            bi_dart_array=dart_bi_multithread(mt_dart_array)
            
            for value in bi_dart_array:
                if value["url"] :
                    if value["dict_data"]:
                        dart_pod.update(value["dict_data"])
                        if "db_performance" in value["dict_data"]:
                            if value["dict_data"]["db_performance"]:
                                if value["db_dart_dict"]:
                                    value["db_dart_dict"].update({"collected_time":value["time"]})
                                    value["db_dart_dict"].update({"db_url":value["db_url"]})
                                    all_db_art.update(value["db_dart_dict"])
                        if "essart_summary" in value["dict_data"]:
                            if value["dict_data"]["essart_summary"]:
                                if value["ess_dart_dict"]:
                                    value["ess_dart_dict"].update({"collected_time":value["time"]})
                                    value["ess_dart_dict"].update({"ess_url":value["ess_url"]})
                                    all_ess_art.update(value["ess_dart_dict"])
                        if "biart_summary" in value["dict_data"]:
                            if value["dict_data"]["biart_summary"]:
                                if value["bi_dart_dict"]:
                                    value["bi_dart_dict"].update({"collected_time":value["time"]})
                                    value["bi_dart_dict"].update({"bi_url":value["bi_url"]})
                                    all_bi_art.update(value["bi_dart_dict"])
                        if "middle_tier_servers_summary" in value["dict_data"]:
                            if value["dict_data"]["middle_tier_servers_summary"]:
                                if value["mt_dart_dict"]:
                                    value["mt_dart_dict"].update({"collected_time":value["time"]})
                                    value["mt_dart_dict"].update({"mt_url":value["mt_url"]})
                                    all_mt_art.update(value["mt_dart_dict"])
                    else:
                        message="{0}Could not get dart dict for URL -> {1}".format(globalvariables.AMBER,value["url"])
                        print(message)
                else:
                    message="{0}Could not found URL for time stamp or url time is out of requested time window  -> {1}".format(globalvariables.AMBER,value["time"])
                    print(message)
        
        # print(all_ess_art)
        return dart_pod, all_db_art, all_ess_art, all_bi_art, all_mt_art
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting dart data for pod func dart_multi_module_data - {0},{1}".format(globalvariables.RED,podname,e)
        print(message)
    
def main():
    #get_pod_dart_data(pdoname,starttime,endtime)
    get_pod_dart_data("EINO-TEST","2023-11-28:07","2023-11-30:08")

if __name__ == "__main__":
    main()