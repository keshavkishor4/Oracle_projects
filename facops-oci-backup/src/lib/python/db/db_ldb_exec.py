#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      database_config.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Zakki Ahmed           08/20/21  - FY21Q1 
"""
#### imports start here ##############################
import glob
import os
import shutil
import sys
import argparse
import getpass

from datetime import datetime
from pwd import getpwuid
from operator import itemgetter

import traceback
import csv

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import ociSDK,apscom,commonutils,globalvariables,load_oci_config,post_backup_metadata,instance_metadata
from db import validate_sbt_test,remote_exec_v2
import json
import traceback
#### imports end here ##############################

# move it to globalvariables
csv_file = globalvariables.remote_backup_states_csv_file
remote_backup_types = globalvariables.remote_backup_types

def wallet_files_checks():
    wallet_config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
    if os.path.exists(wallet_config_file):
        try:
            with open(wallet_config_file) as f:
                wallet_config_data = json.loads(f)
            # 
            print(wallet_config_data)
        
        except Exception as e:
            print(e)

def csvupdater(filename,backup_type,dbname=None,host=None,status=None,pid=None):
    try:
        with open(filename, newline= "",encoding='utf-8') as file:
            readData = [row for row in csv.DictReader(file)]
            for i in range(0, len(readData)):
                if status == 'PENDING':
                    readData[i]['dbname'] = dbname
                    readData[i]['host'] = host
                    readData[i]['backup_type'] = backup_type
                    readData[i]['status'] = status
                    readData[i]['PID'] = pid
                if status =='STARTED' or status =='RUNNING' :
                        if readData[i]['dbname'] == dbname:
                            readData[i]['status'] = status
                            readData[i]['host'] = host
                            if pid:
                                readData[i]['PID'] = pid
                elif readData[i]['dbname'] == dbname and readData[i]['host'] == host:
                    if status=='COMPLETED':
                        readData.remove(readData[i])
                        break
                    else:
                        readData[i]['status'] =status
                        break
                elif readData[i]['dbname'] == dbname:
                    if status=='COMPLETED':
                        readData.remove(readData[i])
                        break

        csvWritter(readData, filename,"update")
    except Exception as e:
        message = "Failed to update csv !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)

def csvWritter(readData, filename,type):
    try:
        with open(filename, 'w+',encoding='utf-8') as csvfile:
            readHeader=['dbname', 'host', 'backup_type' ,'status',"PID"]
            writer = csv.DictWriter(csvfile, fieldnames=readHeader)
            writer.writeheader()
            writer.writerows(readData)
        csvfile.close()
    except Exception as e:
        message = "Failed to add data to csv !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.info(message)


def perform_remote_node_checks(host):
    #check if config-oci.json, pem files and sre_db.cfg is correct else copy
    file_list=['','','']

def validate_database_condition(dbname):
    # this condition to get wheeether min odd number where backup should run
    try:
        is_valid=False
        # make it as argument -- later , refer to rman_wrapper.py
        force_flag = False
        if force_flag:
            is_valid = True
        else:
            host_count=commonutils.get_dbname_db_count(dbname)
            if(int(host_count)>2):
                db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                running_db_odd_hosts,running_db_even_hosts=commonutils.get_dbname_db_nodes(dbname,db_uniq_name)
                min_odd_node_name=min(running_db_odd_hosts, key=lambda odd_node: odd_node['running_db_node_num'])
                if running_db_even_hosts:
                    min_even_node_name = min(running_db_even_hosts,key=lambda even_node: even_node['running_db_node_num'])
                else:
                    min_even_node_name = min(running_db_odd_hosts,key=lambda odd_node: odd_node['running_db_node_num'])

                if min_odd_node_name["running_db_node_name"] == globalvariables.HOST_NAME :
                    is_valid=True
                else:
                    message = "Failed to execute backup on !{0}, backup should run on the minimum odd host {1} , number of nodes for this database are {2}  ".format(globalvariables.HOST_NAME,min_odd_node_name["running_db_node_name"],len(running_db_odd_hosts))
                    apscom.warn(message)
            else:
                is_valid=True
        return is_valid
    except Exception as e:
        message = "Failed to do validate rman conditions!\n{0}".format(e)
        apscom.warn(message)
        raise

def verify_update_csv_status(dbname,backup_type=None,host=None,backup_status=None):
    try:
        if backup_status == None:
            csv_db_status=''
        rman_status=0
        stderr=''
        ret_code=''
        other_backup_progress=False

        with open(csv_file, newline="") as file:
            readData = [row for row in csv.DictReader(file)]
        for i in range(0, len(readData)):
            csv_db_name = readData[i]['dbname']
            csv_host=readData[i]['host']        
            csv_backup_type=readData[i]['backup_type']
            if csv_db_status == '':
                csv_db_status = readData[i]['status']
            csv_pid=readData[i]['PID']
        
            if host:
                if host != csv_host and csv_db_status == "PENDING":
                    csvupdater(csv_file,backup_type,dbname,host,csv_db_status)
                    message = "{4}{3} -  {0} backup can be executed {2}, previous entry was {1} , updated csv to {2} ... ".format(dbname, csv_host,host,backup_type,globalvariables.AMBER)
                    apscom.info(message)
                    break

            # cmd = "su oracle -c 'python {0}/remote_exec_v2.py --type=verify_rman_status --host={1} --dbname={2}'".format(globalvariables.QUERY_POOL_PATH, host, dbname)
        if host:
            cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --dbname {2} --backup_type {3} --action verify_rman_status'".format(globalvariables.QUERY_POOL_PATH, host, dbname,backup_type)
            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
            if ret_code == 0 and rman_status and int(rman_status) > 0:
                message = "{4}{3} -  backup already started for {0} on {1}-- with PID {2}".format(dbname, host,rman_status,backup_type,globalvariables.GREEN)
                other_backup_progress = True
                # csvupdater(csv_file, dbname,host, "RUNNING",rman_status)
                csvupdater(csv_file,backup_type,dbname,host,"RUNNING",rman_status)
                apscom.info(message)
            # 
            if not other_backup_progress:
                with open(csv_file, newline="") as file:
                    readData = [row for row in csv.DictReader(file)]
                for i in range(0, len(readData)):
                    csv_db_name = readData[i]['dbname']
                    csv_host=readData[i]['host']        
                    csv_backup_type=readData[i]['backup_type']
                    csv_db_status = readData[i]['status']
                    csv_pid=readData[i]['PID']
                    # 
                    if dbname == csv_db_name and csv_pid:
                        cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --action check_pid --pid {2}'".format(globalvariables.QUERY_POOL_PATH, host,csv_pid)
                        [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                        if ret_code == 0 and rman_status:
                            if int(rman_status) > 0:
                                other_backup_progress = True
                                # csvupdater(csv_file, dbname,host, "RUNNING",rman_status)
                                csvupdater(csv_file,backup_type,dbname,host,"RUNNING",rman_status)
                                apscom.info(message)
                                break
                            elif int(rman_status) == 0:
                                other_backup_progress = False
                                csvupdater(csv_file,backup_type,dbname,host,"COMPLETED",rman_status)
                                break
            # file.close()
        return other_backup_progress,csv_db_status
    except Exception as e:
        message = "{2}Failed to verify and update csv !\n{0},{1}".format(stderr, e,globalvariables.RED)
        apscom.info(message)

def process_csv(user_backup_type=None):
    try:
        if os.path.exists(csv_file):
            with open(csv_file, newline="") as file:
                readData = [row for row in csv.DictReader(file)]
            has_rows = False
            for i in range(0, len(readData)):
                # verify_update_csv_status(dbname,backup_type,host)
                has_rows = True
                dbname = readData[i]['dbname']
                host=readData[i]['host']        
                backup_type=readData[i]['backup_type']
                db_status = readData[i]['status']
                pid=readData[i]['PID']
                #  
                other_backup_progress,db_status = verify_update_csv_status(dbname,backup_type,host)
                if other_backup_progress:
                    break
                if not other_backup_progress:
                    if db_status.upper() == "PENDING":
                        # Verify connectivty
                        cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --action check_rman_file'".format(globalvariables.QUERY_POOL_PATH, host)
                        [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                        if (ret_code == 0 and rman_status == "True"):
                            # 
                            db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                            running_db_odd_hosts,running_db_even_hosts=commonutils.get_dbname_db_nodes(dbname,db_uniq_name)
                            ols_host = None
                            # 
                            if running_db_even_hosts:
                                min_even_node_name = min(running_db_even_hosts,key=lambda even_node: even_node['running_db_node_num'])
                            elif running_db_odd_hosts:
                                min_even_node_name = min(running_db_odd_hosts,key=lambda odd_node: odd_node['running_db_node_num'])
                            else: 
                                min_even_node_name = None
                            # 
                            if min_even_node_name:
                                ols_host = min_even_node_name["running_db_node_name"]
                                if host != ols_host:
                                    verify_update_csv_status(dbname,backup_type,ols_host)
                            else:
                                verify_update_csv_status(dbname,backup_type,globalvariables.HOST_NAME)

                            # run backup
                            cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --dbname {2} --backup_type {3} --action run_backup'".format(globalvariables.QUERY_POOL_PATH, ols_host,dbname,backup_type)
                            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                            if (ret_code == 0 and rman_status and int(rman_status) > 0):
                                other_backup_progress,db_status = verify_update_csv_status(dbname,backup_type,ols_host)
                                break
                        elif (ret_code == 0 and rman_status == "False"):
                            host = globalvariables.HOST_NAME
                            # verify_update_csv_status(dbname,backup_type,host)
                            cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --dbname {2} --backup_type {3} --action run_backup'".format(globalvariables.QUERY_POOL_PATH, host,dbname,backup_type)
                            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                            if (ret_code == 0 and rman_status and int(rman_status) > 0):
                                other_backup_progress,db_status = verify_update_csv_status(dbname,backup_type,host)
                                break
            # 
            if not has_rows and user_backup_type != None:
                fetch_ldbs(user_backup_type)
        else:
            if user_backup_type != None:
                fetch_ldbs(user_backup_type)
    except Exception as e:
        message = "Not able to process csv file"
        apscom.warn(message)
            

def fetch_ldbs(backup_type):
    if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
        with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json', 'r') as fp:
             data = json.load(fp)
        
        if data['large_db'] :
            # create csv
            csvdata = []
            
            for dbname, size in sorted(data['large_db'].items(), key=itemgetter(1)):
                db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                running_db_odd_hosts,running_db_even_hosts=commonutils.get_dbname_db_nodes(dbname,db_uniq_name)
                ols_host = None
                # 
                if running_db_even_hosts:
                    min_even_node_name = min(running_db_even_hosts,key=lambda even_node: even_node['running_db_node_num'])
                elif running_db_odd_hosts:
                    min_even_node_name = min(running_db_odd_hosts,key=lambda odd_node: odd_node['running_db_node_num'])
                else: 
                    min_even_node_name = None
                # 
                if running_db_odd_hosts:
                   min_odd_node_name = min(running_db_odd_hosts,key=lambda odd_node: odd_node['running_db_node_num'])
                   min_odd_node = min_odd_node_name["running_db_node_name"]                
                   if min_odd_node != globalvariables.HOST_NAME:
                        message = "{2} db {0} will not be processed from this node".format(db_uniq_name,globalvariables.HOST_NAME,globalvariables.AMBER)
                        apscom.warn(message)
                        break
                # 
                if min_even_node_name:
                    ols_host = min_even_node_name["running_db_node_name"]
                else:
                    message = "{2}db {0} not running on any host".format(db_uniq_name,globalvariables.HOST_NAME,globalvariables.AMBER)
                    apscom.warn(message)
                    break
                # 
                if ols_host != None  and ols_host == globalvariables.HOST_NAME:
                    message = "remote host {0} is same as {1} ".format(ols_host,globalvariables.HOST_NAME)
                    apscom.warn(message)
                #  
                if ols_host != None:
                    cmd = "su oracle -c 'python {0}/remote_exec_v2.py --host {1} --action check_rman_file'".format(globalvariables.QUERY_POOL_PATH, ols_host)
                    [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
                    if (ret_code == 0 and rman_status == "False"):
                        ols_host = globalvariables.HOST_NAME
                    # first status - creating csv
                    status="PENDING"
                    PID=""
                    # print("{0},{1},{2},{3}".format(dbname,ols_host,backup_type,PID,status))
                    csv_data = {'dbname': dbname, 'host': ols_host, 'backup_type': backup_type,'status': 'PENDING', 'PID': ''}
                    csvdata.append(csv_data)
                    # csvupdater(globalvariables.DB_BACKUP_LOG_PATH + '/exalogs/ldb_exec_states.csv', dbname,ols_host, status)
                    if csv_data:
                        csvWritter(csvdata, csv_file, "new") 
                else:
                    message = "{1}{0} is not running on any nodes of this cluster".format(dbname,globalvariables.AMBER)
                    apscom.warn(message)
                    # sys.exit(1)
        #



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--backup_type',dest='backup_type',default=None,help='required - backup_type ')
    args = parser.parse_args() 
    # rerememberr this is executed only for full backups
    # if not args.backup_type:
    #     parser.error('--backup_type option ')

    backup_type=args.backup_type
    username = getpass.getuser()
    if username == "oracle":
        message="script to be executed as 'root' user"
        apscom.error(message)
        sys.exit(1)
    else:
        process_csv(backup_type)
    # if backup_type in remote_backup_types:
    #     fetch_ldbs(backup_type)
    #     # wallet_files_checks()
if __name__ == "__main__":
    main()
