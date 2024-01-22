import oracledb
import os
import sys
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
import json
import traceback

def get_cursor():
     try:
          con=oracledb.connect(
               user=str(globalvariables.db_cred['db_user']),
               password=str(globalvariables.db_cred['db_passwd']),
               dsn="fsremwdso_low",
               config_dir=str(globalvariables.db_cred['wallet_loc']),
               wallet_location=str(globalvariables.db_cred['wallet_loc']),
               wallet_password=str(globalvariables.db_cred['wallet_passwd']))
          return con
     except Exception as e:
          traceback.print_exc()
          message="{0} error in getting connection from db {0}".format(globalvariables.AMBER,e)
          print(message)

def dml_operation(j_data,pod_name,comp_type):
     try:
          con=get_cursor()
          cursor = con.cursor()
          # inssql = "insert into FSREMWENV_DART values (:1,:2)"
          inssql="INSERT INTO FSREMWENV_DART (id,POD_NAME,comp_type,json_data) VALUES (row_id.nextval,:1,:2,:3)"
          cursor.execute(inssql, [pod_name,comp_type,j_data])
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1}".format(globalvariables.AMBER,e)
          print(message)
     finally:
          cursor.close()
          con.commit()
          con.close()

def dml_operation_exa_octo(exa_name,j_data):
     try:
          con=get_cursor()
          cursor = con.cursor()
          # inssql = "insert into FSREMWENV_DART values (:1,:2)"
          inssql="INSERT INTO FSREMWENV_EXA_OCTO (id,EXA_NAME,JSON_DATA) VALUES (exa_octo_row_id.nextval,:1,:2)"
          cursor.execute(inssql, [exa_name,j_data])
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1}".format(globalvariables.AMBER,e)
          print(message)
     finally:
          cursor.close()
          con.commit()
          con.close()


def json_read_opeation(sql_statement):
     try:
          response=[]
          con=get_cursor()
          cursor = con.cursor()
          # sql = "SELECT json_data FROM CustomersAsBlob"
          for j, in cursor.execute(sql_statement):
               response.append(json.loads(j.read()))
          return response
     except Exception as e:
          traceback.print_exc()
          message="{0} error in reading json data from db {1}".format(globalvariables.AMBER,e)
          print(message)
     finally:
          cursor.close()
          con.close()

# json_file="{0}/out_data/dart_data/EINO_db_art_perf_data.json".format(BASE_DIR)
# with open(json_file,'r') as dart_data:
#      j_data=json.loads(dart_data.read())

# for dic in j_data:
#      for key in dic.keys():
#           print(type(dic[key]))
# # # data="test"
# # dml_operation(j_data,"test","pod")
# # sql_statement="SELECT json_data FROM FAENVJSONTAB"
# # print(json_read_opeation(sql_statement))



# # dml_operation(str(j_data),"EINO","db")


def df_to_db(df_data: dict):
     datainsert_tuple=[tuple(x) for x in df_data.values ]
     try:
          con=get_cursor()
          cursor = con.cursor()
          # inssql = "insert into FSREMWENV_DART values (:1,:2)"
          inssql="INSERT INTO FSREMWENV_SQLDF (id,total_seconds,aas,distinct_sql_executions,dart_time,sql_id,module,per_exec_time,sql_details,pod) VALUES (FSREMWENV_SQLDF_id.nextval,:1,:2,:3,:4,:5,:6,:7,:8,:9)"
          cursor.executemany(inssql,datainsert_tuple)
     except Exception as e:
          traceback.print_exc()
          message="{0} error in dml oparation for given json {1}".format(globalvariables.AMBER,e)
          print(message)
     finally:
          cursor.close()
          con.commit()
          con.close()