#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      validate_sbt_test.py
    DESCRIPTION
      Validates SBT_TAPE checks
    NOTES

    MODIFIED            (MM/DD/YY)  -   comments 
    Saritha Gireddy     14/05/20    -   initial version
    Zakki Ahmed         27/07/21    -   FY22Q1
"""
import getpass
import json
import os
import sys
import shutil
import optparse
import requests


BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import apscom,commonutils,globalvariables
from db import database_config_bkup_opc_install
from datetime import datetime
import random
def validate_swiftobj_pass(user,passwd,bkup_oss_url):
    try:
        # url = "https://swiftobjectstorage.us-phoenix-1.oraclecloud.com/v1/p1-saasfapreprod1/RMAN_BACKUP"
        if not bkup_oss_url:
            for file in globalvariables.BACKUP_CFG_FILES:
                with open(globalvariables.DB_CONFIG_PATH+file, "r") as fp:
                    lines = fp.readlines()
                    for line in lines:
                        if "bkup_oss_url" in line:
                            bkup_oss_url  = line.split("=")[1]
                            url = bkup_oss_url
        #file_path = "/tmp/backup/test1.txt"
                            file_name = "/tmp/test{0}.txt".format(random.random())
                            with open(file_name,"w") as f:
                                f.write("this is test file")
                            file_url = "{0}/{1}".format(url, file_name)
                            res = requests.put(url=file_url, auth=(user, passwd), data=open(file_name, 'rb'))
        # print(res, res.text, '{0} uploded'.format(file_name))
                            out = requests.get(file_url, auth=(user, passwd))
        # print(out, out.text)
                            if out.text=="this is test file":
                                apscom.info("Successfully validated swiftobj password")
                            try:
                                os.remove(file_name)
                            except Exception as e:
                                pass
                            res = requests.delete(file_url, auth=(user, passwd))
        # print(res,'{0} deleted'.format(file_name))
    except Exception as e:
        message = "Failed to validate swiftobject password for {0}".format(user)
        apscom.warn(message)
        raise Exception(message)
# Bug 32151886 - CLODUOPSTT:oci: SAASFAPREPROD1-STG:DB BACKUP RPM : EXATRA CHECKS TO AVAOID LIB MEDIA MANAGEMENT ERRORS
def verify_copy_file(source_file,dest_file):
    try:
        if os.path.exists(dest_file):
            with open(dest_file, "r") as fp:
                lines = fp.readlines()
                data=[line for line in lines if "swiftobjectstorage"in line]
                if not data:
                    shutil.copy(source_file, dest_file)
                    # fix perm for shared location
                    shutil.chown(dest_file,
                        "oracle", "oinstall")
        else:
            shutil.copy(source_file,dest_file)
            # fix perm for shared location
            shutil.chown(dest_file,
                "oracle", "oinstall")
    except Exception as e:
        message = "Failed to copy file from {0} to {1},{2}!".format(source_file,dest_file,sys.exc_info()[1:2])
        apscom.warn(message)

def validate_sbttest(dbname,oracle_home,libfile_type,force_flag):
    stderr = ""
    try:
        username = getpass.getuser()
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")

        if (libfile_type == 'opc'):
            file_opc = "{0}/oci_backup/{1}/lib/libopc.so".format(globalvariables.FA_RMAN_ORA_PATH,dbname)
            file_ora = "{0}/oci_backup/{1}/opc{1}.ora".format(globalvariables.FA_RMAN_ORA_PATH,dbname)
        elif (libfile_type == 'bkup'):
            file_opc = "{0}/{1}/opc/libopc.so".format(globalvariables.FA_RMAN_ORA_PATH,dbname)
            file_ora = "{0}/{1}/opc/opc{1}.ora".format(globalvariables.FA_RMAN_ORA_PATH,dbname)

        if username == 'oracle':
            cmd = "{1}/bin/sbttest some_file.f -libname {2}".format(dbname, oracle_home,file_opc)
        else:
            # cmd = "su oracle -c 'source {0}/{1}.env;{2}/bin/sbttest some_file.f -libname /var/opt/oracle/dbaas_acfs/{1}/opc/libopc.so'".format("/home/oracle", dbname, oracle_home)
            cmd = "su oracle -c 'source {0}/utils/db/scripts/shell/set_ora_env.sh {1};{2}/bin/sbttest some_file.f -libname {3}'".format(BASE_DIR, dbname, oracle_home,file_opc)
        [sbttest,returncode,stderr]=commonutils.execute_shell(cmd)
        if "sbtinit succeeded" in sbttest and returncode==1:
            message = "Library media management files available"
            apscom.info(message)
        else:
            if username == 'oracle':
                message = 'Backup configuration should be run as root, run as root user following command "source {0}/setpyenv.sh; python {1}/lib/python/db/database_config.py ";  '.format(globalvariables.SETPY_PATH,globalvariables.BASE_DIR)
                apscom.warn(message)
                # raise Exception(message)
            else:
                #lib_file="{1}/{0}/lib/libopc.so".format(dbname,globalvariables.OPC_LIB_PATH)
                lib_file=file_opc
                if os.path.exists(lib_file):
                    os.remove(lib_file)
                
                bkup_log_path = log_file_path + "backup-cfg_{0}_{1}.log".format(dbname,datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
                # os.chmod(globalvariables.BACKUP_CFG_LOCATION+'/bkup_ocifsbackup_sre.cfg', 0o600)
                # message = "Changed file permissions for bkup_ocifsbackup_sre.cfg file"
                # apscom.info(message)
                # shutil.chown(globalvariables.BACKUP_CFG_LOCATION + '/bkup_ocifsbackup_sre.cfg',"root", "root")
                # shutil.chown(
                #     globalvariables.BACKUP_CFG_LOCATION + '/bkup_ocifsbackup_sre.cfg',
                #     "root", "root")
                message = "Running one time config against database {0}".format(dbname)
                apscom.info(message)
                db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
                if (libfile_type == 'opc'):
                    database_config_bkup_opc_install.opc_install(dbname,force_flag)
                elif (libfile_type == 'bkup'):
                    database_config_bkup_opc_install.bkup_install(dbname,force_flag)
                # bkup_str = '{0}/bkup -cfg {1}/bkup_ocifsbackup_sre.cfg  -dbname="{2}" | tee -a {3}'.format(globalvariables.BACKUP_CFG_CMD_LOCATION, globalvariables.BACKUP_CFG_LOCATION,db_uniq_name, bkup_log_path)
                # commonutils.execute_shell(bkup_str)
                message = "Successfully ran backup configuration for db {0}".format(dbname)
                if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_prod.cfg"):
                    shutil.copy(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_prod.cfg",globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_prod.cfg")
                    verify_copy_file(globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_prod.cfg",globalvariables.ARTIFACTS_BACKUP_PATH + "/bkup_ocifsbackup_prod.cfg")
                if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_stage.cfg"):
                    shutil.copy(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_stage.cfg",globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_stage.cfg")
                    verify_copy_file(globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_stage.cfg",globalvariables.ARTIFACTS_BACKUP_PATH + "/bkup_ocifsbackup_stage.cfg")

                #Bug 32314904 - CLODUOPSTT:OCI: SAASFAPREPROD1-STG:DB BACKUP RPM : 2.0.0.0.201002.1-9 : BACKUP CONFIG NOT DONE FOR ALL CDBS
                #shutil.copy(globalvariables.BACKUP_CFG_LOCATION+"/bkup_ocifsbackup_sre.cfg",globalvariables.BACKUP_CFG_LOCATION+"/sre_db.cfg")
                # shutil.copy(globalvariables.BACKUP_CFG_LOCATION + "/sre_db.cfg",
                #             globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_sre.cfg")
                # verify_copy_file(globalvariables.BACKUP_CFG_LOCATION+"/bkup_ocifsbackup_sre.cfg",globalvariables.ARTIFACTS_BACKUP_PATH+"/bkup_ocifsbackup_sre.cfg")
                #    # shutil.copy(globalvariables.BACKUP_CFG_LOCATION+"/bkup_ocifsbackup_sre.cfg",globalvariables.ARTIFACTS_BACKUP_PATH+"/bkup_ocifsbackup_sre.cfg")
                    # fix perm for shared location
                apscom.info(message)
        #Bug 32288114 - CLODUOPSTT:OCI: SAASFAPREPROD1-STG:DB BACKUP RPM : CHANGES NEEDED TO SUPPORT RMAN_USER SWIFT USER PASSWORD RIVISION
        DB_SHELL_SCRIPT_PATH=BASE_DIR+"/utils/db/scripts/shell"
        if username == 'oracle':
            cmd1 = "{0}/check_swiftobj_oss.sh {1} {2}".format(DB_SHELL_SCRIPT_PATH, dbname,globalvariables.DB_BACKUP_LOG_PATH)
        else:
            cmd1 = "su oracle -c '{0}/check_swiftobj_oss.sh {1} {2}'".format(DB_SHELL_SCRIPT_PATH,dbname,globalvariables.DB_BACKUP_LOG_PATH )
        [check_oss_out,returncode,stderr]=commonutils.execute_shell(cmd1)
        if "KBHS-" in check_oss_out:
            # database_config.exec_db_config(dbname,'bkup_ocifsbackup_sre.cfg')
            execute_db_config(dbname,log_file_path)
    except Exception as e:
        message = "Failed to validate sbttest for {0},{1}!\n{2}".format(dbname,e,stderr)
        apscom.warn(message)
        raise
def nonfa_dbaas_validate_sbt(dbname):
    stderr=''
    try:
        username = getpass.getuser()
        crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
        with open(crsctl_json) as json_file:
            json_data = json.load(json_file)
        for key in json_data:
            unique_db_name = json_data[key]['db_unique_name']
            if unique_db_name == dbname:
                dbname=key
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
        # Bug 32288114 - CLODUOPSTT:OCI: SAASFAPREPROD1-STG:DB BACKUP RPM : CHANGES NEEDED TO SUPPORT RMAN_USER SWIFT USER PASSWORD RIVISION
        DB_SHELL_SCRIPT_PATH = BASE_DIR + "/utils/db/scripts/shell"
        if username == 'oracle':
            cmd1 = "{0}/check_swiftobj_oss.sh {1} {2}".format(DB_SHELL_SCRIPT_PATH, dbname, globalvariables.DB_BACKUP_LOG_PATH)
        else:
            cmd1 = "su oracle -c '{0}/check_swiftobj_oss.sh {1} {2}'".format(DB_SHELL_SCRIPT_PATH, dbname,globalvariables.DB_BACKUP_LOG_PATH)
        [check_oss_out, returncode, stderr] = commonutils.execute_shell(cmd1)
        if "KBHS-" in check_oss_out:
            #execute_db_config(dbname, log_file_path)
            #database_config_bkup_opc_install.bkup_install(dbname,force_flag=None)
            dbsid = commonutils.get_oracle_dbsid(dbname)
            oracle_home = commonutils.get_oracle_home(dbsid,dbname)
            database_config_bkup_opc_install.bkup_opc_install(dbname,oracle_home,None)
            # database_config.exec_db_config(dbname,'bkup_ocifsbackup_sre.cfg')
        else:
            msg="Validate sbt successfull for {0}".format(dbname)
            apscom.info(msg)
    except Exception as e:
        message = "Failed to validate sbttest for {0},{1}!\n{2}".format(dbname, e, stderr)
        apscom.warn(message)
        raise

# remove this after all successful tests
def execute_db_config(dbname,log_file_path):
    try:
        username = getpass.getuser()
        if username == 'oracle':
            message = 'Backup configuration should be run as root, run as root user following command "source {0}/setpyenv.sh; python {1}/lib/python/db/database_config.py ";  '.format(
                globalvariables.SETPY_PATH, globalvariables.BASE_DIR)
            raise Exception(message)
        else:
            bkup_log_path = log_file_path + "backup-cfg_{0}_{1}.log".format(dbname,
                                                                            datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
            # os.chmod(globalvariables.BACKUP_CFG_LOCATION + '/bkup_ocifsbackup_sre.cfg', 0o600)
            # message = "Changed file permissions for bkup_ocifsbackup_sre.cfg file"
            # apscom.info(message)
            # shutil.chown(globalvariables.BACKUP_CFG_LOCATION + '/bkup_ocifsbackup_sre.cfg', "root", "root")
            # shutil.chown(
            #     globalvariables.BACKUP_CFG_LOCATION + '/bkup_ocifsbackup_sre.cfg',
            #     "root", "root")
            # message = "Running one time config against database {0}".format(dbname)
            # apscom.info(message)
            # db_uniq_name = commonutils.get_crsctl_data(dbname,'db_unique_name')
            # bkup_str = '{0}/bkup -cfg {1}/bkup_ocifsbackup_sre.cfg  -dbname="{2}" | tee -a {3}'. \
            #     format(globalvariables.BACKUP_CFG_CMD_LOCATION, globalvariables.BACKUP_CFG_LOCATION, db_uniq_name,bkup_log_path)
            # [res, ret_code, stderr]=commonutils.execute_shell(bkup_str)
            # if (res and 'ERROR' in res) or (stderr and 'ERROR' in stderr):
            #     message = "Failed to run backup configuration for db {0} ..{1}".format(dbname,stderr)
            #     apscom.warn(message)
            #     # raise
            # else:
            message = "Successfully ran backup configuration for db {0}".format(dbname)
                # Bug 32314904 - CLODUOPSTT:OCI: SAASFAPREPROD1-STG:DB BACKUP RPM : 2.0.0.0.201002.1-9 : BACKUP CONFIG NOT DONE FOR ALL CDBS
                # shutil.copy(globalvariables.BACKUP_CFG_LOCATION+"/bkup_ocifsbackup_sre.cfg",globalvariables.BACKUP_CFG_LOCATION+"/sre_db.cfg")
            if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_prod.cfg"):
                shutil.copy(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_prod.cfg",globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_prod.cfg")
                verify_copy_file(globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_prod.cfg",globalvariables.ARTIFACTS_BACKUP_PATH + "/bkup_ocifsbackup_prod.cfg")
            if os.path.exists(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_stage.cfg"):
                shutil.copy(globalvariables.BACKUP_CFG_LOCATION + "/sre_db_stage.cfg",globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_stage.cfg")
                verify_copy_file(globalvariables.BACKUP_CFG_LOCATION + "/bkup_ocifsbackup_stage.cfg",globalvariables.ARTIFACTS_BACKUP_PATH + "/bkup_ocifsbackup_stage.cfg")
            apscom.info(message)
    except Exception as e:
        message = "Failed to execute config {0},{1}!\n{2}".format(dbname, sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

def parse_opts():
    try:
        parser = optparse.OptionParser(version="%prog 1.0")
        parser.add_option('--user',dest='user')
        parser.add_option('--password',dest='password')
        parser.add_option('--ossurl',dest='ossurl')
        (opts, args) = parser.parse_args()
        return (opts, args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.error(message)
        sys.exit(1)

if __name__ == "__main__":
    (options, args) = parse_opts()
    user = options.user
    password = options.password
    ossurl=options.ossurl
    validate_swiftobj_pass(user,password,ossurl)