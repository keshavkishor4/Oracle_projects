#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      db_rman_file_gen.py

    DESCRIPTION
        Auto generate rman files for backup execution for full backups

    NOTES

    MODIFIED        (MM/DD/YY)

    Zakki Ahmed           01/24/21  - Enh 33690512 - ENHANCE RMAN BACKUP ON HUGE DB POD - FY22Q3
    Zakki Ahmed           02/16/22  - Enh 33860528 - support channels for one node only
    # include for all backup types -- defined in ldb_flag.txt
    # OPC - ECBF_DEV2 - unique db prod which has DEV in its name
    Jayant Mahishi        02/28/22 -- Distinguish between prod and test/dev/stage env
    Vipin Azad            09/28/22  - Enh 33624729 - PLEASE ENABLE RESUMABLE OPTION WITH RMAN BACKUPS - FY22Q3
    Smita Acharya         09/12/23  - Enh 35735931 - Remove keep until clause from backups
"""
#### imports start here ##############################
from common import ociSDK, apscom, commonutils, globalvariables, load_oci_config, post_backup_metadata, instance_metadata
from db import validate_sbt_test, db_query_pool
from distutils.log import warn
from email import utils
import glob
import os
import shutil
import sys
from datetime import datetime
from pwd import getpwuid
import requests
# import optparse
import argparse
import getpass
import json

import traceback
from tempfile import mkstemp


BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/")
global env_type
global retention_days


#
# Generate rman block
#
def gen_rman_block(nodes, all_running_nodes, sys_val, dbname, sbt_lib_path, opc_file_path, backup_type, user_channels, cdbflag, tag, ret_days,backup_restore_time=None,resume_flag=None):
    try:
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        channel = 1
        release_block = ""

        retention_days = ret_days
        if ret_days == 0:
            env_type = commonutils.get_db_env_type(dbname)
            retention_days = globalvariables.backup_opts[backup_type][env_type]["retention"]
        if tag == None:
            tag = globalvariables.backup_opts[backup_type][env_type]["tag"]

        #rman_block="RUN { \n sql \"alter system switch logfile\"; \n"
        rman_block = "RUN { \n "
        #
        # archivelog_to_oss
        #
        if backup_type == "archivelog_to_oss":
            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels

            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block = release_block + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1
            ##Modified archivelog format
            if cdbflag == "yes":
                rman_block = rman_block + "CONFIGURE CONTROLFILE AUTOBACKUP OFF; \n \
    backup archivelog from time \"trunc(sysdate-{4})\" not backed up 1 times format '{0}/%d_%U_%h_%e_%I.arc' filesperset 1 reuse; \n".format(db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days) \
                    + release_block + "}"
            else:
                rman_block = rman_block + "CONFIGURE CONTROLFILE AUTOBACKUP ON; \n \
    backup archivelog from time \"trunc(sysdate-{4})\" not backed up 1 times format '{0}/%d_%U_%h_%e_%I.arc' filesperset 1 reuse; \n".format(db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days) \
                    + release_block + "}"
            # print(rman_block)
            return rman_block

        #
        # database_compressed_to_oss
        #
        elif backup_type == "database_compressed_to_oss":
            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels
            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE FORMAT '{0}/backupset/%d_L0_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block = release_block + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1

            if cdbflag == "yes":
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP OFF; \n"
                cdbflag_text_post = "ALLOCATE CHANNEL C1_SBT DEVICE TYPE SBT_TAPE  FORMAT '{0}/backupset/ctrl_%I_%T_%t' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n".format(db_uniq_name, sbt_lib_path, opc_file_path) +  \
                    "backup current controlfile; \n " + \
                    "release channel C1_SBT; \n " + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
            else:
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
                cdbflag_text = cdbflag_text + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE SBT_TAPE TO '{0}/backupset/ctrl_%F' ; \n".format(
                        db_uniq_name)
                cdbflag_text_post = "\n"
            #
            # check with zakki on below rman block command.
            if resume_flag and resume_flag.lower() == "yes":
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset not backed up since time \"to_date('{0}','mm-dd-yy hh24:mi:ss')\" database section size 1024G tag {1}; \n".format(backup_restore_time,tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"
            else:
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset full database section size 1024G tag {0} ; \n".format(tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"

            # print(rman_block)
            return rman_block
        #
        # ldb_database_compressed_to_oss
        #
        elif backup_type == "ldb_database_compressed_to_oss":
            # LDB
            all_running_nodes_count = len(all_running_nodes)
            #print("***** {0} *****".format(all_running_nodes))
            if user_channels == 0:
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            if all_running_nodes_count == 1:
                user_channels = globalvariables.backup_opts["database_compressed_to_oss"][env_type]["channels"]

            if nodes >= all_running_nodes_count:
                nodes = all_running_nodes_count
            elif nodes == 0:
                nodes = all_running_nodes_count
            node_count = 1
            channel_count = 1
            while node_count <= nodes:
                node = all_running_nodes[node_count - 1]
                channel = 1
                while channel <= user_channels:
                    rman_block = rman_block + "ALLOCATE CHANNEL C{5}_SBT DEVICE TYPE SBT_TAPE CONNECT 'sys/{0}@{1}:1521/{2}:dedicated as sysdba' FORMAT '{2}/backupset/%d_L0_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={3}, ENV=(OPC_PFILE={4})'; \n".format(
                        sys_val, node, db_uniq_name, sbt_lib_path, opc_file_path, channel_count)
                    release_block = release_block + \
                        "release channel C{0}_SBT; \n".format(channel_count)
                    channel = channel + 1
                    channel_count = channel_count + 1
                node_count = node_count + 1

            if cdbflag == "yes":
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP OFF; \n"
                cdbflag_text_post = "ALLOCATE CHANNEL C1_SBT DEVICE TYPE SBT_TAPE  FORMAT '{0}/backupset/ctrl_%I_%T_%t' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n".format(db_uniq_name, sbt_lib_path, opc_file_path) +  \
                    "backup current controlfile; \n " + \
                    "release channel C1_SBT; \n " + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
            else:
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
                cdbflag_text = cdbflag_text + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE SBT_TAPE TO '{0}/backupset/ctrl_%F' ; \n".format(
                        db_uniq_name)
                cdbflag_text_post = "\n"

            # check with zakki ->
            if resume_flag and resume_flag.lower() == "yes":
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset not backed up since time \"to_date('{0}','mm-dd-yy hh24:mi:ss')\" database section size 1024G tag {1} ; \n".format(backup_restore_time,tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"
            else:
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset full database section size 1024G tag {0} ; \n".format(tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"
            return rman_block
        #
        # database_to_reco
        #
        elif backup_type == "database_to_reco":

            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels

            while channel <= max_channels:
                rman_block = rman_block + \
                    " allocate channel ch{0} device type disk; \n ".format(
                        channel)
                release_block = release_block + \
                    " release channel ch{0}; \n".format(channel)
                channel = channel + 1

            #if cdbflag == "yes":
            cdbflag_text = ""
            cdbflag_text_post = "\n"
            #else:
            #    cdbflag_text = ""
            #    cdbflag_text_post = "\n"
            #
            if resume_flag and resume_flag.lower() == "yes":
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset not backed up since time \"to_date('{0}','mm-dd-yy hh24:mi:ss')\" database section size 1024G tag {1} ; \n".format(backup_restore_time,tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"
            else:
                rman_block = rman_block + cdbflag_text + \
                    "backup as compressed backupset incremental level 0 database section size 1024G tag {0}; \n".format(tag) \
                    + release_block + cdbflag_text_post + \
                    "}"

            # print(rman_block)
            return rman_block
        #
        #  ldb_database_to_reco
        #
        elif backup_type == "ldb_database_to_reco":

            #print("***** {0} *****".format(all_running_nodes))
            all_running_nodes_count = len(all_running_nodes)
            if user_channels == 0:
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            if all_running_nodes_count == 1:
                user_channels = globalvariables.backup_opts["database_to_reco"][env_type]["channels"]

            if nodes >= all_running_nodes_count:
                nodes = all_running_nodes_count
            elif nodes == 0:
                nodes = all_running_nodes_count

            node_count = 1
            channel_count = 1
            while node_count <= nodes:
                node = all_running_nodes[node_count - 1]
                channel = 1
                while channel <= user_channels:
                    rman_block = rman_block + "allocate channel ch{0} device type disk CONNECT 'sys/{1}@{2}:1521/{3}:dedicated as sysdba' ; \n".format(
                        channel_count, sys_val, node, db_uniq_name)
                    release_block = release_block + \
                        " release channel ch{0}; \n".format(channel_count)
                    channel = channel + 1
                    channel_count = channel_count + 1
                node_count = node_count + 1

            #if cdbflag == "yes":
            cdbflag_text = ""
            cdbflag_text_post = "\n"
            #else:
                #cdbflag_text = ""
                #cdbflag_text_post = "\n"
            # check with zakki
            if resume_flag and resume_flag.lower() == "yes":
                rman_block = rman_block + cdbflag_text + \
                    "backup force as compressed backupset not backed up since time \"to_date('{0}','mm-dd-yy hh24:mi:ss')\" database section size 1024G tag {1}; \n".format(backup_restore_time,tag, retention_days) \
                    + release_block + cdbflag_text_post + \
                    "}"
            else:
                rman_block = rman_block + cdbflag_text + \
                    "backup as compressed backupset incremental level 0 database section size 1024G tag {0}; \n".format(tag) \
                    + release_block + cdbflag_text_post + \
                    "}"

            # print(rman_block)
            return rman_block
        #
        # incremental_to_reco
        #
        elif backup_type == "incremental_to_reco":

            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels

            while channel <= max_channels:
                rman_block = rman_block + \
                    " allocate channel ch{0} device type disk; \n ".format(
                        channel)
                release_block = release_block + \
                    " release channel ch{0}; \n".format(channel)
                channel = channel + 1

            #if cdbflag == "yes":
            cdbflag_text = ""
            cdbflag_text_post = "\n"
            #else:
            #    cdbflag_text = ""
            #    cdbflag_text_post = "\n"
            #
            rman_block = rman_block + cdbflag_text + \
                "backup as compressed backupset incremental level 1  for recover of tag {0} database section size 1024G; \n".format(tag) \
                + release_block + cdbflag_text_post + \
                "}"

            # print(rman_block)
            return rman_block
        #
        #  incremental_to_oss
        #
        elif backup_type == "incremental_to_oss":

            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels

            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE FORMAT '{0}/backupset/%d_L1_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    dbname, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block = release_block + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1

            if cdbflag == "yes":
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP OFF; \n"
                cdbflag_text_post = "ALLOCATE CHANNEL C1_SBT DEVICE TYPE SBT_TAPE  FORMAT '{0}/backupset/ctrl_%I_%T_%t' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n".format(dbname, sbt_lib_path, opc_file_path) +  \
                    "backup current controlfile; \n " + \
                    "release channel C1_SBT; \n " + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
            else:
                cdbflag_text = "\nCONFIGURE CONTROLFILE AUTOBACKUP ON; \n"
                cdbflag_text = cdbflag_text + \
                    "CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE SBT_TAPE TO '{0}/backupset/ctrl_%F' ; \n".format(
                        db_uniq_name)
                cdbflag_text_post = "\n"
            #
            rman_block = rman_block + cdbflag_text + \
                "backup as compressed backupset incremental level 1  for recover of tag {0} database section size 1024G ; \n".format(tag, retention_days) \
                + release_block + cdbflag_text_post + \
                "}"

            # print(rman_block)
            return rman_block
        #
        #  pdbseed_to_reco
        #
        elif backup_type == "pdbseed_to_reco":
            # get ORACLE_SID from env
            try:
                ORACLE_SID = os.environ["ORACLE_SID"]
            except KeyError:
                print(
                    "Please set the {0} db env, cannot find ORACLE_SID set".format(dbname))
                sys.exit(1)
            # check query pool file present
            query_output_file = "{0}/{2}/{1}_{2}_query.json".format(
                globalvariables.DB_BACKUP_LOG_PATH, globalvariables.HOST_NAME, ORACLE_SID)
            rman_reco = ''
            rman_data = ''
            try:
                with open(query_output_file, 'r') as db_query_output:
                    query_output = json.load(db_query_output)

                asm_disk_group = query_output["ASM_DISK_GROUP"]
                if len(asm_disk_group) > 0:
                    for data in asm_disk_group:
                        for value in data:
                            if 'REC' in value:
                                rman_reco = value
                            elif 'DAT' in value:
                                rman_data = value
            except Exception as e:
                print(e)

            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels
            while channel <= max_channels:
                rman_block = rman_block + \
                    " allocate channel ch{0} device type disk; \n ".format(
                        channel)
                release_block = release_block + \
                    " release channel ch{0}; \n".format(channel)
                channel = channel + 1

            #if cdbflag == "yes":
            cdbflag_text = ""
            cdbflag_text_post = "\n"
            #else:
            #    cdbflag_text = ""
            #    cdbflag_text_post = "\n"
            #
            rman_block = rman_block + cdbflag_text + \
                "BACKUP PLUGGABLE DATABASE \"PDB$SEED\" FORMAT '+{0}' tag '{1}' NOT BACKED UP; \n".format(rman_reco, tag) \
                + release_block + cdbflag_text_post + \
                "}"

            # print(rman_block)
            return rman_block
        #
        # validate_db_reco
        #
        elif backup_type == "validate_db_reco":
            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels
            while channel <= max_channels:
                rman_block = rman_block + \
                    " allocate channel ch{0} device type disk; \n ".format(
                        channel)
                release_block = release_block + \
                    " release channel ch{0}; \n".format(channel)
                channel = channel + 1

            rman_block = rman_block + \
                "\n BACKUP VALIDATE CHECK LOGICAL DATABASE;\n" + release_block + "}"
            # print(rman_block)
            return rman_block
        #
        # restore_validate_oss
        #
        elif backup_type == "restore_validate_oss":
            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels

            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE FORMAT '{0}/backupset/%d_L0_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block = release_block + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1

            rman_block = rman_block + \
                "\nRESTORE DATABASE VALIDATE CHECK LOGICAL;\n" + release_block + "}"

            # print(rman_block)
            return rman_block
        #
        # ldb_restore_validate_oss
        #
        elif backup_type == "ldb_restore_validate_oss":
            # LDB
            #print("***** {0} *****".format(all_running_nodes))
            all_running_nodes_count = len(all_running_nodes)
            if user_channels == 0:
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            if all_running_nodes_count == 1:
                user_channels = globalvariables.backup_opts["restore_validate"][env_type]["channels"]

            if nodes >= all_running_nodes_count:
                nodes = all_running_nodes_count
            elif nodes == 0:
                nodes = all_running_nodes_count
            node_count = 1
            channel_count = 1
            while node_count <= nodes:
                node = all_running_nodes[node_count - 1]
                channel = 1
                while channel <= user_channels:
                    rman_block = rman_block + "ALLOCATE CHANNEL C{5}_SBT DEVICE TYPE SBT_TAPE CONNECT 'sys/{0}@{1}:1521/{2}:dedicated as sysdba' FORMAT '{2}/backupset/%d_L0_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={3}, ENV=(OPC_PFILE={4})'; \n".format(
                        sys_val, node, db_uniq_name, sbt_lib_path, opc_file_path, channel_count)
                    release_block = release_block + \
                        "release channel C{0}_SBT; \n".format(channel_count)
                    channel = channel + 1
                    channel_count = channel_count + 1
                node_count = node_count + 1

            #if cdbflag == "yes":
            cdbflag_text = ""
            cdbflag_text_post = ""
            #else:
            #    cdbflag_text = ""
            #    cdbflag_text_post = ""

            #
            rman_block = rman_block + cdbflag_text + \
                "\nRESTORE DATABASE VALIDATE CHECK LOGICAL;\n".format(tag, retention_days) \
                + release_block + cdbflag_text_post + \
                "}"
            return rman_block
        #
        # obsolete_backupset_withoss
        #
        elif backup_type == "obsolete_backupset_withoss":
            env_type = commonutils.get_db_env_type(dbname)
            # Setting config value to default of 14 days
            disk_retention_days = globalvariables.backup_opts["incremental_to_reco"][env_type]["retention"]
            if user_channels == 0:
                max_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
            else:
                max_channels = user_channels
            # disk block
            release_block_disk = ""
            # FUSIONSRE-4633 - Added this to ensure the retention policy for disk is applied at the beginning of the Run block
            rman_block =  "CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS; \n\n".format(disk_retention_days) + rman_block
            while channel <= max_channels:
                rman_block = rman_block + \
                    " allocate channel ch{0} device type disk; \n ".format(
                        channel)
                release_block_disk = release_block_disk + \
                    " release channel ch{0}; \n".format(channel)
                channel = channel + 1
            rman_block = rman_block + \
                "\nCROSSCHECK BACKUP OF DATABASE CONTROLFILE SPFILE; \n" + \
                "\ndelete force noprompt obsolete device type disk; \n\n" + \
                release_block_disk + \
                "} \n\n"

            # SBT Block
            channel = 1
            release_block_tape = ""
            rman_block = rman_block + \
                "CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS; \n\n".format(
                    retention_days) + "RUN { \n"
            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE FORMAT '{0}/backupset/%d_L0_bs%s_bp%p_%c_%t_%T' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block_tape = release_block_tape + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1

            #
            rman_block = rman_block + \
                "\nCROSSCHECK BACKUP OF DATABASE CONTROLFILE SPFILE; \n" + \
                "\ndelete force noprompt obsolete device type sbt_tape; \n\n" +  \
                release_block_tape + \
                "} \n\n"  # + \
            #    "\nCONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS;\n".format(disk_retention_days)#

            # SBT Archive log cleanup
            channel = 1
            release_block_tape = ""
            rman_block = rman_block + "CONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS; \n\n".format(retention_days) + \
                "RUN { \n"
            while channel <= max_channels:
                rman_block = rman_block + "ALLOCATE CHANNEL C{3}_SBT DEVICE TYPE SBT_TAPE FORMAT '{0}/%d_%h_%e_%I.arc' PARMS 'SBT_LIBRARY={1}, ENV=(OPC_PFILE={2})'; \n ".format(
                    db_uniq_name, sbt_lib_path, opc_file_path, channel, retention_days)
                release_block_tape = release_block_tape + \
                    "release channel C{0}_SBT; \n".format(channel)
                channel = channel + 1

            #Following lines changed for FUSIONSRE-4630, as the obsolete command was not picking up old archivelogs
            #waiting on BUG 35422157
            # rman_block = rman_block + \
            #     "\ndelete force noprompt  backup of archivelog until time 'sysdate-{0}' device type sbt_tape;\n".format(retention_days) + \
            #     release_block_tape + \
            #     "} \n\n" + \
            #     "\nCONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS;\n".format(
            #         disk_retention_days)

            rman_block = rman_block + \
                 "\nCROSSCHECK BACKUP OF DATABASE CONTROLFILE SPFILE; \n" + \
                 "\ndelete force noprompt obsolete device type sbt_tape; \n\n" +  \
                 release_block_tape  + \
                 "} \n\n" + \
                 "\nCONFIGURE RETENTION POLICY TO RECOVERY WINDOW OF {0} DAYS;\n".format(disk_retention_days)

            # print(rman_block)
            return rman_block
    except Exception as e:
        message = "RMAN generation block failed for database {0}".format(
            dbname)
        apscom.warn(message)


def gen_node_list(dbname, backup_type):
    final_node_list = []
    try:
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        dbhome = commonutils.get_crsctl_data(dbname, 'db_home')
        wallet_loc = "{0}/dbs/dbcs/{1}/wallet/cwallet.sso".format(
            dbhome, db_uniq_name)
        dbaas_acfs_path = "/var/opt/oracle/dbaas_acfs/oci_backup"
        sbt_lib_path = "{0}/{1}/lib/libopc.so".format(dbaas_acfs_path, dbname)
        opc_file_path = "{0}/{1}/opc{1}.ora".format(dbaas_acfs_path, dbname)
        all_running_nodes = []
        final_db_node_list = []
        hosts_exceptions = []
        # final_node_list = []
        # Check if node is part of db_exception_list
        with open(globalvariables.DB_CONFIG_PATH + "/" + "db_node_exceptions.txt", "r") as fp:
            lines = fp.readlines()
            for line in lines:
                if not line.startswith('#'):
                    hosts_exceptions.append(line)

        if 'ldb_' in backup_type:
            status, syspass = get_sys_pass(dbhome, wallet_loc)
            if status:
                odd_nodes, even_nodes = commonutils.get_dbname_db_nodes(
                    dbname, db_uniq_name)
                for odd in odd_nodes:
                    all_running_nodes.append(odd['running_db_node_name'])
                for even in even_nodes:
                    all_running_nodes.append(even['running_db_node_name'])
                #
                # verify connection and syspass
                for node in all_running_nodes:
                    if node not in hosts_exceptions:
                        sys_conn_check = db_query_pool.verify_remote_connection(
                            node, dbname, syspass)
                        if sys_conn_check:
                            final_node_list.append(node)
        else:
            for node in all_running_nodes:
                final_node_list.append(node)

        return True, final_node_list

    except Exception as e:
        message = "failed to generate node list - gen_node_list\n{0} -- {1}".format(
            e, traceback.print_exc())
        apscom.warn(message)

        return False, final_node_list
#


def get_sys_pass(dbhome, wallet_loc):
    try:
        cmd = "{0}/bin/mkstore -wrl {1} -viewEntry SYS | grep -i SYS".format(
            dbhome, wallet_loc)
        [res, ret_code, stderr] = commonutils.execute_shell(cmd)
        sys_val = ""
        #
        if res:
            sys_text, sys_val = res.split('=')
            if sys_val.strip():
                sys_val = sys_val.strip()
                return True, sys_val
            else:
                # print("cannot retrieve sys pass from mkstore, check {0}".format(cmd))
                message = "cannot retrieve sys pass from mkstore, check {0} \n reverting back database_compressed_to_oss block".format(
                    cmd)
                apscom.warn(message)
                return False, sys_val
    except Exception as e:
        message = "Failed to verify sys password!\n{0}".format(e)
        apscom.warn(message)
        return False, sys_val


def pre_checks(dbname, backup_type, nodes, user_channels, cdbflag, nodenames, out_option, tag, ret_days,backup_restore_time=None,resume_flag=None):

    try:
        env_type = commonutils.get_db_env_type(dbname)
        db_uniq_name = commonutils.get_crsctl_data(dbname, 'db_unique_name')
        dbhome = commonutils.get_crsctl_data(dbname, 'db_home')
        wallet_loc = "{0}/dbs/dbcs/{1}/wallet/cwallet.sso".format(
            dbhome, db_uniq_name)
        #dbaas_acfs_path = "/var/opt/oracle/dbaas_acfs/oci_backup"
        opc_sbt_lib_path = "{0}/{1}/lib/libopc.so".format(
            globalvariables.OPC_LIB_PATH, dbname)
        opc_ora_file_path = "{0}/{1}/opc{1}.ora".format(
            globalvariables.OPC_LIB_PATH, dbname)
        bkup_sbt_lib_path = "{0}/{1}/opc/libopc.so".format(
            globalvariables.FA_RMAN_ORA_PATH, dbname)
        bkup_ora_file_path = "{0}/{1}/opc/opc{1}.ora".format(
            globalvariables.FA_RMAN_ORA_PATH, dbname)
        if os.path.exists(opc_sbt_lib_path) and os.path.exists(opc_ora_file_path):
            message = "This host is configured to use OPC libraries"
            apscom.info(message)
            sbt_lib_path = "{0}/{1}/lib/libopc.so".format(
                globalvariables.OPC_LIB_PATH, dbname)
            opc_file_path = "{0}/{1}/opc{1}.ora".format(
                globalvariables.OPC_LIB_PATH, dbname)
        elif os.path.exists(bkup_sbt_lib_path) and os.path.exists(bkup_ora_file_path):
            message = "This host is configured to use BKUP libraries"
            apscom.info(message)
            sbt_lib_path = "{0}/{1}/opc/libopc.so".format(
                globalvariables.FA_RMAN_ORA_PATH, dbname)
            opc_file_path = "{0}/{1}/opc/opc{1}.ora".format(
                globalvariables.FA_RMAN_ORA_PATH, dbname)
        else:
            message = "Backup Libraries are missing on this host. Rerun backup configuration as root!"
            apscom.info(message)

        # all_running_nodes = []
        # hosts_exceptions=[]
        sys_val = None
        #
        if not os.path.exists(wallet_loc):
            if "ldb_" in backup_type:
                message = "{0} not present, cannot execute {1}, exiting ...".format(
                    wallet_loc, backup_type)
                apscom.error(message)
                # sys.exit(1)
            message = "{0} not present ...".format(wallet_loc)
            # apscom.warn(message)
        if not os.path.exists(sbt_lib_path):
            message = "{0} not present ...".format(sbt_lib_path)
            # apscom.warn(message)
            sys.exit(1)
        if not os.path.exists(opc_file_path):
            message = "{0} not present ...".format(sbt_lib_path)
            # apscom.warn(message)
            sys.exit(1)

        #
        # fetch sys pass only for ldb_database_compressed_to_oss
        #

        if backup_type == "ldb_database_compressed_to_oss":
            # pick up sys pass
            sys_pass_status, sys_pass = get_sys_pass(dbhome, wallet_loc)
            if sys_pass_status:
                if sys_pass != "":
                    try:
                        sys_conn_check = db_query_pool.verify_remote_connection(
                            globalvariables.HOST_NAME, dbname, sys_pass)
                        if not sys_conn_check:
                            backup_type = "database_compressed_to_oss"
                            user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        else:
                            sys_val = sys_pass
                    except Exception as e:
                        # print(e)
                        backup_type = "database_compressed_to_oss"
                        user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        pass
            else:
                backup_type = "database_compressed_to_oss"
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]

        # fetch sys pass only for ldb_restore_validate_oss
        #
        elif backup_type == "ldb_restore_validate_oss":

            sys_pass_status, sys_pass = get_sys_pass(dbhome, wallet_loc)
            if sys_pass_status:
                if sys_pass != "":
                    try:
                        sys_conn_check = db_query_pool.verify_remote_connection(
                            globalvariables.HOST_NAME, dbname, sys_pass)
                        if not sys_conn_check:
                            backup_type = "restore_validate_oss"
                            user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        else:
                            sys_val = sys_pass
                    except Exception as e:
                        # print(e)
                        backup_type = "restore_validate_oss"
                        user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        pass
            else:
                backup_type = "restore_validate_oss"
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]

        elif backup_type == "ldb_database_to_reco":

            sys_pass_status, sys_pass = get_sys_pass(dbhome, wallet_loc)
            if sys_pass_status:
                if sys_pass != "":
                    try:
                        sys_conn_check = db_query_pool.verify_remote_connection(
                            globalvariables.HOST_NAME, dbname, sys_pass)
                        if not sys_conn_check:
                            backup_type = "database_to_reco"
                            user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        else:
                            sys_val = sys_pass
                    except Exception as e:
                        # print(e)
                        backup_type = "database_to_reco"
                        user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]
                        pass
            else:
                backup_type = "database_to_reco"
                user_channels = globalvariables.backup_opts[backup_type][env_type]["channels"]

        # get nodes
        status, final_db_node_list = gen_node_list(dbname, backup_type)
        if status:
            out = gen_rman_block(nodes, final_db_node_list, sys_val, dbname, sbt_lib_path,opc_file_path, backup_type, user_channels, cdbflag, tag,ret_days,backup_restore_time,resume_flag)
            # print(out)
            rman_file = "{0}/utils/db/scripts/rman/run/{1}_{2}_{3}.rman".format(
                globalvariables.BASE_DIR, globalvariables.HOST_NAME, dbname, backup_type)
            # print(rman_file)
            # tmp files age are managed in /usr/lib/tmpfiles.d/tmp.conf
            if out_option == "file":
                try:
                    # with open(rman_file, 'w+') as f:
                    #     f.writelines(out)
                    # return(rman_file)
                    fd, path = mkstemp()
                    with open(path, 'w') as f:
                        f.writelines(out)
                    os.close(fd)
                    return(path)

                except Exception as e:
                    # print(e)
                    message = "Failed to generate {0}!\n{1}".format(
                        rman_file, e)
                    apscom.warn(message)
                    return(out)
            else:
                return(out)
        # generate rman file

    except Exception as e:
        message = "Failed to run prechecks!\n{0}".format(sys.exc_info()[1:2])
        print(traceback.print_exc())
        apscom.error(message)
        sys.exit(1)


def parse_opts():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-d', '--dbname', dest='db_name',
                            help='required - pass db unique name')
        parser.add_argument('-b', '--backup_type',
                            dest='backup_type', help='required - backup type')
        parser.add_argument('--hosts', dest='hosts', default=None,
                            help='optional - pass the node names')
        parser.add_argument('-n', '--nodes', type=int, dest='nodes',
                            default=0, help='optional - pass the number of nodes')
        parser.add_argument('-c', '--channels', type=int, dest='channels',
                            default=0, help='optional - pass the number of channels')
        parser.add_argument('-f', '--cdb_flag', type=str, dest='cdbflag',
                            default="no", help='optional - pass cdb flag "yes" or "no"')
        parser.add_argument('--tag', type=str, dest='tag', default=None,
                            help='Optional - provide tag, if other than standard ones')
        parser.add_argument('--retention-days', dest='retention_days', default=0,
                            type=int, help='Optional - Retention days of give backup type.')
        parser.add_argument('--out', type=str, dest='out', default="print",
                            help='optional - "print" or "file" to generate rman file at /opt/faops/spe/ocifabackup/utils/db/scripts/rman/run/')
        # https://jira.oraclecorp.com/jira/browse/SOEDEVSECOPS-1877
        parser.add_argument('--debug_log', action='store', dest='debug_log',
                            default="no", help='Optional - Get logs in debug mode')
        args = parser.parse_args()
        if not args.backup_type:
            parser.error('-b option is required')
        if not args.db_name:
            parser.error('--dbname option is required')
        if not args.cdbflag.lower() in ["yes", "no"]:
            parser.error('--cdbflag option takes "yes" or "no"')
        if not args.out.lower() in ["print", "file"]:
            parser.error('--out option takes "print" or "file"')
        return(args)
    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.error(message)


if __name__ == "__main__":
    username = getpass.getuser()
    if username != 'oracle':
        sys.exit(1)
    else:
        options = parse_opts()
        nodes = options.nodes
        nodenames = options.hosts
        dbname = options.db_name
        backup_type = options.backup_type
        channels = options.channels
        cdbflag = options.cdbflag
        out_option = options.out
        tag = options.tag
        ret_days = options.retention_days
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
        output = pre_checks(dbname, backup_type, nodes, channels,
                            cdbflag, nodenames, out_option, tag, ret_days)
        #
        print(output)
