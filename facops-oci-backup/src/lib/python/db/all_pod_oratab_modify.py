#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      all_pod_oratab_modify.py

    DESCRIPTION
      Modify all pod info file

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       08/12/20 - initial version (code refactoring)
    Zakki Ahmed           10/18/21 - 33426898, 
    Vipin Azad            12/06/22  - FSRE-94
"""
#### imports start here ##############################
import os
import sys
import getpass
import traceback
from datetime import datetime
from time import strftime, gmtime
import optparse
import json
import re
import shutil

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,commonutils,globalvariables
from db import database_config 

#### imports end here ##############################


hostnm = globalvariables.LOCAL_HOST.split('.')[0]
all_pod_log=globalvariables.ALL_POD_INFO_PATH+"/all-pod-info_"+hostnm+".log"
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
rename_flg="N"
del_flg="N"
backup_needed = "n"

def gen_all_pod_info(dbname,dbsid):
    try:
        backup_needed=check_olsnodes()
        with open(globalvariables.pod_info_file, 'a') as fp:
            # if "_dr" in dbname:
            #     backup_needed="n"
            #     str="{0}:{1}:{2}:{3}\n".format(dbname,globalvariables.LOCAL_HOST,dbsid,backup_needed)
            # else:
            #     str="{0}:{1}:{2}:{3}\n".format(dbname,globalvariables.LOCAL_HOST,dbsid,backup_needed)
            str="{0}:{1}:{2}:{3}\n".format(dbname,globalvariables.LOCAL_HOST,dbsid,backup_needed)
            fp.write(str)
    except Exception as e:
        message = "Unable to update {0},{1}!".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)


def check_olsnodes():
    local_host=globalvariables.HOST_NAME
    ols_nodes_json_file=globalvariables.EXALOGS_PATH+'/ols_nodes.json'
    backup_need=""
    try:
        with open(globalvariables.EXALOGS_PATH+'/ols_nodes.json','r') as olsnodes_file:
            olsdata = json.load(olsnodes_file)
        # 
        if olsdata:
         for ols_val in olsdata:
             if ols_val["node_name"] == local_host:
                 if int(ols_val["node_num"]) % 2 == 1:
                     backup_need = "y"
                 elif int(ols_val["node_num"]) % 2 == 0:
                     if even_node_force:
                         backup_need = "y"
                     else:
                         backup_need = "n"
         return backup_need
        else:
         message = "this node {0} do not show up in olsnodes, please check olsnodes!".format(local_host)
         apscom.error(message)
         raise Exception(message)   

        
    except Exception as e:
        message = "Failed to read {0}, {1}!\n{2}".format( ols_nodes_json_file,sys.exc_info()[1:2], e)
        apscom.error(message)
        raise Exception(message) 

def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser()
        parser.add_option('-f','--force', action='store', dest='even_node_force_flag',default=False)
        parser.add_option('-b', action='store', dest='backup_type', default=' ')
        parser.add_option('-d', '--dbname', action='store', dest='db_name',default=None)
        parser.add_option('-t', '--storage-type', action='store', dest='backup_target', default='fss',
                          choices=['fss', 'oss'], help='Storage type of backup target.')
        parser.add_option('--bucket_name', action='store', dest='bucket_name',default=None)
        parser.add_option('--user_name', action='store', dest='user_name', default=None)
        parser.add_option('--action', action='store', dest='action', default=None)
         # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log', default="no",help='Optional - Get logs in debug mode')
        (opts, args) = parser.parse_args()
        return (opts, args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise
 
def main(force_flag=False):
    try:
        global even_node_force
        even_node_force = force_flag
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
        filename = log_file_path + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME,
                                                            os.path.basename(__file__).split(".")[0],
                                                            datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file = apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        if not force_flag:
            (options, args) = parse_opts()
            even_node_force=options.even_node_force_flag
            if options.debug_log == "yes":
                import logging
                # Enable debug logging
                logging.getLogger('oci').setLevel(logging.DEBUG)
                # oci.base_client.is_http_log_enabled(True)
                # logging.basicConfig(filename='/tmp/test.log')
                log_file_path_for_debug = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
                if not os.path.exists(log_file_path_for_debug):
                    os.makedirs(log_file_path_for_debug)
                filename_debug = log_file_path_for_debug+"/oci_debug" + \
                    "_{0}_{1}.log".format(globalvariables.HOST_NAME,
                                        datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
                logging.basicConfig(filename=filename_debug)
        username = getpass.getuser()
        if username == "root":
           user_db_config = "oracle"
        else:
            msg = "This process need to be executed as root"
            apscom.error(msg)
        if os.path.exists(globalvariables.pod_info_file) and rename_flg == "N":
            os.rename(globalvariables.pod_info_file,globalvariables.pod_info_file+"."+timestamp)
        if os.path.exists(globalvariables.pod_info_file) and del_flg == "N":
            os.rename(globalvariables.pod_info_file,globalvariables.pod_info_file+"."+timestamp)
        # old
        # str = 'ps -eawf|grep smon|grep ^oracle|grep -v grep|grep -v ASM|grep -v perl|cut -d"_" -f3'
        # running_instances= commonutils.execute_shell(str)[0]
        # run through script
        running_instances_cmd="/usr/bin/timeout 300 {0}/get_oracle_sids.sh".format(globalvariables.DB_SHELL_SCRIPT)
        [running_instances,returncode,stderror]=commonutils.execute_shell(running_instances_cmd)
        
        # debug
        # message = "{1}running instances {0}".format(running_instances,globalvariables.GREEN)
        # apscom.info(message)
        # 
        # running_instances_list = running_instances.strip().split('\n')
        # message = "{1}running instances list  {0}".format(running_instances_list,globalvariables.GREEN)
        # apscom.info(message)
        # 
        if running_instances:
            for dbsid in running_instances.strip().split('\n'):
                if '//' in dbsid:
                    message = "{1}WARN: FOUND ROGUE entry for running instances output - {0}".format(dbsid,globalvariables.AMBER)
                    apscom.warn(message)
                    pass
                else:
                    ORACLE_HOME=commonutils.get_oracle_home(dbsid)
                    if ORACLE_HOME:
                        #fetches unique db names not actual db names DB_UNIQUE_NAME
                        #dbname_list=commonutils.get_dbname_list()
                        if not ORACLE_HOME:
                            message = "Error: Fail to get Oracle home for! instance - {0}".format(dbsid)
                            apscom.warn(message)
                            raise Exception(message)
                        if not os.path.exists(ORACLE_HOME):
                            message = "Error: Oracle home {0} for {1} does not exist!".format(ORACLE_HOME, dbsid)
                            apscom.warn(message)
                            raise Exception(message)
                        #
                        crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
                        with open(crsctl_json) as json_file:
                            json_data = json.load(json_file)
                        for key in json_data:
                            #
                            if dbsid in json_data[key]['db_sid_list']: ## fix logic of in
                                db_uni_name=json_data[key]['db_unique_name']
                                db_name=json_data[key]['db_name']
                                gen_all_pod_info(db_name,dbsid)
                    else:
                        message = "Error: Oracle home {0} for {1} does not exist!, please check the state of the database".format(ORACLE_HOME, dbsid)
                        apscom.warn(message)
                        pass
            if os.path.exists(globalvariables.pod_info_file):
                shutil.copy(globalvariables.pod_info_file,globalvariables.pod_wallet_file)
        else:
            message = "No DB is running on this exanode"
            apscom.error(message)
    except Exception as e:
        # debug
        message = "stack trace {0}".format(traceback.print_exc())
        apscom.warn(message)
        # 
        message = "Failed to update all pod {0}!".format(e)
        apscom.error(message)
if __name__ == "__main__":
    main()