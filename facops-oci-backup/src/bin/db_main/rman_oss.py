#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      rman_oss.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       08/12/20 - initial version (code refactoring)
    Zakki Ahmed           25/02/21 - support for compressed backups
    Zakki Ahmed           03/10/21 - Bug 33398032,33423812,Bug 33870260
    Jayant Mahishi        04/26/22 - SOEDEVSECOPS-1619
    Vipin Azad            09/28/22  - Enh 33624729 - PLEASE ENABLE RESUMABLE OPTION WITH RMAN BACKUPS - FY22Q3
"""
#### imports start here ##############################

import traceback
import glob
import getpass
import os
import shutil
import sys
import json
import subprocess
import time
import optparse
from datetime import datetime
from time import strftime, gmtime
BASE_DIR = os.path.abspath(__file__ + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import globalvariables, commonutils, apscom, post_backup_metadata,instance_metadata
from db import validate_sbt_test, db_rman_file_gen,resume_backup
env_type = ""
#### imports end here ##############################
timestamp = strftime("%m%d%Y%H%M%S", gmtime())
start_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
BACKUP_METADATA_PATH = globalvariables.DB_CONFIG_PATH + \
    "backup-metadata_{0}.json".format(globalvariables.LOCAL_HOST)

LOG_LOCATION = "/u02/backup/log/{0}".format(globalvariables.HOST_NAME)

try:
    if not os.path.exists(LOG_LOCATION):
        os.makedirs(LOG_LOCATION)
except Exception as e:
    message = "Failed to create backup directories!\n{0}{1}".format(sys.exc_info()[
                                                                    1:2], e)
    apscom.error(message)


def run_rman_cmd(script_str, log_path,):
    stderr = ""
    try:
        #script_loc = "{0}/{1} '{2}' '{3}' {4} \\\"{4}/archivelog\\\" {5}".format(globalvariables.RMAN_SCRIPTS, arc_rman_script, libopc_path,rman_ora_path,dbname,ret_days)
        rman_str = 'rman  nocatalog target / cmdfile=\"{0}\" log="{1}"'.format(
            script_str, log_path)
        # rmanCMD = "{2} > /dev/null ".\
        rmanCMD = "{2} ". \
            format(globalvariables.ORACLE_USER_HOME, dbname, rman_str)
        message = "Executing rman_command {0} in {1} ...".format(
            script_str, log_path)
        apscom.info(message)
        message = "{1}Running rman command: \n {0}".format(
            rmanCMD, globalvariables.GREEN)
        current_time = time.time()
        apscom.info(message)
        [output, ret_code, stderr] = commonutils.execute_shell(rmanCMD)
        end_time = time.time()
        final_time = round(end_time - current_time, 2)
        message = "{1}Time taken for completion of RMAN command is {0} seconds".format(
            final_time, globalvariables.GREEN)
        apscom.info(message)
        if ret_code == 0:
            message = "{2}RMAN executed successfully ...".format(
                script_str, log_path, globalvariables.GREEN)
            apscom.info(message)
        else:
            message = "{2}RMAN command did not execute successfully ...".format(
                script_str, log_path, globalvariables.AMBER)
            apscom.info(message)
            raise
    except subprocess.CalledProcessError as e:
        # traceback.print_exc()
        message = "Failed to do run rman command backup!\n{0}{1}".format(
            stderr, e.output)
        apscom.warn(message)
        raise

def run_rman_cmd_no_raise(script_str, log_path):
    stderr = ""
    try:
        #script_loc = "{0}/{1} '{2}' '{3}' {4} \\\"{4}/archivelog\\\" {5}".format(globalvariables.RMAN_SCRIPTS, arc_rman_script, libopc_path,rman_ora_path,dbname,ret_days)
        rman_str = 'rman  nocatalog target / cmdfile=\"{0}\" log="{1}"'.format(
            script_str, log_path)
        # rmanCMD = "{2} > /dev/null ".\
        rmanCMD = "{2} ". \
            format(globalvariables.ORACLE_USER_HOME, dbname, rman_str)
        message = "Executing rman_command {0} in {1} ...".format(
            script_str, log_path)
        apscom.info(message)
        message = "{1}Running rman command: \n {0}".format(
            rmanCMD, globalvariables.GREEN)
        current_time = time.time()
        apscom.info(message)
        [output, ret_code, stderr] = commonutils.execute_shell(rmanCMD)
        end_time = time.time()
        final_time = round(end_time - current_time, 2)
        message = "{1}Time taken for completion of RMAN command is {0} seconds".format(
            final_time, globalvariables.GREEN)
        apscom.info(message)
        if ret_code == 0:
            message = "{2}RMAN executed successfully ...".format(
                script_str, log_path, globalvariables.GREEN)
            apscom.info(message)
            return True
        else:
            message = "{2}RMAN command did not execute successfully ...".format(
                script_str, log_path, globalvariables.AMBER)
            apscom.warn(message)
            return False
    except subprocess.CalledProcessError as e:
        # traceback.print_exc()
        message = "Failed to do run rman command backup!\n{0}{1}".format(
            stderr, e.output)
        apscom.warn(message)
        return False
        
def run_rman_cmd_block(script_str, log_path,):
    stderr = ""
    try:
        #script_loc = "{0}/{1} '{2}' '{3}' {4} \\\"{4}/archivelog\\\" {5}".format(globalvariables.RMAN_SCRIPTS, arc_rman_script, libopc_path,rman_ora_path,dbname,ret_days)
        # rman_str = 'rman  nocatalog target / cmdfile=\"{0}\" log="{1}"'.format(script_str, log_path)
        rman_str = 'cat "{0}" | rman nocatalog target /  log="{1}"'.format(
            script_str, log_path)
        # rmanCMD = "{2} > /dev/null ".\
        rmanCMD = "{2} ". \
            format(globalvariables.ORACLE_USER_HOME, dbname, rman_str)
        # print(rmanCMD, 'rmanCMD')
        message = "Executing rman_command {0} in {1} ...".format(
            script_str, log_path)
        apscom.info(message)
        message = "{1}Running rman command: \n {0}".format(
            rmanCMD, globalvariables.GREEN)
        current_time = time.time()
        apscom.info(message)
        [output, ret_code, stderr] = commonutils.execute_shell(rmanCMD)
        end_time = time.time()
        final_time = round(end_time - current_time, 2)
        message = "{1}Time taken for completion of RMAN command is {0} seconds".format(
            final_time, globalvariables.GREEN)
        apscom.info(message)
        if ret_code == 0:
            message = "{2}RMAN executed successfully ...".format(
                script_str, log_path, globalvariables.GREEN)
            if (os.path.exists(script_str)):
                try:
                    os.remove(script_str)
                    message = "{1}removed rman file : {0}".format(
                        script_str, globalvariables.GREEN)
                    apscom.info(message)
                except OSError as e:  # if failed, report it back to the user ##
                    message = "Error: %s - %s." % (e.filename, e.strerror)
                    message = "{1}unable to remove rman file :  \n {0}".format(
                        script_str, globalvariables.AMBER)
                    apscom.warn(message)
                    pass

            apscom.info(message)
        else:
            message = "{2}RMAN command did not execute successfully ...".format(
                script_str, log_path, globalvariables.AMBER)
            apscom.info(message)
            if (os.path.exists(script_str)):
                try:
                    os.remove(script_str)
                    message = "{1}removed rman file : {0}".format(
                        script_str, globalvariables.GREEN)
                    apscom.info(message)
                except OSError as e:  # if failed, report it back to the user ##
                    message = "Error: %s - %s." % (e.filename, e.strerror)
                    message = "{1}unable to remove rman file :  \n {0}".format(
                        script_str, globalvariables.AMBER)
                    apscom.warn(message)
                    pass
            raise
    except subprocess.CalledProcessError as e:
        # traceback.print_exc()
        message = "Failed to do run rman command backup!\n{0}{1}".format(
            stderr, e.output)
        apscom.warn(message)
        #
        if (os.path.exists(script_str)):
            try:
                os.remove(script_str)
                message = "{1}removed rman file :  \n {0}".format(
                    script_str, globalvariables.GREEN)
                apscom.info(message)
            except OSError as e:  # if failed, report it back to the user ##
                message = "Error: %s - %s." % (e.filename, e.strerror)
                message = "{1}unable to remove rman file :  \n {0}".format(
                    script_str, globalvariables.AMBER)
                apscom.warn(message)
                pass
        raise

def obsolete_runblock_split(file_path):
    try:
        run_block_reco=""
        run_block_full=""
        run_block_arch=""
        run_block_reco_path=""
        run_block_full_path=""
        run_block_arch_path=""

        with open(file_path) as b:
            block=b.readlines()
        count = 1
        for line in block:
            if count == 1:
                run_block_reco=run_block_reco + line
            elif count == 2:
                run_block_full = run_block_full + line
            elif count == 3 or count == 4:
                run_block_arch = run_block_arch + line
            
            if "}" in line:
                count += 1

        fd, run_block_reco_path = db_rman_file_gen.mkstemp()
        with open(run_block_reco_path, 'w') as f:
            f.writelines(run_block_reco)
        os.close(fd)

        fd, run_block_full_path = db_rman_file_gen.mkstemp()
        with open(run_block_full_path, 'w') as f:
            f.writelines(run_block_full)
        os.close(fd)

        fd, run_block_arch_path = db_rman_file_gen.mkstemp()
        with open(run_block_arch_path, 'w') as f:
            f.writelines(run_block_arch)
        os.close(fd)
        return run_block_reco_path,run_block_full_path,run_block_arch_path
    except Exception as e:
        message = "Failed to do split runblock for obsolete !\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        return run_block_reco_path,run_block_full_path,run_block_arch_path

def obsolete_backupset_withoss(node_count=0, user_channels=0, tag=None, ret_days=0):
    try:
        # type="rman_obsolete_backupset"
        type = "obsolete_backupset_withoss"
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        # logfile = logfile_location + globalvariables.HOST_NAME + \
        #     "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        # gen_json(logfile, "pre", type, "START")
        db_size = query_output["DB_SIZE_GB"]
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["obsolete_backupset_withoss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["obsolete_backupset_withoss"][env_type]["retention"]

        if user_channels == 0:
            if db_size >= 5120:
                channels = 12
            else:
                channels = 8
        else:
            channels = user_channels
        #########
        # implement rman script
        # script_loc = "{0}/obsolete_backupset_withoss.rman '{1}' '{2}' \\\"{3}/backupset\\\"".format(globalvariables.RMAN_SCRIPTS, libopc_path,rman_ora_path, dbname)
        # run_rman_cmd(script_loc,logfile)
        ####
        # new
        backup_type = type
        cdbflag = "no"
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        run_block_reco,run_block_full,run_block_arch=obsolete_runblock_split(rman_file)
        print(run_block_reco,run_block_full,run_block_arch)

        #locak disk cleanup run block run 
        if run_block_reco:
            type="disk_cleanup"
            logfile = logfile_location + globalvariables.HOST_NAME + \
                "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
            gen_json(logfile, "pre", type, "START")
            response_disk = run_rman_cmd_no_raise(run_block_reco,logfile)
            if response_disk:
                gen_json(logfile, "post", type, "SUCCESS")
            else:
                gen_json(logfile, "post", type, "FAILED")
        else:
            message="could not run dick_cleanup in obsolete_backupset_withoss as run_block_reco got empty"
            apscom.warn(message)

        #OSS L0 Full backup cleanup run
        if run_block_full:
            type="full_oss_cleanup"
            logfile = logfile_location + globalvariables.HOST_NAME + \
                "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
            gen_json(logfile, "pre", type, "START")
            response_full = run_rman_cmd_no_raise(run_block_full, logfile)
            if response_full:
                gen_json(logfile, "post", type, "SUCCESS")
            else:
                gen_json(logfile, "post", type, "FAILED")
        else:
            message="could not run full_oss_cleanup in obsolete_backupset_withoss as run_block_full got empty"
            apscom.warn(message)

        #OSS Archive log backup cleanup run 
        if run_block_arch:
            type="archive_oss_cleanup"
            logfile = logfile_location + globalvariables.HOST_NAME + \
                "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
            gen_json(logfile, "pre", type, "START")
            response_arch = run_rman_cmd_no_raise(run_block_arch, logfile)
            if response_arch:
                gen_json(logfile, "post", type, "SUCCESS")
            else:
                gen_json(logfile, "post", type, "FAILED")
        else:
            message="could not run archive_oss_cleanup in obsolete_backupset_withoss as run_block_arch got empty"
            apscom.warn(message)

        message = "Succeeds to backup obsolete_backupset_withoss of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do obsolete_backupset_withoss !\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        if logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                logfile, globalvariables.RED)
            with open(logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(logfile, "post", backup_type, "FAILED")
        else:
            gen_json(logfile, "post", backup_type, "FAILED")
        sys.exit(1)

def database_compressed_to_oss(node_count, user_channels, backup_type, tag=None, ret_days=0, backup_restore_time=None, resume_flag=None):
    # read ldb allow remote channels flag
    ldb_flag_file = "{0}/ldb_flag.txt".format(globalvariables.DB_CONFIG_PATH)
    ldb_flag_data = []
    ldb_flag_dict = {}
    allow_remote_channels = ""
    channels_per_node = 0

    if backup_type == "db_to_reco_db_arch_to_oss":
        backup_type = "database_compressed_to_oss"
    # backup_type="database_compressed_to_oss"
    if backup_type == "ldb_db_to_oss":
        backup_type = "ldb_database_compressed_to_oss"
    if backup_type == "db_to_oss":
        backup_type = "database_compressed_to_oss"

    # backup_type="database_compressed_to_oss"
    #  read ldb_flag.txt

    if os.path.exists(ldb_flag_file):
        with open(ldb_flag_file, 'r') as f:
            ldb_flag_data = f.read().splitlines()

        for line in ldb_flag_data:
            if not line.startswith("#") and line != "":
                try:
                    key, val = line.split("=")
                    ldb_flag_dict[key.strip()] = val.strip()
                except Exception as e:
                    message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                        globalvariables.AMBER, ldb_flag_file)
                    apscom.warn(message)
                    backup_type = "database_compressed_to_oss"
                    pass
        # checking remote backup condition
        if ldb_flag_dict["allow_backup_remote_channels".lower()] == "false":
            backup_type = "database_compressed_to_oss"
        elif ldb_flag_dict["allow_backup_remote_channels".lower()] == "true":
            # backup_type="ldb_database_compressed_to_oss"
            # check databases
            ldb_databases = ldb_flag_dict["databases"]
            ldb_dbs = []
            if ldb_databases != "":
                if "," in ldb_databases:
                    ldb_dbs = ldb_databases.split(",")
                else:
                    ldb_dbs.append(ldb_databases)
            #
                for ldb in ldb_dbs:
                    if ldb == dbname:
                        backup_type = "ldb_database_compressed_to_oss"
                        try:
                            if ldb_flag_dict["nodes"] != "" and ldb_flag_dict["nodes"].isdigit():
                                config_node_count = int(ldb_flag_dict["nodes"])
                                node_count = config_node_count
                        except Exception as e:
                            message = "nodes is not set to number, running on all nodes of this database - {0}".format(
                                dbname)
                            apscom.warn(message)
                            pass
                        # check channels
                        try:
                            if ldb_flag_dict["channels"].isdigit():
                                channels_per_node = int(
                                    ldb_flag_dict["channels"])
                                user_channels = channels_per_node
                        except Exception as e:
                            message = "channels is not set to number, using default 4 channels per node"
                            apscom.warn(message)
                            pass
                        #
                        break
            else:
                backup_type = "database_compressed_to_oss"
        else:
            message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                globalvariables.AMBER, ldb_flag_file)
            apscom.warn(message)
            backup_type = "database_compressed_to_oss"
    #

    rman_logfile = ''
    try:
        type = backup_type
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"

        initialize_configuration(
            node_count, channels_per_node, tag=None, ret_days=0)

        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        rman_logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        gen_json(rman_logfile, "pre", type, "START",resume_flag)
        #########
        # implement rman script
        # for Large dbs if >5TB use 12 channels
        db_size = query_output["DB_SIZE_GB"]
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["db_to_oss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["db_to_oss"][env_type]["retention"]

        if user_channels == 0:
            if channels_per_node != 0:
                channels = channels_per_node
            else:
                if db_size >= 5120:
                    channels = 12
                else:
                    channels = 8
        else:
            channels = user_channels
        #

        #
        # old
        # run_rman_cmd(script_loc,rman_logfile)

        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days, backup_restore_time, resume_flag)
        #
        if backup_type == "ldb_database_compressed_to_oss":
            run_rman_cmd_block(rman_file, rman_logfile)
        else:
            run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS",resume_flag)

        message = "Succeeds to backup database_compressed_to_oss of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do verify oss destination!\n{0}{1}".format(sys.exc_info()[
                                                                        1:2], e)
        apscom.info(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED",resume_flag)
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED",resume_flag)
        sys.exit(1)


def archivelog_to_oss(node_count, user_channels, tag=None, ret_days=0):
    rman_logfile = ''
    try:
        # Bug 33398032

        active_rman = rman_status
        if active_rman > 0:
            arc_rman_script_ext = ".rman_cf_ab_on"
            cdbflag = "yes"
        else:
            arc_rman_script_ext = ".rman"
            cdbflag = "no"

        db_size = query_output["DB_SIZE_GB"]

        if user_channels == 0:
            if db_size >= 5120:
                arc_rman_script = backup_type + '_8' + arc_rman_script_ext
                channels = 8
            else:
                arc_rman_script = backup_type + '_4' + arc_rman_script_ext
                channels = 4
        else:
            channels = user_channels

        initialize_configuration(tag, ret_days)
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+backup_type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", backup_type, "START")
        # implement rman script
        # nonfa_dbaas rman execution
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["archivelog_to_oss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["archivelog_to_oss"][env_type]["retention"]

        # old
#         script_loc = "{0}/{1} '{2}' '{3}' {4} \\\"{4}/archivelog\\\" {5}".format(globalvariables.RMAN_SCRIPTS, arc_rman_script, libopc_path,rman_ora_path,dbname,ret_days)
#         run_rman_cmd(script_loc,rman_logfile)

        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, 'archivelog_to_oss', nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        run_rman_cmd(rman_file, rman_logfile)
        ####

        gen_json(rman_logfile, "post", backup_type, "SUCCESS")
        commonutils.update_db_archive_file(dbname)
        message = "Succeeds to backup archivelog_to_oss of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do archivelog_to_oss backup!\n{0}{1}".format(sys.exc_info()[
                                                                          1:2], e)
        apscom.info(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
            commonutils.update_db_archive_file(dbname)
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")
            commonutils.update_db_archive_file(dbname)
        sys.exit(1)


def database_to_reco(node_count, user_channels, backup_type, tag=None, ret_days=0):
    #
    # read ldb allow remote channels flag
    ldb_flag_file = "{0}/ldb_flag.txt".format(globalvariables.DB_CONFIG_PATH)
    ldb_flag_data = []
    ldb_flag_dict = {}
    allow_remote_channels = ""
    channels_per_node = 0

    if backup_type == "db_to_reco_db_arch_to_oss":
        backup_type = "database_to_reco"
    if backup_type == "db_to_reco":
        backup_type = "database_to_reco"
    if backup_type == "ldb_db_to_reco":
        backup_type = "ldb_database_to_reco"

    else:
        #  read ldb_flag.txt
        if os.path.exists(ldb_flag_file):
            with open(ldb_flag_file, 'r') as f:
                ldb_flag_data = f.read().splitlines()

            for line in ldb_flag_data:
                if not line.startswith("#") and line != "":
                    try:
                        key, val = line.split("=")
                        ldb_flag_dict[key.strip()] = val.strip()
                    except Exception as e:
                        message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                            globalvariables.AMBER, ldb_flag_file)
                        apscom.warn(message)
                        backup_type = "database_to_reco"
                        pass
            # checking remote backup condition
            if ldb_flag_dict["allow_backup_remote_channels".lower()] == "false":
                backup_type = "database_to_reco"
            elif ldb_flag_dict["allow_backup_remote_channels".lower()] == "true":
                # backup_type="ldb_database_compressed_to_oss"
                # check databases
                ldb_databases = ldb_flag_dict["databases"]
                ldb_dbs = []
                if ldb_databases != "":
                    if "," in ldb_databases:
                        ldb_dbs = ldb_databases.split(",")
                    else:
                        ldb_dbs.append(ldb_databases)
                #
                    for ldb in ldb_dbs:
                        if ldb == dbname:
                            backup_type = "ldb_database_to_reco"
                            # check nodes
                            try:
                                if ldb_flag_dict["nodes"] != "" and ldb_flag_dict["nodes"].isdigit():
                                    config_node_count = int(
                                        ldb_flag_dict["nodes"])
                                    node_count = config_node_count
                            except Exception as e:
                                message = "nodes is not set to number, running on all nodes of this database - {0}".format(
                                    dbname)
                                apscom.warn(message)
                                pass
                            # check channels
                            try:
                                if ldb_flag_dict["channels"].isdigit():
                                    channels_per_node = int(
                                        ldb_flag_dict["channels"])
                                    user_channels = channels_per_node
                            except Exception as e:
                                message = "channels is not set to number, using default 4 channels per node"
                                apscom.warn(message)
                                pass
                            break

                else:
                    backup_type = "database_to_reco"
            else:
                message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                    globalvariables.AMBER, ldb_flag_file)
                apscom.warn(message)
                backup_type = "database_to_reco"
    #
    #
    rman_logfile = ''
    try:
        if tag is None:
            tag = globalvariables.backup_opts["database_to_reco"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["database_to_reco"][env_type]["retention"]

        initialize_reco_configuration(tag, ret_days)
        type = backup_type
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", type, "START")

        #########
        # implement rman script
        # for Large dbs if >5TB use 12 channels
        db_size = query_output["DB_SIZE_GB"]
        # if user_channels == 0:
        #     if db_size >= 5120:
        #         script_loc="{0}/database_to_reco_12.rman{1} {2}".format(globalvariables.RMAN_SCRIPTS,cdb_pdb_flag,tag)
        #         channels=12
        #     else:
        #         script_loc="{0}/database_to_reco.rman{1} {2}".format(globalvariables.RMAN_SCRIPTS,cdb_pdb_flag,tag)
        #         channels=8
        # else:
        #     channels = user_channels
        if user_channels == 0:
            if channels_per_node != 0:
                channels = channels_per_node
            else:
                if db_size >= 5120:
                    channels = 12
                else:
                    channels = 8
        else:
            channels = user_channels
        #
        # old
        # run_rman_cmd(script_loc,rman_logfile)

        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        #
        if backup_type == "ldb_database_to_reco":
            run_rman_cmd_block(rman_file, rman_logfile)
        else:
            run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to backup database_to_reco of {0} ...".format(
            dbname)
        apscom.info(message)

    except Exception as e:
        message = "Failed to do database_to_reco backup!\n{0}{1}".format(sys.exc_info()[
                                                                         1:2], e)
        apscom.warn(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")


def validate_db_reco(node_count, user_channels, tag=None, ret_days=0):
    rman_logfile = ''
    try:
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["db_to_reco"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["db_to_reco"][env_type]["retention"]

        initialize_reco_configuration(tag, ret_days)
        type = "validate_db_reco"
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", type, "START")

        #########
        # implement rman script
        # for Large dbs if >5TB use 12 channels
        db_size = query_output["DB_SIZE_GB"]
        if user_channels == 0:
            if db_size >= 5120:
                # script_loc="{0}/validate_database_to_reco_12.rman{1}".format(globalvariables.RMAN_SCRIPTS,cdb_pdb_flag)
                channels = 12
            else:
                # script_loc="{0}/validate_database_to_reco.rman{1}".format(globalvariables.RMAN_SCRIPTS,cdb_pdb_flag)
                channels = 8
        else:
            channels = user_channels
        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        # run_rman_cmd(script_loc,rman_logfile)
        run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to validate backup database_to_reco of {0} ...".format(
            dbname)
        apscom.info(message)

    except Exception as e:
        message = "Failed to validate database_to_reco backup!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")


def validate_db_oss(node_count, user_channels, tag=None, ret_days=0):
    rman_logfile = ''
    try:
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["db_to_oss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["db_to_oss"][env_type]["retention"]

        initialize_configuration(tag, ret_days)
        type = "validate_db_oss"
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", type, "START")

        #########
        # implement rman script
        # for Large dbs if >5TB use 12 channels
        db_size = query_output["DB_SIZE_GB"]
        if user_channels == 0:
            if db_size >= 5120:
                channels = 12
            else:
                channels = 8
        else:
            channels = user_channels

        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        # run_rman_cmd(script_loc,rman_logfile)
        run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to validate backup validate_db_oss of {0} ...".format(
            dbname)
        apscom.info(message)

    except Exception as e:
        message = "Failed to validate validate_db_oss !\n{0}{1}".format(sys.exc_info()[
                                                                        1:2], e)
        apscom.warn(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")


def restore_validate_oss(node_count, user_channels, backup_type, tag=None, ret_days=0):
    # read ldb allow remote channels flag
    ldb_flag_file = "{0}/ldb_flag.txt".format(globalvariables.DB_CONFIG_PATH)
    ldb_flag_data = []
    ldb_flag_dict = {}
    allow_remote_channels = ""
    channels_per_node = 0
    #
    if backup_type == "restore_validate":
        backup_type = "restore_validate_oss"
    # backup_type="restore_validate_oss"
    #
    if backup_type == "ldb_restore_validate_oss":
        backup_type = "ldb_restore_validate_oss"
    else:
        # backup_type="database_compressed_to_oss"
        #  read ldb_flag.txt

        if os.path.exists(ldb_flag_file):
            with open(ldb_flag_file, 'r') as f:
                ldb_flag_data = f.read().splitlines()

            for line in ldb_flag_data:
                if not line.startswith("#") and line != "":
                    try:
                        key, val = line.split("=")
                        ldb_flag_dict[key.strip()] = val.strip()
                    except Exception as e:
                        message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                            globalvariables.AMBER, ldb_flag_file)
                        apscom.warn(message)
                        backup_type = "restore_validate_oss"
                        pass
            # checking remote backup condition
            if ldb_flag_dict["allow_restore_validate_remote_channels".lower()] == "false":
                backup_type = "restore_validate_oss"
            elif ldb_flag_dict["allow_restore_validate_remote_channels".lower()] == "true":
                # backup_type="restore_validate_oss"
                # check databases
                ldb_databases = ldb_flag_dict["databases"]
                ldb_dbs = []
                if ldb_databases != "":
                    if "," in ldb_databases:
                        ldb_dbs = ldb_databases.split(",")
                    else:
                        ldb_dbs.append(ldb_databases)
                #
                    for ldb in ldb_dbs:
                        if ldb == dbname:
                            backup_type = "ldb_restore_validate_oss"

                            try:
                                if ldb_flag_dict["nodes"] != "" and ldb_flag_dict["nodes"].isdigit():
                                    config_node_count = int(
                                        ldb_flag_dict["nodes"])
                                    node_count = config_node_count
                            except Exception as e:
                                message = "nodes is not set to number, running on all nodes of this database - {0}".format(
                                    dbname)
                                apscom.warn(message)
                                pass
                            # check channels
                            try:
                                if ldb_flag_dict["channels"].isdigit():
                                    channels_per_node = int(
                                        ldb_flag_dict["channels"])
                                    user_channels = channels_per_node
                            except Exception as e:
                                message = "channels is not set to number, using default 4 channels per node"
                                apscom.warn(message)
                                pass
                            #
                            break
                else:
                    backup_type = "restore_validate_oss"
            else:
                message = "{1} file does not look to be in correct format, please fix the file, refer to {1}.template".format(
                    globalvariables.AMBER, ldb_flag_file)
                apscom.warn(message)
                backup_type = "restore_validate_oss"
        #
    #
    rman_logfile = ''
    try:
        type = backup_type
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"

        initialize_configuration(
            node_count, channels_per_node, tag=None, ret_days=0)

        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        rman_logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        gen_json(rman_logfile, "pre", type, "START")
        #########
        # implement rman script
        # for Large dbs if >5TB use 12 channels
        db_size = query_output["DB_SIZE_GB"]
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["db_to_reco_db_arch_to_oss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["db_to_reco_db_arch_to_oss"][env_type]["retention"]

        if user_channels == 0:
            if channels_per_node != 0:
                channels = channels_per_node
            else:
                if db_size >= 5120:
                    channels = 12
                else:
                    channels = 8
        else:
            channels = user_channels
        #

        #
        # old
        # run_rman_cmd(script_loc,rman_logfile)

        # new
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        #
        if backup_type == "ldb_restore_validate_oss":
            run_rman_cmd_block(rman_file, rman_logfile)
        else:
            run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to backup restore_validate_oss of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do verify oss destination!\n{0}{1}".format(sys.exc_info()[
                                                                        1:2], e)
        apscom.info(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")
        sys.exit(1)


def pdbseed_to_reco(node_count=0, user_channels=0, tag=None, ret_days=0):
    try:
        rman_reco, rman_data = get_asm_disk_group()
        type = "pdbseed_to_reco"
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        #
        gen_json(logfile, "pre", type, "START")
        db_size = query_output["DB_SIZE_GB"]
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["pdbseed_to_reco"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["pdbseed_to_reco"][env_type]["retention"]

        if user_channels == 0:
            if db_size >= 5120:
                channels = 12
            else:
                channels = 8
        else:
            channels = user_channels

        #########
        # implement rman script
        # old
        # script_loc="{0}/pdbseed_to_reco.rman {1}".format(globalvariables.RMAN_SCRIPTS,rman_reco)
        # run_rman_cmd(script_loc,logfile)
        #
        # new
        backup_type = type
        cdbflag = "no"
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        run_rman_cmd(rman_file, logfile)
        gen_json(logfile, "post", backup_type, "SUCCESS")
        ####
        current_time = time.time()
        message = "Succeeds to backup pdbseed_to_reco of {0} ...".format(
            dbname)
        end_time = time.time()
        final_time = round(end_time - current_time, 2)
        message = "{1}Time taken for completion of backup is {0} seconds".format(
            final_time, globalvariables.GREEN)
        apscom.info(message)
        apscom.info(message)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do pdbseed_to_reco !\n{0}{1}".format(sys.exc_info()[
                                                                  1:2], e)
        apscom.warn(message)
        if logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                logfile, globalvariables.RED)
            with open(logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(logfile, "post", backup_type, "FAILED")
        else:
            gen_json(logfile, "post", backup_type, "FAILED")
        sys.exit(1)


def incremental_to_reco(node_count, user_channels, tag=None, ret_days=0):
    rman_logfile = ''
    try:
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["incre_to_reco_arch_to_oss"][env_type]["tag"]
        if ret_days == 0:
            #ret_days = globalvariables.backup_opts["incre_to_reco_arch_to_oss"][env_type]["retention"]
            #FUSIONSRE-4633 - This will make sure the initial retention for disk back cleanups is set to value for incremental_to_reco
            ret_days = globalvariables.backup_opts["incremental_to_reco"][env_type]["retention"]

        #if "archived log backup" in rman_running_bkup:
        initialize_reco_configuration(tag, ret_days)
        type = "incremental_to_reco"
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", type, "START")
        #########
        # implement rman script
        # nonfa_dbaas rman execution
        # script_loc="{0}/incremental_to_reco.rman{1} {2}".format(globalvariables.RMAN_SCRIPTS,cdb_pdb_flag,tag)
        # run_rman_cmd(script_loc,rman_logfile)
        db_size = query_output["DB_SIZE_GB"]
        if user_channels == 0:
            if db_size >= 5120:
                channels = 12
            else:
                channels = 8
        else:
            channels = user_channels

        # new
        backup_type = type
        cdbflag = "no"
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to backup incremental_to_reco of {0} ...".format(
            dbname)
        apscom.info(message)
        # Bug 33410790
        # elif "full" in rman_running_bkup and rman_running > 0 :
        #     message = "Backup already running for {0},details:{1}, skipping this run".format(dbname,rman_running_bkup)
        #     apscom.warn(message)
        #     raise Exception(message)
        #else:
        #    initialize_reco_configuration(tag, ret_days)
        #    type = "incremental_to_reco"
        #    cdb_pdb_flag = ""
        #    cdbflag = "no"
        #    if CDB_FLAG == "YES":
        #        cdb_pdb_flag = "_cdb"
        #        cdbflag = "yes"
        #    logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        #    rman_logfile = logfile_location + globalvariables.HOST_NAME + \
        #        "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        #    gen_json(rman_logfile, "pre", type, "START")
            #########
            # implement rman script
            # nonfa_dbaas rman execution
            # script_loc = "{0}/incremental_to_reco.rman{1} {2}".format(globalvariables.RMAN_SCRIPTS, cdb_pdb_flag,tag)
            # run_rman_cmd(script_loc, rman_logfile)
        #    db_size = query_output["DB_SIZE_GB"]
        #    if user_channels == 0:
        #        if db_size >= 5120:
        #            channels = 12
        #        else:
        #            channels = 8
        #    else:
        #        channels = user_channels
        #    backup_type = type
        #    cdbflag = "no"
        #    out_option = "file"
        #    nodes = node_count
        #    nodenames = None
        #    rman_file = db_rman_file_gen.pre_checks(
        #        dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        #    run_rman_cmd(rman_file, rman_logfile)
            ####
       #     gen_json(rman_logfile, "post", type, "SUCCESS")

        #    message = "Succeeds to backup incremental_to_reco of {0} ...".format(
        #        dbname)
        #    apscom.info(message)

        # apscom.info(message)
    except Exception as e:
        message = "Failed to do incremental_to_reco backup!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")


def incremental_to_oss(node_count, user_channels, tag=None, ret_days=0):
    rman_logfile = ''
    try:
        if tag is None:
            # tag='compressed_full_to_oss'
            tag = globalvariables.backup_opts["incre_to_oss_arch_to_oss"][env_type]["tag"]
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["incre_to_oss_arch_to_oss"][env_type]["retention"]

        #if "archived log backup" in rman_running_bkup:
        initialize_oss_configuration(tag, ret_days)
        type = "incremental_to_oss"
        cdb_pdb_flag = ""
        cdbflag = "no"
        if CDB_FLAG == "YES":
            cdb_pdb_flag = "_cdb"
            cdbflag = "yes"
        logfile_location = LOG_LOCATION+"/"+ORACLE_SID+"/"
        rman_logfile = logfile_location+globalvariables.HOST_NAME + \
            "_"+ORACLE_SID+"_"+type+"_"+timestamp+".log"
        gen_json(rman_logfile, "pre", type, "START")
        #########
        # implement rman script
        # nonfa_dbaas rman execution

        # script_loc="{0}/incremental_to_oss.rman{1} '{2}' '{3}' \\\"{4}/backupset\\\" '{5}' '{6}'".format(globalvariables.RMAN_SCRIPTS, cdb_pdb_flag, libopc_path,rman_ora_path, dbname,tag,ret_days)
        # run_rman_cmd(script_loc,rman_logfile)
        db_size = query_output["DB_SIZE_GB"]
        if user_channels == 0:
            if db_size >= 5120:
                channels = 12
            else:
                channels = 8
        else:
            channels = user_channels
        backup_type = type
        cdbflag = "no"
        out_option = "file"
        nodes = node_count
        nodenames = None
        rman_file = db_rman_file_gen.pre_checks(
            dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
        run_rman_cmd(rman_file, rman_logfile)
        ####
        gen_json(rman_logfile, "post", type, "SUCCESS")

        message = "Succeeds to backup incremental_to_oss of {0} ...".format(
            dbname)
        apscom.info(message)
        # Bug 33410790
        # elif "full" in rman_running_bkup and rman_running > 0 :
        #     message = "Backup already running for {0},details:{1}, skipping this run".format(dbname,rman_running_bkup)
        #     apscom.warn(message)
        #     raise Exception(message)
        #else:
        #    initialize_oss_configuration(tag, ret_days)
        #    type = "incremental_to_oss"
        #    cdb_pdb_flag = ""
        ##    cdbflag = "no"
         #   if CDB_FLAG == "YES":
         #       cdb_pdb_flag = "_cdb"
         #       cdbflag = "yes"
         #   logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
         #   rman_logfile = logfile_location + globalvariables.HOST_NAME + \
         #       "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
         #   gen_json(rman_logfile, "pre", type, "START")
            #########
            # implement rman script
            # nonfa_dbaas rman execution
            # script_loc="{0}/incremental_to_oss.rman{1} '{2}' '{3}' \\\"{4}/backupset\\\" '{5}' '{6}'".format(globalvariables.RMAN_SCRIPTS, cdb_pdb_flag, libopc_path,rman_ora_path, dbname,tag,ret_days)
            # run_rman_cmd(script_loc, rman_logfile)
        #    db_size = query_output["DB_SIZE_GB"]
         #   if user_channels == 0:
          #      if db_size >= 5120:
          #          channels = 12
          #      else:
          #          channels = 8
          #  else:
          #      channels = user_channels
          #  backup_type = type
          #  cdbflag = "no"
          #  out_option = "file"
          #  nodes = node_count
          #  nodenames = None
          #  rman_file = db_rman_file_gen.pre_checks(
          #      dbname, backup_type, nodes, channels, cdbflag, nodenames, out_option, tag, ret_days)
          #  run_rman_cmd(rman_file, rman_logfile)
          #  ####
          #  gen_json(rman_logfile, "post", type, "SUCCESS")

          #  message = "Succeeds to backup incremental_to_oss of {0} ...".format(
          #      dbname)
          #  apscom.info(message)
    except Exception as e:
        message = "Failed to do incremental_to_oss backup!\n{0}{1}".format(sys.exc_info()[
                                                                           1:2], e)
        apscom.warn(message)
        if rman_logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                rman_logfile, globalvariables.RED)
            with open(rman_logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(rman_logfile, "post", backup_type, "FAILED")
        else:
            gen_json(rman_main_log, "post", backup_type, "FAILED")


def initialize_configuration(node_count, channels, tag=None, ret_days=0):
    try:
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["incre_to_reco_arch_to_oss"][env_type]["retention"]
        rman_reco, rman_data = get_asm_disk_group()
        type = "conf"
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        #########
        # implement rman script
        # nonfa_dbaas rman execution
        script_loc = "{0}/configuration.rman {1} {2} {3}".format(
            globalvariables.RMAN_SCRIPTS, db_uniq_name, rman_data, ret_days)
        run_rman_cmd(script_loc, logfile)
        ####
        message = "Succeeds to initialize_configuration of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do initialize_configuration !\n{0}{1}".format(sys.exc_info()[
                                                                           1:2], e)
        apscom.warn(message)
        if logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                logfile, globalvariables.RED)
            with open(logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(logfile, "post", backup_type, "FAILED")
        else:
            gen_json(logfile, "post", backup_type, "FAILED")
        sys.exit(1)


def initialize_reco_configuration(node_count, channels, tag=None, ret_days=0):
    try:
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["incre_to_reco_arch_to_oss"][env_type]["retention"]
        type = "conf"
        rman_reco, rman_data = get_asm_disk_group()
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        #########
        # implement rman script
        # nonfa_dbaas rman execution
        script_loc = "{0}/configuration_reco.rman {1} {2} {3} {4}".format(
            globalvariables.RMAN_SCRIPTS, db_uniq_name, rman_reco, rman_data, ret_days)
        run_rman_cmd(script_loc, logfile)
        ####
        message = "Succeeds to initialize_reco_configuration of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do initialize_reco_configuration !\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        if logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                logfile, globalvariables.RED)
            with open(logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(logfile, "post", backup_type, "FAILED")
        else:
            gen_json(logfile, "post", backup_type, "FAILED")
        sys.exit(1)


def initialize_oss_configuration(node_count, channels, tag=None, ret_days=0):
    try:
        if ret_days == 0:
            ret_days = globalvariables.backup_opts["incre_to_oss_arch_to_oss"][env_type]["retention"]
        
        type = "conf"
        rman_reco, rman_data = get_asm_disk_group()
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        logfile = logfile_location + globalvariables.HOST_NAME + \
            "_" + ORACLE_SID + "_" + type + "_" + timestamp + ".log"
        #########
        # implement rman script
        # nonfa_dbaas rman execution
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        script_loc = "{0}/configuration_oss.rman {1} {2} {3}".format(
            globalvariables.RMAN_SCRIPTS, db_uniq_name, rman_data, ret_days)
        run_rman_cmd(script_loc, logfile)
        ####
        message = "Succeeds to initialize_oss_configuration of {0} ...".format(
            dbname)
        apscom.info(message)
    except Exception as e:
        message = "Failed to do initialize_oss_configuration !\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        if logfile:
            message = "{1}Errors recorded in file {0} \n".format(
                logfile, globalvariables.RED)
            with open(logfile, 'r') as file:
                for line in file:
                    if 'error' in line:
                        message = message + line
            apscom.warn(message)
            gen_json(logfile, "post", backup_type, "FAILED")
        else:
            gen_json(logfile, "post", backup_type, "FAILED")
        sys.exit(1)


def gen_json(logfile, pre_post_flag, type, status,resume_flag=None):
    try:
        logfile_location = LOG_LOCATION + "/" + ORACLE_SID + "/"
        file_name = logfile_location+globalvariables.HOST_NAME+"_" + \
            ORACLE_SID+"_"+type+"_"+timestamp+"_"+pre_post_flag+".json"
        data = create_backup_metadata(
            logfile, type, pre_post_flag, status, dbname,resume_flag=resume_flag)
        with open(file_name, 'w') as outfile:
            json.dump(data, outfile, indent=4, sort_keys=True)
        outfile.close()

        if "pre" not in pre_post_flag and not commonutils.check_em_systemtype() and not commonutils.check_dbaas_systemtype():
            commonutils.oss_upload_backup_metadata(file_name)
    except Exception as e:
        message = "Failed to generate json!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


def runsql_cmd(sql_file_name, cdb_param="", pdb_param=""):
    sql_output = ""
    stderror = ""
    err_code = 0
    try:
        if len(query_output["FUSION_PDB"]) > 0:
            if sql_file_name.startswith("pdb_", 0, 4):
                sql_cmd = 'sqlplus -s -L "/ as sysdba" @'+globalvariables.DB_QUERY_LOCATION + \
                    '/' + sql_file_name + ' ' + \
                    query_output["FUSION_PDB"]+' '+pdb_param
                execute_pdb_sql = "{3}".format(
                    globalvariables.ORACLE_USER_HOME, dbname, globalvariables.SETPY_PATH, sql_cmd)
                [sql_output, err_code, stderror] = commonutils.execute_shell(
                    execute_pdb_sql)
            elif sql_file_name.startswith("cdb_", 0, 4):
                sql_cmd = 'sqlplus -s -L "/ as sysdba" @' + \
                    globalvariables.DB_QUERY_LOCATION+'/'+sql_file_name+' '+cdb_param
                execute_cdb_sql = "{3}". \
                    format(globalvariables.ORACLE_USER_HOME, dbname,
                           globalvariables.SETPY_PATH, sql_cmd)
                [sql_output, err_code, stderror] = commonutils.execute_shell(
                    execute_cdb_sql)
            if err_code != 0:
                sql_output = "NULL"
            return sql_output.lstrip("\n").lstrip().rstrip("\n")
        else:
            message = "Unable to run runsql_cmd : either FUSION_PDB value is null or db connection failed \n{0}".format(
                stderror)
            apscom.info(message)
            return "NULL"
    except Exception as e:
        message = "Unable to run runsql_cmd !\n{0}{1}".format(stderror, e)
        apscom.warn(message)
        raise


def create_backup_metadata(log_file, type, pre_post_flag, status, db_name, host=None,resume_flag=None):
    """ Create backup metadata.
    Args:
        log_file (str): oss/fss
        type (str): backup path if backup target is fss
                           object name if backup target is oss
    Returns:
        backup_metadata (dict): Info of backup metadata.
    """
    single_tag = ""
    target_location = ""
    target_type = ""
    db_info = []
    BREAKGLASS_ENABLED = ''
    DB_BACKUP_SIZE = ''
    json_query_output = {}
    general_metadata = {}
    piece_info = ''
    tag = ''
    try:
        env_type = commonutils.get_db_env_type(db_name)
        faops_backup_oss_info_file = "{0}/config/faops-backup-oss-info.json".format(
            BASE_DIR)
        if os.path.exists(faops_backup_oss_info_file):
            with open(faops_backup_oss_info_file, 'r') as f:
                faops_backup_oss_info = json.load(f)
        if os.path.exists(globalvariables.OCI_SDK_META_FILE):
            with open(globalvariables.OCI_SDK_META_FILE, 'r') as f:
                oci_tenancy_info = json.load(f)
        for ns in faops_backup_oss_info:
            if ns == oci_tenancy_info["ns"]:
                if faops_backup_oss_info[ns]["tenancy"] == oci_tenancy_info["tenancy_name"]: 
                    if env_type == "em_exa" :
                        bucket_name = faops_backup_oss_info[ns]["em_rman_oss_bn"]
                    elif env_type == "dbaas":
                        bucket_name = faops_backup_oss_info[ns]["dbaas_rman_oss_bn"]
                    else:
                        bucket_name = faops_backup_oss_info[ns]["fa_rman_oss_bn"][env_type]

        backup_end_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        backup_metadata = {}
        metadata_t = open(globalvariables.BACKUP_METADATA_TEMPLATE, 'r')
        metadata_data = json.load(metadata_t)
        metadata_t.close()

        # retention_days=14
        # _type(db_name)
        env_type = commonutils.get_db_env_type(db_name)
        retention_days = globalvariables.backup_opts["database_to_reco"][env_type]["retention"]
        try:
            if log_file:
                tag_str = "grep \'^piece handle=\' {0} | grep tag|awk -F'[ =]'  \'{{print $5}}\'| sort -u |tr '\\n' ','| sed 's/,$//g'|sed 's/^,\{{1\}}//'".format(
                    log_file)
                tag = commonutils.execute_shell(tag_str)[0]
                single_tag = tag.split(',')[0]
            else:
                tag = ''
        except Exception as e:
            message = "failed to get piece info , error: {0}".format(e)
            apscom.warn(message)
            single_tag = ""
            pass
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            if not 'wrapper' in pre_post_flag and 'rman_oss' not in pre_post_flag and "sec_node_full" not in pre_post_flag:
                db_info = db_info_array
                BREAKGLASS_ENABLED = runsql_cmd(
                    'pdb_get_bg_status.sql').strip().lstrip().rstrip()
                if tag:
                    DB_BACKUP_SIZE = runsql_cmd(
                        'cdb_db_backup_size2.sql', cdb_param=single_tag)
                json_query_output = query_output

        if("oss" in type):
            # retention_days=60
            retention_days = globalvariables.backup_opts["database_compressed_to_oss"][env_type]["retention"]
            target_type = "oss"
            if "archivelog" in type:
                target_location = db_name+"/archivelog"
            else:
                target_location = db_name+"/backupset"
        elif type == 'incremental_to_reco' or type == 'database_to_reco' or type == 'ldb_database_to_reco':
            target_type = "fra"

        con_id = "null"
        try:
            if "sec_node_full" not in pre_post_flag:
                piece_str = "grep \'^piece handle=\' {0} | awk -F'[ =]'  \'{{print $3}}\'| tr '\\n' ',' | sed 's/,$//g'".format(
                    log_file)
                piece_info = commonutils.execute_shell(piece_str)[0].strip()
            else:
                piece_info = ''
        except Exception as e:
            message = "failed to get piece info , error: {0}".format(e)
            apscom.warn(message)
            piece_info = ""
            pass

        if not host:
            host = globalvariables.LOCAL_HOST
        if not resume_flag:
            resume_flag="No"
        # whenever a file name starts with pdb_ , should pass the container value query_output["PDB_NAME"]
        # if file name starts with cdb_ , dont pass container name
        # get metadata from commonutils
        
        if json_query_output:
            db_unique_name = json_query_output["DB_UNIQUE_NAME"]
            general_metadata = commonutils.get_metadata_info(db_unique_name)
        
        error_code=""
        if status.upper() == "FAILED":
            error_code=commonutils.check_error_code(log_file)

        #Adding code for adding the SCN number in backup metadata
        SCN_NUMBER=""
        if status.upper() == "SUCCESS":
            SCN_NUMBER = runsql_cmd('cdb_scn_number.sql')

        # Generate backup metadata
        backup_metadata["BACKUP_TOOL"] = "rman"
        backup_metadata["resume_flag"] = resume_flag
        backup_metadata["TAG"] = tag
        backup_metadata["PRE_POST_FLAG"] = pre_post_flag
        backup_metadata["LOG_FILE"] = log_file
        backup_metadata["BTIMESTAMP"] = start_time
        backup_metadata["ETIMESTAMP"] = backup_end_time
        backup_metadata["HOSTNAME"] = host
        backup_metadata["CLIENT_TYPE"] = "database"
        backup_metadata["CLIENT_NAME"] = db_name
        backup_metadata["FUSION_PDB"] = json_query_output["FUSION_PDB"] if json_query_output else ""
        backup_metadata["BACKUP_TYPE"] = type
        backup_metadata["TARGET_TYPE"] = target_type
        backup_metadata["TARGET_LOCATION"] = target_location
        backup_metadata["PIECE_NAME"] = piece_info
        backup_metadata["RETENTION_DAYS"] = retention_days
        backup_metadata["STATUS"] = status
        backup_metadata["DB_INCR_ID"] = db_info[1] if db_info else ""
        backup_metadata["DB_ID"] = db_info[0] if db_info else ""
        backup_metadata["CON_ID"] = con_id
        backup_metadata["POD_NAME"] = ""
        backup_metadata["DB_ROLE"] = db_info[2] if db_info else ""
        backup_metadata["RPM_VER"] = general_metadata["rpm_ver"] if general_metadata else ""
        backup_metadata["DBAAS_VER"] = general_metadata["dbaas_ver"] if general_metadata else ""
        backup_metadata["DB_SIZE_GB"] = json_query_output["DB_SIZE_GB"] if json_query_output else ""
        backup_metadata["DB_INSTANCE_VERSION"] = json_query_output["INSTANCE_VERSION"] if json_query_output else ""
        backup_metadata["DB_BACKUP_SIZE"] = DB_BACKUP_SIZE
        backup_metadata["BREAKGLASS_ENABLED"] = BREAKGLASS_ENABLED
        backup_metadata["DB_CREATED"] = json_query_output["DB_CREATED"] if json_query_output else ""
        backup_metadata["INSTANCE_START_TIME"] = json_query_output["INSTANCE_START_TIME"] if json_query_output else ""
        backup_metadata["DB_UNIQUE_NAME"] = json_query_output["DB_UNIQUE_NAME"] if json_query_output else ""
        backup_metadata["OSS_NAMESPACE"] = post_backup_metadata.get_namespace_from_sre(
        )
        backup_metadata["OS_VER"] = general_metadata["os_ver"] if general_metadata else ""
        backup_metadata["LIBOPC_BUILD_VER"] = general_metadata["libopc_build_ver"] if general_metadata else ""
        backup_metadata["LDB_REMOTE_SCALING"] = general_metadata["ldb_remote_scaling"] if general_metadata else ""
        backup_metadata["EXADATA_SHAPE"] = instance_metadata.ins_metadata(
        ).system_type
        backup_metadata["DB_BACKUP_EXCEPTIONS"] = read_exception_list()
        backup_metadata["DB_SHAPE"] = json_query_output["DB_SHAPE"] if json_query_output else ""
        backup_metadata["RMAN_SESSION_GT24HRS"] = json_query_output["RMAN_SESSION_GT24HRS"] if json_query_output else ""
        backup_metadata["DR_ENABLED_CHK"] = json_query_output["DR_ENABLED_CHK"] if json_query_output else ""
        backup_metadata["PDB_LIST"] = json_query_output["PDB_LIST"] if json_query_output else ""
        backup_metadata["OSS_BUCKET"] = bucket_name if json_query_output else ""
        backup_metadata["ODS_PDB_COUNT"] = json_query_output["ODS_PDB_COUNT"] if json_query_output else ""
        backup_metadata["ERROR_CODE"] = error_code
        backup_metadata["SCN"] = SCN_NUMBER
        metadata_data["backup"]["db_mt_os"][0] = backup_metadata
        # Save the backup metadata to a json file.
        metadata_report = open(BACKUP_METADATA_PATH, 'w')
        json.dump(metadata_data, metadata_report, indent=4,
                  sort_keys=True, separators=(',', ':'))
        metadata_report.close()
        try:
            if os.path.exists(BACKUP_METADATA_PATH):
                shutil.chown(BACKUP_METADATA_PATH, "oracle", "oinstall")
        except Exception as e:
            message = "Failed to change permission {0}".format(
                BACKUP_METADATA_PATH)
            apscom.warn(message)
        return backup_metadata

    except Exception as e:
        message = traceback.print_exc()
        apscom.error(message)
        message = "Failed to create metadata for this backup!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise


def read_exception_list():
    exception_list_str = ''
    exception_list = []
    try:
        with open(globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt", "r") as fp:
            lines = fp.readlines()
        for line in lines:
            exception_list.append(line.strip())
        exception_list_str = ",".join(exception_list)
        return exception_list_str
        # return exception_list
    except Exception as e:
        message = "Failed to read backup exceptions!\n{0}{1}".format(sys.exc_info()[
                                                                     1:2], e)
        apscom.warn(message)
        return exception_list_str
        # raise


def take_action_backup():
    (options, args) = parse_opts()
    tag = options.tag
    ret_days = options.retention_days
    channels = options.channels
    nodes = options.nodes
    backup_restore_time = options.backup_restore_time
    resume_flag = options.resume_flag

    try:
        if resume_flag and resume_flag.lower() == "yes" and backup_type in globalvariables.resume_backup_types:
            try:
                back_type, backup_restore_time_res,status = resume_backup.resumable_check(ORACLE_SID)
                if status :
                    if backup_restore_time:
                        database_compressed_to_oss(nodes, channels, backup_type, tag, ret_days, backup_restore_time, resume_flag)
                        restore_validate_oss(nodes, channels, backup_type, tag, ret_days)
                    else:
                        database_compressed_to_oss(nodes, channels, back_type, tag, ret_days, backup_restore_time_res, resume_flag)
                        restore_validate_oss(nodes, channels, backup_type, tag, ret_days)
                else:
                    message = "Starting Full backup, as there was no failed backup found to resume"
                    apscom.info(message)
                    database_compressed_to_oss(
                    nodes, channels, backup_type, tag, ret_days)
            except Exception as e:
                    message = "Failed to do resumable backup!\n{0}{1}".format(sys.exc_info()[1:2], e)
                    apscom.warn(message)        
        else:
            if backup_type == "archivelog_to_oss":
                archivelog_to_oss(nodes,channels,tag,ret_days)
            elif backup_type == "incre_to_reco_arch_to_oss":
                incremental_to_reco(nodes, channels, tag, ret_days)
            elif backup_type == "incre_to_oss_arch_to_oss":
                incremental_to_oss(nodes, channels, tag, ret_days)
            elif backup_type == "db_to_reco_db_arch_to_oss":
                database_to_reco(nodes, channels, backup_type, tag,
                                ret_days)
                database_compressed_to_oss(
                    nodes, channels, backup_type, tag, ret_days)
            elif backup_type == "db_to_reco":
                database_to_reco(nodes, channels, backup_type, tag,
                                ret_days)
            elif backup_type == "db_to_oss":
                database_compressed_to_oss(
                    nodes, channels, backup_type, tag, ret_days)
            elif backup_type == "ldb_db_to_oss":
                database_compressed_to_oss(
                    nodes, channels, backup_type, tag, ret_days)
            elif backup_type == "validate_db_reco":
                validate_db_reco(nodes, channels, tag, ret_days)
            elif backup_type == "validate_db_oss":
                validate_db_oss(nodes, channels, tag, ret_days)
            elif backup_type == "validate":
                validate_db_reco(nodes, channels, tag, ret_days)
                # validate_db_oss(tag,ret_days)
            elif backup_type == "restore_validate_oss":
                restore_validate_oss(nodes, channels, backup_type, tag, ret_days)
            elif backup_type == "ldb_restore_validate_oss":
                restore_validate_oss(nodes, channels, backup_type, tag, ret_days)
            elif backup_type == "restore_validate":
                restore_validate_oss(nodes, channels, backup_type, tag, ret_days)

    except Exception as e:
        message = "Failed to do backup!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        # message = traceback.print_exc()
        # apscom.warn(message)
        gen_json(rman_main_log, "post", backup_type, "FAILED")
        sys.exit(1)


def get_asm_disk_group():
    try:
        rman_reco = ''
        rman_data = ''
        asm_disk_group = query_output["ASM_DISK_GROUP"]
        if len(asm_disk_group) > 0:
            for data in asm_disk_group:
                for value in data:
                    if 'REC' in value:
                        rman_reco = value
                    elif 'DAT' in value:
                        rman_data = value
        return rman_reco, rman_data
    except Exception as e:
        # message = traceback.print_exc()
        # apscom.warn(message)
        message = "Failed to get ASM disk group!\n{0}{1}".format(sys.exc_info()[
                                                                 1:2], e)
        apscom.warn(message)


def database_backup(backuptype, db_name, dbsid, oraclehome=None):
    try:
        global dbname
        global backup_type
        global ORACLE_SID
        global ORACLE_HOME
        global LARGE_DB_FLAG
        global CDB_FLAG
        global rman_status
        global db_info_array
        global query_output
        global BREAKGLASS_ENABLED
        global rman_running
        global rman_running_bkup
        global rman_ora_path
        unique_db_name = ''
        global libopc_path
        dbname = db_name
        username = getpass.getuser()

        if ("nfs" in backuptype):
            msg = "Error: ${rtype} is not supported. This script supports OSS for OCI envs."
            apscom.error(msg)
        else:
            backup_type = backuptype
            query_res_json = globalvariables.DB_BACKUP_LOG_PATH + "/" + dbsid + \
                "/" + globalvariables.HOST_NAME + "_" + dbsid + "_query.json"
            if not os.path.exists(query_res_json):
                message = "Error: Not active {0}".format(dbname)
                apscom.info(message)
                return None
            query_file = open(query_res_json.strip(), 'r')
            query_output = json.load(query_file)
            dbname = query_output["DB_NAME"]
            rman_status = query_output["RMAN_STATUS"]
            CDB_FLAG = query_output["CDB_STATUS"]
            DB_SIZE = query_output["DB_SIZE"]
            rman_running = query_output["RMAN_RUNNING_STATUS"]
            rman_running_bkup = query_output["RMAN_RUNNING_BKP"]
            DB_Full_Status    = query_output["DB_Full_Sts"]
            DB_Archive_status = query_output["DB_Archive_sts"]
            if DB_SIZE > 5:
                LARGE_DB_FLAG = "Y"
            else:
                LARGE_DB_FLAG = "N"
            db_info_array = query_output["DB_INFO"]
            ORACLE_SID = query_output["INSTANCE_NAME"]
            crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
            with open(crsctl_json) as json_file:
                json_data = json.load(json_file)
            for key in json_data:
                if dbname == key:
                    unique_db_name = json_data[key]['db_unique_name']
            # fa dbname is euql to unique_db_name and in non fa dbname and unique_db_name is different to execute rman scripts assiging unique_db_name to dbname
            # dbname=unique_db_name
            if oraclehome:
                ORACLE_HOME = oraclehome
            else:
                ORACLE_HOME = commonutils.get_oracle_home(ORACLE_SID, dbname)
            # validate_sbt_test.validate_sbttest(dbname,ORACLE_HOME)
            chk_output = ''
            try:
                chk_output = commonutils.check_conflicts_v2(
                    backup_type, dbname, file_name=__file__,DB_Full_Status=DB_Full_Status,DB_Archive_status=DB_Archive_status)
            except Exception as e:
                message = "Error: running commonutils.check_conflicts for {0}  {1}..\n{2}".format(
                    __file__, backup_type, chk_output)
                apscom.warn(message)
                gen_json(rman_main_log, "post", backuptype, "FAILED")
                sys.exit(1)

            # if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            #     list_of_files = glob.glob(globalvariables.OPC_LIB_PATH + '/' + dbname + '/opc' + dbname + '.ora')
            #     #print("List of files:-", list_of_files)
            #     rman_ora_path = max(list_of_files, key=os.path.getmtime)
            #     #print("RMAN ORA PATH:- ", rman_ora_path)
            #     list_libopc = glob.glob(globalvariables.OPC_LIB_PATH + '/' + dbname + '/lib/libopc.so')
            #     #print("List of libopc:-", list_libopc)
            #     libopc_path = max(list_libopc, key=os.path.getmtime).rstrip()
            #     #print("Libopc path :-",libopc_path)
            # else:
            #     list_of_files = glob.glob(globalvariables.NONFA_DBAAS_RMAN_OPC_PATH+'/**/*' + dbname + '.ora')
            #     rman_ora_path = max(list_of_files, key=os.path.getmtime)
            #     list_libopc = glob.glob(globalvariables.NONFA_DBAAS_LIBOPC+'/**/libopc.so')
            #     libopc_path = max(list_libopc, key=os.path.getmtime).rstrip()
            if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
                list_of_files = glob.glob(
                    globalvariables.OPC_LIB_PATH + '/' + dbname + '/opc' + dbname + '.ora')
                if not list_of_files:
                    message = "The file {0}/{1}/opc{1}.ora file is missing. Please run rman_wrapper/database_config.py to reconfigure the libraries.".format(
                        globalvariables.OPC_LIB_PATH, dbname)
                    apscom.error(message)
                else:
                    rman_ora_path = max(list_of_files, key=os.path.getmtime)
                list_libopc = glob.glob(
                    globalvariables.OPC_LIB_PATH + '/' + dbname + '/lib/libopc.so')
                if not list_libopc:
                    message = "The opc lib file {0}/{1}/lib/libopc.so file is missing. Please run rman_wrapper/database_config.py to reconfigure the libraries.".format(
                        globalvariables.OPC_LIB_PATH, dbname)
                    apscom.error(message)
                else:
                    libopc_path = max(
                        list_libopc, key=os.path.getmtime).rstrip()
            else:
                #list_of_files = glob.glob(
                #    globalvariables.NONFA_DBAAS_RMAN_OPC_PATH+'/**/*' + dbname + '.ora')
                list_of_files = glob.glob(
                    globalvariables.OPC_LIB_PATH + '/' + dbname + '/opc' + dbname + '.ora')
                if not list_of_files:
                    message = "The file {0}/**/*{1}.ora file is missing. Please run rman_wrapper/database_config.py to reconfigure the libraries.".format(
                        globalvariables.NONFA_DBAAS_RMAN_OPC_PATH, dbname)
                    apscom.error(message)
                else:
                    rman_ora_path = max(list_of_files, key=os.path.getmtime)
                list_libopc = glob.glob(
                    globalvariables.NONFA_DBAAS_LIBOPC+'/**/libopc.so')
                if not list_libopc:
                    message = "The opc lib file {0}/**/libopc.so file is missing. Please run rman_wrapper/database_config.py to reconfigure the libraries.".format(
                        globalvariables.NONFA_DBAAS_LIBOPC, dbname)
                    apscom.error(message)
                else:
                    libopc_path = max(
                        list_libopc, key=os.path.getmtime).rstrip()
            take_action_backup()
            obsolete_backupset_withoss()
            if CDB_FLAG == 'YES':
                pdbseed_to_reco()
            # remove sql output json file
            # os.remove(query_res_json)
            query_file.close()
    except Exception as e:
        # message = traceback.print_exc()
        # apscom.warn(message)
        message = "Failed to do database backup!\n{0}{1}".format(
            backuptype, sys.exc_info()[1:2], e)
        apscom.warn(message)
        gen_json(rman_main_log, "post", backuptype, "FAILED")
        sys.exit(1)


usage_str = """
    rman_oss.py - DB Backup tool to backup FA on OCI Pod DB Backups.

    ** Should be run as oracle user **
    /opt/faops/spe/ocifabackup/bin/rman_oss.sh -b <backup option> -d <db unique name>

    -b                  - Required - Backup Options Supported:
                            db_to_reco_db_arch_to_oss : Full Database Backup to Reco followed by Full Databaes Backup to OSS
                            incre_to_reco_arch_to_oss : Incremental Backup to Disk
                            incre_to_oss_arch_to_oss : Incremental Backup to OSS
                            db_to_reco : Database Backup to Reco
                            db_to_oss: Database Backup to OSS
                            ldb_db_to_oss: Use this option to create rman channeels across the cluster, refer Backup FAQ for details
                            archivelog_to_oss: Archivelog Backup to OSS
                            restore_validate_oss: runs restore validate on oss backups for given database
                            ldb_restore_validate_oss :  Use this option to create rman channeels across the cluster, refer Backup FAQ for details



    -d                  - Optional - DB unique name

    --retention-days    - Optional - Retention days of give backup type.

    -f                  - Optional - Use this option to force backup on even node'

    --tag               - Optional - Optional tag, if other than standard ones

    --debug_log         - Optional Use this oprion to enable logging as debug mode

    --resume_flag       - Optional - provide resume_flag yes

    --backup_restore_time - Optional - sample string "10-13-22\ 06:40:11"
