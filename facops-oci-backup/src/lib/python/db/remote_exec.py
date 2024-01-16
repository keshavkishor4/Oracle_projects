#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      commonutils.py
    DESCRIPTION
      implement all common methods
    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
"""
#### imports start here ##############################
import optparse
import time
import paramiko
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
        apscom.info(message)

def connect_remote_exec(host,dbname,backup_option):
    try:
        running_process=''
#       rman_cmd = 'sh {0}/bin/rman_oss.sh --dbname={1} -b {2} > /dev/null 2>&1 &'.format(BASE_DIR, dbname, backup_option)
        env_type = commonutils.get_db_env_type(dbname)
        tag=globalvariables.backup_opts[backup_option][env_type]["tag"]
        retention_days=globalvariables.backup_opts[backup_option][env_type]["retention"]
        rman_cmd = '{0}/utils/db/scripts/shell/remote_actions.sh backup {1} {2} {3} {4}'.format(BASE_DIR, dbname, backup_option,tag,retention_days)
        [stdout, stderr]=exec_on_remote(host,rman_cmd)
        if stderr:
            running_process=''
        else:
            running_process=stdout
        print(running_process)
        return True
    except Exception as e:
        #traceback.print_exc()
        message = "Failed to connect{0},{1}!\n{2}".format(host,sys.exc_info()[1:2], e)
        apscom.info(message)
        return False

def verify_rman_status(host,pid=None,dbname=None):
    try:
        if pid:
            # cmd = 'ps -ef|grep {0}|grep -v grep|wc -l'.format(pid)
            #cmd = 'ps -ax | grep -v grep | grep -w  {0}|wc -l'.format(pid)
            cmd  = '{0}/utils/db/scripts/shell/remote_actions.sh check {1}'.format(BASE_DIR, pid)
        elif dbname:
            # cmd = 'pgrep -f "/opt/faops/spe/ocifabackup/bin/rman_oss.sh --dbname={0} -b {1}"'.format(dbname,"db_to_reco_db_arch_to_oss")
            cmd = "ps -ax | grep -w 'rman_oss.py --dbname={0} -b {1}' | grep -v '/usr/bin/script'  | grep -v grep | awk '{{print $1}}' ".format(dbname,"db_to_reco_db_arch_to_oss")
        else:
            cmd = "ps -ef|grep rman_oss.py|grep -v grep | grep -v /usr/bin/script |awk '{{print $2}}'"

        [stdout, stderr]=exec_on_remote(host,cmd)
        if not stderr:
            print(stdout)
            return True
        else:
            print('')
            return False
    except Exception as e:
        message = "Failed to connect{0},{1}!\n{2}".format(host,sys.exc_info()[1:2], e)
        apscom.info(message)

def check_conflicts(host,dbname,backup_type):
    try:
        cmd = 'ps -ef|grep {0}|grep -v grep |grep {1}|grep rman_oss.py|wc -l'.format(dbname,backup_type)
        [stdout, stderr] = exec_on_remote(host, cmd)
        if not stderr:
            print(stdout)
            return True
        else:
            print('')
            return False
    except Exception as e:
        message = "Failed to connect{0},{1}!\n{2}".format(host,sys.exc_info()[1:2], e)
        apscom.info(message)
        
def remote_exec(host):
    try:
        ver_str = "rpm -qa|grep -m 1 -i backup|uniq"
        [stdout, stderr] = exec_on_remote(host, ver_str)
        if not stderr:
            print(stdout)
            return True
        else:
            print('')
            return False
    except Exception as e:
        message = "Failed to connect{0},{1}!\n{2}".format(host,sys.exc_info()[1:2], e)
        apscom.info(message)
        return False
def parse_opts():
    try:
        parser = optparse.OptionParser(version="%prog 1.0")
        parser.add_option('--type', action='store', dest='type',help='Specify the action.')
        parser.add_option('--host', action='store', dest='host',default='')
        parser.add_option('--dbname', action='store', dest='dbname', help='Specify the action.')
        parser.add_option('-b', action='store', dest='backup',help='Specify the action.')
        parser.add_option('--pid', action='store', dest='pid', help='Specify the action.')
        (opts, args) = parser.parse_args()
        return (opts, args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[1:2])
        apscom.error(message)
        sys.exit(1)
def main():
    try:
        (options, args) = parse_opts()
        type = options.type
        host = options.host
        dbname=options.dbname
        backup_option=options.backup
        pid = options.pid
        if type == "verify_ols_connect":
            remote_exec(host)
        elif type == "remote":
            connect_remote_exec(host,dbname,backup_option)
        elif type == "verify_rman_status":
            verify_rman_status(host,pid,dbname)
        elif type == "check_conflicts":
            check_conflicts(host, dbname, backup_option)
        else:
            message = "please enter options!"
            apscom.error(message)
            sys.exit(1)
    except Exception as e:
        message = "Failed to connect {0}!\n{1}".format(sys.exc_info()[1:2], e)
        apscom.info(message)
        return False
def execute_command(host,command):
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(host, timeout=60)
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        channel.exec_command(command)
        ssh_client.close()
        print("True")
    except Exception as e:
        message = "Failed to connect {0},{1}!\n{2}".format(host,sys.exc_info()[1:2], e)
        apscom.info(message)

if __name__ == "__main__":
    main()
