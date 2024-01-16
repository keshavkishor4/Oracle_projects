#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import paramiko
import sys
import oci
import errno
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import globalvariables, test_configs, apscom

wallet_config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
private_key_path = globalvariables.PRIVATE_KEY_PATH_FILES
python_path = globalvariables.BASE_DIR+"/utils/python3/el7/bin/python"
script_path = globalvariables.BASE_DIR + "/lib/python/common/test_wallet_temp.py"
myhost = globalvariables.HOST_NAME
def client_ssh(node):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(node)
    sftp = ssh_client.open_sftp()
    temp_path = sftp.stat(script_path)
    if not temp_path:
        sftp.put(script_path,script_path,confirm=True)
    path = sftp.stat(python_path)
    sftp.close()
    if path:
        cmd_str = "source "+ globalvariables.BASE_DIR + "/lib/python/common/setpyenv.sh;"+python_path + " " + script_path
        stdin, stdout, stderr = ssh_client.exec_command(cmd_str)
        param=stdout.readlines()[-1].strip('\n').split(':')
    ssh_client.close()
    return param
def copy_ssh(file_path,node):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(node, timeout = 60)
    sftp = ssh_client.open_sftp()
    sftp.put(file_path,file_path,confirm=True)
    sftp.close()
def copy_files(file_push,node):
    if file_push == "config_file":
        try:
            copy_ssh(wallet_config_file,node)
        except Exception as e:
            if e.errno != errno.ENOENT:
                # ignore "No such file or directory", but re-raise other errors
                message = "[copy_ssh]: failed to copy\n{0}{1}".format(sys.exc_info()[1:2],e)
                apscom.warn(message)
    elif file_push == "Private_file":
        try:
            for private_key_file in private_key_path:
                if os.path.exists(private_key_file):
                    copy_ssh(private_key_file,node)
        except Exception as e:
            if e.errno != errno.ENOENT:
                # ignore "No such file or directory", but re-raise other errors
                message = "[copy_ssh]: failed to copy\n{0}{1}".format(sys.exc_info()[1:2],e)
                apscom.warn(message)
    elif file_push == "config_key":
        try:
            copy_ssh(wallet_config_file,node)
            for private_key_file in private_key_path:
                if os.path.exists(private_key_file):
                    copy_ssh(private_key_file,node)
        except Exception as e:
            if e.errno != errno.ENOENT:
                # ignore "No such file or directory", but re-raise other errors
                message = "[copy_ssh]: failed to copy\n{0}{1}".format(sys.exc_info()[1:2],e)
                apscom.warn(message)
def wallet_files_checks():
    #wallet_config_file="/opt/faops/spe/ocifabackup/config/wallet/config-oci-template.json"
    if os.path.exists(wallet_config_file):
        try:
            with open(wallet_config_file) as f:
                wallet_config_data = json.load(f)
            #
            private_key_path = wallet_config_data["private_key_path"]
            if private_key_path != "":
                #check private key path exists
                if os.path.exists(private_key_path):
                    status = test_configs.get_tenancy_info()
                    if status:
                        return True,'Good'
                    if not status:
                        file_push = "config_key"
                        return False,file_push
                else:
                    file_push = "Private_file"
                    return False,file_push
            else:
                file_push = "config_file"
                return False,file_push
        except Exception as e:
            print(e) 
    else:
        file_push = "config_file"
        return False,file_push
def main():
    node = sys.argv[1]
    if node==myhost:
        status,File=wallet_files_checks()
        if status==True:
            return status
        else:
            print(status,File)
            return status
    else:
        for i in range(3):
            param=client_ssh(node)
            if param[0]=='False':
                file_push = param[1]
                copy_files(file_push,node)
                print(param[0])
            else:
                print(param[0])
                return param[0]
                #break
if __name__ == "__main__":
    main() 