"""


def parse_opts():
    try:
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('-b', action='store', dest='backup_type',
                          help='Required - Specify the action: db_to_reco_db_arch_to_oss,incre_to_reco_arch_to_oss,incre_to_oss_arch_to_oss,archivelog_to_oss,db_to_reco,db_to_oss,validate_reco_backup,validate_oss_backup,validate,validate_db_oss,validate_db_reco')
        parser.add_option('-d', '--dbname', action='store',
                          dest='db_name', help='Required - pass db unique name')
        parser.add_option('-f', '--force', action='store',
                          dest='force_flag', default=False)
        # fix for https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1035
        parser.add_option('--retention-days', action='store', dest='retention_days',
                          default=0, type=int, help='Optional - Retention days of give backup type.')
        parser.add_option('--tag', action='store', dest='tag', default=None,
                          help='Optional - provide tag, if other than standard ones')
        parser.add_option('--nodes', action='store', dest='nodes',
                          default=0, type=int, help='Optional - provide number of nodes')
        parser.add_option('--channels', action='store', dest='channels',
                          default=0, type=int, help='Optional - provide number of channels')
        parser.add_option('--resume_flag', action='store', dest='resume_flag',
                          default=None, help='Optional - provide resume_flag yes/no')
        parser.add_option('--backup_restore_time', action='store', dest='backup_restore_time',
                          default=None, help='Optional - sample string - "10-13-22\ 06:40:11"')
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_option('--debug_log', action='store', dest='debug_log',
                          default="no", help='Optional - Get logs in debug mode')

        (opts, args) = parser.parse_args()
        if not opts.backup_type or not opts.db_name:
            parser.error(
                '-b option is required and --dbname option is required')
        if not opts.db_name:
            parser.error('--dbname option is required')
        if opts.resume_flag and opts.resume_flag != "yes":
            parser.error('--resume_flag option must be yes')
        if opts.backup_restore_time:
            dtsr=opts.backup_restore_time
            try:
                dt = datetime.strptime(dtsr,'%m-%d-%y %H:%M:%S')
            except Exception:
                parser.error('--backup_restore_time option must be in format "10-13-22\ 06:40:11"')
        return (opts, args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.error(message)
        sys.exit(1)


def main():
    #adp exa check as part of FAOCI-775#
    adp_status=''
    statuscode=''
    cmd="/usr/bin/timeout 300 {0}/adp_enabled_check.sh".format(globalvariables.DB_SHELL_SCRIPT)
    [adp_status,statuscode,stderr]=commonutils.execute_shell(cmd)
    if statuscode > 0:
        apscom.error(adp_status)
    stderror = ""
    global rman_main_log
    global env_type
    (options, args) = parse_opts()
    backuptype = options.backup_type
    db_name = options.db_name
    env_type = commonutils.get_db_env_type(db_name)
    if options.debug_log == "yes":
        import logging
        # Enable debug logging
        logging.getLogger('oci').setLevel(logging.DEBUG)
        # oci.base_client.is_http_log_enabled(True)
        # logging.basicConfig(filename='/tmp/test.log')
        log_file_path_for_debug = globalvariables.DB_BACKUP_LOG_PATH + \
            "/{0}/".format("exalogs")
        if not os.path.exists(log_file_path_for_debug):
            os.makedirs(log_file_path_for_debug)
        filename_debug = log_file_path_for_debug+"/oci_debug" + \
            "_{0}_{1}.log".format(globalvariables.HOST_NAME,
                                  datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        logging.basicConfig(filename=filename_debug)
    try:
        bdsid_dir = db_name+globalvariables.HOST_NAME[-1]
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + \
            "/{0}/".format(bdsid_dir)
        filename = log_file_path + "{0}_{1}_{2}_{3}.log".format(globalvariables.HOST_NAME, bdsid_dir,
                                                                os.path.basename(
                                                                    __file__).split(".")[0],
                                                                datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        rman_main_log = apscom.init_logger(
            __file__ + db_name, log_dir=log_file_path, logfile=filename)
        # check script invocation
        # invocation = os.getenv('BKP_INVOCATION')
        # if invocation == "cron":
        #     apscom.info("rman_wrapper script invoked using cron or mcollective or jc")
        # elif invocation == "manual":
        #     apscom.info("rman_wrapper script invoked manually")
        # else:
        #     apscom.info("cannot determine how rman_wrapper script was invoked")
        #
        crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
        if not os.path.exists(crsctl_json):
            apscom.error(
                "{0} is not present, ensure you run /opt/faops/spe/ocifabackup/bin/rman_wrapper_oss.sh first as root user".format(crsctl_json))
            raise
        
        if commonutils.check_em_systemtype():
            str_querypool = "python {3}/db_query_pool.py {4}". \
                format(globalvariables.ORACLE_USER_HOME, db_name, globalvariables.SETPY_PATH,
                    globalvariables.QUERY_POOL_PATH, "em_query.txt")
        elif commonutils.check_dbaas_systemtype():
            str_querypool = "python {3}/db_query_pool.py {4}". \
                format(globalvariables.ORACLE_USER_HOME, db_name, globalvariables.SETPY_PATH,
                    globalvariables.QUERY_POOL_PATH, "dbaas_query.txt")
        else:
            str_querypool = "python {3}/db_query_pool.py {4}". \
                format(globalvariables.ORACLE_USER_HOME, db_name, globalvariables.SETPY_PATH,
                    globalvariables.QUERY_POOL_PATH, "query.txt")
        [query_res_json, ret_code, stderror] = commonutils.execute_shell(
            str_querypool)
        query_file = open(query_res_json.strip(), 'r')
        query_output = json.load(query_file)
        dbsid = query_output["ORACLE_SID"]
        query_file.close()
        rman_running = query_output["RMAN_RUNNING_STATUS"]
        rman_running_bkup = query_output["RMAN_RUNNING_BKP"]
        database_backup(backuptype, db_name, dbsid)
    except Exception as e:
        message = "Failed to execute the query {0}\n{1} ...".format(
            e, stderror)
        apscom.warn(message)
        create_backup_metadata(rman_main_log, backuptype,
                               "rman_oss", "FAILED", db_name)
        raise


if __name__ == "__main__":
    main()
