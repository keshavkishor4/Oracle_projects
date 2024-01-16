#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      commonutils.py
    DESCRIPTION
      implement all common methods
    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy     07/29/20 - initial version (code refactoring)
    Zakki ahmed         10/03/21 - Bug 33372938  
    Vipin Azad          12/16/22 - BUG 34781623
    Vipin Azad          08/10/23 - Jira FUSIONSRE-8245
"""
#### imports start here ##############################
from email import message
import requests
import urllib3
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter, Retry
import csv
import socket
import fileinput
import getpass
import glob
import hashlib
import re
import shlex
import shutil
import sys
import os
import tarfile
import time
import subprocess
import fcntl
import traceback
import OpenSSL
from datetime import datetime, timedelta
from time import gmtime, strftime
from cffi.backend_ctypes import xrange
import psutil
import paramiko
import re
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common/")
import instance_metadata
import ociSDK
import json
import globalvariables
import apscom
from Crypto.PublicKey import RSA
from datetime import timedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import post_backup_metadata
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
#import update_password_file
from datetime import datetime

#### imports end here ##############################

class colors:
    reset = '\033[0m'
    red = '\033[31m'
    green = '\033[32m'
    orange = '\033[33m'
    blue = '\033[34m'
    yellow = '\033[93m'


def get_region_env():
    # esya11-wmsbn5.poddbfrontend1.prd01syd01lcm01.oraclevcn.com
    try:
        FA_ENV = ""
        region_key = ""
        if (instance_metadata.ins_metadata().inst_metadata["regionInfo"]["regionKey"]):
            region_key = instance_metadata.ins_metadata(
            ).inst_metadata["regionInfo"]["regionKey"].lower().strip()

        env_types = ['dev', 'ppd', 'prd']
        fqdn_split = socket.getfqdn().split('.')
        for val in fqdn_split:
            for env in env_types:
                if (env in val) and ('lcm' in val):
                    FA_ENV = env.strip()
                    break
        # if FA_ENV is empty
        if not FA_ENV:
            for env in env_types:
                if env in fqdn_split[2]:
                    FA_ENV = env.strip()
                    break
        return FA_ENV
    except Exception as e:
        message = "Failed on get_region_env  {0}!\n{1}".format(sys.exc_info()[
                                                               1:2], e)
        apscom.warn(message)
        raise Exception(message)


def load_oci_config():
    # oci_config_file="../config/mt/config-oci_v2.json"  # Change it when finalized
    oci_config_file = BASE_DIR+"/config/mt/config-oci_v2.json"
    try:
        with open(oci_config_file, 'r') as ocf:
            oci_config_data = json.load(ocf)
            env = get_region_env()
            if not env:
                message = "Error: unable to determine the env, check config-oci_v2.json!"
                print(message)
                apscom.warn(message)

            # get values
            if (instance_metadata.ins_metadata().realmKey):
                realmKey = instance_metadata.ins_metadata().realmKey
            else:
                realmKey = "oc1"
            if not oci_config_data["backup_compartment_ocid"][realmKey][env]:
                message = "Error: backup_compartment_ocid for {0} is emtpy,review config-oci_v2.json".format(
                    env)
                print(message)
                apscom.warn(message)
            if not oci_config_data["backup_compartment_bn"][env]:
                message = "Error: backup_compartment_bn for {0} is emtpy,review config-oci_v2.json".format(
                    env)
                print(message)
                apscom.warn(message)
            # Set the values
            bc_ocid = oci_config_data["backup_compartment_ocid"][realmKey][env]
            bc_bn = oci_config_data["backup_compartment_bn"][env]
            ocf.close()
            return bc_ocid, bc_bn

    except Exception as e:
        message = "Failed to load oci_config!\n{0}".format(e)
        apscom.warn(message)
        print(message)
        raise Exception(message)

def generate_fingerprint(private_key_path=None, key_file_obj=None,
                         passphrase=None):
    """
    Returns the fingerprint of the public portion of an RSA key as a
    47-character string (32 characters separated every 2 characters by a ':').
    The fingerprint is computed using the MD5 (hex) digest of the DER-encoded
    RSA public key.
    """
    try:
        privkey = get_rsa_key(key_location=private_key_path, key_file_obj=key_file_obj,
                              passphrase=passphrase, use_pycrypto=True)
        pubkey = privkey.publickey()
        md5digest = hashlib.md5(pubkey.exportKey('DER')).hexdigest()
        fingerprint = insert_char_every_n_chars(md5digest, ':', 2)
        return fingerprint
    except Exception as e:
        message = "{3}Failed to generate fingerprint for {0}!\n{1}!\n{2}".format(
            private_key_path, sys.exc_info()[1:2], e,globalvariables.RED)
        apscom.warn(message)


def insert_char_every_n_chars(string, char='\n', every=64):
    return char.join(
        string[i:i + every] for i in xrange(0, len(string), every))


def get_rsa_key(key_location=None, key_file_obj=None, passphrase=None,
                use_pycrypto=False):
    key_fobj = key_file_obj or open(key_location)
    try:
        if use_pycrypto:
            key = RSA.importKey(key_fobj.read())
        else:
            key = paramiko.RSAKey.from_private_key(key_fobj,
                                                   password='')
        return key
    except Exception as e:
        message = "Invalid RSA private key file or missing passphrase: {0}!\n{1}!\n{2}".format(
            key_location, sys.exc_info()[1:2], e)
        apscom.warn(message)


def list_objects_curl(oss_namespace, oss_bucket, oci_wallet_config, prefix=""):
    try:
        oci_config_file = open(oci_wallet_config, 'r')
        oci_config = json.load(oci_config_file)
        user_ocid = oci_config["user_ocid"]
        private_key_path = oci_config["private_key_path"]
        fingerprint = generate_fingerprint(oci_config["private_key_path"])
        tenancy_ocid = oci_config["tenancy_ocid"]
        key_id = tenancy_ocid + "/" + user_ocid + "/" + fingerprint
        globalvariables.OCI_OSS_HOST = globalvariables.OCI_OSS_HOST + "." + \
            instance_metadata.ins_metadata().region + ".oraclecloud.com"
        api_str = "/n/{0}/b/{1}/o?fields=name&prefix={2}".format(
            oss_namespace, oss_bucket, prefix)
        out = oci_curl(key_id, private_key_path,
                       globalvariables.OCI_OSS_HOST, "GET", api_str)
        oci_config_file.close()
        return out
    except Exception as e:
        message = "Failed to list object url: {0}!\n{1}!\n{2}".format(
            oci_wallet_config, sys.exc_info()[1:2], e)
        apscom.warn(message)


def oci_curl(key_id, private_key_path, host, method, api_str):
    """ Send REST API request to oci
    Args:
        key_id (str): $tenancyId/$authUserId/$keyFingerprint
        private_key_path (str): path of private key to do REST API call
        host (str): hostname of API endpoint, e.g. "filestorage.us-phoenix-1.oraclecloud.com"
        method (str): GET/DELETE/HEAD/POST/PUT
        api_str  (str): oci_curl.sh <key-id> <private-key-path> <host> <method> "api_str", e.g. "/20171215/fileSystems"
    Returns:
        str: output string if succeeded
    Raises:
        Exception: run_cmd errors
    """
    try:
        cmd = [globalvariables.OCI_CURL_TOOL,
               key_id, private_key_path, host, method]
        api_str_list = api_str.split()
        cmd.extend(api_str_list)
        out = apscom.run_cmd(cmd, timeout_secs=36000)
        return out
    except Exception:
        msg = "Failed to send {0} request {1} to {2}!\n{3}".format(
            method, api_str, host, sys.exc_info()[1:2])
        apscom.warn(msg)
        raise Exception(msg)


def cleanup_dir(dir_path):
    try:

        if os.path.exists(dir_path):
            
            f = open(globalvariables.RETENTION_POLICY_PATH_DEFAULT, 'r')
            retention_policy = json.load(f)
            f.close()
            retention_days = retention_policy["backup_to_local"]
            message = "clearing files older than {1} days in {0}".format(
                dir_path,retention_days)
            apscom.info(message)
            for path in os.listdir(dir_path):
                full_path = dir_path + "/" + path
                if (time.time() - os.path.getmtime(full_path)) > int(retention_days)*86400:
                    message = "deleting file {0}".format(full_path)
                    apscom.info(message)
                    if os.path.islink(full_path):
                        os.unlink(full_path)
                    elif os.path.isfile(full_path):
                        os.remove(full_path)
                    elif os.path.isdir(full_path):
                        shutil.rmtree(full_path)
        else:
            pass

    except Exception as e:
        message = "Failed to cleanup {0}!\n{1}!{2}".format(
            dir_path, sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)


def get_rpm_ver():
    rpm_ver = ""
    try:
        ver_str = "rpm -qa|grep -m 1 -i backup|uniq"
        [rpm_ver, returncode, stderror] = execute_shell(ver_str)
        return rpm_ver
    except Exception as e:
        message = "Failed to get backup rpm version!\n{0}{1}".format(sys.exc_info()[
                                                                     1:2], e)
        apscom.info(message)


def get_os_ver():
    os_ver = ""
    try:
        os_ver = execute_shell("cat /etc/redhat-release")[0].strip()
        return os_ver
    except Exception as e:
        message = "failed to get os version"
        apscom.warn(message)


def backup_lock_exit():
    try:
        cur_pid = str(os.getpid())
        if os.path.isfile(globalvariables.BACKUP_LOCK_FILE):
            now = datetime.now()
            totsec = 6 * 60 * 60
            file_ctime = os.path.getctime(globalvariables.BACKUP_LOCK_FILE)
            file_time = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(file_ctime))
            file_time2 = datetime.strptime(file_time, '%Y-%m-%d %H:%M:%S')
            t4 = datetime(int(now.strftime('%Y')), int(now.strftime('%m')), int(now.strftime('%d')),
                          int(now.strftime('%H')),
                          int(now.strftime('%M')))
            t5 = datetime(int(file_time2.strftime('%Y')), int(file_time2.strftime('%m')),
                          int(file_time2.strftime('%d')), int(
                              file_time2.strftime('%H')),
                          int(file_time2.strftime('%M')))
            tot_sec = timedelta.total_seconds(t4 - t5)
            if (tot_sec > totsec):
                os.remove(globalvariables.BACKUP_LOCK_FILE)
            else:
                flock_file = open(globalvariables.BACKUP_LOCK_FILE, 'r')
                flock_pid = flock_file.read().strip()
                flock_file.close()
                if flock_pid == cur_pid:
                    os.remove(globalvariables.BACKUP_LOCK_FILE)
    except Exception as e:
        message = "Failed to exit backup lock!\n{0}{1}".format(sys.exc_info()[
                                                               1:2], e)
        apscom.warn(message)
        raise Exception(message)


def backup_lock_enter():
    try:
        global flock_file

        if os.path.isfile(globalvariables.BACKUP_LOCK_FILE):
            flock_file = open(globalvariables.BACKUP_LOCK_FILE, 'r')
            flock_pid = flock_file.read().strip()
            flock_file.close()

            pid_file = "/proc/" + flock_pid
            if not os.path.exists(pid_file):
                message = "Process {0} not exist any more, removing the lock file {1} ...".format(flock_pid,
                                                                                                  globalvariables.BACKUP_LOCK_FILE)
                apscom.info(message)
                os.remove(globalvariables.BACKUP_LOCK_FILE)
            else:
                message = "Another backup process {0} is in progress, existing ...".format(
                    flock_pid)
                apscom.warn(message)
                return globalvariables.BACKUP_FAILED

        flock_file = open(globalvariables.BACKUP_LOCK_FILE, 'w')
        fcntl.flock(flock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        flock_file.write(str(os.getpid()))
        flock_file.flush()
        flock_file.close()

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to enter lock for backup process!{0}".format(e)
        apscom.warn(message)
        raise Exception(message)


def get_top_dir_perm(path_list):
    try:
        dir_perm = {}

        for path in path_list:
            top_dir = "/" + path.split("/")[1]
            if top_dir not in dir_perm.keys():
                # Get the last 4 digit of st_mode
                stat = os.stat(top_dir)
                perm = oct(stat.st_mode)[-4:]
                dir_perm[top_dir] = perm
        return dir_perm

    except Exception as e:
        message = "Failed to get permission of top dir!\n{0}{1}".format(sys.exc_info()[
                                                                        1:2], e)
        apscom.warn(message)
        raise Exception(message)


def split_files(file_path, split_name):
    try:
        file_dir = os.path.dirname(os.path.realpath(file_path))
        file_size_G = int(os.path.getsize(file_path)/1024/1024/1024)

        num_suffix = 0
        while True:
            file_size_G = int(file_size_G/10)
            num_suffix = num_suffix + 1
            if file_size_G == 0:
                break

        os.chdir(file_dir)
        cmd = ["split", "-b", "1G", "-a",
               "{0}".format(num_suffix), "-d", file_path, "{0}_".format(split_name)]
        out = apscom.run_cmd(cmd, timeout_secs=36000)

        file_parts = "{0}/{1}_*".format(file_dir, split_name)
        file_list = glob.glob(file_parts)

        return file_list

    except Exception as e:
        message = "Failed to split files!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)


def is_file_older_than(file, delta):
    cutoff = datetime.utcnow() - delta
    mtime = datetime.utcfromtimestamp(os.path.getmtime(file))
    if mtime < cutoff:
        return True
    return False


def get_object_storage_config(oci_config_file):
    try:
        with open(oci_config_file, 'r') as config_file:
            oci_config = json.load(config_file)
        fingerprint = generate_fingerprint(oci_config["private_key_path"])
        config = {
            "user": oci_config["user_ocid"],
            "key_file": oci_config["private_key_path"],
            "fingerprint": fingerprint,
            "tenancy": oci_config["tenancy_ocid"],
            "region": oci_config["region"]
        }
        config_file.close()
        return config
    except Exception as e:
        message = "Failed to generate config!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)

def get_db_env_type(dbname):
    env_type=None
    try:
        DB_SHAPE=get_db_query_data(dbname,'DB_SHAPE')
        #if  '_TEST' not in FUSION_PDB and '_DEV' not in FUSION_PDB and FUSION_PDB != "":
        fusion_pdb =get_db_query_data(dbname,'FUSION_PDB')
        
        if "em" in DB_SHAPE:
            env_type = "em_exa"
        elif "dbaas" in DB_SHAPE:
            env_type = "dbaas"
        elif not fusion_pdb:
            env_type = "non_fa"
        elif  '_STAGE' in DB_SHAPE and DB_SHAPE != "":
           #return True
           env_type = "stage"
        elif '_PROD' in DB_SHAPE: 
           #return False
           DR_ENABLED_CHK=get_db_query_data(dbname,'DR_ENABLED_CHK')
           if DR_ENABLED_CHK == 0:
                env_type = 'prod'
           else:
                env_type = 'prod_dr_enabled'
        else:
            message = "Envrionment has been identified as {0}".format(env_type)
            apscom.warn(message)        
        return env_type        
    except Exception as e:
        message = "Failed to identify environment type !\n{0}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        #return False
        return env_type 

def validateJSON(jsonData):
    try:
        message = json.loads(jsonData)
        if ("code" in message):
            if("ObjectNotFound" in message["code"]):
                apscom.warn(message["message"])
                raise Exception(message)
    except Exception as err:
        return False
    return True


def execute_shell(command):
    # ensure environment is already sourced, execute shell does not source .env files
    try:
        err_msg = ""
        inst_meta = instance_metadata.ins_metadata()
        inst_metadata = inst_meta.get_inst_metadata()
        if "dbSystemShape" in inst_metadata["metadata"]:
            system_type = "EXA"
        else:
            system_type = "MT"
        com_list = command.split('|')
        lstPopen = []

        for i in range(0, len(com_list)):
            if i == 0:
                lstPopen = [subprocess.Popen(shlex.split(
                    com_list[0]), stdout=subprocess.PIPE, stderr=subprocess.PIPE)]
            else:
                lstPopen.append(subprocess.Popen(shlex.split(
                    com_list[i]), stdin=lstPopen[i-1].stdout, stdout=subprocess.PIPE))
                lstPopen[i-1].stdout.close()

        final_pid = lstPopen[-1].pid
        if system_type == 'EXA':
            if not os.path.exists(globalvariables.PROCESS_LIST_FILE_LOCATION):
                with open(globalvariables.PROCESS_LIST_FILE_LOCATION, 'w') as fp:
                    shutil.chown(
                        globalvariables.PROCESS_LIST_FILE_LOCATION, "oracle", "oinstall")
                    pass
            with open(globalvariables.PROCESS_LIST_FILE_LOCATION, 'a') as plf:
                if "/opt/faops/spe/ocifabackup/config/db/decrypt" in command:
                    command=command.split(" ")[0]
                plf.write('{0}:"{1}"\n'.format(final_pid, command))

        str_process_info, std_error = lstPopen[-1].communicate()
        return_code = lstPopen[-1].returncode
        return [str_process_info.decode('utf-8').rstrip(), return_code, std_error]
    except Exception as e:
        message = "Could not run execute_shell !\n{0}{1}".format(sys.exc_info()[
                                                                 1:2], e)
        apscom.warn(message)
        raise Exception(message)

def get_oracle_dbsid(dbname):
    try:
        # phxcf:epxa31-orpsd1.poddbfrontend3.dev01phx01lcm01.oraclevcn.com:phxcf1:y
        if os.path.exists(globalvariables.pod_info_file):
            dbsid_file=globalvariables.pod_info_file
        else:
            dbsid_file=globalvariables.pod_wallet_file
        with open(dbsid_file, "r") as all_pod:
            lines = all_pod.readlines()
        for line in lines:
            ora_db_name, ora_db_host, ora_db_sid, ora_db_flag = line.split(
                ":")
            if dbname == ora_db_name:
                #dbsid = line.split(":")[2]
                dbsid = ora_db_sid
                # apscom.info("********** {0} ***********".format(dbsid))
                return(dbsid)
    except Exception as e:
        message = "Failed to get get_oracle_dbsid !\n{0}{1}".format(sys.exc_info()[
                                                                    1:2], e)
        apscom.warn(message)


# Bug 33372938
def get_oracle_home_using_os(dbsid, dbname=None, debug=None):
    try:
        if debug == "yes":
            message = "{1}Debug: getting ORACLE_HOME for {0}".format(
                dbsid, globalvariables.GREEN)
            apscom.info(message)
        username = getpass.getuser()
        if username == 'oracle':
            # cmd = "cat /home/oracle/" + dbname + ".env | grep ORACLE_HOME|cut -d= -f2|cut -d\";\" -f 1| tr -d \"\""
            # oracle_home = execute_shell(cmd)[0]
            oracle_home = os.environ['ORACLE_HOME']
        else:
            out = "ps -eawf|grep smon|grep ^oracle|grep {0}|grep -v grep|grep -v ASM|grep -v perl|awk '{{print $2\":\"$NF}}'".format(
                dbsid)
            p = out.strip()
            #

            proc_id = execute_shell(p)[0]
            if debug == "yes":
                message = "{1}Debug: getting proc_id for {0}".format(
                    proc_id, globalvariables.GREEN)
                apscom.info(message)

            v = "echo {0}|cut -d\":\" -f1".format(proc_id)
            #
            v_proc = execute_shell(v.strip())[0]
            if debug == "yes":
                message = "{1}Debug: getting proc_id for {0}".format(
                    v_proc, globalvariables.GREEN)
                apscom.info(message)
            #
            h = "strings /proc/{0}/environ | grep ORACLE_HOME|tr -d [[:space:]]".format(
                v_proc)
            oracle_home = execute_shell(h.strip())[0]
            if debug == "yes":
                message = "{1}Debug: getting ORACLE_HOME from environ for {0}".format(
                    h, globalvariables.GREEN)
                apscom.info(message)
            #
            h = "echo {0}|cut -d\"=\" -f2".format(oracle_home)
            oracle_home = execute_shell(h.strip())[0]
            if debug == "yes":
                message = "{1}Debug: getting ORACLE_HOME from environ for {0}".format(
                    h, globalvariables.GREEN)
                apscom.info(message)

        return str(oracle_home)
    except Exception as e:
        message = "Failed to get oracle home {0} {1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        # debug
        message = "stack trace {0}".format(traceback.print_exc())
        apscom.warn(message)
        # raise Exception(message)

# Bug 33372938


def get_oracle_home(dbsid, dbname=None, debug=None):
    try:
        # try getting from get_oracle_home_using_os
        # debug="yes"
        if debug == "yes":
            message = "{1}Debug: getting ORACLE_HOME for {0}".format(
                dbsid, globalvariables.GREEN)
            apscom.info(message)
        #
        # ORACLE_HOME = get_oracle_home_using_os(dbsid,debug)
        crsctl_json = globalvariables.EXALOGS_PATH + '/crsctl_output.json'
        with open(crsctl_json) as json_file:
            json_data = json.load(json_file)
            for key in json_data:
                db_sid_list = json_data[key]['db_sid_list']
                if dbsid in db_sid_list:
                    unique_sids = db_sid_list.split(',')
                    for unique_sid in unique_sids:
                        if dbsid == unique_sid:
                            db_uni_name = json_data[key]['db_unique_name']
                            db_home = json_data[key]['db_home']
                            return str(db_home)
    except Exception as e:
        traceback.print_exc()
        message = "Failed to get oracle home for {2}!\n{0}{1}".format(sys.exc_info()[
                                                                      1:2], e, dbsid)
        apscom.warn(message)
        # debug
        message = "stack trace {0}".format(traceback.print_exc())
        apscom.warn(message)
        #
        raise Exception(message)


def check_conflicts(b_type, db_name='""', file_name=None):
    try:
        p = "ps -ef|grep {0}|grep {1}|grep {2}|grep -v ssh |grep -v /usr/bin/script|grep -v grep|grep -v $$|wc -l".\
            format(file_name, b_type, db_name)
        PROCS = execute_shell(p)[0]
        #cmd = 'ps -ef | grep -i rman_wrapper.py | grep -v grep'
        # num_of_pro=execute_shell(cmd)[0]

        if int(PROCS) > 1:
            pid_cmd = "ps -ef|grep {0}|grep {1}|grep {2}|grep -v ssh |grep -v /usr/bin/script|grep -v grep|grep -v $$". \
                format(file_name, b_type, db_name)
            PID = execute_shell(pid_cmd)[0]
            message = "Error: the script {0} already running for {1}\n{2}.. PID details below \n ====\n{3} \n===\n".format(
                file_name, b_type, PROCS, PID)
            apscom.warn(message)
            raise Exception(message)
    except Exception as e:
        message = "Check conflicts check_conflicts failed\n{0}{1}".format(sys.exc_info()[
                                                                          1:2], e)
        # apscom.warn(message)
        raise Exception(message)

#check_conflicts_v2 created to manage resume backup situation 
def check_conflicts_v2(b_type, db_name='""', file_name=None,DB_Full_Status=None,DB_Archive_status=None):
    try:
        p = "ps -ef|grep {0}|grep {1}|grep {2}|grep -v ssh |grep -v /usr/bin/script|grep -v grep|grep -v $$|wc -l".\
            format(file_name, b_type, db_name)
        PROCS = execute_shell(p)[0]
        #cmd = 'ps -ef | grep -i rman_wrapper.py | grep -v grep'
        # num_of_pro=execute_shell(cmd)[0]

        if b_type == "archivelog_to_oss" and DB_Archive_status == 0:
            PROCS = 0

        if int(PROCS) > 1:
            pid_cmd = "ps -ef|grep {0}|grep {1}|grep {2}|grep -v ssh |grep -v /usr/bin/script|grep -v grep|grep -v $$". \
                format(file_name, b_type, db_name)
            PID = execute_shell(pid_cmd)[0]
            message = "Error: the script {0} already running for {1}\n{2}.. PID details below \n ====\n{3} \n===\n".format(
                file_name, b_type, PROCS, PID)
            apscom.warn(message)
            raise Exception(message)
    except Exception as e:
        message = "Check conflicts check_conflicts failed\n{0}{1}".format(sys.exc_info()[
                                                                          1:2], e)
        # apscom.warn(message)
        raise Exception(message)

def check_conflicts_other_node(b_type, db_name='', file_name=None):
    try:
        # host_name=get_next_db_node(db_name)
        db_uniq_name = db_name
        running_db_odd_hosts, running_db_even_hosts = get_dbname_db_nodes(
            db_name, db_uniq_name)
        min_odd_node_name = min(
            running_db_odd_hosts, key=lambda odd_node: odd_node['running_db_node_num'])
        min_even_node_name = min(
            running_db_even_hosts, key=lambda even_node: even_node['running_db_node_num'])
        host_name = min_even_node_name["running_db_node_name"]
        #
        cmd = "python {0}/remote_exec.py --type=check_conflicts --host={1} --dbname={2} -b {3}".format(
            globalvariables.QUERY_POOL_PATH, host_name, db_name, b_type)

        [data, ret_code, stderror] = execute_shell(cmd)

        if ret_code == 0 and int(data) > 0:
            message = "Error: the script {0} already running for {1} on {2}".format(
                file_name, b_type, host_name)
            apscom.warn(message)
            raise Exception(message)
    except Exception as e:
        message = "Check conflicts check_conflicts_other_node failed\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def get_gridhome():
    try:
        grid_home = None

        if os.path.isfile(globalvariables.OLR_LOC):
            f = open(globalvariables.OLR_LOC, "r")
            for line in f:
                matched = re.compile(
                    "^crs_home=(?P<grid_home>\S+)").match(line)
                if matched:
                    grid_home = matched.group('grid_home')
                    f.close()
                    return grid_home
            f.close()

        # If not found in olr.loc
        if os.path.isfile(globalvariables.ORATAB):
            f = open(globalvariables.ORATAB, "r")
            for line in f:
                matched = re.compile(
                    "^\+ASM\d\:(?P<grid_home>\S+):[YyNn]").match(line)
                if matched:
                    grid_home = matched.group('grid_home')
                    f.close()
                    return grid_home
            f.close()
        return grid_home
    except Exception as e:
        message = "Failed to get grid home!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        # apscom.warn(message)
        raise Exception(message)
# fetches unique db names not actual db names DB_UNIQUE_NAME


def get_dbname_list():
    try:
        dbname_list = []

        grid_home = get_gridhome()
        if not grid_home:
            message = "Could not get grid home!"
            apscom.warn(message)
            return dbname_list

        srvctl_tool = grid_home + "/bin/srvctl"
        cmd = [srvctl_tool, 'config', 'database', '-v']
        out = apscom.run_cmd(cmd)

        for line in out.splitlines():
            dbname = line.strip().split()[0]
            dbname_list.append(dbname.decode('utf-8'))

        return dbname_list

    except Exception as e:
        message = "Failed to get dbname list!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def get_db_query_data(dbname, key):
    try:
        dbsid = get_oracle_dbsid(dbname)
        query_file = "{0}/{1}/{2}_{1}_query.json".format(
            globalvariables.DB_BACKUP_LOG_PATH, dbsid, globalvariables.HOST_NAME)
        with open(query_file, 'r') as fp:
            data = json.load(fp)
            return(data[key])
    except Exception as e:
        message = "Failed to get get_db_query_data !\n{0}{1} check query.json - {2}".format(sys.exc_info()[
                                                                     1:2], e,query_file)
        apscom.warn(message)


def get_crsctl_data(dbname, key):
    try:
        crsctl_json = "{0}/crsctl_output.json".format(
            globalvariables.EXALOGS_PATH)
        with open(crsctl_json, 'r') as fp:
            data = json.load(fp)
            return(data[dbname][key])
    except Exception as e:
        message = "Failed to get get_db_query_data !\n{0}{1}".format(sys.exc_info()[
                                                                     1:2], e)
        apscom.warn(message)


def gen_crsctl_dump():
    try:
        # Take backup
        now = datetime.now()
        ts = now.strftime('%Y%m%d_%H%M%S')
        crsctl_json = "{0}/crsctl_output.json".format(
            globalvariables.EXALOGS_PATH)
        crsctl_json_bkp = "{0}/crsctl_output.json_bkp_{1}".format(
            globalvariables.EXALOGS_PATH, ts)
        #
        if os.path.exists(crsctl_json):
            shutil.copy(crsctl_json, crsctl_json_bkp)
        else:
            message = "{0} does not exist ".format(crsctl_json)
            apscom.warn(message)
            # raise Exception(message)
        #
        crsctl_run = "/usr/bin/timeout 300 {0}/gen_crs_db_inv.sh".format(
            globalvariables.DB_SHELL_SCRIPT)
        [crsctl_run_out, returncode, stderror] = execute_shell(crsctl_run)

        if returncode != 0:
            message = "Failed to run crsctl!\n{0} with error {1}".format(
                str(returncode), stderror.decode('utf-8'))
            if (os.path.exists(crsctl_json_bkp)):
                message = "crsctl command timed out waiting for 300 seconds with {0}, using previous crsctl json {1} ".format(
                    str(returncode), crsctl_json_bkp)
                shutil.copy(crsctl_json_bkp, crsctl_json)
                apscom.warn(message)
            else:
                raise Exception(message)
        else:
            message = "successfully generated {0}".format(
                globalvariables.EXALOGS_PATH + '/crsctl_output.json')
            apscom.info(message)

    except Exception as e:
        message = "Failed to run crsctl output!\n{0}{1}".format(sys.exc_info()[
                                                                1:2], e)
        raise Exception(message)


def db_backup_lock_exit(dbname):
    try:
        cur_pid = str(os.getpid())
        backup_lock = "{0}/lock.{1}".format(
            globalvariables.DB_BACKUP_LOG_PATH, dbname)

        if os.path.isfile(backup_lock):
            flock_file = open(backup_lock, 'r')
            flock_pid = flock_file.read().strip()
            flock_file.close()
            if flock_pid == cur_pid:
                os.remove(backup_lock)

    except Exception as e:
        message = "Failed to exit backup lock!\n{0}{1}".format(sys.exc_info()[
                                                               1:2], e)
        apscom.warn(message)
        raise Exception(message)


def db_backup_lock_enter(dbname):
    try:
        global flock_file
        backup_lock = "{0}/lock.{1}".format(
            globalvariables.DB_BACKUP_LOG_PATH, dbname)
        exclusive_list = [
            "{0}/lock.all".format(globalvariables.DB_BACKUP_LOG_PATH)]

        if dbname == "all":
            dbname_list = get_dbname_list()
            for dbname in dbname_list:
                exclusive_lock = "{0}/lock.{1}".format(
                    globalvariables.DB_BACKUP_LOG_PATH, dbname)
                exclusive_list.append(exclusive_lock)

        else:
            exclusive_list.append(backup_lock)

        for exclusive_lock in exclusive_list:
            if os.path.isfile(exclusive_lock):
                flock_file = open(exclusive_lock, 'r')
                flock_pid = flock_file.read().strip()
                flock_file.close()

                pid_file = "/proc/" + flock_pid
                if not os.path.exists(pid_file):
                    message = "Process {0} not exist any more, removing the lock file {1} ...".format(flock_pid,
                                                                                                      exclusive_lock)
                    apscom.info(message)
                    os.remove(exclusive_lock)
                else:
                    message = "Another backup process {0} is in progress, existing ...".format(
                        flock_pid)
                    apscom.warn(message)
                    return globalvariables.BACKUP_FAILED

        flock_file = open(backup_lock, 'w')
        fcntl.flock(flock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        flock_file.write(str(os.getpid()))
        flock_file.flush()
        flock_file.close()

        return globalvariables.BACKUP_SUCCESS

    except Exception as e:
        message = "Failed to enter lock for backup process!\n{0}{1}".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)


def read_line_from_file(filepath):
    path_list = []
    with open(filepath) as fp:
        line = fp.readline()
        cnt = 1
        while line:
            #print("Line {}: {}".format(cnt, line.strip()))
            line = fp.readline()
            if line.startswith('/'):
                path_list.append(line.strip())
            cnt += 1
    fp.close()
    return path_list


def get_dbaas_ver():
    dbaas_ver = ""
    try:
        dbaas_ver_str = "rpm -qa|grep -m 1 -i dbaas|uniq"
        [dbaas_ver, returncode, stderror] = execute_shell(dbaas_ver_str)
        return dbaas_ver
    except Exception as e:
        message = "Failed to get dbaas rpm version!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)

def get_metadata_info(dbname=None):
    metadata_info={
        "dbaas_ver":"",
        "rpm_ver":"",
        "os_ver":"",
        "ldb_remote_scaling":"",
        "libopc_build_ver":""
    }
    try:
        dbaas_ver_str = "rpm -qa|grep -m 1 -i dbaas|uniq"
        [dbaas_ver, returncode, stderror] = execute_shell(dbaas_ver_str)
        metadata_info["dbaas_ver"]=dbaas_ver
    except Exception as e:
        message = "Failed to get dbaas rpm version!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        metadata_info["dbaas_ver"]=""
    # 
    try:
        ver_str = "rpm -qa|grep -m 1 -i fa-spe-oci-backup|uniq"
        [rpm_ver, returncode, stderror] = execute_shell(ver_str)
        metadata_info["rpm_ver"]=rpm_ver
    except Exception as e:
        message = "Failed to get backup rpm version!\n{0}{1}".format(sys.exc_info()[1:2], e)
        apscom.info(message)
        metadata_info["rpm_ver"]=""
    
    try:
        os_ver_str = "cat /etc/redhat-release"
        [os_ver, returncode, stderror] = execute_shell(os_ver_str)
        metadata_info["os_ver"]=os_ver
    except Exception as e:
        message = "failed to get os version"
        apscom.warn(message)
        metadata_info["os_ver"]=""
    # capture libopc version
    try:
        opc_lib_location = "{0}/{1}/lib/libopc.so".format(globalvariables.OPC_LIB_PATH,dbname)
        bkup_lib_location = "{0}/{1}/opc/libopc.so".format(globalvariables.FA_RMAN_ORA_PATH,dbname)
        # print(opc_lib_location)
        # print(bkup_lib_location)
        if os.path.exists(opc_lib_location):
            libopc_str = "strings -a {0}| grep -i 'build label'".format(opc_lib_location)
            [libopc_build_ver, returncode, stderror] = execute_shell(libopc_str)
            metadata_info["libopc_build_ver"]=libopc_build_ver
        elif os.path.exists(bkup_lib_location):
            libopc_str = "strings -a {0}| grep -i 'build label'".format(bkup_lib_location)
            [libopc_build_ver, returncode, stderror] = execute_shell(libopc_str)
            metadata_info["libopc_build_ver"]=libopc_build_ver
        else:
            metadata_info["libopc_build_ver"]=""

    except Exception as e:
        message = "failed to get libopc version"
        apscom.warn(message)
        metadata_info["libopc_build_ver"]=""
    # capture ldb flags
    try:
        ldb_data={
            "ldb_databases":"",
            "ldb_backup_remote_channels":"",
            "ldb_restore_validate_remote_channels":"",
            "ldb_nodes":""

        }
        ldb_flag_file="{0}/ldb_flag.txt".format(globalvariables.DB_CONFIG_PATH)

        if os.path.exists(ldb_flag_file): 
            with open(ldb_flag_file,'r') as f:
                data=f.readlines()
            if data:
                for line in data:
                    if '#' not in line:
                        if 'databases=' in line:
                            ldb_dbs = line.split('=')
                            ldb_data["ldb_databases"] = ldb_dbs[1].strip()
                        if 'allow_backup_remote_channels=' in line:
                            ldb_dbs = line.split('=')
                            ldb_data["ldb_backup_remote_channels"] = ldb_dbs[1].strip()
                        if 'allow_restore_validate_remote_channels=' in line:
                            ldb_dbs = line.split('=')
                            ldb_data["ldb_restore_validate_remote_channels"] = ldb_dbs[1].strip()
                        if 'nodes=' in line:
                            ldb_dbs = line.split('=')
                            ldb_data["ldb_nodes"] = ldb_dbs[1].strip()
        # 
        metadata_info["ldb_remote_scaling"]=ldb_data
    except Exception as e:
        message = "failed to get ldb flag data from {0}".format(ldb_flag_file)
        apscom.warn(message)
        metadata_info["ldb_remote_scaling"]=ldb_data
    
    return metadata_info


def update_flag_driver(all_pod_file):
    try:
        with open(globalvariables.DB_CONFIG_PATH + "/" + "db_backup_exceptions.txt", "r") as fp:
            lines = fp.readlines()
        with open(all_pod_file, "r") as file:
            data = file.read()
        for line in lines:
            ex_values = line.strip().split(",")
            if ex_values[0]:
                for i in range(0, len(ex_values)):
                    if (data.find(ex_values[i].strip()) != -1):
                        replace_line(all_pod_file, ex_values[i].strip())
        file.close()
        fp.close()
    except Exception as e:
        message = "failed to update flag driver {0},{1}!".format(sys.exc_info()[
                                                                 1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def replace_line(all_pod_file, value, line_nums=[]):
    try:
        count = 0
        for line in fileinput.FileInput(all_pod_file, inplace=True):
            count = count+1
            if line_nums and len(line_nums) > 0:
                if count in line_nums:
                    #line = line.replace(ok2backup, "n")
                    line = re.sub(r".$", "n",line)
            else:
                if value in line:
                    #line = line.replace(ok2backup, "n")
                    line = re.sub(r".$", "n",line)
            # Don't remove print
            print(line.strip())
    except Exception as e:
        message = "failed to replace line {0},{1}!".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise Exception(message)


def comment_backup_cron():
    try:
        EXA_LOG_PATH = globalvariables.EXALOGS_PATH
        cron_file = "/etc/crontab"
        cron_file_bkp = "{0}/crontab_{1}".format(
            EXA_LOG_PATH, globalvariables.ts)

        if os.path.exists(cron_file):
            shutil.copy(cron_file, cron_file_bkp)
        else:
            message = "{0} does not exist ".format(cron_file)
            apscom.warn(message)

        cron_list = []
        final_list = []
        uncomment_list = []
        with open(cron_file, 'r') as f:
            for line in f:
                if '/var/opt/oracle/cleandb/cleandblogs.pl' in line and not line.startswith('#'):
                    comment = "#{0}".format(line.strip())
                    uncomment_list.append(comment)
                elif line.strip().startswith('#'):
                    if '/var/opt/oracle/cleandb/cleandblogs.pl' not in line.strip():
                        cron_list.append(line.strip())
                    else:
                        uncomment_list.append(line.strip())
                else:
                    for entry in globalvariables.ETC_CRONTAB_COMMENT_VALUES:
                        if entry in line.strip():
                            comment = "#{0}".format(line.strip())
                            cron_list.append(comment)
        #
        uncomment_items = [x if ('/var/opt/oracle/cleandb/cleandblogs.pl' not in x)
                           else x.replace('#', '') for x in uncomment_list]
        uncomment_items_sort = set(uncomment_items)
        #
        for line in cron_list:
            if '/var/opt/oracle/cleandb/cleandblogs.pl' not in line:
                final_list.append(line.strip())
        for line in uncomment_items_sort:
            final_list.append(line.strip())

        with open(cron_file, 'w') as f:
            for line in final_list:
                f.write("%s\n" % line)
        #
        os.chmod(cron_file, 0o600)

    except Exception as e:
        message = "failed to replace line {0},{1}!".format(
            sys.exc_info()[1:2], e)
        shutil.copy(cron_file_bkp, cron_file)
        # apscom.warn(message)
        raise Exception(message)


def backup_files(backup_path, config_path, prefix):
    """ Backup files per config file
    Args:
        config_path (str): config file with backup file list
        prefix (str): prefix of backup file name
    Returns:
        str: full path of backup files
    Raises:
    """
    try:
        f = None
        tar = None
        backup_list = None
        backup_name = backup_path + "/" + prefix + "_" + globalvariables.HOST_NAME + "." + time.strftime("%Y-%m-%d.%H%M%S",
                                                                                                         time.gmtime()) + ".tgz"
        backup_files = []
        backup_dirs = []
        path_list = []

        # Get backup file list
        f = open(config_path, 'r')
        backup_list = json.load(f)
        if "backup_file" in backup_list.keys():
            backup_files = backup_list["backup_file"]
            path_list.extend(backup_files)
        if "backup_dir" in backup_list.keys():
            backup_dirs = backup_list["backup_dir"]
            path_list.extend(backup_dirs)
        f.close()

        dir_perm = get_top_dir_perm(path_list)

        # Backup files to backup_name.
        tar = tarfile.open(backup_name, "w:gz")

        # Preserve top dir permission of backup files
        for top_dir in dir_perm.keys():
            ti = tarfile.TarInfo(top_dir)
            ti.mode = int(dir_perm[top_dir], 8)
            ti.type = tarfile.DIRTYPE
            tar.addfile(ti)

        for backup_file in backup_files:
            if "*" in backup_file:
                for matched_file in glob.glob(backup_file):
                    message = "Backing up file {0} ...".format(matched_file)
                    apscom.info(message)
                    tar.add(matched_file)
            else:
                if os.path.exists(backup_file):
                    message = "Backing up file {0} ...".format(backup_file)
                    apscom.info(message)
                    tar.add(backup_file)

        for backup_dir in backup_dirs:
            if "*" in backup_dir:
                for matched_dir in glob.glob(backup_dir):
                    message = "Backing up dir {0} ...".format(matched_dir)
                    apscom.info(message)
                    tar.add(matched_dir)
            else:
                if os.path.exists(backup_dir):
                    message = "Backing up dir {0} ...".format(backup_dir)
                    apscom.info(message)
                    tar.add(backup_dir)

        tar.close()
        return backup_name

    except Exception as e:
        message = "Failed to backup files in {0}!\n{1}{2}".format(
            config_path, sys.exc_info()[1:2], e)
        # apscom.warn(message)
        raise Exception(message)

    finally:
        if f:
            f.close()
        if tar:
            tar.close()


def load_databse_variables(dbname):
    try:
        db_variables = {}
        with open(globalvariables.base_path_ini+'/'+dbname+'.ini', "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if "db_home" in line:
                    ORACLE_HOME = line.split("=")[-1]
                    db_variables["ORACLE_HOME"] = ORACLE_HOME
        fp.close()
        return db_variables
    except Exception as e:
        message = "Failed to load variables in {0}!\n{1}".format(sys.exc_info()[
                                                                 1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def get_gi_home():
    try:
        ocssd_bin_home = ""
        #ocssd_bin = execute_shell(
         #   "ps -ewaf|grep grid|grep ocssd.bin|grep -v grep|awk '{print $NF}'")[0]
        ocssd_bin = execute_shell("ps -ewaf|grep grid|grep ocssd.bin|grep -v grep")[0]
        ocssd_bin_values = ocssd_bin.split(" ")
        for value in ocssd_bin_values:
            if "ocssd.bin" in value:
                ocssd_bin_home = value.strip()
        if not ocssd_bin_home:
            message = "Found crs not running (cannot determine if host is 1st db node ) ..."
            apscom.error(message)
        gbin = os.path.dirname(ocssd_bin_home)
        GI_HOME = os.path.split(gbin)[0]
        if not GI_HOME:
            message = "Not able to find proper GI HOME ..."
            apscom.error(message)
        if not os.path.exists(GI_HOME + "/bin/olsnodes"):
            message = "Not able to find 'olsnodes' command ..."
            apscom.error(message)
        return GI_HOME
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.warn(message)
        raise


def check_olsnodes():
    FIRST_NODE = None
    host = globalvariables.LOCAL_HOST
    gi_home = get_gi_home()
    GI_BIN = gi_home + "/bin"
    OLSN = execute_shell(GI_BIN + "/olsnodes -l -n |awk '{print $NF}'")[0]
    if not OLSN:
        message = "Not able to use $GI_BIN/olsnodes ..."
        apscom.error(message)
    elif OLSN % 2 == 1:
        FIRST_NODE = host
    elif OLSN % 2 == 0:
        FIRST_NODE = execute_shell(
            GI_BIN + "/olsnodes | grep -B1" + host + "|head -1")[0]
    else:
        message = "olsnodes error : {0}" .format(OLSN)
        apscom.error(message)
    return (OLSN, FIRST_NODE)


def gen_ols_node_json():
    try:
        gi_home = get_gi_home()
        GI_BIN = gi_home + "/bin"
        ols_nodes = execute_shell(GI_BIN + "/olsnodes -n")[0]
        nodes = ols_nodes.split("\n")
        json_out = []
        ols_nodes_json_file = globalvariables.EXALOGS_PATH+'/ols_nodes.json'
        for node in nodes:
            data = {}
            node_name, node_number = node.split("\t")
            data["node_num"] = int(node_number.strip())
            data["node_name"] = node_name.strip()
            json_out.append(data)
        #
        try:
            with open(ols_nodes_json_file, 'w+') as file:
                # print(json.dumps(json_out, ensure_ascii=False))
                json.dump(json_out, file, ensure_ascii=False, indent=4)
        except Exception as e:
            message = "Failed to write {0}, {1}!\n{2}".format(
                ols_nodes_json_file, sys.exc_info()[1:2], e)
            # apscom.warn(message)
            raise Exception(message)

    except Exception as e:
        message = "Failed to generate ols node json {0}!\n{1}".format(sys.exc_info()[
                                                                      1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def gen_ols_node_csv():
    try:
        gi_home = get_gi_home()
        GI_BIN = gi_home + "/bin"
        nodes = execute_shell(GI_BIN + "/olsnodes")[0]
        ols_nodes = nodes.split("\n")
        with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/ols_nodes.csv', 'w+') as file:
            writer = csv.writer(file)
            writer.writerow(ols_nodes)
        file.close()
    except Exception as e:
        message = "Failed to generate ols node csv {0}!\n{1}".format(sys.exc_info()[
                                                                     1:2], e)
        # apscom.warn(message)
        raise Exception(message)


def csvWritter(readData, filename, type):
    try:
        with open(filename, 'w+', encoding='utf-8') as csvfile:
            readHeader = ['dbname', 'host', 'status', "PID"]
            writer = csv.DictWriter(csvfile, fieldnames=readHeader)
            writer.writeheader()
            writer.writerows(readData)
        csvfile.close()
    except Exception as e:
        message = "Failed to add data to csv !\n{0},{1}".format(sys.exc_info()[
                                                                1:2], e)
        apscom.info(message)


def csvupdater(filename, dbname=None, host=None, status=None, pid=None):
    try:
        with open(filename, newline="", encoding='utf-8') as file:
            readData = [row for row in csv.DictReader(file)]
            for i in range(0, len(readData)):
                if status == 'STARTED' or status == 'RUNNING':
                    if readData[i]['dbname'] == dbname:
                        readData[i]['status'] = status
                        readData[i]['host'] = host
                        if pid:
                            readData[i]['PID'] = pid
                elif readData[i]['dbname'] == dbname and readData[i]['host'] == host:
                    if status == 'COMPLETED':
                        readData.remove(readData[i])
                        break
                    else:
                        readData[i]['status'] = status
                        break
                elif readData[i]['dbname'] == dbname:
                    if status == 'COMPLETED':
                        readData.remove(readData[i])
                        break

        csvWritter(readData, filename, "update")
    except Exception as e:
        message = "Failed to update csv !\n{0},{1}".format(
            sys.exc_info()[1:2], e)
        apscom.info(message)


def verify_ols_connect(host):
    try:
        inst_meta = instance_metadata.ins_metadata()
        inst_metadata = inst_meta.get_inst_metadata()
        if "dbSystemShape" in inst_metadata["metadata"]:
            system_type = "exa"
        else:
            system_type = "mt"
        if(system_type == "exa"):
            # gen_ols_node_csv()
            if not is_node_exception_list(host):
                cmd = "su oracle -c 'python {0}/remote_exec.py --type=verify_ols_connect --host={1}'".format(
                    globalvariables.QUERY_POOL_PATH, host)
                [sec_rpm_ver, ret_code, stderror] = execute_shell(cmd)
                rpm_ver = get_rpm_ver()
                if ret_code == 0 and sec_rpm_ver == rpm_ver:
                    return True
                else:
                    apscom.warn("backup rpm versions do not match, target node {0} has {1} rpm , running backup on {2}".format(
                        host, sec_rpm_ver, globalvariables.HOST_NAME))
                    return False
            else:
                return False
        else:
            msg = "olsnodes connectivity applicable for Exadata"
            apscom.error(msg)
    except Exception as e:
        message = "Failed to verify the ols node connectivity".format(sys.exc_info()[
                                                                      1:2], e)
        # apscom.warn(message)
        apscom.info(message)
        return False


def gen_ols_node_list():
    try:
        ols_num_to_host_node_dict = {}
        ols_host_to_num_node_dict = {}
        EXA_LOG_PATH = globalvariables.EXALOGS_PATH
        with open(EXA_LOG_PATH+'/ols_nodes.json', 'r') as olsnodes_file:
            olsdata = json.load(olsnodes_file)

        if olsdata:
            for ols_val in olsdata:
                ols_node_num = int(ols_val["node_num"])
                ols_node_name = ols_val["node_name"]
                ols_num_to_host_node_dict[ols_node_num] = ols_node_name
                ols_host_to_num_node_dict[ols_node_name] = ols_node_num

        if ols_num_to_host_node_dict and ols_host_to_num_node_dict:
            return ols_num_to_host_node_dict, ols_host_to_num_node_dict
        else:
            message = "failed to generate gen_ols_node_list !\n{0}".format(e)
            apscom.error(message)

    except Exception as e:
        message = "failed to generate gen_ols_node_list !\n{0}".format(e)
        apscom.error(message)
        raise


def get_dbname_db_count(dbname):
    try:
        count = 0
        username = getpass.getuser()
        if username == 'oracle':
            cmd = "srvctl status database -db {0} | grep -i Instance | wc -l".format(
                dbname)
        else:
            cmd = "su - oracle -c 'source /home/oracle/{0}.env;srvctl status database -db {0}' | grep -i Instance | wc -l".format(
                dbname)
            # cmd = "su - oracle -c 'source {0}/utils/db/scripts/shell/set_ora_env.sh {1};srvctl status database -db {1}' | wc -l".format(BASE_DIR,dbname)
        [output, ret_code, stderror] = execute_shell(cmd)
        if ret_code == 0:
            count = output
        return count
    except Exception as e:
        message = "Failed to get ols node count for !{0} \n {1}".format(
            dbname, e)
        apscom.warn(message)

def download_passwd_file():
    try:
        #
        oci_config_path = globalvariables.DB_CONFIG_PATH_DEFAULT
        oci_sdk = ociSDK.ociSDK(oci_config_path)
        oss_bucket = get_bucket_details_from_oss()
        #download_file_loc = globalvariables.download_file_loc
        oci_sdk.download_wallet_backup(".passwd.json", globalvariables.BACKUP_CFG_LOCATION,globalvariables.DB_CONFIG_PATH_DEFAULT,oss_bucket)
        #ociSDK.ociSDK().download_file_passwdjson(oss_bucket,download_file_loc)
        message = "Downloaded {0} to {1}".format(".passwd.json",globalvariables.BACKUP_CFG_LOCATION)
        apscom.info(message)
    except Exception as e:
        message = "Cannot download .passwd.json as unable to access the bucket, check config-oci.json , new db backup configuration will fail.{0}!\n{1} \n please refer to BASE_DIR/config/db/README.passwd.son".format(
            sys.exc_info()[1:2], e)
        apscom.warn(message)
        raise

def get_dbname_db_nodes(dbname, db_uniq_name):
    try:
        node_list = []
        username = getpass.getuser()
        if username == 'oracle':
            cmd = "srvctl status database -db {0} | sort -V".format(
                db_uniq_name)
            # cmd = "source {0}/utils/db/scripts/shell/set_ora_env.sh {1};srvctl status database -db {2} | sort -V".format(BASE_DIR,dbname,db_uniq_name)
        else:
            # cmd = "su - oracle -c 'source /home/oracle/{0}.env;srvctl status database -db {0}' | sort -V".format(dbname)
            cmd = "su - oracle -c 'source {0}/utils/db/scripts/shell/set_ora_env.sh {1};srvctl status database -db {2}' | sort -V".format(
                BASE_DIR, dbname, db_uniq_name)
        [output, ret_code, stderror] = execute_shell(cmd)
        output_str = output
        hosts = output_str.split('\n')

        for line in hosts:
            if ('is running on' in line):
                ols_host = line.split(' ')[-1]
                node_list.append(ols_host)

        # get node number for every host returned
        dbname_db_nodes = []
        EXA_LOG_PATH = globalvariables.EXALOGS_PATH
        with open(EXA_LOG_PATH+'/ols_nodes.json', 'r') as olsnodes_file:
            olsdata = json.load(olsnodes_file)
        if olsdata:
            for ols_val in olsdata:
                ols_node_num = int(ols_val["node_num"])
                ols_node_name = ols_val["node_name"]
                for db_node_name in node_list:
                    dbname_db_node_dict = {}
                    if db_node_name == ols_node_name:
                        # apscom.warn(db_node_name)
                        # apscom.warn(ols_node_num)
                        dbname_db_node_dict["running_db_node_name"] = db_node_name
                        dbname_db_node_dict["running_db_node_num"] = ols_node_num
                        dbname_db_nodes.append(dbname_db_node_dict)

        # apscom.info(dbname_db_nodes)
        running_db_odd_hosts = []
        running_db_even_hosts = []
        for node in dbname_db_nodes:
            if node["running_db_node_num"] % 2 != 0:
                running_db_odd_hosts.append(node)
            else:
                running_db_even_hosts.append(node)

        return running_db_odd_hosts, running_db_even_hosts

    except Exception as e:
        message = "Failed to get ols node count for !{0} \n {1}".format(
            dbname, e)
        apscom.warn(message)


def remove_backup_oss_passwd():
    try:
        for file in globalvariables.BACKUP_CFG_FILES:
            try:
                with open(globalvariables.DB_CONFIG_PATH+'/'+file, "r") as fp:
                    lines = fp.readlines()
                fp.close()
                with open(globalvariables.DB_CONFIG_PATH+'/'+file, "w") as f:
                    for line in lines:
                        if "bkup_oss_passwd" not in line:
                            f.write(line)
                f.close()
                message = "Successfully removed password from {0}".format(
                    globalvariables.DB_CONFIG_PATH+'/'+file)
                apscom.info(message)
            except Exception as e:
                message = "unable to remove password from {0}".format(
                    globalvariables.DB_CONFIG_PATH+'/'+file)
                apscom.warn(message)
                pass
        # remove password from artifact location
        for file in globalvariables.BACKUP_CFG_FILES:
            try:
                with open(globalvariables.ARTIFACTS_BACKUP_PATH+'/'+file, "r") as fp:
                    lines = fp.readlines()
                fp.close()
                with open(globalvariables.ARTIFACTS_BACKUP_PATH+'/'+file, "w") as f:
                    for line in lines:
                        if "bkup_oss_passwd" not in line:
                            f.write(line)
                f.close()
                message = "Successfully removed password from {0}".format(
                    globalvariables.ARTIFACTS_BACKUP_PATH+'/'+file)
                apscom.info(message) 
            except Exception as e:
                message = "unable to remove password from {0}".format(
                    globalvariables.ARTIFACTS_BACKUP_PATH+'/'+file)
                apscom.warn(message)
                pass
        # remove password from configuration.rman
        try:
            with open(globalvariables.RMAN_SCRIPTS+'/configuration.rman', "r") as config_file:
                config_lines = config_file.readlines()
            with open(globalvariables.RMAN_SCRIPTS + '/configuration.rman', "w") as wconfig_file:
                for line in config_lines:
                    if "set encryption on identified" not in line:
                        wconfig_file.write(line)
        except Exception as e:
            message = "unable to remove password from {0}".format(
                globalvariables.RMAN_SCRIPTS+'/configuration.rman')
            apscom.warn(message)
            pass

    except Exception as e:
        message = "Failed to remove password from {2} \n{0},{1}".format(
            sys.exc_info()[1:2], e, file)
        apscom.warn(message)
        raise


def is_node_exception_list(host=None):
    try:
        is_node_exception = False
        if not host:
            host = globalvariables.HOST_NAME
        with open(globalvariables.DB_CONFIG_PATH + "/" + "db_node_exceptions.txt", "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if host in line:
                    is_node_exception = True
        return is_node_exception
    except Exception as e:
        message = "Failed to verify node exception List \n{0},{1}".format(sys.exc_info()[
                                                                          1:2], e)
        apscom.warn(message)
        raise


def bucket_validate(bucket_name):
    try:
        region = instance_metadata.ins_metadata().region
        with open(globalvariables.DB_CONFIG_PATH_DEFAULT, 'r') as oci_config_file:
            oci_config = json.load(oci_config_file)
        oss_namespace = oci_config["oss_namespace"]
        download_passwd_file()
        cred_f = "{0}/.passwd.json".format(globalvariables.DB_CONFIG_PATH)
        with open(cred_f, 'r') as f:
            data = json.load(f)
            user = list(data[oss_namespace].keys())[0]
            bucket_oss_passwd = data[oss_namespace][user]
        cmd = "{0} --key {1}".format(globalvariables.DECRYPT_TOOL,
                                    bucket_oss_passwd)
        [output, ret_code, stderror] = execute_shell(cmd)
        password = output

        retry_strategy= Retry(total=5, backoff_factor=1, status_forcelist=[502,503,504,500,429])
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http = requests.session()
        http.mount('https://', adapter)
        http.mount('http://', adapter)
        if not "uk-gov-" in region:
            URL='https://swiftobjectstorage.{0}.oraclecloud.com/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)
        else:
            URL='https://swiftobjectstorage.{0}.oraclegovcloud.uk/v1/{1}/{2}'.format(region,oss_namespace,bucket_name)

        #removing new line character from URL string#
        URL = URL.strip()
        response = http.head(URL, auth=HTTPBasicAuth(user, password))
        # print(response.status_code,URL)
        if response.status_code == 204:
            return True
        else:
            return False
    except Exception as e:
        message = "Bucket validate got failed with status False"
        apscom.warn(message)
        raise

def get_bucket_details(dbname,oss_namespace):
    try:
        config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
        oci_sdk=ociSDK.ociSDK(config_file)
        password_file_name = globalvariables.password_file_name
        if not oss_namespace:
            with open (globalvariables.OCI_SDK_META_FILE,'r') as f:
                data = json.load(f)
                oss_namespace = data["ns"]
        region = instance_metadata.ins_metadata().region
        with open(globalvariables.FAOPS_OSS_INFO) as oss_file:
            oci_config = json.load(oss_file)
        env = get_db_env_type(dbname)
        if env == "em_exa":
            oss_bucket = oci_config[oss_namespace]["em_rman_wallet_bn"]
        elif env == "dbaas":
            oss_bucket = oci_config[oss_namespace]["dbaas_rman_wallet_bn"]
        else:
            oss_bucket = oci_config[oss_namespace]["fa_rman_wallet_bn"][env]
        return oss_bucket
    except Exception as e:
        message = "Not able to get bucket details for database {0} and namespace {1}".format(dbname,oss_namespace)
        apscom.warn(message)
    
def get_bucket_details_from_oss():
    try:
        config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
        oci_sdk=ociSDK.ociSDK(config_file)
        password_file_name = globalvariables.password_file_name
        with open (globalvariables.OCI_SDK_META_FILE,'r') as f:
            data = json.load(f)
            oss_namespace = data["ns"]
        oss_config_file = globalvariables.FAOPS_OSS_INFO
        with open (oss_config_file, 'r') as file:
            oci_config_file = json.load(file)
            oss_bucket = oci_config_file[oss_namespace]["fa_rman_wallet_bn"]["stage"]
        if oci_sdk.check_object_exist(oss_bucket,password_file_name,oss_namespace):
            return oss_bucket
        else:
            config_file = globalvariables.DB_CONFIG_PATH_DEFAULT
            oci_sdk=ociSDK.ociSDK(config_file)
            #Need to remove hardcode value
            with open(config_file) as f:
                data=json.load(f)
                oss_bucket = data["oss_bucket"]
                ns = data["oss_namespace"]
            return oss_bucket
    except Exception as e:
        message = "Failed to get bucket name from {0} and {1}".format(globalvariables.FAOPS_OSS_INFO,globalvariables.DB_CONFIG_PATH_DEFAULT)
        apscom.warn(message)


def get_lib_file_type():
    try:
        realm = instance_metadata.ins_metadata().realmKey
        region = instance_metadata.ins_metadata().region
        if "uk-gov" in region:
            artifactory_url="{0}/artifactory/list/generic-fa/".format(globalvariables.ARTIFACTORY_URL_OC4)
        else:
            artifactory_url="{0}/artifactory/list/generic-fa/".format(globalvariables.ARTIFACTORY_URL_OC1)
        r = requests.get(artifactory_url)
        #print("The status code is :",r.status_code)
        if (r.status_code == 200):
            if realm not in ['oc1','oc4']:
                #print("The realm key is :", realm)
                libfile_type='bkup'
            else:
                #print("The realm key is :", realm)
                libfile_type='opc'
        return libfile_type
    except Exception as e:
        message = "Not able to get libfile type"
        apscom.warn(message)

#Jira Reference - FSRE-101 for below function-      
def archivelog_backup_schedule(dbname):
    """To check the batabase shape so that it can execute archive log hourly

    Args:
        dbname (str): Name of database

    Returns:
        Boolean: True or False
    """
    try:
        archive_log_hourly_exception_file = globalvariables.DB_CONFIG_PATH + "/archive_log_hourly_exception_file.txt"
        DB_SHAPE=get_db_query_data(dbname,'DB_SHAPE')
        DR_CHECK=get_db_query_data(dbname,'DR_ENABLED_CHK')
        CUR_HOUR=datetime.now()
        MOD=CUR_HOUR.hour % 4
        buckup_return = False
        if os.path.exists(archive_log_hourly_exception_file):
            with open(archive_log_hourly_exception_file, 'r') as f:
                hourly_run = f.readlines()
                hourly_run = list(map(lambda s: s.strip(), hourly_run))
                if dbname in hourly_run:
                    buckup_return = True
        
        if buckup_return or MOD == 0 :
            return True
        elif ('PROD' in DB_SHAPE) and (DR_CHECK == 0):
            return True
        else:
            return False
    except Exception as e:
        message = "Failed to get archive log backup schedule update. {0}".format(e)
        apscom.warn(message)
            

# Below function added as part of requirement in BUG 34781623
def cert_check():
    try:
        response  = requests.get(globalvariables.instance_cert)
        http_code=response.status_code
        if http_code == 200 :
            cert = response.text.strip()
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
            valid_upto = x509.get_notAfter().decode().strip('Z')
            #valid_from = x509.get_notBefore().decode().strip('Z')
            not_valid = x509.has_expired()
            valid_upto_dt=datetime.strptime(valid_upto,'%Y%m%d%H%M%S')
            #valid_from_dt=datetime.strptime(valid_from,'%Y%m%d%H%M%S')
            if not_valid:
                message="{1} Instance certificate has expired  on {0}, Please work with OCI Team".format(valid_upto_dt,globalvariables.RED)
                apscom.warn(message)
            else:
                message="Instance certificate is good and valid till {}".format(valid_upto_dt)
                apscom.info(message)
        else:
            message="{1} Instance certifacate metadata URL {0} not working on this exa please work with OCI Team".foramt(globalvariables.instance_cert,globalvariables.RED)
            apscom.warn(message)
    except Exception as e:
        message = "Not able to get certificate validity. {0}".format(e)
        apscom.warn(message)

def check_error_code(backup_log):
    try:
        error_code=""
        error_code_json=globalvariables.DB_ERROR_CODE_JSON
        with open(error_code_json,'r') as errdata:
            jdata=json.load(errdata)
        if backup_log and os.path.exists(backup_log):
            with open(backup_log,'r') as logdata:
                lines=logdata.readlines()
                for line in lines:
                    for key,value in jdata.items():
                        if value in line:
                            error_code = key
                            break
        
            return error_code
        else:
            message="backup log file is not present to check error code on {0}".format(backup_log)
            apscom.warn(message)
            return error_code
    except Exception as e:
        message = "Not able to get error code. {0}".format(e)
        apscom.warn(message)

#Below function added as part of jira -> FUSIONSRE-3103
def db_archive_backup_list():
    try:
        apscom.info("creating db_archive_backup file  - {0}".format(globalvariables.db_archive_backup_path ))
        if os.path.exists(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json'):
            with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json', 'r') as fp:
                dbs = json.load(fp)
                all_dbs = list(dbs['large_db'].keys()) + list(dbs['medium_db'].keys()) + list(dbs['small_db'].keys())
                for db in all_dbs:
                    db = db.strip()
                    if archivelog_backup_schedule(db):
                        with open(globalvariables.db_archive_backup_path , 'a+') as f:
                                f.seek(0)
                                db_string=f.read()
                                if db not in db_string.split(','):
                                    if len(db_string) != 0 :
                                        if db_string[-1] == ',':
                                            f.write(db)
                                        else:
                                            f.write(',' + db)
                                    else:
                                        f.write(db)
    except Exception as e:
        message = "Not able to write file. {0}".format(e)
        apscom.warn(message)

#Below function added as part of jira -> FUSIONSRE-3103
def archivelog_backup_enabled(dbname):
    try:
        with open(globalvariables.db_archive_backup_path ,'r') as db:
            db_data=db.read().split(',')
            apscom.info("current archive backup queue => {0}".format(db_data))
            db_env_type = get_db_env_type(dbname)
            if dbname in db_data:
                return True
            else:
                apscom.info("{0} having env type - {1} is not available in archive backup queue and not eligible for hourly backup ".format(dbname,db_env_type))
                return False
    except Exception as e:
        message = "error in reading file -> {0} -  {1}".format(globalvariables.db_archive_backup_path,e)
        apscom.warn(message)

#Below function added as part of jira -> FUSIONSRE-3103
def update_db_archive_file(dbname):
    try:
        apscom.info("updating db_archive_backup file  - {0}".format(globalvariables.db_archive_backup_path))
        with open(globalvariables.db_archive_backup_path,'r') as db:
            db_data=db.read().split(',')
            if dbname in db_data:
                db_data.remove(dbname)
        db_string=','.join(db_data)
        with open(globalvariables.db_archive_backup_path,'w') as db:
            db.write(db_string)
    except Exception as e:
        message = "error in updating file -> {0} -  {1}".format(globalvariables.db_archive_backup_path,e)
        apscom.warn(message)

def oss_upload_backup_metadata(BACKUP_METADATA_FILE):
    try:
        rman_cmd = "/bin/bash {0}/bin/rman_upload_metadata.sh --action upload --file_path {1} ".format(BASE_DIR,BACKUP_METADATA_FILE)
        [res, ret_code,stderr] = execute_shell(rman_cmd)
        if res:
            apscom.info(res)
        else:
            message="Failed to upload {0} to bucket".format(BACKUP_METADATA_FILE)
            apscom.warn(message)
    except Exception as e:
        message = "error in uploading file -> {0} -  {1}".format(BACKUP_METADATA_FILE,e)
        apscom.warn(message)

################################################################################### Incremental and validate queueing functionality ###################################################################################################
def check_backup_priority_flag(bkp_type):
    try:
        with open(globalvariables.BACKUP_PRIORITY,'r') as priority:
                backup_priority = json.load(priority)
        return backup_priority[bkp_type]
    except Exception as e:
        message = "error in checking backup priority flag -> {0} -  {1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)   

def check_incremental_backup_eligibility(dbname):
    try:
        with open(globalvariables.BACKUP_PRIORITY,'r') as priority:
            backup_priority = json.load(priority)
        apscom.info("checking Incremental eligibility for db   - {0}".format(dbname)) 
        priority_list=backup_priority["Incremental_Backup"]
        DB_Full_Sts=get_db_query_data(dbname,'DB_Full_Sts')
        DB_Val_Sts=get_db_query_data(dbname,'DB_Val_Sts')
        incremental_priority_backups=backup_priority["incremental_priority_backups"]
        if check_backup_priority_flag("Incremental_backup_priority_enabled"):
            if ("Full_Backup" in priority_list and DB_Full_Sts != 0 ) or ("Validate_Backup" in priority_list and  DB_Val_Sts != 0 ) or check_priority_bkp_status(incremental_priority_backups) or check_ldb_backup_status(dbname):
                apscom.info(" Other priority backups are in progress. skipping incremental for db {0} ".format(dbname))
                return False
            else:
                return True
        else:
            apscom.info("Incremental backup priority is disabled on this exa node ")
            return True
    except Exception as e:
        message = "error in checking incremental backup eligibility -> {0} -  {1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

def check_validate_backup_eligibility(dbname,validate_backup_queue):
    try:
        with open(validate_backup_queue , 'r') as f:
            db_queue_list=f.read().split(',')
        apscom.info("current validate queue status :{0}".format(db_queue_list))
        apscom.info("checking validate eligibility for db   - {0}".format(dbname))
        with open(globalvariables.BACKUP_PRIORITY,'r') as priority:
            backup_priority = json.load(priority)
        priority_list=backup_priority["Validate_Backup"]  ##This is the list of entries for Validate which is ['Full_Backup', 'Incremental_Backup']
        DB_Full_Sts=get_db_query_data(dbname,'DB_Full_Sts')
        DB_Incr_Sts=get_db_query_data(dbname,'DB_Incr_Sts')
        Validate_priority_backup=backup_priority["validate_priority_backups"]
        #Check priority_list
        if dbname in db_queue_list:
            if check_backup_priority_flag("Validate_backup_priority_enabled"):
                if ("Full_Backup" in priority_list and DB_Full_Sts != 0 ) or ("Incremental_Backup" in priority_list and  DB_Incr_Sts != 0 ) or check_priority_bkp_status(Validate_priority_backup) or check_ldb_backup_status(dbname):
                    apscom.info(" Other priority backups are in progress. skipping validate for db {0} ".format(dbname))
                    return False
                else:
                    return True
            else:
                apscom.info("Validate backup priority is disabled on this exa node ")
                return True
        else:
            apscom.info("validate backup for {0} already completed  for this schedule ".format(dbname))
            return False
    except Exception as e:
        message = "error in checking validate backup eligibility -> {0} -  {1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)   

def check_ldb_backup_status(dbname):
    try:
        csv_file = globalvariables.remote_backup_states_csv_file
        status=False
        if os.path.exists(csv_file):
            with open('ldb_exec_states_v2.csv',newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for line in reader:
                    if line['dbname'] == dbname and line['status'].upper() == "RUNNING":
                        status=True
        return status
    except Exception as e:
        message = "error in checking LDB backup status -> {0} -  {1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message) 

def check_priority_bkp_status(backup_array,backup_type=""):
    try:
        priority_bkp_running_status=False
        for btp in backup_array:
            now = datetime.now()
            ts = now.strftime('%Y%m%d_%H%M%S')
            backup_status_process_file=globalvariables.EXALOGS_PATH + "/" + btp + "_status_" + ts + ".txt"
            if backup_type and btp in globalvariables.validate_queue_btp:
                cmd = "ps -ef | grep {0} | grep -v grep | grep {1} ".format(btp,"/usr/bin/script")
            else:
                cmd = "ps -ef | grep {0} | grep -v grep | grep -v {1}".format(btp,"/usr/bin/script")
            [res, ret_code,stderr] = execute_shell(cmd)
            with open(backup_status_process_file,'w') as ps:
                ps.write(res)
            if is_priority_bkp_running(btp,backup_status_process_file,backup_type):
                apscom.info("{0} is running.. will skip the current backup ".format(btp))
                priority_bkp_running_status=True
        return priority_bkp_running_status
    except Exception as e:
        message="error in checking priority_bkp_running_status check_priority_bkp_status function  {0} - {1} ".format(sys.exc_info()[1:2],e)
        apscom.warn(message)

def is_priority_bkp_running(btp,backup_status_process_file,backup_type):
    try:
        status=False
        with open(backup_status_process_file,'r') as sts:
            process_lines=sts.readlines()
        for process in process_lines:
            if "--action" in process:
                p_list=process.strip().split('=')
            else:
                p_list=process.strip().split()
            if btp in p_list:
                if backup_type and btp in globalvariables.validate_queue_btp :
                    if  "--dbname" in process:
                        pid=p_list[1]
                    else:
                        pid=p_list[0].split()[1]
                    cmd="ps -p {0} -o lstart | grep -v STARTED".format(pid)
                    [res, ret_code,stderr] = execute_shell(cmd)
                    delta=timedelta(minutes=5)
                    if check_pid_time(res,delta):
                        status=True
                else:
                    status=True
        return status
    except Exception as e:
        message="error in is_bkp_running fun for backup type  {0} for file {3} - {1} {2} ".format(btp,sys.exc_info()[1:2],e,backup_status_process_file)
        apscom.warn(message)

def check_pid_time(pidstrtime,delta):
    try:
        pidtimeobj=datetime.strptime(pidstrtime,'%a %b %d %H:%M:%S %Y')
        now = datetime.now()
        pid_file=now - delta
        if pid_file > pidtimeobj:
            return True
        else:
            return False
    except Exception as e:
        message = "Error in checking pid timestamp for time stamp - {2}  {0} {1}".format(sys.exc_info()[1:2],e,pidstrtime)
        apscom.warn(message)
        raise

def gen_validate_queue(queue_file):
    try:
        apscom.info("creating validate backup queue {0}".format(queue_file))
        if os.path.exists(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json'):
            with open(globalvariables.DB_BACKUP_LOG_PATH+'/exalogs/db_group_by_size.json', 'r') as fp:
                dbs = json.load(fp)
            all_dbs = list(dbs['large_db'].keys()) + list(dbs['medium_db'].keys()) + list(dbs['small_db'].keys())
            count=0
            for db in all_dbs:
                db = db.strip()
                with open(queue_file , 'a+') as f:
                    f.seek(0)
                    db_string=f.read()
                    db_env_type = get_db_env_type(db)
                    if db not in db_string.split(',') and 'prod' in db_env_type:
                        count +=1 
                        if count == 1:
                            f.write(db)
                        else:
                            f.write(',' + db)
    except Exception as e:
        message = "Error in generating validate queue file {0}, {1} {2}".format(queue_file,sys.exc_info()[1:2],e)
        apscom.warn(message)

def check_validate_queue_status(validate_backup_queue):
    try:
        if os.path.exists(validate_backup_queue):
            if is_file_older_than(validate_backup_queue,timedelta(days=globalvariables.validate_backup_queue_delata)):
                apscom.info("validate queue file {0} is older than defined delta {1} days ".format(validate_backup_queue,globalvariables.validate_backup_queue_delata))
                now = datetime.now()
                ts = now.strftime('%Y%m%d_%H%M%S')
                validate_backup_queue_bkp = validate_backup_queue + "_" + ts
                os.rename(validate_backup_queue,validate_backup_queue_bkp)
            else:
                message="validate queue file {0} is latest as per delta define {1} days ".format(validate_backup_queue,globalvariables.validate_backup_queue_delata)
                apscom.info(message)
    except Exception as e:
        message="error in checking timestamp for validate queue file {0} - {1} {2} ".format(validate_backup_queue,sys.exc_info()[1:2],e)
        apscom.warn(message)

def update_db_validate_file(dbname,validate_backup_queue):
    try:
        apscom.info("updating db validate backup queue file  - {0}".format(validate_backup_queue))
        with open(validate_backup_queue, 'r') as f:
            db_data=f.read().split(',')
            if dbname in db_data:
                db_data.remove(dbname)
        db_string=','.join(db_data)
        with open(validate_backup_queue, 'w') as f:
            f.write(db_string)
    except Exception as e:
        message = "Error in updating validate queue file:- {0}, {1} {2}".format(validate_backup_queue,sys.exc_info()[1:2],e)
        apscom.warn(message)

############################################################ DBAAS and EM changes ############################################################
def check_em_systemtype():
    try:
        if "emdb" in globalvariables.LOCAL_HOST.split(".")[1].lower() :
            return True
        else:
            return False
    except Exception as e:
        message = "could not check em systemtype -> {0}".format(e)
        apscom.warn(message)
        
def check_dbaas_systemtype():
    try:
        if ("Exa" in instance_metadata.ins_metadata().dbSystemShape):
            return False
        else:
            return True
    except Exception as e:
        message = "could not check em systemtype -> {0}".format(e)
        apscom.warn(message)
        return None