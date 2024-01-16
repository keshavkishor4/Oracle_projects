#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      database_config.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       08/12/20 - initial version (code refactoring)
    Zakki Ahmed           08/20/21  - FY21Q1
    Vipin Azad            12/05/22 - Jira - FSRE-75
"""
#### imports start here ##############################
import glob
import os
import shutil
import sys
from datetime import datetime
from pwd import getpwuid
import requests

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import ociSDK,apscom,commonutils,globalvariables,load_oci_config,post_backup_metadata,instance_metadata
from db import validate_sbt_test,database_config_bkup_opc_install
import json
import traceback
env_type = ""
#### imports end here ##############################

hostnm = globalvariables.LOCAL_HOST.split('.')[0]
silver_dr_file = globalvariables.DB_CONFIG_PATH + "/silver_dr.txt"
force_flag=""
db_group_dict = {}
db_group_dict['large_db'] = {}
db_group_dict['medium_db'] = {}
db_group_dict['small_db'] = {}
def get_prerequisites(dbname):
    try:
        stderror=""
        crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
        with open(crsctl_json) as json_file:
            json_data = json.load(json_file)
        for key in json_data:
            if dbname == json_data[key]['db_name']:
                dbname=key
        
        if commonutils.check_em_systemtype():
            str_dbcfg_querypool = "su oracle -c 'source {2}/setpyenv.sh;source {0}/utils/db/scripts/shell/set_ora_env.sh {1};python {3}/db_query_pool.py {4}'".\
                    format(BASE_DIR,dbname,globalvariables.SETPY_PATH,globalvariables.QUERY_POOL_PATH,"em_query.txt")
        elif commonutils.check_dbaas_systemtype():
            str_dbcfg_querypool = "su oracle -c 'source {2}/setpyenv.sh;source {0}/utils/db/scripts/shell/set_ora_env.sh {1};python {3}/db_query_pool.py {4}'".\
                    format(BASE_DIR,dbname,globalvariables.SETPY_PATH,globalvariables.QUERY_POOL_PATH,"dbaas_query.txt")
        else:
            str_dbcfg_querypool = "su oracle -c 'source {2}/setpyenv.sh;source {0}/utils/db/scripts/shell/set_ora_env.sh {1};python {3}/db_query_pool.py {4}'".\
                    format(BASE_DIR,dbname,globalvariables.SETPY_PATH,globalvariables.QUERY_POOL_PATH,"query.txt")
        
        [dbconfig_res_json,ret_code,stderror]=commonutils.execute_shell(str_dbcfg_querypool)
        query_file = open(dbconfig_res_json.strip(), 'r')
        query_output = json.load(query_file)
        query_file.close()
        return query_output
    except Exception as e:
        message = "Failed to run get_prerequisite!{0},check db status for {0}.....\n{1} {2}".format(dbname,stderror,e)
        apscom.info(message)
        return None

def db_group_by_size(query_output,dbname):
    try:
        db_size = query_output["DB_SIZE_GB"]
        with open(globalvariables.DB_CONFIG_PATH_JSON, 'r') as dbsize:
            data = json.load(dbsize)
        ldb_size=data["db_size"]["large_db"]
        sdb_size=data["db_size"]["small_db"]
        if db_size:
            if  db_size > ldb_size:
                db_type = 'large_db'
            elif ldb_size > db_size > sdb_size:
                db_type = 'medium_db'
            else:
                db_type = 'small_db'
        else:
            db_type = 'small_db'
            db_size = ''
        db_group_dict[db_type][dbname] = db_size

    except Exception as e:
        message = "Failed to run get_prerequisite!{0},{1},check db status for {0}.....{2}".format(dbname,
                                                                                               sys.exc_info()[1:2],e)
        apscom.info(message)
        return None
def restore_rmanconfig_passwd():
    try:
        rman_file_name=globalvariables.RMAN_SCRIPTS+'/configuration.rman'
        file_name=globalvariables.DB_CONFIG_PATH+'/bkup_ocifsbackup_sre.cfg'
        with open(file_name,"r") as fp:
            lines = fp.readlines()
            for line in lines:
                if "swiftobjectstorage" in line:
                    ns = line.split("=")[1].split("/")[-2]
                if "user" in line:
                    oss_user = line.split("=")[1]
            if not (oss_user or ns):
                message="oss_user or tenancy cannot be determined, ensure {0} is correctly filled".format(file_name)
                apscom.warn(message)
        if not os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json"):
            commonutils.download_passwd_file()
        with open(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json", 'r') as passrdfile:
            passwd_file = json.load(passrdfile)
        backup_oss_passwd = passwd_file[ns.strip()][oss_user.strip()]
        cmd = "{0} --key {1}".format(globalvariables.DECRYPT_TOOL, backup_oss_passwd)
        [output, ret_code, stderror] = commonutils.execute_shell(cmd)
        # run validate oss_passwd based out output
        with open(rman_file_name, "a") as rman_config:
            # sre_cfg.write("\n")
            rman_config.write("set encryption on identified by '"+output+"' only;")
    except Exception as e:
        message = "unable to set encryption for the backups.".format(sys.exc_info()[1:2], e)
        apscom.warn(message)


def validate_library_path_cross(dbname, bucket_name, sre_file_name):
    try:
        # "/var/opt/oracle/dbaas_acfs/oci_backup/${db_name}"
        file_opc =  globalvariables.FA_RMAN_ORA_PATH + \
            "/oci_backup/" + dbname + "/lib/libopc.so"
        file_ora = globalvariables.FA_RMAN_ORA_PATH + \
            "/oci_backup/" + dbname + "/opc" + dbname + ".ora"
        bucket_name = bucket_name.strip()
        if os.path.exists(file_opc) and os.path.exists(file_ora):
            with open(file_ora, 'r') as f:
                for line in f:
                    if "OPC_CONTAINER" in line:
                        # print(line)
                        data = line.split("=")[1].strip()
                        if data != bucket_name:
                            cmd = "su root -c '/bin/bash {0}/opc_install_config.sh {1}  {2}/{3} {4}'".format(
                                    globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_CONFIG_PATH, sre_file_name, bucket_name)
                            [rman_status, ret_code,
                                stderr] = commonutils.execute_shell(cmd)
                            
                            if ret_code == 0:
                                cmd = "su oracle -c '/bin/bash {0}/check_swiftobj_oss.sh {1}  {2} '".format(
                                globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_BACKUP_LOG_PATH)
                                [rman_status, ret_code,
                                    stderr] = commonutils.execute_shell(cmd)
                                #Calling opc_ifr_param to add param for Bug 34419101 - OCIBACKUP OPTION TO MOVE RMAN BACKUP TO OSS IA TIER 
                                database_config_bkup_opc_install.opc_ifr_param(file_ora)
                        else:
                            message = "OPC_Container value and bucket name is same in opc{0}.ora file ".format(
                                dbname)
                            apscom.info(message)
                    # return ret_code
        else:
            cmd = "su root -c '/bin/bash {0}/opc_install_config.sh {1}  {2}/{3} {4}'".format(
                                    globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_CONFIG_PATH, sre_file_name, bucket_name)
            message = "starting opc install config {0}".format(cmd)
            apscom.info(message)
            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
            message = "RMAN_STATUS {0}, RETURN_CODE {1}, STDERR {2}".format(rman_status, ret_code,stderr)
            apscom.info(message)
            if ret_code == 0:
                cmd_swift = "su oracle -c '/bin/bash {0}/check_swiftobj_oss.sh {1}  {2} '".format(
                    globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_BACKUP_LOG_PATH)
                message = "Starting check swiftobj oss {0}".format(cmd_swift)
                apscom.info(message)
                [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd_swift)
                message = "RMAN_STATUS {0}, RETURN_CODE {1}, STDERR {2}".format(rman_status, ret_code,stderr)
                apscom.info(message)
                
                #Calling opc_ifr_param to add param for Bug 34419101 - OCIBACKUP OPTION TO MOVE RMAN BACKUP TO OSS IA TIER 
                database_config_bkup_opc_install.opc_ifr_param(file_ora)
            # return ret_code

        with open(file_ora, 'r') as f:
            for line in f:
                if "OPC_CONTAINER" in line:
                    # print(line)
                    data = line.split("=")[1].strip()
                    if data == bucket_name:
                        cmd = "su oracle -c '/bin/bash {0}/check_swiftobj_oss.sh {1}  {2} '".format(
                            globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_BACKUP_LOG_PATH)
                        [rman_status, ret_code,
                            stderr] = commonutils.execute_shell(cmd)
                        if ret_code == 1:
                            cmd = "su root -c '/bin/bash {0}/opc_install_config.sh {1}  {2}/{3} {4}'".format(
                                globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_CONFIG_PATH, sre_file_name, bucket_name)
                            [rman_status, ret_code,
                                stderr] = commonutils.execute_shell(cmd)
                        # return ret_code
                    else:
                        message = "OPC_Container value and bucket name is not same in opc{0}.ora file ".format(
                            dbname)
                        apscom.warn(message)
    except Exception as e:
        message = "Failed to validate library configuration for {0} {1}".format(
            dbname,e)
        apscom.warn(message)

def restore_backup_oss_passwd(new_file_name):
    try:
        oss_user = None
        ns = None
        bkup_pass_available=False
        if os.path.exists("{0}/{1}".format(globalvariables.DB_CONFIG_PATH,new_file_name)):
            file_name = "{0}/{1}".format(globalvariables.DB_CONFIG_PATH,new_file_name)
        elif os.path.exists("{0}/{1}".format(globalvariables.ARTIFACTS_BACKUP_PATH,new_file_name)):
            file_name = new_file_name
        elif os.path.exists(new_file_name):
            file_name = new_file_name
        else:
            message="{0} file does not exist".format(new_file_name)  
            apscom.warn(message) 
            
        if os.path.exists(file_name): 
            #with open(BASE_DIR+'/config/db/'+file_name+'',"r") as fp:    
            with open(file_name,"r") as fp:            
                lines = fp.readlines()
                for line in lines:
                    if "swiftobjectstorage" in line:
                        ns = line.split("=")[1].split("/")[-2]
                    if "user" in line:
                        oss_user = line.split("=")[1]
                    if "bkup_oss_passwd" in line:
                        bkup_pass_available= True
                    if "bkup_oss_url" in line:
                        bkup_oss_url  = line.split("=")[1]
                if not (oss_user or ns):
                    message="{1}oss_user or tenancy cannot be determined, ensure {0} is correctly filled".format(file_name, globalvariables.RED)
                    apscom.warn(message)
                if not bkup_pass_available and oss_user:
                    # Internal testing comment above three lines, that will refer to local file.
                    if not os.path.exists(globalvariables.BACKUP_CFG_LOCATION+"/.passwd.json"):
                        commonutils.download_passwd_file()
                    #TBI
                    with open(globalvariables.BACKUP_CFG_LOCATION+"/.passwd.json", 'r') as passrdfile:
                        passwd_file = json.load(passrdfile)
                    backup_oss_passwd = passwd_file[ns.strip()][oss_user.strip()]
                    cmd = "{0} --key {1}".format(globalvariables.DECRYPT_TOOL,backup_oss_passwd)
                    [output,ret_code,stderror]=commonutils.execute_shell(cmd)
                    # run validate oss_passwd based out output
                    validate_sbt_test.validate_swiftobj_pass(oss_user.strip(),output.strip(),bkup_oss_url.strip())
                    #with open(globalvariables.DB_CONFIG_PATH+'/'+file_name, "a") as sre_cfg:
                    with open(file_name, "a") as sre_cfg:    
                        #sre_cfg.write("\n")
                        sre_cfg.write("bkup_oss_passwd="+output)
    except Exception as e:
        message = "failed to update the bkup_oss_passwd password {0},{1}!".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)

def update_all_pod_flag(dbname,update=False):
    try:
        with open(globalvariables.pod_info_file, "r") as fp:
            lines = fp.readlines()
            count = 0
            line_num = 0
            line_nums = []
            for line in lines:
                line_num = line_num + 1
                if (line.startswith(dbname) and ":y" in line):
                    count += 1
                    if count > 1 or update:
                        line_nums.append(line_num)
            fp.close()
            if count > 1 or update:
                commonutils.replace_line(globalvariables.pod_info_file,"",line_nums)
    except Exception as e:
        message = "Failed to update all pod flag {0},{1}!".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)
    
#Enh 35378766 - OMS BACKUP RPM - PLEASE REVEIW AND BACKORT ALL LATEST DESIRED CHANGES FOR OMS BACKUP RPM
def non_fa_em_prerequisites_check(dbname,prerqs,prereq1,prereq4,prereq4_plug_or_rename,oracle_home):
    try:
        message='non_fa_em_prerequisites_check for {0}'.format(dbname)
        apscom.info(message)
        DB_ROLE=prerqs['DATABASE_ROLE']
        if prereq1 != 1:
            message = "SQL return code: {0},{1} is not 0 so DB connectivity failed. Not running config".format(dbname,prereq1)
            apscom.warn(message)
            raise Exception(message)
        else :
            if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
                # re-check for ODS databases and non-fa databases
                db_group_by_size(prerqs, dbname)
                update_all_pod_flag(dbname, update=True)
                if not 'PHYSICAL' in DB_ROLE:
                    # lib_type = commonutils.get_lib_file_type()
                    # validate_sbt_test.validate_sbttest(dbname, oracle_home,lib_type,None)
                    database_config_bkup_opc_install.bkup_opc_install(dbname,oracle_home,None)
                else:
                    message="{0} is a {1} not executing backup config".format(dbname,DB_ROLE)
                    apscom.warn(message)
    except Exception as e:
        message = "Failed to check prerequisites for em DB - {0},{1}!".format(dbname, e)
        apscom.warn(message)
        raise Exception(message)
    
def non_fa_prerequisites_check(dbname,prerqs,prereq1,prereq4,prereq4_plug_or_rename,oracle_home):
    try:
        message='non_fa_prerequisites_check for {0}'.format(dbname)
        apscom.info(message)
        DB_ROLE=prerqs['DATABASE_ROLE']
        if prereq1 != 1:
            message = "SQL return code: {0},{1} is not 0 so DB connectivity failed. Not running config".format(dbname,prereq1)
            apscom.warn(message)
            raise Exception(message)
        else :
            if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
                # re-check for ODS databases and non-fa databases
                if prereq4_plug_or_rename > 8:
                    db_group_by_size(prerqs, dbname)
                    update_all_pod_flag(dbname, update=True)
                    if not 'PHYSICAL' in DB_ROLE:
                        lib_type = commonutils.get_lib_file_type()
                        validate_sbt_test.validate_sbttest(dbname, oracle_home,lib_type,None)
                        #database_config_bkup_opc_install.bkup_opc_install(dbname,oracle_home,None)
                    else:
                       message="{0} is a {1} not executing backup config".format(dbname,DB_ROLE)
                       apscom.warn(message)
            else:
                if prereq4_plug_or_rename > 8:
                    db_group_by_size(prerqs, dbname)
                    lib_type = commonutils.get_lib_file_type()
                    #validate_sbt_test.validate_sbttest(dbname, oracle_home,lib_type,None)
                    validate_sbt_test.nonfa_dbaas_validate_sbt(dbname)
                else:
                    message = "Condition not met for {0} (got the value={1}) since elasped of DB creation less than 8 hours, hence not running config".format(
                        dbname, prereq4_plug_or_rename)
                    apscom.warn(message)
                    update_all_pod_flag(dbname, update=True)
    except Exception as e:
        message = "Failed to check prerequisites {0},{1}!".format(dbname, e)
        apscom.warn(message)
        raise Exception(message)
    
def fa_prerequisites_check(prerqs, prereq1, prereq2, prereq3, prereq4, prereq5, dbname, bucket_name, oracle_home, cross_region_flag,force_flag="", sre_file=None):
    try:
        if prereq1 != 1:
            message = "SQL return code: {0},{1} is not 0 so DB connectivity failed. Not running config".format(dbname,prereq1)
            apscom.warn(message)
            raise Exception(message)
        elif prereq2 >= 2:
            message = "Checking if there are more than 0 PDBs in Read/Write mode for {0}-> Values is {1}".format(dbname,prereq2)
            apscom.info(message)
            if prereq3 == 0:
                message = "Checking value of condition4 which should be greater than 8 for {0}".format(dbname)
                apscom.info(message)
                if prereq4 > 8:
                    if prereq5 == 'PRIMARY':
                        message = "Checking value of condition5 database to be PRIMARY for {0}".format(dbname)
                        apscom.info(message)
                        db_group_by_size(prerqs, dbname)
                        if oracle_home:
                            #sre_file_name = "{0}/{1}".format(globalvariables.DB_CONFIG_PATH,"sre_db.cfg")
                            if cross_region_flag == 'y':
                                flag_str = validate_library_path_cross(dbname, bucket_name, sre_file_name)
                            else:
                                #print("Inside else block to execute opc install")
                                #flag_str = validate_library_path(dbname, sre_file_name)
                                flag_str = database_config_bkup_opc_install.bkup_opc_install(dbname,oracle_home,force_flag)
                            # flag_str = '/var/opt/oracle/bkup_api/bkup_api bkup_chkcfg --dbname="{0}" |grep "Config files"|cut -d: -f4'.format(dbname)
                    else:
                        message = "Condition5 not met for {0} (got the value={1}) database role is {1} ".format(dbname, prereq5)
                        apscom.warn(message)
                        update_all_pod_flag(dbname, update=True)
                else:
                    message = "Condition4 not met for {0} (got the value={1}) since elasped of DB creation less than 8 hours, hence not running config".format(
                        dbname, prereq4)
                    apscom.warn(message)
                    update_all_pod_flag(dbname, update=True)
            else:
                message = "Condition3 not met for {0} (got the value={1}) i.e PDBs other than the POD PDBs exist in the CDB, hence not running config".format(
                    dbname, prereq3)
                apscom.warn(message)
                update_all_pod_flag(dbname, update=True)
        else:
            message = "Condition2 {1} Instance does not contains 2 PDBs in read write mode for {0}, so not running config".format(
                dbname, prereq2)
            apscom.warn(message)
            update_all_pod_flag(dbname, update=True)
    except Exception as e:
        traceback.print_exc()
        message = "Failed to check prerequisites {0},{1}!".format(dbname, e)
        apscom.warn(message)

def cross_region_backup(dbname,bucket_name,backup_type,rman_user, cross_region_flag):
    file = globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt"
    try:
        #Add dbname to db_backup_exceptions.txt
        global retention_days
        env_type = commonutils.get_db_env_type(dbname)
        tag=globalvariables.backup_opts[backup_type][env_type]["tag"]
        retention_days=globalvariables.backup_opts[backup_type][env_type]["retention"]
        update_or_delete_line_from_txt(file,dbname,'Y')
        #Automate generation of sre_db_remote_<db_name>_<timestamp>.cfg -> ensure values are captured for PPD/PROD/GOV/EURA tenancy only from faops-backup-oss-info.json
        gen_sre_db_with_bucket(dbname,bucket_name,rman_user)
        #run db_config only for the database name provided through optional argument, else it will run for all databases
        # add get_prerequisites(dbname)
        prerqs = get_prerequisites(dbname)
        prereq1 = prerqs["CONN_STATUS"]
        prereq2 = prerqs["PDB_RW_COUNT"]
        prereq3 = prerqs["DIFF_NON-PDB_AND_RW-PDB"]
        prereq4 = prerqs["PROV_TIME"]
        prereq5=prerqs["DATABASE_ROLE"]
        fusion_db = prerqs["FUSION_PDB"]
        dbsid = commonutils.get_oracle_dbsid(dbname)
        oracle_home = commonutils.get_oracle_home(dbsid,dbname)
        fa_prerequisites_check(prerqs, prereq1, prereq2, prereq3, prereq4,prereq5, dbname, bucket_name,oracle_home,cross_region_flag,"-f",sre_file_name)
        # exec_db_config(dbname,sre_file_name)

        #add success condition
        #run backup
        # rman_cmd = "su oracle -c '/bin/bash {0}/bin/rman_oss.sh --dbname={1} -b {2}'".format(BASE_DIR, dbname, backup_type)
        rman_cmd = "su oracle -c 'sh {0}/bin/rman_oss.sh --dbname={1} --tag={3} --retention-days={4} -b {2}'".format(BASE_DIR, dbname, backup_type,tag,str(retention_days))
        message = "Running backup command: {0}".format(rman_cmd)
        apscom.info(message)
        [res, ret_code, stderr] = commonutils.execute_shell(rman_cmd)
        apscom.info(res)
        #restore config
        message = "Restoring original config"
        apscom.info(message)
        fa_prerequisites_check(prerqs, prereq1, prereq2, prereq3, prereq4,prereq5, dbname, bucket_name,oracle_home,"n","-f",sre_file_name)
        for sre_cfg_file in globalvariables.BACKUP_CFG_FILES:
            sre_file = globalvariables.BACKUP_CFG_LOCATION+ "/" + sre_cfg_file
            if os.path.exists(sre_file):
                shutil.chown(sre_file, "root", "root")
                restore_backup_oss_passwd(sre_cfg_file)
        #
        #exec_db_config(dbname,'bkup_ocifsbackup_sre.cfg',globalvariables.BACKUP_CFG_LOCATION+"/"+sre_file_name)
        #delete the data from db_backup_exceptions.txt
        update_or_delete_line_from_txt(file, dbname, 'N')
    except Exception as e:
        # clear files
        os.remove(globalvariables.BACKUP_CFG_LOCATION+"/"+sre_file_name)
        update_or_delete_line_from_txt(file, dbname, 'N')
        message = "Failed to do cross region backup!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise
    finally:
        update_or_delete_line_from_txt(file, dbname, 'N')

def cross_region_backup_silver_dr(dbname,bucket_name,rman_user, cross_region_flag):
    file = globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt"
    try:
        #Add dbname to db_bac
        bucket_name = bucket_name.strip()
        #Automate generation of sre_db_remote_<db_name>_<timestamp>.cfg -> ensure values are captured for PPD/PROD/GOV/EURA tenancy only from faops-backup-oss-info.json
        gen_sre_db_with_bucket(dbname,bucket_name,rman_user)
        #run db_config only for the database name provided through optional argument, else it will run for all databases
        # add get_prerequisites(dbname)
        prerqs = get_prerequisites(dbname)
        prereq1 = prerqs["CONN_STATUS"]
        prereq2 = prerqs["PDB_RW_COUNT"]
        prereq3 = prerqs["DIFF_NON-PDB_AND_RW-PDB"]
        prereq4 = prerqs["PROV_TIME"]
        prereq5=prerqs["DATABASE_ROLE"]
        fusion_db = prerqs["FUSION_PDB"]
        dbsid = commonutils.get_oracle_dbsid(dbname)
        oracle_home = commonutils.get_oracle_home(dbsid,dbname)
        fa_prerequisites_check(prerqs, prereq1, prereq2, prereq3, prereq4,prereq5, dbname, bucket_name,oracle_home,cross_region_flag,"-f",sre_file_name)
    except Exception as e:
        message = "Failed to do cross region backup!\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        # raise


def update_or_delete_line_from_txt(filename,db_name,insertline='N'):
    try:
        if insertline=='Y':
            with open(filename, "r") as fp:
                lines = fp.readlines()
            with open(filename, "a") as file:
                add='Y'
                for line in lines:
                    if db_name in line:
                        add='N'
                if add == 'Y':
                    file.write("{0} \n".format(db_name))

        else:
            with open(filename, "r") as fp:
                lines = fp.readlines()
            with open(filename, "w") as f:
                for line in lines:
                    if db_name not in line:
                        f.write(line)
            f.close()
    except Exception as e:
        message = "{1} with {2}....!\n{0},{1}".format(sys.exc_info()[1:2],filename,db_name)
        apscom.warn(message)
        raise

def gen_sre_db_with_bucket(dbname,bucket_name,rman_user):
    global sre_file_name
    try:
        if not rman_user:
            faops_backup_oss_info_file = globalvariables.FAOPS_OSS_INFO
            if os.path.exists(faops_backup_oss_info_file):
                with open(faops_backup_oss_info_file,'r') as f:
                    faops_backup_oss_info = json.load(f)
            if os.path.exists(globalvariables.OCI_SDK_META_FILE):
                with open(globalvariables.OCI_SDK_META_FILE,'r') as f:
                    oci_tenancy_info = json.load(f)
            for ns in faops_backup_oss_info:
                if ns == oci_tenancy_info["ns"]:
                    rman_user = faops_backup_oss_info[ns]["fa_rman_user"]
        env_type = commonutils.get_db_env_type(dbname)
        if env_type == "stage":
            retention_days = globalvariables.ENV_TYPE_STAGE
        else:
            retention_days = globalvariables.ENV_TYPE_PROD    
        sre_file_name = "sre_db_remote_{1}_{2}.cfg".format(
            globalvariables.DB_CONFIG_PATH, dbname, datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        sre_file="{0}/{1}".format(globalvariables.DB_CONFIG_PATH,sre_file_name)
        region = instance_metadata.ins_metadata().region
        #downloading password file to update sre_db_remote_<db_name>_.cfg with password
        with open(globalvariables.DB_CONFIG_PATH_DEFAULT, 'r') as oci_config_file:
            oci_config = json.load(oci_config_file)
        oss_namespace = oci_config["oss_namespace"]
        with open(globalvariables.CONFIG_PATH+'/faops-backup-oss-info.json','r') as oss_info:
            data = json.load(oss_info)
            for val in data:
                if oss_namespace in val:
                    valid_ns=True
        if not valid_ns:
            message = "{0} do not belongs to standard FA tenancy  ".format(oss_namespace)
            apscom.warn(message)
            return
        else:
            with open(sre_file, "w") as f:
                f.write('bkup_disk=yes\n')
                f.write('bkup_oss=yes\n')
                url_str='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                if not "uk-gov-" in region:
                    url_str='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                else:
                    url_str='https://swiftobjectstorage.{0}.oraclegovcloud.uk/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                f.write('bkup_oss_url='+url_str+'\n')
                f.write('bkup_oss_user='+rman_user+'\n')
                f.write('bkup_oss_recovery_window={0}\n'.format(retention_days))
                f.write('bkup_disk_recovery_window=14\n')
                f.write('bkup_daily_time=06:45\n')
                f.write('bkup_cron_entry=no\n')
            try:
                os.chmod(sre_file, 0o600)
                restore_backup_oss_passwd(sre_file_name)
            except Exception as e:
                message = "{3}Failed to change the permissions {2}\n{0}{1}".format(sys.exc_info()[1:2], e,sre_file,globalvariables.RED)
                apscom.warn(message)
                sys.exit(1)
    except Exception as e:
        message = "Failed gen_sre_db_with_bucket with to configure sre_db config for given bucket !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


def gen_sre_db_config():
    try:
        region = instance_metadata.ins_metadata().region
        local_sre_file="{0}/sre_db.cfg".format(globalvariables.DB_CONFIG_PATH)
        local_sre_file_status=False
        if os.path.exists(local_sre_file):
            with open(local_sre_file, 'r') as f:
                sre_data = f.readlines()
            for line in sre_data:
                if "swiftobjectstorage" in line:
                    local_sre_file_status = True
                    break

        if not local_sre_file_status:
            faops_backup_oss_info_file = "{0}/config/faops-backup-oss-info.json".format(BASE_DIR)
            if os.path.exists(faops_backup_oss_info_file):
                with open(faops_backup_oss_info_file,'r') as f:
                    faops_backup_oss_info = json.load(f)
            if os.path.exists(globalvariables.OCI_SDK_META_FILE):
                with open(globalvariables.OCI_SDK_META_FILE,'r') as f:
                    oci_tenancy_info = json.load(f)
            #
            for ns in faops_backup_oss_info:
                if ns == oci_tenancy_info["ns"]:
                    if faops_backup_oss_info[ns]["tenancy"] == oci_tenancy_info["tenancy_name"]:
                        bucket_name=faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]
                        oss_namespace=ns
                        rman_user=faops_backup_oss_info[ns]["fa_rman_user"]
                        with open(local_sre_file, "w") as f:
                            f.write('bkup_disk=yes\n')
                            f.write('bkup_oss=yes\n')
                            if not "uk-gov-" in region:
                                url_str='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                            else:
                                url_str='https://swiftobjectstorage.{0}.oraclegovcloud.uk/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                            f.write('bkup_oss_url='+url_str+'\n')
                            f.write('bkup_oss_user='+rman_user+'\n')
                            f.write('bkup_oss_recovery_window={0}\n'.format(retention_days))
                            f.write('bkup_disk_recovery_window=14\n')
                            f.write('bkup_daily_time=06:45\n')
                            f.write('bkup_cron_entry=no\n')
                        try:
                            os.chmod(local_sre_file, 0o600)
                            shutil.chown(local_sre_file, "oracle", "oinstall")

                        except Exception as e:
                            message = "{3}Failed to change the permissions {2}\n{0}{1}".format(sys.exc_info()[1:2], e,local_sre_file,globalvariables.RED)
                            apscom.warn(message)
                            # sys.exit(1)

                        break
                else:
                    pass
    except Exception as e:
        message = "Failed gen_sre_db.cfg with to configure sre_db config for given bucket !\n{0},{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

# to be completed later - 04/11/21
def validate_sre_db_config():
    try:
        region = instance_metadata.ins_metadata().region
        local_sre_file="{0}/sre_db.cfg".format(globalvariables.DB_CONFIG_PATH)
        faops_backup_oss_info_file = "{0}/config/faops-backup-oss-info.json".format(BASE_DIR)
        if os.path.exists(faops_backup_oss_info_file):
            with open(faops_backup_oss_info_file,'r') as f:
                faops_backup_oss_info = json.load(f)
        if os.path.exists(globalvariables.OCI_SDK_META_FILE):
            with open(globalvariables.OCI_SDK_META_FILE,'r') as f:
                oci_tenancy_info = json.load(f)
    except Exception as e:
        message = "Not able to validate sre db config"
        apscom.warn(message)

def main():
    #adp exa check as part of FAOCI-775#
    adp_status=''
    statuscode=''
    cmd="/usr/bin/timeout 300 {0}/adp_enabled_check.sh".format(globalvariables.DB_SHELL_SCRIPT)
    [adp_status,statuscode,stderr]=commonutils.execute_shell(cmd)
    print(statuscode)
    if statuscode > 0:
        apscom.error(adp_status)
    try:
        global log_file_db_config
        global log_file_path
        global bucket_name
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)
            for file_name in glob.glob(globalvariables.DB_BACKUP_LOG_PATH+"/**", recursive=True):
                shutil.chown(file_name, "oracle","oinstall")

        filename = log_file_path + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME,os.path.basename(__file__).split(".")[0],datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file_db_config = apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        load_oci_config.main()
        #
        # restore_backup_oss_passwd("bkup_ocifsbackup_sre.cfg")
        faops_backup_oss_info_file = "{0}/config/faops-backup-oss-info.json".format(BASE_DIR)
        if os.path.exists(faops_backup_oss_info_file):
            with open(faops_backup_oss_info_file,'r') as f:
                faops_backup_oss_info = json.load(f)
        if os.path.exists(globalvariables.OCI_SDK_META_FILE):
            with open(globalvariables.OCI_SDK_META_FILE,'r') as f:
                oci_tenancy_info = json.load(f)
        #
        for ns in faops_backup_oss_info:
            if ns == oci_tenancy_info["ns"]:
                if faops_backup_oss_info[ns]["tenancy"] == oci_tenancy_info["tenancy_name"]:
                    if commonutils.check_em_systemtype():
                        rman_user=faops_backup_oss_info[ns]["em_rman_user"] 
                    elif commonutils.check_dbaas_systemtype():
                        rman_user = faops_backup_oss_info[ns]["dbaas_rman_user"]
                    else:
                        rman_user=faops_backup_oss_info[ns]["fa_rman_user"] 
                    #bucket_name=faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]       
        #restore_rmanconfig_passwd()
        with open(globalvariables.pod_info_file, "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if globalvariables.LOCAL_HOST in line:
                    ok2backup = line.split(":")[-1]
                    if ok2backup.strip() == "y":
                        dbsid = line.split(":")[2]
                        dbname = line.split(":")[0]
                        #checking on silver DR db config 
                        if not database_config_bkup_opc_install.silver_dr_validate(dbname,rman_user):                        
                            oracle_home=commonutils.get_oracle_home(dbsid)
                            dir_path = globalvariables.DB_BACKUP_LOG_PATH + "/" + dbsid
                            if not os.path.exists(dir_path):
                                os.makedirs(dir_path)
                            if (getpwuid(os.stat(dir_path).st_uid).pw_name == 'root'):
                                shutil.chown(dir_path, "oracle", "oinstall")
                            prerqs=get_prerequisites(dbname)
                            if not prerqs:
                                continue
                            prereq1=prerqs["CONN_STATUS"]
                            prereq2=prerqs["PDB_RW_COUNT"]
                            prereq3=prerqs["DIFF_NON-PDB_AND_RW-PDB"]
                            prereq4=prerqs["PROV_TIME"]
                            prereq4_plug_or_rename=prerqs["PROV_TIME_PLUG_OR_RENAME"]
                            prereq5=prerqs["DATABASE_ROLE"]
                            fusion_db = prerqs["FUSION_PDB"]
                            print(prereq1,prereq2,prereq3,prereq4,prereq4_plug_or_rename,prereq5,fusion_db)
                            # with open(globalvariables.OCI_SDK_META_FILE,'r') as meta_info:
                            #     data = json.load(meta_info)
                            #     ns = data['ns']
                            #     #("Namespace is : ",ns)
                            # with open(globalvariables.FAOPS_OSS_INFO,'r') as oss_info:
                            #     data = json.load(oss_info)
                            #     for val in data:
                            #         if ns == val:
                            #             bucket_name = data[val]["fa_rman_oss_bn"][env_type]
                            env_type = commonutils.get_db_env_type(dbname)
                            if env_type == None:
                                message = "Unable to determine the envrionment type is stage or prod, for db {0}. Skipping backup for this database".format(dbname)
                                apscom.warn(message) 
                                pass
                            if env_type == "em_exa":
                                bucket_name = faops_backup_oss_info[ns]["em_rman_oss_bn"]
                            elif env_type == "dbaas":
                                bucket_name = faops_backup_oss_info[ns]["dbaas_rman_oss_bn"]
                            else:
                                bucket_name=faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]   
                            #bucket_name = "RMAN_BACKUP"
                            if fusion_db:
                                print("Executing this block")
                                fa_prerequisites_check(prerqs,prereq1,prereq2,prereq3,prereq4,prereq5,dbname,bucket_name,oracle_home,"n","",None)
                            elif commonutils.check_em_systemtype():
                                print("executing elif block")
                                non_fa_em_prerequisites_check(dbname,prerqs,prereq1,prereq4,prereq4_plug_or_rename,oracle_home)
                            else:
                                print("Executing else block")
                                non_fa_prerequisites_check(dbname,prerqs,prereq1,prereq4,prereq4_plug_or_rename,oracle_home)
        if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json"):
            os.remove(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json")
        file_name = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/db_group_by_size.json".format("exalogs")
        try:
            with open(file_name, 'w') as outfile:
                json.dump(db_group_dict, outfile, indent=4, sort_keys=True)
            outfile.close()
            message = "Successfully created {0} ....".format(file_name)
            apscom.info(message)
        except Exception as e:
            message = "unable to create {0} file_name , error with {1} ".format(file_name,e)
            apscom.error(message)
        #
    except Exception as e:
        message = "{2}Failed to do database config {0} with {1}!".format(sys.exc_info()[1:2],e,globalvariables.RED)
        apscom.warn(message)
    finally:
        if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json"):
            os.remove(globalvariables.BACKUP_CFG_LOCATION + "/.passwd.json")

if __name__ == "__main__":
    main()
