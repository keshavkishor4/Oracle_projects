import glob
import os
import stat
import sys
import json
import time
from datetime import datetime,timedelta
from operator import itemgetter
import requests

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import globalvariables,apscom
too_many_req_count=0
other_count=0
trace_list=[]

def gen_json(file,dbname,db_sid):
    global too_many_req_count
    global other_count
    try:
        inst_metadata = get_inst_metadata()
        region=inst_metadata["canonicalRegionName"]
        ociAdName=inst_metadata["ociAdName"]
        faultDomain=inst_metadata["faultDomain"]

        with open (file,'r')as data:
            lines=data.readlines()
        for line in lines:
            if "KBHS-00719" in line:
                error_type=''
                trace_data = {}
                trace_data['db_name']=dbname
                trace_data['db_sid'] = db_sid
                trace_data['hostname'] = globalvariables.HOST_NAME
                trace_data['db_error'] = line.rstrip()
                if "Too many requests" in line:
                    too_many_req_count += 1
                    error_type="Too Many requests"
                    trace_data['db_error_count'] = too_many_req_count
                else:
                    error_type="other"
                    other_count += 1
                    trace_data['db_error_count'] = other_count
                trace_data['BTIMESTAMP'] = start_date
                trace_data['ETIMESTAMP'] = fin_date
                trace_data['region'] = region
                trace_data["faultDomain"]=faultDomain
                trace_data["ociAdName"]= ociAdName
                if error_type=="other" and other_count ==1 :
                    trace_list.append(trace_data)
                elif error_type=="Too Many requests" and too_many_req_count==1:
                    trace_list.append(trace_data)
                else:
                    for d in trace_list:
                        if dbname==d['db_name']:
                            for k, v in d.items():
                                if k=='db_error' and error_type=="Too Many requests" and "Too many requests" in str(v):
                                    d.update(db_error_count=too_many_req_count)
                                elif k=='db_error' and error_type=="other" and "Too many requests" not in str(v):
                                    d.update(db_error_count=other_count)

                #if(error_type=="other" and other_count ==1) or (error_type=="Too Many requests" and too_many_req_count==1):

    except Exception as e:
        message = "Failed to popualate data from  {2} for {3}\n{0}{1}".format(sys.exc_info()[1:2],e,file,dbname)
        apscom.warn(message)
def list_latest_log(dirpath):
    try:
        global start_date
        global fin_date
        date_list=[]
        fin_date=''
        list_of_files = glob.glob(dirpath+ "/*database_compressed_to_oss*post.json")
        latest_file = max(list_of_files, key=os.path.getctime)
        msg="latest database_compressed_to_oss post.json {0}".format(latest_file)
        apscom.info(msg)
        with open(latest_file,'r') as db_comp_to_oss:
            data = json.load(db_comp_to_oss)
            if data:
                start_date=data["BTIMESTAMP"]
                fin_date=data["ETIMESTAMP"]
                d = datetime.strptime(fin_date, '%Y-%m-%d %H:%M:%S')
                for i in range(1, 10):
                    d = d + timedelta(minutes=-1)
                    date_list.append(datetime.strftime(d, "%b %d %H:%M"))
        return date_list
    except Exception as e:
        message = "Failed to list latest file from  {2} \n{0}{1}".format(sys.exc_info()[1:2],e,dirpath)
        apscom.warn(message)

def list_sbt_files(path,dbname,db_sid,dbsize):
    try:
        files_sorted_by_date = []
        num_of_files=8
        if dbsize>5000:
            num_of_files=12

        filepaths = [os.path.join(path, file) for file in os.listdir(path)]

        file_statuses = [(os.stat(filepath), filepath) for filepath in filepaths]
        files = ((status[stat.ST_CTIME], filepath) for status, filepath in file_statuses if
                 stat.S_ISREG(status[stat.ST_MODE]))
        for creation_time, filepath in sorted(files):
            creation_date = time.ctime(creation_time)
            filename = os.path.basename(filepath)
            files_sorted_by_date.append(creation_date + " " + filepath)
        date_time_list=list_latest_log(globalvariables.DB_BACKUP_LOG_PATH+'/'+db_sid)
        count=0
        for file in files_sorted_by_date:
            for date_time in date_time_list:
                if "sbtio" in file and date_time in file :
                    #if "sbtio" in file:
                    msg="sbt file --- {0}".format(file)
                    apscom.info(msg)
                    count =count+1
                    if count > num_of_files:
                        return True
                    gen_json(file.split(' ')[-1],dbname,db_sid)
    except Exception as e:
        message = "Failed to list sbtfiles from {2} for {3} \n{0}{1}".format(sys.exc_info()[1:2],e,path,dbname)
        apscom.warn(message)
