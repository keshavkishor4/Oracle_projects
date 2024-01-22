#!/usr/bin/env python
# -*- coding: utf-8 -*-
import oracledb
import getpass
import os
import sys
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
# import pandas as pd
import json
import traceback

def get_cursor():
     try:
          un = 'faenv'
          cs = 'localhost:1521/faopspdb.ad1.fusionappsdphx1.oraclevcn.com'
          passwd = "welcome123"
          con=oracledb.connect(
               user=un,
               password=passwd,
               dsn=cs)
          return con
     except Exception as e:
          traceback.print_exc()
          message="{0} error in getting connection from db {0}".format(globalvariables.AMBER,e)
          print(message)

def dml_operation_many(dart_list):
     try:
          con=get_cursor()
          cursor = con.cursor()
          inssql="INSERT INTO DBART_STAGE_TEMP (J_DATA,COLLECTED_TIME,POD_NAME) VALUES (:1,TO_TIMESTAMP(:2, 'YYYY-MM-DD_HH24:MI'),:3)"
          cursor.setinputsizes(oracledb.DB_TYPE_JSON,None,None)
          cursor.executemany(inssql,dart_list)
          # cursor.execute(inssql, [jdata,col_time,podname])
          
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1}".format(globalvariables.AMBER,e)
          print(message)
          raise
     finally:
          cursor.close()
          con.commit()
          con.close()

def ess_dml_operation(dart_list):
     try:
          con=get_cursor()
          cursor = con.cursor()
          inssql="INSERT INTO ESSART_STAGE_TEMP (J_DATA,COLLECTED_TIME,POD_NAME) VALUES (:1,TO_TIMESTAMP(:2, 'YYYY-MM-DD_HH24:MI'),:3)"
          cursor.setinputsizes(oracledb.DB_TYPE_JSON,None,None)
          cursor.executemany(inssql,dart_list)
          
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1} func - ess_dml_operation".format(globalvariables.AMBER,e)
          print(message)
          raise
     finally:
          cursor.close()
          con.commit()
          con.close()

def bi_dml_operation(dart_list):
     try:
          con=get_cursor()
          cursor = con.cursor()
          inssql="INSERT INTO BIART_STAGE_TEMP (J_DATA,COLLECTED_TIME,POD_NAME) VALUES (:1,TO_TIMESTAMP(:2, 'YYYY-MM-DD_HH24:MI'),:3)"
          cursor.setinputsizes(oracledb.DB_TYPE_JSON,None,None)
          cursor.executemany(inssql,dart_list)
          
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1} func - bi_dml_operation".format(globalvariables.AMBER,e)
          print(message)
          raise
     finally:
          cursor.close()
          con.commit()
          con.close()

def mt_dml_operation(dart_list):
     try:
          con=get_cursor()
          cursor = con.cursor()
          inssql="INSERT INTO MTART_STAGE_TEMP (J_DATA,COLLECTED_TIME,POD_NAME) VALUES (:1,TO_TIMESTAMP(:2, 'YYYY-MM-DD_HH24:MI'),:3)"
          cursor.setinputsizes(oracledb.DB_TYPE_JSON,None,None)
          cursor.executemany(inssql,dart_list)
          
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1} func - mt_dml_operation ".format(globalvariables.AMBER,e)
          print(message)
          raise
     finally:
          cursor.close()
          con.commit()
          con.close()

def main():
    pass

if __name__ == "__main__":
    main()
