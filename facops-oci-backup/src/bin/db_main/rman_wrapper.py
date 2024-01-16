#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      rman_wrapper.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
    Zakki Ahmed           25/02/21 - updates
    Vipin Azad            08/10/23 - Jira FUSIONSRE-8245
"""
#### imports start here ##############################
import json
import getpass
import optparse
import os
import sys
import glob
import time
from datetime import datetime,timedelta
import shutil
import signal
from operator import itemgetter

from pwd import getpwuid
import psutil
import rman_oss
import db_tasks

BASE_DIR = os.path.abspath(__file__ + "/../../")
# BASE_DIR = os.path.abspath("./../") ## -- used for testing--
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables,commonutils,instance_metadata,post_backup_metadata,ociSDK
from db import all_pod_oratab_modify,database_config,db_ldb_exec, database_config_bkup_opc_install
#### imports start here ##############################

BACKUP_SUPPORTED = globalvariables.BACKUP_SUPPORTED

start_time = time.time()

def verify_lib_files(dbname):
    try:    
        dbhome = commonutils.get_crsctl_data(dbname,'db_home')
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            list_of_files = glob.glob(globalvariables.OPC_LIB_PATH + '/' + dbname + '/opc' + dbname + '.ora')
            if not list_of_files:
                message = "The file {0}/{1}/opc{1}.ora file is missing. Rerunning configuration!".format(globalvariables.OPC_LIB_PATH,dbname)
                apscom.info(message)
                database_config_bkup_opc_install.bkup_opc_install(dbname,dbhome,force_flag=None)
            else:    
                rman_ora_path = max(list_of_files, key=os.path.getmtime)
            list_libopc = glob.glob(globalvariables.OPC_LIB_PATH + '/' + dbname + '/lib/libopc.so')
            if not list_libopc:
                message = "The opc lib file {0}/{1}/lib/libopc.so file is missing. Rerunning configuration!".format(globalvariables.OPC_LIB_PATH,dbname)
                apscom.warn(message)    
                database_config_bkup_opc_install.bkup_opc_install(dbname,dbhome,force_flag=None)
            else:
                libopc_path = max(list_libopc, key=os.path.getmtime).rstrip()
        else:
            list_of_files = glob.glob(globalvariables.NONFA_DBAAS_RMAN_OPC_PATH+'/**/*' + dbname + '.ora')
            if not list_of_files:
                message = "The file {0}/**/*{1}.ora file is missing. Please rerun the config and retry".format(globalvariables.NONFA_DBAAS_RMAN_OPC_PATH,dbname)
                apscom.warn(message)
            else: 
                rman_ora_path = max(list_of_files, key=os.path.getmtime)

            list_libopc = glob.glob(globalvariables.NONFA_DBAAS_LIBOPC+'/**/libopc.so')
            if not list_libopc:
                message = "The opc lib file {0}/**/libopc.so file is missing. Please rerun the config and retry".format(globalvariables.NONFA_DBAAS_LIBOPC,dbname)
                apscom.warn(message)    
            else:
                libopc_path = max(list_libopc, key=os.path.getmtime).rstrip()
    except Exception as e:
        message = "Failed to verify the opclib.so and opc.ora file. Please verify if dbname is being passed to the function! \n{0},{1}".format(sys.exc_info()[1:2], e)

def take_action_validate(options):
    try:
        username = getpass.getuser()
        if username != "root":
            msg = "This process need to be executed as root ..."
            apscom.error(msg)
        #
        validate_option=None
        if options.action in ['validate','validate_db_reco']:
            validate_option = options.action
        elif options.action == 'validate_db_oss':
            validate_option = options.action
        elif options.action == 'restore_validate':
            validate_option = options.action
        else:
            apscom.error("Not a valid validate option, use validate_oss or validate_reco or restore_validate")
        # 
        commonutils.gen_ols_node_json()
        commonutils.gen_crsctl_dump()
        # all_pod_oratab_modify.main(force_flag)
        commonutils.update_flag_driver(globalvariables.pod_info_file)
        database_config.main()
        #
        validate_backup_queue = globalvariables.EXALOGS_PATH + "/" + validate_option + "_queue.txt"
        
        commonutils.check_validate_queue_status(validate_backup_queue)
        if not os.path.exists(validate_backup_queue):
            commonutils.gen_validate_queue(validate_backup_queue)

        tag = options.tag
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json', 'r') as fp:
                data = json.load(fp)
                if data['small_db'] :
                    for dbname in data['small_db']:
                        if verify_lib_files(dbname):
                            message = "Verified the library files (libopc.so & opc.ora)!"
                            apscom.info(message)
                        env_type = commonutils.get_db_env_type(dbname)
                        if ('prod' in env_type and validate_database_condition(dbname) and commonutils.check_validate_backup_eligibility(dbname,validate_backup_queue)) or env_type == "em_exa" or env_type == "dbaas":
                            message = "{3}running rman {0} on {1} with fusion pdb of environment type {2} ... ".format(validate_option,dbname,env_type.upper(),globalvariables.GREEN)
                            apscom.info(message)
                            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} '".format(BASE_DIR,dbname,validate_option,tag)
                            # print(rman_cmd)
                            [res, ret_code,stderr] = commonutils.execute_shell(rman_cmd)
                            apscom.info(res)
                            commonutils.update_db_validate_file(dbname,validate_backup_queue)
                if data['medium_db']:
                    for dbname in data['medium_db']:
                        if verify_lib_files(dbname):
                            message = "Verified the library files (libopc.so & opc.ora)!"
                            apscom.info(message)
                        env_type = commonutils.get_db_env_type(dbname)
                        if ('prod' in env_type and validate_database_condition(dbname) and commonutils.check_validate_backup_eligibility(dbname,validate_backup_queue)) or env_type == "em_exa" or env_type == "dbaas":
                            message = "{3}running rman {0} on {1} with fusion pdb of environment type {2} ... ".format(validate_option,dbname,env_type.upper(),globalvariables.GREEN)
                            apscom.info(message)
                            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} '".format(BASE_DIR,dbname,validate_option,tag)
                            # print(rman_cmd)
                            [res, ret_code,stderr] = commonutils.execute_shell(rman_cmd)
                            apscom.info(res)
                            commonutils.update_db_validate_file(dbname,validate_backup_queue)
                if data['large_db'] :
                    for dbname in data['large_db']:
                        if verify_lib_files(dbname):
                            message = "Verified the library files (libopc.so & opc.ora)!"
                            apscom.info(message)
                        env_type = commonutils.get_db_env_type(dbname)
                        if ('prod' in env_type and validate_database_condition(dbname) and commonutils.check_validate_backup_eligibility(dbname,validate_backup_queue)) or env_type == "em_exa" or env_type == "dbaas":
                            message = "{3}running rman {0} on {1} with fusion pdb of environment type {2} ... ".format(validate_option,dbname,env_type.upper(),globalvariables.GREEN)
                            apscom.info(message)
                            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} '".format(BASE_DIR,dbname,validate_option,tag)
                            # print(rman_cmd)
                            [res, ret_code,stderr] = commonutils.execute_shell(rman_cmd)
                            apscom.info(res)
                            commonutils.update_db_validate_file(dbname,validate_backup_queue)
    except Exception as e:
        if dbname and validate_backup_queue:
            commonutils.update_db_validate_file(dbname,validate_backup_queue)
        message = "Failed to run validate!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        # apscom.warn(traceback.print_exc())
#         rman_oss.create_backup_metadata(log_file_wrapper, backup_type, "rman_wrapper", "FAILED", dbname)
        sys.exit(1)

def take_action_backup(options):
    backup_type = options.backup
    try:
        db_trigger = False
        csvfileName=globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/ldb_exec_states.csv'
        username = getpass.getuser()
        # 
        backup_option = options.backup
        force_flag = options.force_flag
        dbname = options.db_name
        bucket_name = options.bucket_name
        rman_user=options.user_name

        # 
        message="{0} started ....".format(backup_type)
        apscom.debug(message)
        if username != "root":
            msg = "This process need to be executed as root ..."
            apscom.error(msg)
        # 
        oci_sdk=ociSDK.ociSDK(globalvariables.DB_CONFIG_PATH_DEFAULT)
        oci_sdk.get_tenancy_info(globalvariables.DB_CONFIG_PATH_DEFAULT)
        #commentimg check_conflicts to allow multiple backup type execution
        #commonutils.check_conflicts(backup_type,file_name=__file__)
        message = "executing comment_backup_cron ..."
        apscom.debug(message)
        #
        commonutils.comment_backup_cron()
        message = "executing all_pod_oratab_modify ..."
        apscom.debug(message)
        #
        commonutils.gen_ols_node_json()
        # crsctl dump
        commonutils.gen_crsctl_dump()
        all_pod_oratab_modify.main(force_flag)
        commonutils.update_flag_driver(globalvariables.pod_info_file)
        message = "executing database_config ..."
        apscom.debug(message)
        #
        if dbname and bucket_name and bucket_name!='RMAN_BACKUP':
            database_config.cross_region_backup(dbname,bucket_name,backup_option,rman_user)
        else:
            database_config.main()
        # 
        message = "executing execute_house_keeping ..."
        apscom.debug(message)
        #
        execute_house_keeping()

        if backup_type == "archivelog_to_oss" and not commonutils.check_em_systemtype() and not commonutils.check_dbaas_systemtype():
            commonutils.db_archive_backup_list()
            shutil.chown(globalvariables.db_archive_backup_path, "oracle", "oinstall")

        #apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json', 'r') as fp:
            data = json.load(fp)
            csvdata = []
            no_of_large_db = len(data['large_db'])
            
            # 
            #  ** csv now part of db_ldb_exec.py
            if backup_type in globalvariables.remote_backup_types:
                if os.path.exists(globalvariables.remote_backup_states_csv_file):
                    os.remove(globalvariables.remote_backup_states_csv_file)
                db_ldb_exec.process_csv(backup_type)
            # 
            # small db processing
            for dbname, size in sorted(data['small_db'].items(), key=itemgetter(1)):
                if validate_database_condition(dbname):
                    take_rman_backup(backup_type, dbname)
            # 
            # medium db processing
            for dbname, size in sorted(data['medium_db'].items(), key=itemgetter(1)):
                if validate_database_condition(dbname):
                    take_rman_backup(backup_type, dbname)
            # 
            # process large db
            for dbname, size in sorted(data['large_db'].items(), key=itemgetter(1)):
                db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                    # ols_host = commonutils.get_next_db_node(dbname)
                running_db_odd_hosts,running_db_even_hosts=commonutils.get_dbname_db_nodes(dbname,db_uniq_name)
                min_odd_node_name=min(running_db_odd_hosts, key=lambda odd_node: odd_node['running_db_node_num'])
                if running_db_even_hosts:
                    min_even_node_name = min(running_db_even_hosts,key=lambda even_node: even_node['running_db_node_num'])
                else:
                    min_even_node_name = min(running_db_odd_hosts,key=lambda odd_node: odd_node['running_db_node_num'])
                ols_host = min_even_node_name["running_db_node_name"]

                if validate_database_condition(dbname):
                    other_backup_progress=''
                    db_status=''
                    if backup_type in globalvariables.NODE1_BACKUP_TYPES:
                        db_ldb_exec.process_csv()
                        
                        # peform regular backups
                        take_rman_backup(backup_type, dbname)
                        #Read the validate queue and run validate if backup type is archivelog
                    else:   
                        db_ldb_exec.process_csv(backup_type)

        commonutils.remove_backup_oss_passwd()
        end_time = time.time()
        final_time = round(end_time - start_time, 2)
        message = "Time taken to execute complete script is {0} seconds".format(
            final_time)
        apscom.info(message)
        fp.close()
    except Exception as e:
        message = "Failed to do backup!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        # apscom.warn(traceback.print_exc())
        rman_oss.create_backup_metadata(log_file_wrapper, backup_type, "rman_wrapper", "FAILED", dbname)
        sys.exit(1)

def take_rman_backup(backup_option, dbname, dbsid=None):
    stderr = ''
    rman_cmd = ''
    (options, args) = parse_opts()
    tag = options.tag
    retention_days = options.retention_days
    try:
        #https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1099
        sre_path='{0}/sre_db_remote_{1}*.cfg'.format(globalvariables.BACKUP_CFG_LOCATION,dbname)
        sre_files = glob.glob(sre_path)
        if not sre_files:
            pass
        else:
            latest_sre_remote = max(sre_files, key=os.path.getmtime).rstrip()
            message=" {0} file exists, please review and delete such files, review and delete ...".format(latest_sre_remote)
            apscom.warn(message)
            # database_config.exec_db_config(dbname, 'bkup_ocifsbackup_sre.cfg', latest_sre_remote)
            

        with open(globalvariables.pod_info_file, "r") as all_pod:
            lines = all_pod.readlines()
        for line in lines:
            if dbname in line:
                dbsid = line.split(":")[2]
        ORACLE_HOME = commonutils.get_oracle_home(dbsid)
        if not ORACLE_HOME:
            message = "Error: Fail to get Oracle home for!\n{0}".format(dbname)
            apscom.warn(message)
            raise
        if not os.path.exists(ORACLE_HOME):
            message = "Error: Oracle home {0} for {1} does not exist!".format(ORACLE_HOME,dbname)
            apscom.warn(message)
            raise
        query_res_json = "{0}/{1}/{2}_{1}_query.json".format(globalvariables.DB_BACKUP_LOG_PATH,dbsid,globalvariables.HOST_NAME)
        if not os.path.exists(query_res_json):
            message = "Error: Not active {0}".format(dbname)
            apscom.info(message)
            return None
        query_file = open(query_res_json.strip(), 'r')
        query_output = json.load(query_file)
        query_file.close()
        if query_output["NEWLY_PROVISIONED"]==0:
            backup_option = "db_to_reco_db_arch_to_oss"
            #db_wallet_backup.main(db_name=dbname, bkp_target="oss",retention_days=retention_days, action='backup')
            #db_artifacts_backup.main(db_name=dbname, bkp_target="oss",retention_days=retention_days, action='backup')
        apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        apscom.info("Please wait taking {1} backup for {0} ..............".format(dbname,backup_option))
        rman_running=query_output["RMAN_RUNNING_STATUS"]

        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            if verify_lib_files(dbname):
                message = "Verified the library files (libopc.so & opc.ora)!"
                apscom.info(message)
            if backup_option == "archivelog_to_oss" and not commonutils.check_em_systemtype() :
                if commonutils.archivelog_backup_enabled(dbname):
                    rman_cmd=backup_rman_cmd(backup_option,dbname,retention_days,tag)
            elif backup_option == "incre_to_reco_arch_to_oss" and not commonutils.check_em_systemtype():
                if commonutils.check_incremental_backup_eligibility(dbname):
                    rman_cmd=backup_rman_cmd(backup_option,dbname,retention_days,tag)
            else:
                rman_cmd=backup_rman_cmd(backup_option,dbname,retention_days,tag)
        else:
            crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
            with open(crsctl_json) as json_file:
                json_data = json.load(json_file)
            for key in json_data:
                unique_db_name = json_data[key]['db_unique_name']
                if unique_db_name == dbname:
                    if retention_days == 0 and tag is not None:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3}  '".format(BASE_DIR, key, backup_option,tag)
                    elif tag is None:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --retention-days={3} '".format(BASE_DIR, key, backup_option,retention_days)
                    elif tag is None and retention_days == 0:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} '".format(BASE_DIR, key, backup_option)
                    else:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} --retention-days={4}  '".format(BASE_DIR, key, backup_option,tag,retention_days)
                else:
                    if retention_days == 0 and tag is not None:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3}  '".format(BASE_DIR, key, backup_option,tag)
                    elif tag is None:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --retention-days={3} '".format(BASE_DIR, key, backup_option,retention_days)
                    elif tag is None and retention_days == 0:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} '".format(BASE_DIR, key, backup_option)
                    else:
                        rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} --retention-days={4}  '".format(BASE_DIR, key, backup_option,tag,retention_days)
        if rman_cmd:
            [res, ret_code,stderr] = commonutils.execute_shell(rman_cmd)
            apscom.info(res)
        # run metrics
        oci_sdk=ociSDK.ociSDK(globalvariables.DB_CONFIG_PATH_DEFAULT)
        # oci_sdk.get_oci_metrics(globalvariables.DB_CONFIG_PATH_DEFAULT)
        
    except Exception as e:
            message = "Failed to do rman backup!\n{0},{1}".format(stderr, e)
            # clear files
            sre_path='{0}/sre_db_remote_{1}*.cfg'.format(globalvariables.BACKUP_CFG_LOCATION,dbname)
            sre_files = glob.glob(sre_path)
            for sre_file in sre_files:
                os.remove(sre_file)
            apscom.warn(message)
            raise

def backup_rman_cmd(backup_option,dbname,retention_days,tag):
    try:
        if retention_days == 0 and tag is not None:
            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} '".format(BASE_DIR,dbname,backup_option,tag)
        elif tag is None:
            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --retention-days={3} '".format(BASE_DIR,dbname,backup_option,retention_days)
        elif tag is None and retention_days == 0:
            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} '".format(BASE_DIR,dbname,backup_option)
        else:
            rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} --retention-days={4} '".format(BASE_DIR,dbname,backup_option,tag,retention_days)
        return rman_cmd
    except Exception as e:
        message="failed to generate rman_cmd to take backup".format(sys.exc_info()[1:2],e)
        apscom.warn(message)
        raise

# to ensure backup runs only on the minumum node of a cluster
def validate_database_condition(dbname):
    try:
        is_valid=False
        if force_flag:
            is_valid = True
        else:
            host_count=commonutils.get_dbname_db_count(dbname)
            if(int(host_count)>2):
                db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                running_db_odd_hosts,running_db_even_hosts=commonutils.get_dbname_db_nodes(dbname,db_uniq_name)
                min_odd_node_name=min(running_db_odd_hosts, key=lambda odd_node: odd_node['running_db_node_num'])
                if running_db_even_hosts:
                    min_even_node_name = min(running_db_even_hosts,
                                             key=lambda even_node: even_node['running_db_node_num'])
                else:
                    min_even_node_name = min(running_db_odd_hosts,
                                             key=lambda odd_node: odd_node['running_db_node_num'])

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

def execute_house_keeping():
    try:
        cmd2="pgrep -f db_tasks.py"
        out=commonutils.execute_shell(cmd2)[0]
        if not out:
            db_tasks.housekeeping_logs()
    except Exception as e:
        message = "Failed to execute db_tasks!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

TAKE_ACTION = {
    "backup": take_action_backup,
    "validate": take_action_validate,
    "validate_db_reco": take_action_validate,
    "validate_db_oss": take_action_validate,
    "restore_validate": take_action_validate
}

usage_str = """
    rman_wrapper_oss.py - Backup tool to backup FA on OCI Pod DB Backups.

    ** Should be run as root user**
    /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh -b <backup type>

    -b                  - Required - Backup Options Supported:
                            db_to_reco_db_arch_to_oss : Full Database Backup to Reco followed by Full Databaes Backup to OSS
                            incre_to_reco_arch_to_oss : Incremental Backup to Disk
                            incre_to_oss_arch_to_oss : Incremental Backup to OSS        
                            db_to_reco : Database Backup to Reco
                            db_to_oss: Database Backup to OSS
                            archivelog_to_oss: Archivelog Backup to OSS
    
    -d                  - Optional - DB unique name - only for alternative buckets

    --retention-days    - Optional - Retention days of give backup type.
    
    -f                  - Optional - Use this option to force backup on even node'

    --tag               - Optional - Optional tag, if other than standard ones
    
    --bucket_name       - Optional - does one off backup to given bucket name, ensure policies and permissions to write to bucket are in place

    --user_name         - Optional - OSS user name performed for one off backup if other than default user
    --debug_log         - Optional Use this oprion to enable logging as debug mode


