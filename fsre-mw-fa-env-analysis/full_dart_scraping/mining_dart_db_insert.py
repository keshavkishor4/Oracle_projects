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
        dart_array=[]
        for j_data in dart_data_list:
            col_time=j_data["collected_time"]
            para_tuple=(j_data,col_time,podname)
            dart_array.append(para_tuple)   
        if dart_array:
            try:
                length=len(dart_array)
                print(f'procssing file {json_file} with length {length}')
                data_mining_db_con.dml_operation_many(dart_array)
            except Exception as e:
                traceback.print_exc()
                message="error in data insert for pod  {0} and json {1}".format(podname,json_file)
                print(message)
                print(f'file name -> {json_file}')
                raise
            file_name=json_file.split("/")[-1]
            processed_dir=json_file.replace(file_name,"processed")
            processed_file="{0}/{1}".format(processed_dir,file_name)
            if not os.path.exists(processed_dir):
                os.mkdir(processed_dir)
            shutil.move(json_file,processed_file)
    except Exception as e:
          traceback.print_exc()
          message="{0} error in data insert for file => {1} {2}".format(globalvariables.AMBER,json_file,e)
          print(message)

def ess_art_json_insert(json_file: list)-> None:
    try:
        podname=json_file.split("/")[-1].split("_")[0]
        with open(json_file,'r') as ess_art:
            dart_data_list=json.loads(ess_art.read())

        dart_array=[]
        for j_data in dart_data_list:
            col_time=j_data["collected_time"]
            para_tuple=(j_data,col_time,podname)
            dart_array.append(para_tuple)   
        if dart_array:
            try:
                length=len(dart_array)
                print(f'procssing file {json_file} with length {length}')
                data_mining_db_con.ess_dml_operation(dart_array)
            except Exception as e:
                traceback.print_exc()
                message="error in data insert for pod  {0} and json {1}".format(podname,json_file)
                print(message)
                print(f'file name -> {json_file}')
                raise
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

def bi_art_json_insert(json_file: list)-> None:
    try:
        podname=json_file.split("/")[-1].split("_")[0]
        file_size=int(os.path.getsize(json_file)/1000000)
        with open(json_file,'r') as ess_art:
            dart_data_list=json.loads(ess_art.read())

        dart_array=[]
        for j_data in dart_data_list:
            col_time=j_data["collected_time"]
            para_tuple=(j_data,col_time,podname)
            dart_array.append(para_tuple)   
        if dart_array:
            try:
                length=len(dart_array)
                if file_size > 3:
                    print(f'procssing file {json_file}')
                    t_batch=int(length/2) + 1
                    print(f'Total Batches={t_batch}')
                    batch_start=0
                    batch_size=2
                    for batch_no in range(t_batch):
                        print(f'Batch started => {batch_no}')
                        batch=dart_array[batch_start:batch_size]
                        batch_start=batch_size
                        batch_size+=2
                        data_mining_db_con.bi_dml_operation(batch)
                else:
                    print(f'procssing file {json_file} with length {length}')
                    data_mining_db_con.bi_dml_operation(dart_array)
            except Exception as e:
                traceback.print_exc()
                message="error in data insert for pod  {0} and json {1}".format(podname,json_file)
                print(message)
                print(f'file name -> {json_file}')
                raise
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

def mt_art_json_insert(json_file: list)-> None:
    try:
        podname=json_file.split("/")[-1].split("_")[0]
        with open(json_file,'r') as ess_art:
            dart_data_list=json.loads(ess_art.read())

        dart_array=[]
        for j_data in dart_data_list:
            col_time=j_data["collected_time"]
            para_tuple=(j_data,col_time,podname)
            dart_array.append(para_tuple)   
        if dart_array:
            try:
                length=len(dart_array)
                print(f'procssing file {json_file} with length {length}')
                data_mining_db_con.mt_dml_operation(dart_array)
            except Exception as e:
                traceback.print_exc()
                message="error in data insert for pod  {0} and json {1}".format(podname,json_file)
                print(message)
                print(f'file name -> {json_file}')
                raise
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

@globalvariables.timer
def get_db_art_file_list(dir_path):
    try:
        file_str="{0}/*db_art_perf*".format(dir_path)
        file_list=glob.glob(file_str)
        if file_list:
            # with ThreadPoolExecutor(max_workers=3) as executer:
            #     result = executer.map(db_art_json_insert,file_list)
            for db_art_file in file_list:
                db_art_json_insert(db_art_file)
    except Exception as e:
        traceback.print_exc()
        message="{0} error in getting file array for db art files {0}".format(globalvariables.AMBER,e)
        print(message)

@globalvariables.timer
def get_ess_art_file_list(dir_path):
    try:
        file_str="{0}/*ess_art_perf*".format(dir_path)
        file_list=glob.glob(file_str)
        if file_list:
            # with ThreadPoolExecutor(max_workers=3) as executer:
            #     result = executer.map(ess_art_json_insert,file_list)
            for db_art_file in file_list:
                ess_art_json_insert(db_art_file)
    except Exception as e:
        traceback.print_exc()
        message="{0} error in getting file array for ess art files {0}".format(globalvariables.AMBER,e)
        print(message)

@globalvariables.timer
def get_bi_art_file_list(dir_path):
    try:
        file_str="{0}/*bi_art_perf*".format(dir_path)
        file_list=glob.glob(file_str)
        if file_list:
            # with ThreadPoolExecutor(max_workers=3) as executer:
            #     result = executer.map(bi_art_json_insert,file_list)
            for db_art_file in file_list:
                bi_art_json_insert(db_art_file)
    except Exception as e:
        traceback.print_exc()
        message="{0} error in getting file array for ess art files {0}".format(globalvariables.AMBER,e)
        print(message)

@globalvariables.timer
def get_mt_art_file_list(dir_path):
    try:
        file_str="{0}/*mt_art_perf*".format(dir_path)
        file_list=glob.glob(file_str)
        if file_list:
            # with ThreadPoolExecutor(max_workers=3) as executer:
            #     result = executer.map(mt_art_json_insert,file_list)
            for db_art_file in file_list:
                mt_art_json_insert(db_art_file)
    except Exception as e:
        traceback.print_exc()
        message="{0} error in getting file array for ess art files {0}".format(globalvariables.AMBER,e)
        print(message)

def main():
    # date_range=["20231103"]
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
                get_ess_art_file_list(dir_path)
                get_bi_art_file_list(dir_path)
                get_mt_art_file_list(dir_path)
                # with ThreadPoolExecutor(max_workers=4) as executer:
                #     executer.submit(get_db_art_file_list,dir_path)
                #     executer.submit(get_ess_art_file_list,dir_path)
                #     executer.submit(get_bi_art_file_list,dir_path)
                #     executer.submit(get_mt_art_file_list,dir_path)
        else:
            print("provide the range of start time and end time")
            sys.exit(1)
    except Exception as e:
        message="error on main {0}".format(e)
        print(message)

if __name__ == "__main__":
    main()

