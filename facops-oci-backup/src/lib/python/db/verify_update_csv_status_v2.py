
import os
import sys
import traceback
import csv
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import apscom
from common import globalvariables

def verify_update_csv_status(dbname,host=None):
    try:
        db_status=''
        rman_status=0
        stderr=''
        ret_code=''
        other_backup_progress=False
        if host:
            cmd = "su oracle -c 'python {0}/remote_exec.py --type=verify_rman_status --host={1} --dbname={2}'".format(globalvariables.QUERY_POOL_PATH, host, dbname)
            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
            if ret_code==0 and rman_status and int(rman_status) > 0:
                message = "Backup already started for {0} on {1}-- with PID {2}".format(dbname, host,rman_status)
                other_backup_progress = True
                commonutils.csvupdater(globalvariables.DB_BACKUP_LOG_PATH + '/exalogs/ldb_exec_states.csv', dbname,host, "RUNNING",rman_status)
                apscom.info(message)
        else:
            with open(globalvariables.DB_BACKUP_LOG_PATH + '/exalogs/ldb_exec_states.csv', newline="") as file:
                readData = [row for row in csv.DictReader(file)]
                for i in range(0, len(readData)):
                    if readData[i]['dbname']==dbname and readData[i]['status'] == 'PENDING':
                        db_status = 'PENDING'
                    if readData[i]['status'] != 'PENDING':
                        host=readData[i]['host']
                        pid=readData[i]['PID']
                        update_dbname=readData[i]['dbname']
                        if pid:
                            cmd = "su oracle -c 'python {0}/remote_exec.py --type=verify_rman_status --host={1} --pid={2}'".format(
                                globalvariables.QUERY_POOL_PATH, host,pid)
                            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                            if (ret_code ==0 and rman_status and int(rman_status)>0):
                                status = "RUNNING"
                                other_backup_progress=True
                                #post metadata for ldb on sec node
                                rman_oss.create_backup_metadata("", "db_to_reco_db_arch_to_oss", "sec_node_full_backup",
                                                                "RUNNING", update_dbname,host)
                            else:
                                status = "COMPLETED"
                                #sleep  fro 5 sec and verify the status again and update the status
                            commonutils.csvupdater(globalvariables.DB_BACKUP_LOG_PATH + '/exalogs/ldb_exec_states.csv', update_dbname,
                                                   host, status)

            file.close()
        return other_backup_progress,db_status
    except Exception as e:
        message = "Failed to verify and update csv !\n{0},{1}".format(stderr, e)
        apscom.info(message)