"""

def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('-b', action='store', dest='backup',choices=BACKUP_SUPPORTED, help='Required - Specify the action: db_to_reco_db_arch_to_oss,incre_to_reco_arch_to_oss,incre_to_oss_arch_to_oss,archivelog_to_oss,db_to_reco,db_to_oss')
        parser.add_option('-c', '--config-file', action='store', dest='oci_config_path',default=globalvariables.DB_CONFIG_PATH_DEFAULT, type='string',help='Optional -Path of oci config file.')
        parser.add_option('--retention-days', action='store', dest='retention_days', default=0, type=int,help='Optional - Retention days of give backup type.')
        # parser.add_option('--backup-status', action='store', dest='backup_status', default='active',choices=['active', 'obsolete', 'all', 'failed'])
        parser.add_option('-f','--force', action='store', dest='force_flag',default=False,help='Optional - Use this option to force backup on even node')
        # fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1099
        parser.add_option('-d', '--dbname', action='store', dest='db_name',default=None,help='Optional - pass db unique name')
        parser.add_option('--bucket_name', action='store', dest='bucket_name',default=None,help='Optional - does one off backup to given bucket name, ensure policies and permissions to write to bucket are in place ')
        parser.add_option('--user_name', action='store', dest='user_name', default=None,help='Optional - OSS user name performed for one off backup if other than default user')
        # validate
        parser.add_option('-a','--action', action='store', dest='action', help='Pass action like validate,restore_validate etc ')

        #fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1035
        parser.add_option('--tag', action='store', dest='tag', default=None,help='Optional - provide tag, if other than standard ones')
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log', default="no",help='Optional - Get logs in debug mode')

        (opts, args) = parser.parse_args()
        if opts.backup:
            return (opts, args)
        elif opts.action:
            return (opts, args)
        else:
            parser.error('-b not passed nor --action is passed, either -b or --action option is required')
            
        return (opts, args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.warn(message)
        raise

def cleanup_sigint():
    sre_path='{0}/sre_db_remote_{1}*.cfg'.format(globalvariables.BACKUP_CFG_LOCATION,dbname)
    sre_files = glob.glob(sre_path)
    if (sre_files):
        for sre_file in sre_files:
            os.remove(sre_file)
    # 
    passwd_file='{0}/.passwd.json'.format(globalvariables.BACKUP_CFG_LOCATION)
    # 
    db_exceptions_file = globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt"
    message = "review {0} and correct the entries ".format(db_exceptions_file)
    apscom.info(message)
    # 
    if (os.path.exists(passwd_file)):
        os.remove(passwd_file)

def exit_gracefully(signum, frame):
    # restore the original signal handler as otherwise evil things will happen
    # in raw_input when CTRL+C is pressed, and our signal handler is not re-entrant
    signal.signal(signal.SIGINT, original_sigint)
    signal.signal(signal.SIGTERM, original_sigint)

    try:
        if input("\nReally quit? (y/n)> ").lower().startswith('y'):
            cleanup_sigint()
            sys.exit(1)

    except KeyboardInterrupt:
        print("quitting ....")
        sys.exit(1)

    # restore the exit gracefully handler here    
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

def main():
    #adp exa check as part of FAOCI-775#
    adp_status=''
    statuscode=''
    cmd="/usr/bin/timeout 300 {0}/adp_enabled_check.sh".format(globalvariables.DB_SHELL_SCRIPT)
    [adp_status,statuscode,stderr]=commonutils.execute_shell(cmd)
    if statuscode > 0:
        apscom.error(adp_status)
    backup_option=None
    validate_option=None
    global force_flag
    global log_file_wrapper
    global dbname
    global bucket_name
    global tag
    try:
        global filename
        global log_file_path
        (options, args) = parse_opts()
        if options.backup:
            backup_option = options.backup
        elif options.action:
            validate_option = options.action
        # 
        force_flag = options.force_flag
        dbname = options.db_name
        bucket_name = options.bucket_name
        rman_user=options.user_name
        tag = options.tag
        retention_days=options.retention_days
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

        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
        filename = log_file_path + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME,
                                                            os.path.basename(__file__).split(".")[0],
                                                            datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file_wrapper = apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        # check invocation
        # invocation = os.getenv('BKP_INVOCATION')
        # if invocation == "cron":
        #     apscom.info("rman_wrapper script invoked using cron or mcollective or jc")
        # elif invocation == "manual":
        #     apscom.info("rman_wrapper script invoked manually")
        # else:
        #     apscom.info("cannot determine how rman_wrapper script was invoked")
        # 
        if(getpwuid(os.stat('/u02/backup/').st_uid).pw_name=='root'):
            for file_name in glob.glob('/u02/backup/**', recursive=True):
                shutil.chown(file_name, "oracle","oinstall")
        try:
            if(getpwuid(os.stat(log_file_path).st_uid).pw_name=='root'):
                shutil.chown(log_file_path,"oracle","oinstall")
            if os.path.exists(globalvariables.PROCESS_LIST_FILE_LOCATION):
                file_name = globalvariables.PROCESS_LIST_FILE_LOCATION.split('.')[0]
                file_name_prev = file_name + "_" + 'previous.txt'
                if os.path.exists(file_name_prev):
                    os.remove(file_name_prev)
                os.rename(globalvariables.PROCESS_LIST_FILE_LOCATION, file_name_prev)
                with open(file_name_prev, "r") as fnp:
                    lines = fnp.readlines()
                    for line in lines:
                        proc_id=line.split(":")[0]
                        if proc_id and psutil.pid_exists(int(proc_id)):
                            ps_proc_id = psutil.Process(int(proc_id))
                            if ps_proc_id.status() == 'zombie':
                                parent_proc_id=ps_proc_id.ppid()
                                if parent_proc_id !=1:
                                    ps_parent_proc_id=psutil.Process(parent_proc_id)
                                    ps_parent_proc_id.kill()
                fnp.close()
        except Exception as e:
            message = "Failed to validate existed process!\n{0} {1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)

        if options.backup:
            if backup_option not in BACKUP_SUPPORTED:
                msg = "please enter valid backup type"
                apscom.error(msg)

            if not commonutils.is_node_exception_list():
                # fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1099
                if dbname and bucket_name and bucket_name!='RMAN_BACKUP':
                    database_config.cross_region_backup(dbname,bucket_name,backup_option,rman_user, cross_region_flag='y')
                elif dbname:
                    rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2} --tag={3} --retention-days={4} '". \
                        format(BASE_DIR, dbname, backup_option,tag,retention_days)
                    [res, ret_code, stderr] = commonutils.execute_shell(rman_cmd)
                else:
                    TAKE_ACTION.get("backup")(options)
                # TAKE_ACTION.get("backup")(options)
            else:
                message = "Exiting backups as {0} added in db_node_exceptions.txt!".format(globalvariables.HOST_NAME)
                apscom.warn(message)
                raise
            # if backup_option=="incre_to_reco_arch_to_oss" or backup_option=="incre_to_oss_arch_to_oss":
            #     rpmupdates.verify_upgrade_rpm()
        # 
        if commonutils.check_backup_priority_flag("Validate_backup_priority_enabled"):
            if options.action in globalvariables.validate_queue_btp:
                backup_to_check=[options.action]
                if commonutils.check_priority_bkp_status(backup_to_check,options.action):
                    message="{0} is already running on this node".format(options.action)
                    apscom.error(message)

        if options.action == 'validate_db_oss':            
            TAKE_ACTION.get("validate_db_oss")(options)
        if options.action == 'validate_db_reco':            
            TAKE_ACTION.get("validate_db_reco")(options)
        if options.action == 'validate':            
            TAKE_ACTION.get("validate")(options)
        if options.action == 'restore_validate':            
            TAKE_ACTION.get("restore_validate")(options)

    except Exception as e:
        message = "Failed to do {0},{1}!".format(backup_option,e)
        apscom.warn(message)
        rman_oss.create_backup_metadata(log_file_wrapper, backup_option, "rman_wrapper", "FAILED", "")
        sys.exit(1)
    finally:
        commonutils.remove_backup_oss_passwd()
        end_time = time.time()
        final_time = round(end_time - start_time, 2)
        message = "Time taken to execute complete script is {0} seconds".format(
            final_time)
        apscom.info(message)
        if backup_option != 'archivelog_to_oss':
            post_backup_metadata.post_database_exception()
        # if backup_option=="incre_to_reco_arch_to_oss" or backup_option=="incre_to_oss_arch_to_oss":
        #     rpmupdates.verify_upgrade_rpm()

if __name__ == "__main__":
    original_sigint = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    main()