def read_databases():
    try:
        db_list={}
        with open(globalvariables.DB_BACKUP_LOG_PATH + '/exalogs/db_group_by_size.json', 'r') as fp:
            data = json.load(fp)
        for dbtype in data:
            for dbname, size in sorted(data[dbtype].items(), key=itemgetter(1)):
               db_list[dbname]=size
        return db_list
    except Exception as e:
        message = "Failed to read data from {0}!\n{1}{2}".format(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json',sys.exc_info()[1:2], e)
        apscom.warn(message)
def read_sid(dbname):
    query_res_json = ''
    try:
        dbsid=''
        with open(globalvariables.pod_info_file, "r") as all_pod:
            lines = all_pod.readlines()
        for line in lines:
            if dbname in line:
                dbsid = line.split(":")[2]
        if dbsid:
            query_res_json = globalvariables.DB_BACKUP_LOG_PATH + "/" + dbsid + "/" + globalvariables.HOST_NAME + "_" + dbsid + "_query.json"
            query_file = open(query_res_json.strip(), 'r')
            query_output = json.load(query_file)
            dbsid = query_output["ORACLE_SID"]
        return dbsid
    except Exception as e:
        message = "Failed to read query.json data from {0}!\n{1}{2}".format(
            query_res_json, sys.exc_info()[1:2], e)
        apscom.warn(message)
def get_inst_metadata():
    """curl -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/"""
    instance_metadata_url="http://169.254.169.254/opc/v2/instance/"
    try:
        f=requests.get(instance_metadata_url,headers={'Authorization': 'Bearer Oracle'})
        out = json.dumps(f.json())
        json_res = json.loads(out)
        return json_res
    except Exception as e:
        message = "failed to get instance metadata \n{0}{1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise
def main():
    global too_many_req_count
    global other_count
    global kbhs_error_log
    try:
        filename = globalvariables.EXALOGS_PATH + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME,
                                                            os.path.basename(__file__).split(".")[0],
                                                            datetime.now().strftime(
                                                                "%Y%m%d_%H%M%S_%f"))
        kbhs_error_log = apscom.init_logger(__file__, log_dir=globalvariables.EXALOGS_PATH, logfile=filename)
        db_list=read_databases()
        for dbname in db_list:
            too_many_req_count=0
            other_count=0
            dbsize=db_list[dbname]
            db_sid=read_sid(dbname)
            trace_path="/u02/app/oracle/diag/rdbms/{0}/{1}/trace".format(dbname,db_sid)
            msg="KBHS error for {0}, trace path {1}...".format(dbname,trace_path)
            apscom.info(msg)
            list_sbt_files(trace_path,dbname,db_sid,dbsize)
            msg="too_many_req_count count for {0} -- {1}... other error count {2}".format(dbname,too_many_req_count,other_count)
            apscom.info(msg)
        #list_sbt_files('/u02/app/oracle/diag/rdbms/no1ajqo/no1ajqo1/trace')
        timestamp = time.strftime("%m%d%Y%H%M%S", time.gmtime())
        kbhs_json = "{0}/{1}_KBHS_errors_{2}.json".format(globalvariables.EXALOGS_PATH,globalvariables.LOCAL_HOST,timestamp)
        with open(kbhs_json, 'w') as outfile:
            json.dump(trace_list, outfile, indent=4, sort_keys=True)
            msg = "Successfully generated {0}".format(kbhs_json)
            apscom.info(msg)
    except Exception as e:
        message = "failed to exectute KBHS trace eroors main \n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

if __name__ == "__main__":
    main()




