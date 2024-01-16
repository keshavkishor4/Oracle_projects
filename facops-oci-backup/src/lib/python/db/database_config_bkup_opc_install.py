#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      database_config_bkup_opc_install.py

    DESCRIPTION
      Functions for libopc install and config.

    NOTES

    MODIFIED        (MM/DD/YY)

    Jayant Mahishi       12/07/22 - initial version (code refactoring)
    Vipin Azad           02/12/22 - fixes for Bug 34853232
"""
#### imports start here ##############################
import glob
from math import prod
import os
import shutil
import sys
from datetime import datetime
from pwd import getpwuid
# from tkinter import N
import requests

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import ociSDK,apscom,commonutils,globalvariables,load_oci_config,post_backup_metadata,instance_metadata
from db import validate_sbt_test,database_config
import json
import traceback
import optparse
env_type = ""
#### imports end here ##############################
silver_dr_file = globalvariables.DB_CONFIG_PATH + "/silver_dr.txt"
backup_exception_file = globalvariables.DB_CONFIG_PATH + "/backup_exception_target_oss.txt"

def gen_sre_db_config(dbname):
    try :
        print("running gen_sre_db_config")
        local_sre_file=''
        realm = instance_metadata.ins_metadata().realmKey
        region = instance_metadata.ins_metadata().region
        env_type = commonutils.get_db_env_type(dbname)
        local_sre_file="{0}/sre_db_{1}.cfg".format(globalvariables.DB_CONFIG_PATH,env_type)
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
                    if env_type == "em_exa":
                        bucket_name = faops_backup_oss_info[ns]["em_rman_oss_bn"]
                        rman_user=faops_backup_oss_info[ns]["em_rman_user"]
                    elif env_type == "dbaas":
                        bucket_name = faops_backup_oss_info[ns]["dbaas_rman_oss_bn"]
                        rman_user=faops_backup_oss_info[ns]["dbaas_rman_user"]
                    else:
                        bucket_name=faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]
                        rman_user=faops_backup_oss_info[ns]["fa_rman_user"]
                    oss_namespace=ns
                    with open(local_sre_file, "w") as f:
                        f.write('bkup_disk=yes\n')
                        f.write('bkup_oss=yes\n')
                        if not "uk-gov-" in region:
                            url_str='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                        else:
                            url_str='https://swiftobjectstorage.{0}.oraclegovcloud.uk/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
                        f.write('bkup_oss_url='+url_str+'\n')
                        f.write('bkup_oss_user='+rman_user+'\n')
                        #f.write('bkup_oss_recovery_window='+retention_days+'\n')
                        f.write('bkup_oss_recovery_window=61\n')
                        f.write('bkup_disk_recovery_window=14\n')
                        f.write('bkup_daily_time=06:45\n')
                        f.write('bkup_cron_entry=no\n')
                    try:
                        os.chmod(local_sre_file, 0o600)
                        shutil.chown(local_sre_file, "oracle", "oinstall")
                        break
                        #local_sre_filename = os.path.basename(local_sre_file)
                        #database_config.restore_backup_oss_passwd(local_sre_file)

                    except Exception as e:
                        message = "{3}Failed to change the permissions {2}\n{0}{1}".format(sys.exc_info()[1:2], e,local_sre_file,globalvariables.RED)
                        apscom.warn(message)
                            
        #local_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type)
        fss_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type) 
        if os.path.exists(local_sre_file):
            shutil.copy(local_sre_file,"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type))
            validate_sbt_test.verify_copy_file("{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type),"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type))   
            database_config.restore_backup_oss_passwd(fss_sre_file)
    except Exception as e:
        message = "Failed to generate sre_db file. Please verify {0}".format(e)
        apscom.warn(message)


def opc_ifr_param(file_ora):
    try :
        existing_param = []
        with open (globalvariables.DB_CONFIG_PATH_JSON) as data:
            ia_tier =json.load(data)
            ia_tier_enable= ia_tier["enable_ia_tier"]["enable"].lower()
            ia_tier_param_low = [param.lower() for param in  ia_tier["enable_ia_tier"]["param"]]
            if ia_tier_enable == 'y':
                with open(file_ora,'a+') as add_data:
                    add_data.seek(0)
                    lines = add_data.readlines()
                    for line in lines:
                        if line.lower() in ia_tier_param_low:
                            existing_param.append(line.lower())
                    if not existing_param:
                        for param in ia_tier["enable_ia_tier"]["param"]:
                            if param.lower() not in existing_param:
                                add_data.write(param)
                                add_data.write("\n")

                        message="enable_ia_tier found to be Y, hence respective params added to {0}".format(file_ora)
                        apscom.info(message)
                    else:
                        message="enable_ia_tier found to be Y, However respective parameter already present in {0}".format(file_ora)
                        apscom.info(message)
            else:
                message="enable_ia_tier found to be N, hence skipping to add params to {0}".format(file_ora)
                apscom.info(message)
    except Exception as e:
        message = "Failed add ia_tier params for  {0}".format(file_ora)
        apscom.warn(message)


def opc_install(dbname,force_flag,bucket_name=None):
    try:
        # "/var/opt/oracle/dbaas_acfs/oci_backup/${db_name}"

        file_opc =  globalvariables.FA_RMAN_ORA_PATH + \
            "/oci_backup/" + dbname + "/lib/libopc.so"
        file_ora = globalvariables.FA_RMAN_ORA_PATH + \
            "/oci_backup/" + dbname + "/opc" + dbname + ".ora"

        #add_opc_param = True
        if os.path.exists(file_ora):
            with open(file_ora, 'r') as f:
                lines = f.readlines()
                for line in lines:
                    if 'OPC_CONTAINER' in line:
                        bucket, bucket_val = line.split("=")
                        bucket_val = bucket_val.strip()
                    # Bug 34419101 - OCIBACKUP OPTION TO MOVE RMAN BACKUP TO OSS IA TIER
                    # read db_config.json for enable_ia_tier key, if parameter already exists , no action, else add the new params
                    # _OPC_DEFERRED_DELETE=false
                    # _OPC_INFREQ_ACCESS=true
                    #if 'OPC_INFREQ_ACCESS' in line:
                    #    add_opc_param = False

            #If there is not earlier entry for OPC_DEFERED parameter in orafile
            #if add_opc_param :
        if os.path.exists(file_ora):
            opc_ifr_param(file_ora)
        #New condition added for bucket validation bucket_val == bucket_name (BUG 34853232)
        if os.path.exists(file_opc) and os.path.exists(file_ora) and force_flag != '-f' and bucket_val == bucket_name:
            try:
                cmd_swift = "su oracle -c '/bin/bash {0}/check_swiftobj_oss.sh {1}  {2} '".format(
                    globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_BACKUP_LOG_PATH)
                [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd_swift)
                #return ret_code

            except Exception as e:
                message = "Not able to connect to swift object please validate connectivity"
                apscom.error(message)

        else:
            env_type = commonutils.get_db_env_type(dbname)
            local_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type)
            if not os.path.exists(local_sre_file):
                if os.path.exists("{0}/sre_db_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type)):
                    shutil.copy("{0}/sre_db_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type),"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type))
                    validate_sbt_test.verify_copy_file("{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type),"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type))
            database_config.restore_backup_oss_passwd(local_sre_file)
            cmd = "su root -c '/bin/bash {0}/opc_install_config.sh {1}  {2} '".format(
                                    globalvariables.DB_SHELL_SCRIPT, dbname, local_sre_file)
            message = "starting opc install config {0}".format(cmd)
            apscom.info(message)
            [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd)
            message = "RMAN_STATUS {0}, RETURN_CODE {1}, STDERR {2}".format(rman_status, ret_code,stderr)
            apscom.info(message)
            #Calling opc_ifr_param to add param for Bug 34419101 - OCIBACKUP OPTION TO MOVE RMAN BACKUP TO OSS IA TIER
            opc_ifr_param(file_ora)

            if ret_code == 0:
                cmd_swift = "su oracle -c '/bin/bash {0}/check_swiftobj_oss.sh {1}  {2} '".format(
                    globalvariables.DB_SHELL_SCRIPT, dbname, globalvariables.DB_BACKUP_LOG_PATH)
                message = "Starting check swiftobj oss {0}".format(cmd_swift)
                apscom.info(message)
                [rman_status, ret_code,stderr] = commonutils.execute_shell(cmd_swift)
                message = "RMAN_STATUS {0}, RETURN_CODE {1}, STDERR {2}".format(rman_status, ret_code,stderr)
                apscom.info(message)
                #return ret_code

    except Exception as e:
        message = "Failed to validate library configuration for {0}".format(
            dbname)
        apscom.warn(message)

def bkup_install(dbname,force_flag):
    log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
    try:
        env_type = commonutils.get_db_env_type(dbname)
        local_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type)
        if not os.path.exists(local_sre_file):
            if ("{0}/sre_db_{1}cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type)):
                shutil.copy("{0}/sre_db_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type),"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type))
                validate_sbt_test.verify_copy_file("{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type),"{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type))    
        bkup_log_path = log_file_path + "backup-cfg_{0}_{1}.log".format(dbname,datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        flag_str = '/var/opt/oracle/bkup_api/bkup_api bkup_chkcfg --dbname="{0}" |grep "Config files"|cut -d: -f4'.format(dbname)
        database_config.restore_backup_oss_passwd(local_sre_file)
        flag = commonutils.execute_shell(flag_str)[0]
        if (force_flag == '-f' or flag == 'no'):
            bkup_str = '{0}/bkup -cfg {4}  -dbname="{2}" | tee -a {3}'.format(globalvariables.BACKUP_CFG_CMD_LOCATION, globalvariables.BACKUP_CFG_LOCATION, dbname,bkup_log_path,local_sre_file)
            #print("Inside bkup_install, the backup string",bkup_str)
            apscom.info('Running backup config command: {0}'.format(bkup_str))
            stderr=''
            [res, ret_code, stderr]=commonutils.execute_shell(bkup_str)
            if (res and 'ERROR' in res) or (stderr and 'ERROR' in stderr):
                message = "Failed to run backup configuration for db {0}.. {1}".format(dbname,stderr)
                apscom.warn(message)
            # raise
        else:
            message = "Successfully ran backup configuration for db {0}".format(dbname)
            apscom.info(message)
            opc_file_path="{0}/{1}/opc/opc{1}.ora".format(globalvariables.FA_RMAN_ORA_PATH,dbname)
            #Calling opc_ifr_param to add param for Bug 34419101 - OCIBACKUP OPTION TO MOVE RMAN BACKUP TO OSS IA TIER
            opc_ifr_param(opc_file_path)
    except Exception as e:
        message = "Failed to to run backup configuration for db {2}....!\n{0},{1}".format(sys.exc_info()[1:2], e,dbname)
        apscom.warn(message)


def silver_dr_validate(dbname,rman_user) :
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
        if not commonutils.is_node_exception_list():
            # fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1099
            if os.path.exists(silver_dr_file) or os.path.exists(backup_exception_file):
                cross_region_flag = 'y'
                if os.path.exists(silver_dr_file):
                    file_name = silver_dr_file
                else:
                    file_name = backup_exception_file
                with open(file_name, 'r') as f:
                    silver_dr_data = f.readlines()
                    # print("Silver DR Data is:- ", silver_dr_data)
                    for line in silver_dr_data:
                        cr_dbname, bucket_val = line.split(":")
                        if cr_dbname == dbname:
                            bucketname = bucket_val.split("~")
                            for item in bucketname:
                                #print("Bucket name is:-", item)
                                bucketname = item.strip()
                                if commonutils.bucket_validate(bucketname):
                                    if cr_dbname:
                                        if dbname == cr_dbname:
                                            database_config.cross_region_backup_silver_dr(cr_dbname, bucketname,rman_user, cross_region_flag)
                                            message="{0}{1} belong to {3} and DB backup will be taken as per silver DR configuration on bucket : {2}".format(globalvariables.GREEN,cr_dbname,bucketname,file_name)
                                            apscom.info(message)
                                            return True
                                    else:
                                        message = "{1} file format is not correct for {0}".format(cr_dbname,file_name)
                                        apscom.warn(message)
                                        return False
                                else:
                                    message = "Bucket {0} is not authorized for access".format(bucketname)
                                    apscom.warn(message)
                                    return False
                        else:
                            pass

                # return True
            else :
                return False
    except Exception as e:
        message = "Failed to do database configuration for {1} database {0}".format(dbname,file_name)
        apscom.warn(message)
        return False
        
def bkup_opc_install(dbname,oracle_home,force_flag):
    try:
        bucket_val=''
        fss_bucket_val=''
        realm = instance_metadata.ins_metadata().realmKey
        region = instance_metadata.ins_metadata().region
        env_type = commonutils.get_db_env_type(dbname)
        local_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.BACKUP_CFG_LOCATION,env_type)
        fss_sre_file="{0}/bkup_ocifsbackup_{1}.cfg".format(globalvariables.ARTIFACTS_BACKUP_PATH,env_type)
        faops_backup_oss_info_file = "{0}/config/faops-backup-oss-info.json".format(BASE_DIR)
        if os.path.exists(faops_backup_oss_info_file):
            with open(faops_backup_oss_info_file,'r') as f:
                faops_backup_oss_info = json.load(f)
        if os.path.exists(globalvariables.OCI_SDK_META_FILE):
            with open(globalvariables.OCI_SDK_META_FILE,'r') as f:
                oci_tenancy_info = json.load(f)
        for ns in faops_backup_oss_info:
            if ns == oci_tenancy_info["ns"]:
                if faops_backup_oss_info[ns]["tenancy"] == oci_tenancy_info["tenancy_name"]:
                    if  env_type == "em_exa" :
                        bucket_name = faops_backup_oss_info[ns]["em_rman_oss_bn"]
                    elif env_type == "dbaas":
                        bucket_name = faops_backup_oss_info[ns]["dbaas_rman_oss_bn"]
                    else:
                        bucket_name = faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]
        if os.path.exists(local_sre_file):
            with open(local_sre_file, "r") as fp:
                lines = fp.readlines()
                for line in lines:
                    if "bkup_oss_url" in line:
                        bkup_oss_url  = line.split("=")[1]
                        url = bkup_oss_url
                        #bucket_val = url.rsplit('/', 1)[-1]
                        bucket_val = os.path.basename(url)
                        bucket_val = bucket_val.strip()
        if os.path.exists(fss_sre_file):
            with open(fss_sre_file, "r") as fp:
                lines = fp.readlines()
                for line in lines:
                    if "bkup_oss_url" in line:
                        bkup_fss_oss_url  = line.split("=")[1]
                        fss_url = bkup_fss_oss_url
                        #bucket_val = url.rsplit('/', 1)[-1]
                        fss_bucket_val = os.path.basename(fss_url)
                        fss_bucket_val = fss_bucket_val.strip()
        if not os.path.exists(local_sre_file) or not os.path.exists(fss_sre_file) or bucket_name != bucket_val or bucket_name != fss_bucket_val:
            if os.path.exists(fss_sre_file) and bucket_name != fss_bucket_val:
                now = datetime.now()
                ts = now.strftime('%Y%m%d_%H%M%S')
                filename=fss_sre_file.split('/')[-1]
                bkp_fss_file= globalvariables.EXALOGS_PATH + "/" + filename + "_" + ts
                shutil.copy(fss_sre_file,bkp_fss_file)
                os.remove(fss_sre_file)
            gen_sre_db_config(dbname)
        else:    
            database_config.restore_backup_oss_passwd(fss_sre_file)
        #gen_sre_db_with_bucket(dbname,bucket_name)
        #gen_sre_db_config(dbname)
        if "uk-gov" in region:
            artifactory_url="{0}/artifactory/list/generic-fa/".format(globalvariables.ARTIFACTORY_URL_OC4)
        else:
            artifactory_url="{0}/artifactory/list/generic-fa/".format(globalvariables.ARTIFACTORY_URL_OC1)
        r = requests.get(artifactory_url)
        #print("The status code is :",r.status_code)
        if (r.status_code == 200):
            if realm not in ['oc1','oc4']:
                bkup_install(dbname,force_flag)
                #print("The realm key is :", realm)
                libfile_type='bkup'
                validate_sbt_test.validate_sbttest(dbname, oracle_home,libfile_type,force_flag)
            else:
                #print("The realm key is :", realm)
                opc_install(dbname,force_flag,bucket_name)
                libfile_type='opc'
                validate_sbt_test.validate_sbttest(dbname, oracle_home,libfile_type,force_flag)
        #commonutils.remove_backup_oss_passwd()
    except Exception:
        message = "{1}Failed to configure using BKUP or OPC install utility!\n{0}".format(sys.exc_info()[1:2], globalvariables.RED)
        apscom.warn(message)
        #sys.exit(1)

def parse_opts():
    try:
        parser = optparse.OptionParser(version="%prog 1.0")
        parser.add_option('--dbname',dest='dbname')
        parser.add_option('--dbsid',dest='dbsid')
        parser.add_option('--force_flag',dest='force_flag',default="")
       # parser.add_option('--bucket_name',dest='bucket_name')
       # parser.add_option('--sre_file_name',dest='sre_file_name')
        (opts, args) = parser.parse_args()
        if not opts.dbname or not opts.dbsid:
            parser.error(
                '--dbname option is required and --dbsid option is required')
        return (opts, args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.error(message)
        sys.exit(1)

if __name__ == "__main__":
    (options, args) = parse_opts()
    dbname = options.dbname
    dbsid = options.dbsid
    force_flag = options.force_flag
    #bucket_name = options.bucket_name
    region = instance_metadata.ins_metadata().region
    realm = instance_metadata.ins_metadata().realmKey
    #print("The db name is ", dbname)
    #print("The bucket_name is", bucket_name)
    gen_sre_db_config(dbname)
    oracle_home=commonutils.get_oracle_home(dbsid)
    #print("The sre_db_config_file is", sre_file_name)
    #print("The sre_db_config_file location is", sre_file)
    bkup_opc_install(dbname,oracle_home,force_flag)
