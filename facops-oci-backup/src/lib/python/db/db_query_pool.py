#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      db_query_pool.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)
    Srinivas Nallur : added execute query logic
    Saritha Gireddy       08/28/20 - initial version (code refactoring)
"""
#### imports start here ##############################
import os
import socket
import sys
from time import strftime, gmtime
import cx_Oracle
import json
import threading


BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables
#### imports end here ##############################
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
def execute_query(key, value):
    try:
        con = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA, encoding="UTF-8")
        ConnectionTimeout=globalvariables.db_con_timeout
        # con.callTimeout=ConnectionTimeout
        session_timer = threading.Timer(ConnectionTimeout,con.cancel)
        session_timer.start()
        cursor = con.cursor()
        cursor.execute(value.strip())
        result = cursor.fetchall()
        session_timer.cancel()
        if not result:
          return ""
        return result
    except Exception as e:
        message = "Failed to execute query for {0} {1}...".format(key,e)
        apscom.warn(message)
        raise

def text_to_dict(text_file):
    try:
        db_query_input = {}
        with open(globalvariables.DB_QUERY_LOCATION+"/"+text_file) as f:
            for line in f:
                (key, val) = line.split(":##")
                db_query_input[key] = val
        query_output_map = {}
        dbsid=None
        for key, value in db_query_input.items():
            output=execute_query(key.strip(), value)
            if isinstance(output,list):
                value = [list(tup) for tup in output]
                if len(value)==1:
                    if len(value[0])==1:
                        query_output_map[key.strip()]=value[0][0]
                    else:
                        query_output_map[key.strip()] = value[0]
                else:
                   query_output_map[key.strip()]=value
                if key.strip() == "ORACLE_SID":
                    dbsid = value[0][0]
            else:
                query_output_map[key.strip()]=""
        dir_path=globalvariables.DB_BACKUP_LOG_PATH+"/"+dbsid
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        file_name = dir_path+'/'+globalvariables.HOST_NAME+"_"+dbsid+"_query.json"
        if os.path.exists(file_name):
            rename_older_sql(file_name)
        f.close()
        try:
            with open(file_name, 'w') as fp:
                json.dump(query_output_map, fp,indent=4, sort_keys=True)
            #return file name
            fp.close()
            return file_name
        except Exception as e:
            #post catalog_ db
            message = "Failed to generate json {0} ...".format(e)
            apscom.warn(message)
            raise
    except Exception as e:
        message = "Failed to convert data to dictionary {0} ...".format(e)
        apscom.warn(message)
        raise
def rename_older_sql(file_name):
    try:
        if(os.path.exists(file_name)):
            os.rename(file_name,file_name+"_"+timestamp)
    except Exception as e:
        message = "Failed to rename older file {0} ...".format(e)
        apscom.warn(message)
        raise
def verify_connection():
    global con
    try:
        con = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA, encoding="UTF-8")
    except Exception as e:
        message = "Failed to connect database!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)

def verify_remote_connection(host,dbname,syspass):
    global con1
    try:
        dsn="{0}:1521/{1}".format(host,dbname)
        con1 = cx_Oracle.Connection(user="sys", password=syspass, dsn=dsn,mode=cx_Oracle.SYSDBA, encoding="UTF-8")
        return True 
    except Exception as e:
        message = "Failed to connect database with connect string {2} !\n{0}{1}".format(sys.exc_info()[1:2], e,dsn)
        apscom.warn(message)
        raise Exception(message)
def main():
    try:
        verify_connection()
        text_file = sys.argv[1]
        file_name=text_to_dict(text_file)
        return file_name
    except Exception as e:
        message = "Failed to execute the query {0} ...".format(e)
        apscom.warn(message)
        raise
if __name__ == "__main__":
    file_name=main()
    print(file_name)