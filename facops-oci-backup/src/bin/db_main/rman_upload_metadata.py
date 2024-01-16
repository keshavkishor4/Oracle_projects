#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    NAME
      rman_upload_metadata.py

    DESCRIPTION
      To upload backup metadata to oss bucket.

    NOTES

    MODIFIED           (MM/DD/YY)
    Vipin Azad         06/08/23 - jira FUSIONSRE-7494
    
"""
import json

import os
import sys
import optparse
from datetime import datetime
from time import gmtime, strftime

BASE_DIR = os.path.abspath(sys.argv[0] + "/../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom, ociSDK, globalvariables


def upload_metadata(file_path,bucket):
    try:
        if os.path.exists(file_path):
            object_name = file_path.split("/")[-1]
            out = oci_sdk.put_object(
                file_path, oss_namespace, bucket, object_name)
            if out:
                message = "Succeed to upload file {0} to oss bucket - {1}.".format(
                    object_name,bucket)
                apscom.info(message)
            else:
                message = "Failed to upload file {0} to oss bucket - {1}.".format(
                    object_name,bucket)
                apscom.warn(message)
        else:
            message = "Provided file_path does not exist - {0}.".format(file_path)
            apscom.error(message)
    except Exception as e:
        message = "Failed to backup artifacts!\n{0} {1}".format(
            sys.exc_info()[1:2],e)
        apscom.warn(message)

usage_str = """
    rman_upload_metadata.py - To upload backup metadata to oss bucket.

    # User Case 1: Do backup action
    rman_upload_metadata.py --action upload --file_path "<file path>"
"""

def parse_opts():
    try:
        """ Parse program options """
        parser = optparse.OptionParser(usage=usage_str, version="%prog 1.0")
        parser.add_option('--action', action='store', dest='action',
                          choices=['upload'], help='Specify the action chose action from list "upload".')
        parser.add_option('-c', '--config-file', action='store', dest='oci_config_path',
                          default=globalvariables.DB_CONFIG_PATH_DEFAULT, type='string', help='Path of oci config file.')
        parser.add_option('--file_path', action='store', dest='file_path', help='Used to specify tag in backup metadata')
        parser.add_option('--bucket-name', action='store', dest='bucket_name', default="")
      
        (opts, args) = parser.parse_args()
        if not opts.action or not opts.file_path:
            parser.error(
                '--action and --file_path options are require')
        return (opts, args)

    except Exception:
        message = "Failed to parse program options!\n{0}".format(sys.exc_info()[
                                                                 1:2])
        apscom.warn(message)


def main():
    try:
        global oci_sdk
        global oss_namespace
        with open(globalvariables.OCI_SDK_META_FILE, 'r') as f:
            data = json.load(f)
            oss_namespace = data["ns"]

        (options, args) = parse_opts()
        oci_config_path = options.oci_config_path
        oci_sdk = ociSDK.ociSDK(oci_config_path)
        action  = options.action
        file_path  = options.file_path
        bucket_name  = options.bucket_name
        if not bucket_name:
            with open(globalvariables.DB_CONFIG_PATH_DEFAULT,'r') as config_file:
                config_object = json.load(config_file)
                bucket_name=config_object["oss_bucket"]
        if action:
            upload_metadata(file_path,bucket_name)
        else:
            message = '"Specify the action chose action from list "upload"'
    except Exception as e:
        message = "Failed to upload file!\n{0} {1}".format(sys.exc_info()[
                                                                 1:2],e)
        apscom.error(message)

if __name__ == "__main__":
    main()