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

def db_art_json_insert(json_file: list)-> None:
    try:
        podname=json_file.split("/")[-1].split("_")[0]
        with open(json_file,'r') as db_art:
            dart_data_list=json.loads(db_art.read())

        for j_data in dart_data_list:
            col_time=j_data["collected_time"]
            try:
                time.sleep(5)
                data_mining_db_con.dml_operation(podname,col_time,json.dump(j_data))
            except Exception as e:
                traceback.print_exc()
                message="error in data insert for pod  {0} and json {1}".format(podname,j_data)
                print(message)
                print(f'file name -> {json_file}')
        
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

def main():
    file_name=sys.argv[1]
    db_art_json_insert(file_name)

if __name__ == "__main__":
    main()

