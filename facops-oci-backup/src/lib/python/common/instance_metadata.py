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
    Zakki Ahmed           11/02/21 - Refactor major sections
"""
#### imports start here ##############################
import sys
import json
import os
import socket
BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python/common")
import apscom
import requests
import commonutils
from datetime import timedelta

#### imports end here ##############################

class ins_metadata():
    def __init__(self):
        try:
            inst_metadata = self.get_inst_metadata()
            self._inst_metadata=inst_metadata
            self._post_inst_metadata = inst_metadata
            if "compartmentId" in inst_metadata.keys():
                self._app_compart_ocid = inst_metadata["compartmentId"]
            if "availabilityDomain" in inst_metadata.keys():
                self._availability_domain = inst_metadata["availabilityDomain"]
            if "id" in inst_metadata.keys():
                self._instance_ocid = inst_metadata["id"]
            if "canonicalRegionName" in inst_metadata.keys():
                self._region = inst_metadata["canonicalRegionName"]
            if "regionInfo" in inst_metadata.keys():
                self._realmKey = inst_metadata["regionInfo"]["realmKey"]
            else:
                self._realmKey = "oc1"
            if "dbSystemShape" in inst_metadata["metadata"]:
                self._dbSystemShape = inst_metadata["metadata"]["dbSystemShape"]
            system_category = self.get_system_category(inst_metadata)
            self._system_category=system_category
            self._post_system_category = system_category
            system_type = self.get_system_type(system_category)
            self._system_type=system_type
            self._default_bucket = self.get_default_bucket(system_category)
            if "userdata" in inst_metadata["metadata"]:
                userdata = inst_metadata["metadata"]["userdata"]
                if "block_enabled" in userdata.keys():
                    self._block_enabled = inst_metadata["metadata"]["userdata"]["block_enabled"]
                else:
                    self._block_enabled = "false"
                if "fa_service_name" in inst_metadata["metadata"]["userdata"]:
                    self._fa_service_name = inst_metadata["metadata"]["userdata"]["fa_service_name"]
                if "fadb_connstr" in userdata.keys():
                    self._fadb_connstr = inst_metadata["metadata"]["userdata"]["fadb_connstr"]
                else:
                    self._fadb_connstr = ''
            if "componentType" in inst_metadata["metadata"]:
                self._component_type = inst_metadata["metadata"]["componentType"]
        except Exception as e:
            message = "Failed to get instance metadata!\n{0}{1}".format(sys.exc_info()[1:2],e)
            apscom.warn(message)
            raise

    def get_system_type(self, system_category):
        system_type = "Unknown"
        if system_category == "FA":
            vm_list = self.inst_metadata["metadata"]["serviceVM"]
            for vm_num, vm_info in vm_list.items():
                if "this" in vm_info.keys() and vm_info["this"]:
                    system_type = vm_list[vm_num]["component"]
                    return system_type

        elif system_category == "Exadata":
            system_type = self.inst_metadata["metadata"]["dbSystemShape"]

        elif system_category == "Admin":
            system_type = "Admin"
        elif system_category == "OHS":
            system_type = "OHS"
        elif system_category == "IDM":
            system_type = "IDM"

        return system_type

    def gen_inst_metadata(self):
        instance_metadata_url="http://169.254.169.254/opc/v2/instance/"
        try:
            f=requests.get(instance_metadata_url,headers={'Authorization': 'Bearer Oracle'})
            out = json.dumps(f.json())
            json_res = json.loads(out)
            return json_res
        except Exception as e:
            message = "failed to get instance metadata \n{0}{1}".format(sys.exc_info()[1:2],e)
            print(message)
            # apscom.warn(message)
            raise
    
    def gen_inst_metadata_file(self):
        instance_metadata_url="http://169.254.169.254/opc/v2/instance/"
        LOCAL_HOST = socket.getfqdn()
        HOST_NAME=LOCAL_HOST.split(".")[0]
        OCI_INST_META_FILE= "{0}/config/{1}_instance_md.json".format(BASE_DIR,HOST_NAME)
        try:
            f=requests.get(instance_metadata_url,headers={'Authorization': 'Bearer Oracle'})
            out = json.dumps(f.json())
            with open(OCI_INST_META_FILE,'w') as f:
                json.dump(json.loads(out), f, ensure_ascii=False, indent=4)
        except Exception as e:
            message = "failed to get instance metadata \n{0}{1}".format(sys.exc_info()[1:2],e)
            print(message)
            # apscom.warn(message)
            raise


    def get_inst_metadata(self):
        """curl -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/"""
        # instance_metadata_url="http://169.254.169.254/opc/v2/instance/"
        LOCAL_HOST = socket.getfqdn()
        HOST_NAME=LOCAL_HOST.split(".")[0]
        OCI_INST_META_FILE= "{0}/config/{1}_instance_md.json".format(BASE_DIR,HOST_NAME)
        try:
            if os.path.exists(OCI_INST_META_FILE):
                status=commonutils.is_file_older_than(OCI_INST_META_FILE,timedelta(seconds=86400))
                if status:
                    apscom.info("refreshing {0}".format(OCI_INST_META_FILE))
                    self.gen_inst_metadata_file()
                    # 
                    try:
                        with open(OCI_INST_META_FILE,'r') as oci_im:
                            json_res = json.load(oci_im)
                            return json_res
                    except Exception as e:
                        message = "failed to generate instance metadata from file {2} \n{0}{1}".format(sys.exc_info()[1:2],e,OCI_INST_META_FILE)
                        apscom.warn(message)
                        self.gen_inst_metadata_file()
                        self.get_inst_metadata()
                        # raise
                else:
                    try:
                        with open(OCI_INST_META_FILE,'r') as oci_im:
                            json_res = json.load(oci_im)
                            return json_res
                    except Exception as e:
                        message = "failed to generate instance metadata from file,retrying {2} \n{0}{1}".format(sys.exc_info()[1:2],e,OCI_INST_META_FILE)
                        self.gen_inst_metadata_file()
                        self.get_inst_metadata()
                        apscom.warn(message)
                        # raise
            else:
                apscom.info("creating {0}".format(OCI_INST_META_FILE))
                self.gen_inst_metadata_file()
                # 
                try:
                    with open(OCI_INST_META_FILE,'r') as oci_im:
                        json_res = json.load(oci_im)
                        return json_res
                except Exception as e:
                    message = "failed to generate instance metadata from file {2} \n{0}{1}".format(sys.exc_info()[1:2],e,OCI_INST_META_FILE)
                    apscom.warn(message)
                    self.gen_inst_metadata_file()
                    self.get_inst_metadata()
                    # raise
            
            
        except Exception as e:
            message = "failed to get instance metadata \n{0}{1}".format(sys.exc_info()[1:2],e)
            # print(message)
            apscom.warn(message)
            raise

    # def get_inst_metadata(self):
    #     """curl -sL -H "Authorization: Bearer Oracle" http://169.254.169.254/opc/v2/instance/"""
    #     instance_metadata_url="http://169.254.169.254/opc/v2/instance/"
    #     try:
    #         f=requests.get(instance_metadata_url,headers={'Authorization': 'Bearer Oracle'})
    #         out = json.dumps(f.json())
    #         json_res = json.loads(out)
    #         return json_res
    #     except Exception as e:
    #         message = "failed to get instance metadata \n{0}{1}".format(sys.exc_info()[1:2],e)
    #         print(message)
    #         # apscom.warn(message)
    #         raise

    def get_system_category(self, inst_metadata):
        system_category = "Unknown"

        if "serviceVM" in inst_metadata["metadata"]:
            vm_list = inst_metadata["metadata"]["serviceVM"]

            for vm_num,vm_info in vm_list.items():
                if vm_info["component"] == "ADMIN" and "this" in vm_info.keys() and vm_info["this"]:
                    system_category = "Admin"
                    return system_category
                elif vm_info["component"] == "OHS" and "this" in vm_info.keys() and vm_info["this"]:
                    system_category = "OHS"
                    return system_category
                elif "IDM" in vm_info["component"] and "this" in vm_info.keys() and vm_info["this"]:
                    system_category = "IDM"
                    return system_category
                else:
                    system_category = "FA"
        else:
            if "dbSystemShape" in inst_metadata["metadata"]:
                system_category = "Exadata"

        return system_category
    def get_default_bucket(self, system_category):
        if system_category == "Exadata":
            oss_bucket = "rman_wallet_backup"
        else:
            oss_bucket = "MT_BACKUP"

        return oss_bucket

    # using property decorator
    # a getter function
    @property
    def inst_metadata(self):
        return self._inst_metadata

    @property
    def post_inst_metadata(self):
        return self._post_inst_metadata

    @property
    def app_compart_ocid(self):
        return self._app_compart_ocid

    @property
    def availability_domain(self):
        return self._availability_domain

    @property
    def instance_ocid(self):
        return self._instance_ocid

    @property
    def region(self):
        return self._region

    @property
    def realmKey(self):
        return self._realmKey

    @property
    def system_category(self):
        return self._system_category

    @property
    def post_system_category(self):
        return self._post_system_category

    @property
    def system_type(self):
        return self._system_type

    @property
    def fa_service_name(self):
        return self._fa_service_name

    @property
    def component_type(self):
        return self._component_type

    @property
    def fadb_connstr(self):
        return self._fadb_connstr

    @property
    def default_bucket(self):
        return self._default_bucket

    @property
    def block_enabled(self):
        return self._block_enabled

    @property
    def dbSystemShape(self):
        return self._dbSystemShape


