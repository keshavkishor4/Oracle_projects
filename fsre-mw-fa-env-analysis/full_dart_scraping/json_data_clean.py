#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json,os,sys,glob,traceback,shutil,time
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from db_module import data_mining_db_con
from common import globalvariables
from concurrent.futures import ThreadPoolExecutor
import dict_dart
from datetime import datetime,timedelta

def clean_json_file(json_file: list)-> None:
    try:
        podname=json_file.split("/")[-1].split("_")[0]
        date=json_file.split("/")[-2]
        valid_data=[]
        with open(json_file,'r') as db_art:
            dart_data_list=json.loads(db_art.read())
        for j_data in dart_data_list:
            col_time=j_data["collected_time"].split("_")[0].replace("-","")
            if col_time == date:
                valid_data.append(j_data)
        if valid_data:
            dict_dart.json_file_dump(valid_data,json_file,"","pod")
        else:
            file_name=json_file.split("/")[-1]
            processed_dir=json_file.replace(file_name,"processed")
            processed_file="{0}/{1}".format(processed_dir,file_name)
            if not os.path.exists(processed_dir):
                os.mkdir(processed_dir)
            shutil.move(json_file,processed_file)

    except Exception as e:
          traceback.print_exc()
          message="{0} error in data insert {0}".format(globalvariables.AMBER,e)
          print(message)

def get_db_art_file_list(dir_path):
    try:
        file_str="{0}/*.json".format(dir_path)
        file_list=glob.glob(file_str)
        if file_list:
            with ThreadPoolExecutor(max_workers=10) as executer:
                result = executer.map(clean_json_file,file_list)
            # for db_art_file in file_list:
            #     clean_json_file(db_art_file)
    except Exception as e:
        traceback.print_exc()
        message="{0} error in getting file array for db art files {0}".format(globalvariables.AMBER,e)
        print(message)

def main():
    # date_range=["20231101"]
    try:
        if len(sys.argv) > 1:
            start=sys.argv[1]
            end=sys.argv[2]
            start_time=datetime.strptime(start,"%Y%m%d") 
            end_time=datetime.strptime(end,"%Y%m%d") 
            dates=dict_dart.get_date_time_list(start_time,end_time)
            for date in dates:
                dir_path="{0}/{1}".format(globalvariables.dart_data,date)
                print(dir_path)
                get_db_art_file_list(dir_path)
        
                    
        else:
            print("provide the range of start time and end time")
            sys.exit(1)
    except Exception as e:
        message="error on main {0}".format(e)
        print(message)

if __name__ == "__main__":
    main()