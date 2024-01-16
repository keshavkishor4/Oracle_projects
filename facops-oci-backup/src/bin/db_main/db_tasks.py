# -*- coding: utf-8 -*-
#
# Performs DB Tasks
#
#
#   Created
#      01/09/2020  -- Saritha Gireddy
#       18/02/2020      -  Zakki Ahmed
#
import glob
import os
import socket
import time
import shutil
import sys
from datetime import datetime, date

LOCAL_HOST = socket.gethostname()
# for DEV
# BASE_DIR=os.getcwd()+"/.."
BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables
import json
# fix for 31246268 CLOUDOPSTT:OCI:SAASFAPREPROD1: DB BACKUP RPM :UPDATE RPM WITH 19C CRS LOGS LOCATION
HK_DB_CONFIG_PATH=BASE_DIR + "/config/db/housekeeping-db_v2.json"
BACKUP_SUCCESS = 0
BACKUP_FAILED = 1
time_now = time.time()

def copyFolderStructure(inputpath,outputpath,retention_days):
    try:
        NUM_DAYS = 60 * 60 * 24 * retention_days
        for dirpath, dirnames, filenames in os.walk(inputpath):
            sourceFolder = os.path.join(inputpath, dirpath[len(inputpath):])
            destiFolder = os.path.join(outputpath, dirpath[len(inputpath):])
            try:
                if not os.path.isdir(destiFolder):
                   os.makedirs(destiFolder)
                   message = "created folder {0}".format(destiFolder)
                   apscom.debug(message)
                else:
                    pass

                for file in os.listdir(sourceFolder):
                    if not os.path.isdir(os.path.join(sourceFolder,file)):
                        sourcefile=os.path.join(sourceFolder,file)
                        if (time_now - os.path.getmtime(sourcefile)) > NUM_DAYS:
                            try:
                                shutil.copy2(sourcefile, destiFolder)
                                if (os.path.getsize(sourcefile) > 20000):
                                    time.sleep(5)
                                message = "File {0} copied successfully to {1}".format(sourcefile,destiFolder)
                                apscom.debug(message)
                                os.remove(sourcefile)
                                message = "File {0} deleted successfully".format(sourcefile)
                                apscom.debug(message)
                            except Exception as e:
                                message = "Error occurred while copying {0} , with {1}".format(sourcefile,e)
                                apscom.debug(message)
                                pass
            except Exception as e:
                message = "copy files faced error {0}".format(e)
                apscom.debug(message)
    except Exception as e:
        message = "copy files faced error {0}".format(e)
        apscom.debug(message)

