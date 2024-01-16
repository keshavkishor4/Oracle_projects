#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      resume_backup.py

    DESCRIPTION
        precheck for resume failed backup

    NOTES

    MODIFIED        (MM/DD/YY)

    Vipin Azad            09/28/22  - Enh 33624729 - PLEASE ENABLE RESUMABLE OPTION WITH RMAN BACKUPS - FY22Q3

"""
#### imports start here ##############################


import glob
import os
import sys
import json
import argparse
from tempfile import mkstemp
from datetime import date, datetime, timedelta
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
from common import globalvariables, commonutils, apscom


# resumable_check fun : will be checking for latest post json file  \
# and call the process_post_json function to process it for further processing.
def get_post_json(ORACLE_SID):
    log_file_loc = globalvariables.DB_BACKUP_LOG_PATH+"/"+ORACLE_SID
    post_json_file = None
    try:
        if os.path.isdir(log_file_loc):
            #fixed=> need to search for post.json with complete filename 
            post_file_list = glob.glob(
                "{0}/*compressed*_post.json".format(log_file_loc))
            if len(post_file_list) >0:
            # backup_files = glob.glob(atifacts_path.strip() + "/*.spec")
                latest_post_file = max(post_file_list, key=os.path.getmtime)
                message="Latest Post file : {0}".format(latest_post_file)
                apscom.info(message)
                if os.path.exists(latest_post_file):
                    post_json_file = latest_post_file
                else:
                    post_json_file = None
                    message="Post json File does not exist "
                    apscom.info(message)
            else:
                post_json_file = None
                message="could not found any post json for Full backup"
                apscom.info(message)
        return post_json_file
    except Exception as e:
        message="DB SID log path does not exist : \n {0}\n{1}\n{2}".format(log_file_loc,sys.exc_info()[1:2],e)
        apscom.warn(message)
    


#resumable_check Fun will be processing Post.json file will be calling fun get_post_json to get the lastest post json file for full backup. 
def resumable_check(ORACLE_SID):
    resume_status = False
    backup_restore_time = None
    back_type = None
    try:
        post_json_file = get_post_json(ORACLE_SID)
        if post_json_file:
            with open(post_json_file, 'r') as data:
                post_data = json.load(data)
                back_type = post_data["BACKUP_TYPE"]
                status = post_data["STATUS"]
                log_file = post_data["LOG_FILE"]
                # if condition for failed backup
                # if condition would be on status and backup type.
                if status == "FAILED" and back_type in globalvariables.resume_backup_types and os.path.exists(log_file):
                    with open(log_file, 'r') as data:
                        log_txt = data.readlines()
                        backup_restore_time_list = []
                        for dt in log_txt:
                            # Fixed =>  define list of error for failure in global variable-> ToDO
                            for error in globalvariables.resume_backup_restore_error:
                                if error in dt:
                                    # getting backup failure timestamp from rman log file.
                                    # sample string - > RMAN-03002: failure of backup command at 09/22/2022 05:39:10
                                    #
                                    time_stamp = dt.split("at")[1].strip()
                                    if len(time_stamp) > 0:
                                        # string to datetime convert with strptime
                                        #Fixed -=> check for Null Time Stamp -> break the loop with print warning
                                        dtt = datetime.strptime(time_stamp, '%m/%d/%Y %H:%M:%S')
                                        # createing timedelta object for 1hr
                                        n = timedelta(hours=1)
                                        # subtracing 1hr from backup failure time to start the resumable backup 1hr before failure.
                                        backup_restore_time = dtt-n
                                        # datetime object to string convert
                                        backup_restore_time = backup_restore_time.strftime(
                                            '%m-%d-%y %H:%M:%S')
                                        #Populating "backup_restore_time_list" with backup restore time.
                                        backup_restore_time_list.append(backup_restore_time)
                                # print(dt.strip())
                        if len(backup_restore_time_list) > 0 :
                            resume_status = True
                            backup_restore_time=backup_restore_time_list[0].strip()
                            message = "last Full backup got failed and failure restore time would be  {0}".format(backup_restore_time)
                            apscom.info(message)
                        else:
                            resume_status = False
                            message = "last Full backup got failed, however failure time could not found in rman log file {0}".format(log_file)
                            apscom.info(message)
                else:
                    message = "No failure found for any of the resume backup type:   {0}".format(globalvariables.resume_backup_types)
                    apscom.info(message)
        return back_type, backup_restore_time,resume_status
    except Exception as e:
        message = "Failed to do resume check : {0} \n {1}".format(sys.exc_info()[1:2],e)
        apscom.warn(message)


def parse_opts():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-d', '--dbsid', dest='ORACLE_SID', help='required - DBSID')
        args = parser.parse_args()
        if not args.ORACLE_SID:
            parser.error('-d option is required')
        return(args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.error(message)

# "RMAN-03002: failure of restore command at 09/22/2022 05:39:10"


def main(ORACLESID=None):
    if  not ORACLESID:
        options = parse_opts()
        ORACLESID = options.ORACLE_SID
    back_type, backup_restore_time,status = resumable_check(ORACLESID)
    
    message = "Backup Type : {0}\t Backup_restore_time : {1}\t resume status : {2}".format(
        back_type, backup_restore_time,status)
    apscom.info(message)


if __name__ == "__main__":
    main()

