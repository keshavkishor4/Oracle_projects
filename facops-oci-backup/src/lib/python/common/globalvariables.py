#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      instance_metadata.py

    DESCRIPTION
      load instance metadata and initialize instance variables

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
    Zakki Ahmed           08/17/21  - Updates and changes for Aug'21 release
    Vipin Azad            08/10/23 - Jira FUSIONSRE-8245 ( updates and channges for Aug 23 release)
"""
#### imports start here ##############################
import os
import socket
from datetime import datetime

# color codes
RED='\033[31m'
AMBER='\033[33m'
GREEN='\033[32m'

now = datetime.now()
ts = now.strftime('%Y%m%d_%H%M%S')

# apsbkcom
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
# 
RETENTION_POLICY_PATH_DEFAULT = "{0}/config/mt/config-retention-policy_v2.json".format(BASE_DIR)
BACKUP_CONFIG_PATH = "{0}/config/mt/backup_config/".format(BASE_DIR)
OHS_BACKUP_CONFIG_PATH = "{0}/config/mt/ohs_backup_config/".format(BASE_DIR)
FAOPS_BACKUP_VER = "{0}/config/faops-backup-ver.json".format(BASE_DIR)
FAOPS_BACKUP_STAGE_VER = "{0}/config/stage/faops-backup-ver.json".format(BASE_DIR)
BACKUP_SUCCESS = 0
BACKUP_FAILED = 1
LOCAL_HOST = socket.getfqdn()
HOST_NAME=LOCAL_HOST.split(".")[0]
OCI_FSS_HOST = "filestorage"
OCI_OSS_HOST = "objectstorage"
OCI_CURL_TOOL = "{0}/utils/oci_curl.sh".format(BASE_DIR)
OCI_INST_META_FILE= "{0}/config/{1}_instance_md.json".format(BASE_DIR,HOST_NAME)
OCI_SDK_META_FILE= "{0}/config/oci_sdk_meta.json".format(BASE_DIR)


# ocifsconfig
FS_LIST_TEMPLATE = BASE_DIR + "/config/mt/config-fs-list.json_template"
BACKUP_METADATA_TEMPLATE = BASE_DIR + "/config/backup-metadata.json_template"
# Use uniq name for each vm in case conflicts between vms of the same component.
FS_LIST_PATH = BASE_DIR + "/config/mt/config-fs-list_{0}.json".format(LOCAL_HOST)
BACKUP_METADATA_PATH = BASE_DIR + "/config/mt/backup-metadata_{0}.json".format(LOCAL_HOST)
MT_CONFIG_PATH_DEFAULT = BASE_DIR + "/config/mt/config-oci.json"

BACKUP_SQLDB_PATH = "/var/log/backup_db.sqlite"
OBJ_BACKUP_SQLDB = "backup_db_{0}.sqlite".format(LOCAL_HOST)
BACKUP_FILES_PATH = "/u01/SRE/oci_backup/{0}/files/".format(LOCAL_HOST)
BACKUP_FS_PATH = "/u01/SRE/oci_backup/{0}/fs".format(LOCAL_HOST)
RESTORE_FS_PATH = "/u01/SRE/oci_restore/{0}/fs/".format(LOCAL_HOST)
RESTORE_FILES_PATH = "/u01/SRE/oci_restore/{0}/files/".format(LOCAL_HOST)
RESTORE_OBJ_PATH = "/u01/SRE/oci_restore/{0}/obj/".format(LOCAL_HOST)
RESTORE_EXCLUDE_DEFAULT = BASE_DIR + "/config/mt/config-restore-exclude-list.json_template"
RESTORE_EXCLUDE_LIST = BASE_DIR + "/config/mt/exclude-list_{0}.json".format(LOCAL_HOST)

MONUT_TAB = "/etc/mtab"
FA_COMPONENT_LIST = ["FA_REL13"]
IDM_COMPONENT_LIST = ["IDM_REL13"]
OHS_COMPONENT_LIST = ["OHS"]
ACTION_SUPPORTED = ["update-fs-list", "backup", "restore", "download-mt", "cleanup", "schedule-enable", "list-backups",
                    "create-snapshot", "list-snapshot-tags", "list-tag", "restore-tag", "list-orphan", "cleanup-orphan","post-metadata"]
STORAGE_SUPPORTED = ["fss", "oss","local"]
OPTION_SUPPORTED = ["full", "snapshot"]
BACKUP_STATUS_SUPPORTED = ["active", "obsolete", "all", "failed"]
CATALOG_DB_SUPPORTED = ["local", "remote"]

# ocifsconfigV2
BACKUP_LOG_DIR = "/var/log/ocifsbackup"
BACKUP_BACKUP_DIR= "/podscratch/SRE/oci_backup"
BACKUP_RESTORE_DIR = "/podscratch/SRE/oci_restore"
# OHS_FILE_PATH = "/podscratch/logs/ohslogs"
BACKUP_FILES_PATH_V1 = BACKUP_BACKUP_DIR + "{0}/files".format(LOCAL_HOST)
BACKUP_FILES_PATH_V2 = BACKUP_BACKUP_DIR + "/{0}/files".format(LOCAL_HOST)
BACKUP_FS_PATH_V2 = BACKUP_BACKUP_DIR + "/{0}/fs".format(LOCAL_HOST)
BACKUP_LOCK_FILE = BACKUP_LOG_DIR + "/backup.lock"
RESTORE_FS_PATH_V2 = BACKUP_RESTORE_DIR + "/{0}/fs/".format(LOCAL_HOST)
RESTORE_OBJ_PATH_V2 = BACKUP_RESTORE_DIR + "/{0}/obj/".format(LOCAL_HOST)
FILE_PATTERN_PATH = BASE_DIR + "/config/mt/config-file-patterns.json"
BACKUP_LOG_PATH = "/var/log"
RESTORE_FILES_PATH_V1 = BACKUP_RESTORE_DIR + "{0}/files/".format(LOCAL_HOST)
RESTORE_FILES_PATH_V2 = BACKUP_RESTORE_DIR + "/{0}/files/".format(LOCAL_HOST)

SECONDS_PER_DAY = 86400
RSYNC_TIMEOUT = 36000
TAR_TIMEOUT = 36000
NUM_DAYS = 60 * 60 * 24 * 30

DB_CONFIG_PATH_DEFAULT = BASE_DIR + "/config/wallet/config-oci.json"
DB_BACKUP_LOG_PATH = "/u02/backup/log/{0}".format(HOST_NAME)
EXALOGS_PATH=DB_BACKUP_LOG_PATH+"/exalogs"
PRIVATE_KEY_PATH = BASE_DIR + "/config/wallet/oci_api_key.pem"
PRIVATE_KEY_PATH_FILES = [
  BASE_DIR + "/config/wallet/oci_api_key.pem",
  '/usr/local/bin/SRE/SRA_HOME/ocifsbackup/config/wallet/oci_api_key.pem'
]

OLR_LOC = "/etc/oracle/olr.loc"
ORATAB = "/etc/oratab"

# utils
JQ_LOCATION=BASE_DIR+"/utils"
ARTIFACTORY_URL="https://artifactory-master.cdaas.oraclecloud.com/artifactory/list/generic-fa"
ARTIFACTORY_URL_OC1="https://artifactory-master.cdaas.oraclecloud.com"
ARTIFACTORY_URL_OC4="https://artifactory-ltn-prod.cdaas.ocs.oraclegovcloud.uk"
PROD_RPM_REPO_URL="https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/list/rpm-fa-backup/repo/fa-oci-backup"
DEV_RPM_REPO_URL="https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/list/rpm-fa-backup-dev/repo/fa-oci-backup"

#database scripts paths
RMAN_SCRIPTS=BASE_DIR+"/utils/db/scripts/rman"
# NONFA_DBAAS_RMAN_SCRIPTS=BASE_DIR+"/utils/db/scripts/rman/nonfa_dbaas"
DB_SHELL_SCRIPT=BASE_DIR+"/utils/db/scripts/shell"
DB_QUERY_LOCATION=BASE_DIR+"/utils/db/sql"
FA_RMAN_ORA_PATH='/var/opt/oracle/dbaas_acfs'
NONFA_DBAAS_RMAN_OPC_PATH='/opt/oracle/dcs/commonstore/objectstore/opc_pfile'
NONFA_DBAAS_LIBOPC='/opt/oracle/dcs/commonstore/pkgrepos/oss'
OPC_LIB_PATH='{0}/oci_backup'.format(FA_RMAN_ORA_PATH)


#database config paths
TEMP_DB_SPEC_FILE = "{0}/config/db/db_spec_file.spec".format(BASE_DIR)
DB_CONFIG_PATH=BASE_DIR+"/config/db"
WALLET_CONFIG_PATH=BASE_DIR+"/config/wallet"
CONFIG_PATH=BASE_DIR+"/config"
ALL_POD_INFO_PATH=BASE_DIR+"/utils/db"
pod_info_file = ALL_POD_INFO_PATH + '/all-pod-info_' + HOST_NAME + '.txt'
pod_wallet_file = EXALOGS_PATH + '/all-pod-info_' + HOST_NAME + '.txt'
DECRYPT_TOOL=DB_CONFIG_PATH+"/decrypt"

#query pool path
ORACLE_USER_HOME="/home/oracle"
SETPY_PATH=BASE_DIR+"/lib/python/common"
QUERY_POOL_PATH=BASE_DIR+"/lib/python/db"

#backup cfg paths
BACKUP_CFG_LOCATION=DB_CONFIG_PATH
BACKUP_CFG_SHARED_LOCATION="/fss/oci_backup/"
#BACKUP_CFG_FILES=['sre_db.cfg','bkup_ocifsbackup_sre.cfg','sre_db_prod.cfg','bkup_ocifsbackup_prod.cfg','sre_db_stage.cfg','bkup_ocifsbackup_stage.cfg']
BACKUP_CFG_FILES=['bkup_ocifsbackup_prod.cfg','bkup_ocifsbackup_prod_dr_enabled.cfg','bkup_ocifsbackup_stage.cfg','bkup_ocifsbackup_non_fa.cfg','bkup_ocifsbackup_dbaas.cfg']

BACKUP_CFG_LOG_DIR=ALL_POD_INFO_PATH
BACKUP_CFG_CMD_LOCATION="/var/opt/oracle/ocde/assistants/bkup"
PROCESS_LIST_FILE_LOCATION=DB_BACKUP_LOG_PATH+"/exalogs/"+"process_list.txt"
SHARED_FSS_LOCATION="/fss/oci_backup/stage/"
ENV_TYPE_PROD = 60
ENV_TYPE_STAGE = 30

#Update password file 
lock_file_path = "/tmp/passwd.lock"
lock_file_name = "passwd.lock"
password_file_name = ".passwd.json"
password_file_path = "/tmp/.passwd.json"
format_data1 = "%Y-%m-%dT%H:%M:%S"
#wallet and artifacts 
ARTIFACTS_BASE_PATH = FA_RMAN_ORA_PATH
FAOPS_OSS_INFO = "{0}/config/faops-backup-oss-info.json".format(BASE_DIR)
BACKUP_PRIORITY = "{0}/backup_priority.json".format(DB_CONFIG_PATH)
RETRY_INFO = "{0}/config/oci_retry.json".format(BASE_DIR)
# ARTIFACTS_BACKUP_PATH = "/fss/oci_backup/artifacts"
ARTIFACTS_BACKUP_PATH = "/fss/oci_backup/artifacts/{0}".format(HOST_NAME)
base_path_ini="/var/opt/oracle/creg"
DB_CONFIG_PATH_JSON=DB_CONFIG_PATH+"/db_config.json"
#WALLET_BACKUP_CONFIG_PATH=DB_CONFIG_PATH+"/db_wallet.json"
NONFA_ARTIFACTS_CONFIG_PATH=DB_CONFIG_PATH+"/nonfa_db_artifacts.json"
NONFA_WALLET_BACKUP_CONFIG_PATH=DB_CONFIG_PATH+"/nonfa_db_wallet.json"
INI_LOCATION='/var/opt/oracle/creg/'

##Add wallet & artificats backup config. prod: 60, stage: 30
#Bug 35433487 - WALLET BACKUPS ARE CONSUMING TERA BYTES OF SPACE ON FSS  added new key "offline_db" : 120
backup_opts_wallet_artifact = {
  "wallet_artifacts": {
       "prod" : {
         "retention":60
       },
       "prod_dr_enabled" : {
         "retention":60
       },
       "non_fa" : {
         "retention":60
       },
       "stage" : {
         "retention":30
       },
       "offline_db" : {
         "retention":120
       },
       "em_exa" : {
         "retention":60
       },
       "dbaas" : {
         "retention":60
       }
  }
}

# Database Backup Configs
BACKUP_SUPPORTED = [ 
  "db_to_reco_db_arch_to_oss", 
  "incre_to_reco_arch_to_oss", 
  "incre_to_oss_arch_to_oss", 
  "archivelog_to_oss",
  "db_to_reco",
  "db_to_oss",
  "validate",
  "validate_db_reco",
  "validate_db_oss",
  "restore_validate",
  "restore_validate_reco",
  "restore_validate_oss"
  ]
backup_opts = {
  "db_to_reco_db_arch_to_oss": {
       "prod" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "stage" : {
         "retention":30,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "em_exa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "dbaas" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12

       }
  },
  "database_compressed_to_oss": {
       "prod" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "stage" : {
         "retention":30,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
        "em_exa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
        "dbaas" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12

       }
  },
  "ldb_database_compressed_to_oss": {
       "prod" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 4
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "stage" : {
         "retention":30,
         "tag": "compressed_full_to_oss",
         "channels": 4
       },
        "em_exa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12

       },
        "dbaas" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12

       }
  },
  "db_to_oss": {
       "prod" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
       "stage" : {
         "retention":30,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
        "em_exa" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12
       },
        "dbaas" : {
         "retention":60,
         "tag": "compressed_full_to_oss",
         "channels": 12

       }
  },
  "incre_to_reco_arch_to_oss": {
      "prod" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":30,
         "tag": "backupset_level_0",
         "channels": 12
       },
        "em_exa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
        "dbaas" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "incremental_to_reco": {
      "prod" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "incre_to_oss_arch_to_oss": {
       "prod" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":30,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "incremental_to_oss": {
      "prod" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":30,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "archivelog_to_oss": {
      "prod" : {
         "retention":7,
         "tag": "backupset_level_0",
         "channels": 4
       },
       "prod_dr_enabled" : {
         "retention":7,
         "tag": "backupset_level_0",
         "channels": 4
       },
       "non_fa" : {
         "retention":7,
         "tag": "backupset_level_0",
         "channels": 4
       },
      "stage" : {
         "retention":7,
         "tag": "NA",
         "channels": 4
       },
       "em_exa" : {
         "retention":7,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":7,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "db_to_reco": {
      "prod" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "database_to_reco": {
      "prod" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "ldb_database_to_reco": {
      "prod" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 4
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 4
       },
       "non_fa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 4
       },
      "stage" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 4
       },
       "em_exa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "pdbseed_to_reco": {
      "prod" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "non_fa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
      "stage" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "em_exa" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "backupset_level_0",
         "channels": 12
       }
  },
  "obsolete_backupset_withoss": {
      "prod" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 8
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 8
       },
       "non_fa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 8
       },
      "stage" : {
         "retention":30,
         "tag": "backupset_level_0",
         "channels": 8
       },
       "em_exa" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 8
       },
       "dbaas" : {
         "retention":60,
         "tag": "backupset_level_0",
         "channels": 8
       }
  },
  "validate": {
       "prod" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "non_fa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
      "stage" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "em_exa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "dbaas" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       }
  },
  "validate_db_reco": {
      "prod" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       },
       "non_fa" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       },
      "stage" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       },
       "em_exa" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       },
       "dbaas" : {
         "retention":14,
         "tag": "NA",
         "channels": 12
       }
  },
  "validate_db_oss": {
      "prod" : {
         "retention":60,
         "tag": "NA",
         "channels": 8
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "NA",
         "channels": 8
       },
       "non_fa" : {
         "retention":60,
         "tag": "NA",
         "channels": 8
       },
      "stage" : {
         "retention":30,
         "tag": "NA",
         "channels": 8
       },
       "em_exa" : {
         "retention":60,
         "tag": "NA",
         "channels": 8
       },
       "dbaas" : {
         "retention":60,
         "tag": "NA",
         "channels": 8
       }
  },
  "restore_validate": {
      "prod" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "non_fa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
      "stage" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "em_exa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "dbaas" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       }
  },
  "restore_validate_reco": {
      "prod" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "prod_dr_enabled" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "non_fa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
      "stage" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "em_exa" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       },
       "dbaas" : {
         "retention":14,
         "tag": "NA",
         "channels": 8
       }
  },
  "restore_validate_oss": {
      "prod" : {
         "retention":60,
         "tag": "NA",
         "channels": 12
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "NA",
         "channels": 12
       },
       "non_fa" : {
         "retention":60,
         "tag": "NA",
         "channels": 12
       },
      "stage" : {
         "retention":30,
         "tag": "NA",
         "channels": 12
       },
       "em_exa" : {
         "retention":60,
         "tag": "NA",
         "channels": 12
       },
       "dbaas" : {
         "retention":60,
         "tag": "NA",
         "channels": 12
       }
  },
  "ldb_restore_validate_oss": {
       "prod" : {
         "retention":60,
         "tag": "NA",
         "channels": 4
       },
       "prod_dr_enabled" : {
         "retention":60,
         "tag": "NA",
         "channels": 4
       },
       "non_fa" : {
         "retention":60,
         "tag": "NA",
         "channels": 4
       },
      "stage" : {
         "retention":30,
         "tag": "NA",
         "channels": 4
       },
       "em_exa" : {
         "retention":60,
         "tag": "NA",
         "channels": 4
       },
       "dbaas" : {
         "retention":60,
         "tag": "NA",
         "channels": 4
       }
  }
}
NODE1_BACKUP_TYPES=["incre_to_reco_arch_to_oss", "incre_to_oss_arch_to_oss", "archivelog_to_oss"]
remote_backup_types = ['db_to_oss','db_to_reco','db_to_reco_db_arch_to_oss']

remote_backup_states_csv_file = "{0}/exalogs/ldb_exec_states_v2.csv".format(DB_BACKUP_LOG_PATH)

ETC_CRONTAB_COMMENT_VALUES = [
  "grid /var/opt/oracle/cleandb/cleandblogs.pl",
  "oracle /var/opt/oracle/cleandb/cleandblogs.pl", 
  "/var/opt/oracle/bkup_api/bkup_api", 
  "oracle /var/opt/oracle/misc/backup_db_wallets.pl",
  "root /var/opt/oracle/misc/archive_del_oh.pl"
  ]


#Resume backup variables 

resume_backup_restore_error=["RMAN-03002",'RMAN-03009']
resume_backup_types = ['db_to_oss','ldb_db_to_oss','database_compressed_to_oss','ldb_database_compressed_to_oss']

#instance cert validation

instance_cert="http://169.254.169.254/opc/v1/identity/cert.pem"
POD_REL_INFO="/u01/APPLTOP/instance/lcm/metadata/pod.properties"

ohs_backup_file = "/opt/faops/spe/ocifabackup/config/mt/ohs_backup_config/ohs_backup.json"
#fabackup error code 
DB_ERROR_CODE_JSON=DB_CONFIG_PATH+"/fabackup_error_code.json"
db_archive_backup_path=DB_BACKUP_LOG_PATH + '/exalogs/db_archive_backup.txt'
db_con_timeout=300
validate_backup_queue_delata=4

validate_queue_btp = ["validate","restore_validate"]