# Bug 30792023 - Housekeeping of logs , define it in config/db/housekeeping-db_v2.json
def housekeeping_logs():
    global log_file
    try:
        log_file_path = globalvariables.DB_BACKUP_LOG_PATH + "/{0}/".format("exalogs")
        if not os.path.exists(log_file_path):
            os.makedirs(log_file_path)
        filename = log_file_path + "{0}_{1}_{2}.log".format(globalvariables.HOST_NAME,
                                                                os.path.basename(__file__).split(".")[0],
                                                                datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        log_file = apscom.init_logger(__file__, log_dir=log_file_path, logfile=filename)
        with open(HK_DB_CONFIG_PATH,'r') as config:
            data = json.load(config)
            for val in data:
                message = "checking for {0} ...".format(val)
                apscom.info(message)
                if val=="backup_logs":
                    src = data[val]['src_loc']
                    rm_retention_days = int(data[val]['rm_retention_days'])
                    for root, dirs, files in os.walk(src):
                        for dir in dirs:
                            if os.path.isdir(os.path.join(root, dir)): # dir is your directory path
                                diff_between_current_day=find_diff_between_current_day(os.path.join(root, dir))
                                if diff_between_current_day>rm_retention_days-10:
                                    ret_days=diff_between_current_day+15
                                else :
                                    ret_days = rm_retention_days
                                deleteFiles(os.path.join(root, dir), ret_days)
                elif val=="file_pattern_deletion":
                    for file_patt in data[val]:
                        location=data[val][file_patt]['loc']
                        rm_retention_days =  data[val][file_patt]['rm_retention_days']
                        delete_file_pattern(location,rm_retention_days)
                else:
                    src = data[val]['src_loc']
                    tgt = data[val]['tgt_loc']
                    avail_space = checkFreeSpace(tgt)
                    if (avail_space < 50):
                        message = "{0} target doesn't have sufficient space ...".format(tgt)
                        apscom.debug(message)
                    else:
                        retention_days = int(data[val]['retention_days'])
                        rm_retention_days = int(data[val]['rm_retention_days'])
                        try:
                            if os.path.exists(tgt):
                                deleteFiles(tgt, rm_retention_days)
                            if os.path.exists(src):
                                if os.path.exists(tgt):
                                    copyFolderStructure(src,tgt,retention_days)
                                else:
                                    message = "{0} does not exist creating folder {0} ...".format(tgt)
                                    apscom.debug(message)
                                    if not os.path.exists(tgt):
                                        os.makedirs(tgt)
                                    copyFolderStructure(src,tgt,retention_days)
                            else:
                                # print("Source folder {0} does not exist passing ...").format(src)
                                message = "Source folder {0} does not exist passing ...".format(src)
                                apscom.debug(message)
                                pass
                        except Exception as e:
                            message = "copy files faced error {0}".format(e)
                            apscom.debug(message)
        config.close()
    except Exception as e:
        message = "copy files faced error {0}".format(e)
        apscom.debug(message)
def delete_file_pattern(location,retention_days):
    try:
        message = "Deleting files with the pattern.. ".format(location)
        apscom.debug(message)
        NUM_DAYS = 60 * 60 * 24 * int(retention_days)
        for file in glob.glob(location):
            if (time_now - os.path.getmtime(file)) > NUM_DAYS:
                if not os.path.isdir(file):
                    #print(file)
                    try:
                        os.remove(file)
                        message = "Successfully deleted .. {0}".format(file)
                        apscom.debug(message)
                    except Exception as e:
                        message = "failed to delete file {0}... {1}".format(file, e)
                        apscom.debug(message)
                        pass

    except Exception as e:
        message = "failed to delete files from  {0}... {1}".format(location,e)
        apscom.debug(message)

def checkFreeSpace(targetpath):
    try:
        path = '/'.join(targetpath.split('/')[:2])
        space = os.statvfs(path)
        block_size = space.f_frsize
        total_blocks = space.f_blocks
        free_blocks = space.f_bfree
        gb = 1024 * 1024 * 1024
        total_size = total_blocks * block_size / gb
        free_size = free_blocks * block_size / gb
        used = (space.f_blocks - space.f_bfree) * space.f_frsize / gb
        return free_size
    except Exception as e:
        message = "failed to verify free space {0}".format(e)
        apscom.debug(message)
# fix for 31246268 CLOUDOPSTT:OCI:SAASFAPREPROD1: DB BACKUP RPM :UPDATE RPM WITH 19C CRS LOGS LOCATION
def deleteFiles(cleanup_path,retention_days):
    try:
        NUM_DAYS = 60 * 60 * 24 * retention_days
        for dirpath, dirnames, filenames in os.walk(cleanup_path):
            dest_folder = os.path.join(cleanup_path, dirpath[len(cleanup_path):])
            for file in os.listdir(dest_folder):
                del_file = os.path.join(dest_folder, file)
                if (time_now - os.path.getmtime(del_file)) > NUM_DAYS:
                    if not os.path.isdir(del_file):
                        os.remove(del_file)
        message = "Succeed to cleanup obsolete backup data of backup id {0}.".format(cleanup_path)
        apscom.debug(message)
    except Exception as e:
        message = "Failed to cleanup logs {0}".format(e)
        apscom.debug(message)
def find_diff_between_current_day(dirpath):
    try:
        date_object = date.today()
        list_of_files = glob.glob(dirpath)
        latest_file = max(list_of_files, key=os.path.getctime)
        ctime = os.path.getctime(latest_file)
        date_time = time.strftime('%Y-%m-%d', time.localtime(ctime))
        fdate_object = datetime.strptime(date_time, '%Y-%m-%d')
        date1 = date(fdate_object.year, fdate_object.month, fdate_object.day)
        date2 = date(date_object.year, date_object.month, date_object.day)
        delta = date2 - date1
        numberofdays = delta.days
        #print(numberofdays)
        return numberofdays
    except Exception as e:
        message = "Failed to get latest file {0}".format(e)
        apscom.debug(message)

if __name__ == "__main__":
    housekeeping_logs()