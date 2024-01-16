#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      commonutils.py
    DESCRIPTION
      implement all common methods
    NOTES

    MODIFIED        (MM/DD/YY)

    Zakki Ahmed       02/20/22 - initial version (code refactoring)
"""
#### imports start here ##############################
import optparse
import argparse
import time
import paramiko
import getpass
import os
import sys
import traceback
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import apscom
from common import globalvariables,commonutils

#### imports start here ##############################

def exec_on_remote(host,cmd=None):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host, timeout=60)
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
        out=stdout.read().decode('utf-8').rstrip()
        error=stderr.read().decode('utf-8').rstrip()
        ssh_client.close()
        return [out,error]
    except Exception as e:
        message = "Failed to connect{0},{1}!\n{2}".format(host, sys.exc_info()[1:2], e)
        apscom.warn(message)


def process_tasks(dbname,backup_type,action,host,pid,file):
    # check conflicts
    if action == "check_conflicts":
        if backup_type and dbname:
            cmd = 'ps -ef|grep {0}|grep -v grep |grep {1}|grep rman_oss.py|wc -l'.format(dbname,backup_type)
            [stdout, stderr] = exec_on_remote(host, cmd)
            if not stderr:
                # print(stdout)
                if int(stdout) >= 1:
                    return True
                else:
                    return False
            else:
                # print('')
                return True
        else:
            message = "required --dbname and --backup_type "
            apscom.warn(message)
    
    # check existence of rman_oss.sh on target node
    if action == "check_rman_file":
        cmd = '[ -f "{0}/bin/rman_oss.sh" ] && echo 0 || echo 1'.format(BASE_DIR)
        [stdout, stderr] = exec_on_remote(host, cmd)
        if not stderr:
            # print(stdout)
            if int(stdout) == 0:
                return True
            else:
                return False
        else:
            # print('')
            return False
    
    # check rpm on other node
    if action == "rpmcheck":
        cmd =  "rpm -qa|grep -m 1 -i backup|uniq"
        [stdout, stderr] = exec_on_remote(host, cmd)
        if not stderr:
            # print(stdout)
            if int(stdout) == 0:
                return True
            else:
                return False
        else:
            # print('')
            return False

    # verify rman status and return pid
    if action == "verify_rman_status":
        if backup_type  and dbname:
            # cmd = "ps -ax | grep -w \"rman_oss.py --dbname=" + str(dbname) + " -b " + str(backup_type) + "\" | grep -v '/usr/bin/script'  | grep -v grep | awk '{print $1}'"
            cmd = "ps -ax | grep -w 'rman_oss.py --dbname={0} -b {1}' | grep -v '/usr/bin/script'  | grep -v grep | awk '{{print $1}}' ".format(dbname,backup_type)
            [stdout, stderr] = exec_on_remote(host, cmd)
            if not stderr:
                if stdout:
                    return stdout
                else:
                    return 0
            else:
                return 0
        else:
            message = "required --dbname and --backup_type "
            apscom.warn(message)
   
    # verify PID on target node
    if action == "check_pid":
        if pid:
            # cmd = "ps -ax | grep -w \"rman_oss.py --dbname=" + str(dbname) + " -b " + str(backup_type) + "\" | grep -v '/usr/bin/script'  | grep -v grep | awk '{print $1}'"
            # cmd = "ps -ax | grep -w 'rman_oss.py --dbname={0} -b {1}' | grep -v '/usr/bin/script'  | grep -v grep | awk '{{print $1}}' ".format(dbname,backup_type)
            cmd = "ps --pid $$ -N -a | grep \"\\b{0}\\b\" | awk '{{print $1}}' ".format(pid)
            [stdout, stderr] = exec_on_remote(host, cmd)
            if not stderr:
                if stdout:
                    return stdout
                else:
                    return 0
                # return stdout
            else:
                return None
        else:
            message = "required --pid "
            apscom.warn(message)

    # run backup
    env_type = commonutils.get_db_env_type(dbname)
    retention=globalvariables.backup_opts[backup_type][env_type]["retention"]    
    if action == "run_backup":
        if backup_type  and dbname:
            check_rman_file_status = process_tasks(None,None,"check_rman_file",host,None,None)
            check_rman_check_conflicts = process_tasks(dbname,backup_type,"check_conflicts",host,None,None)
            if check_rman_file_status: 
                if not check_rman_check_conflicts:
                    # cmd = "nohup python executefile.py >/dev/null 2>&1 &"
                    # tag=globalvariables.backup_opts[backup_type]["tag"]
                    #if backup_type == "db_to_oss" or backup_type == "database_compressed_to_oss" or backup_type == "ldb_database_compressed_to_oss":
                    #FUSION_PDB=commonutils.get_db_env_type(dbname)
                    #if not FUSION_PDB:
                    #    env_type="prod"
                    #else:
                    #    env_type="stage"
                    #    retention_days = globalvariables.backup_opts[backup_type][env_type]["retention"]    
                    #else:
                    #retention=globalvariables.backup_opts[backup_type][env_type]["retention"]
                    cmd = "nohup {0}/bin/rman_oss.sh --dbname={1} -b {2} --retention-days={3} >/dev/null 2>&1 &".format(BASE_DIR,dbname,backup_type,str(retention))
                    [stdout, stderr] = exec_on_remote(host, cmd)
                    if not stderr:
                        # verify rman backup
                        time.sleep(10)
                        running_pid=process_tasks(dbname,backup_type,"verify_rman_status",host,None,None)
                        if running_pid != None:
                            return running_pid
                    else:
                        return 0
                else:
                    running_pid=process_tasks(dbname,backup_type,"verify_rman_status",host,None,None)
                    message ="cannot run backup on target {0} as backup already running with pid {1} ".format(host,running_pid)
                    apscom.warn(message)
                    return 0
                   
            else:
                message = "cannot find {0}/bin/rman_oss.sh on target host {1} , proceeding with backup on {2}".format(BASE_DIR,host,globalvariables.LOCAL_HOST)
                apscom.warn(message)
                cmd = "nohup {0}/bin/rman_oss.sh --dbname={1} -b {2} --retention-days={3} >/dev/null 2>&1 &".format(BASE_DIR,dbname,backup_type,str(retention))
                stderr=''
                [res, ret_code, stderr]=commonutils.execute_shell(cmd)
                running_pid=process_tasks(dbname,backup_type,"verify_rman_status",globalvariables.LOCAL_HOST,None,None)
                if running_pid != None:
                    return running_pid
                return None
            
           
        else:
           message = "required --dbname and --backup_type "
           apscom.warn(message)
           return None

    # run script file on target node -- script should be available on target node
    if file:
        cmd = file
        [stdout, stderr] = exec_on_remote(host, cmd)
        if not stderr:
            return stdout
        else:
            return None
    # 

def parse_opts():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--dbname',dest='dbname',help='required - pass db unique name')
        parser.add_argument('--host',dest='host',help='required - pass host')
        parser.add_argument('-a', '--action',dest='action',help='required - action  ')
        parser.add_argument('-f', '--file',dest='file',help='optional - pass shell script location to execute ')
        parser.add_argument('-b', '--backup_type',dest='backup_type',help='required - backup_type ')
        parser.add_argument('-p', '--pid',dest='pid',help='optional - pid')
        args = parser.parse_args() 
        if not args.host:
            parser.error('--host option is required')
        # if not args.dbname:
        #     parser.error('--dbname option is required')
        if not args.action:
            parser.error('--action option ')
        # if not args.backup_type.lower():
        #     parser.error('--backup_type')
        return(args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.error(message)

def main():
    username = getpass.getuser()
    if username != 'oracle':
        sys.exit(1)
    else:
        options = parse_opts()
        dbname = options.dbname
        backup_type = options.backup_type
        action = options.action
        host = options.host
        pid = options.pid
        file = options.file
        output = process_tasks(dbname,backup_type,action,host,pid,file)
        print(output)
        

if __name__ == "__main__":
    main()
