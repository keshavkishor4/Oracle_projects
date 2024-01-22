#!/usr/bin/env python3
import os
import sys
import requests
import oci
sys.path.append("../")
from common import globalvariables

try:
   import oci
   from oci.exceptions import *
   from oci.object_storage.transfer.constants import MEBIBYTE
   from oci.object_storage import UploadManager
   from oci.retry import DEFAULT_RETRY_STRATEGY
except ImportError:
   from urllib.error import HTTPError as ServiceError


class OciSdk():
    def __init__(self,account):
        # self.profile = profile
        self.account = account
        self.signer = self.__get_oci_auth_signer(globalvariables.env_dictionary[self.account]['oci_config'])
        #self.signer = oci.Signer(globalvariables.oci_config)
        #print(self.signer)
    def __get_oci_auth_signer(self, oci_config):
        print(oci_config)
        print("inside oci SDK function")
        key_file_loc = "../creds/{0}".format(oci_config.get('key_file'))
        signer = oci.Signer(tenancy=oci_config.get('tenancy'), user=oci_config.get('user'),
                                fingerprint=oci_config.get('fingerprint'),
                                #private_key_file_location=oci_config.get('key_file'),
                                private_key_file_location=key_file_loc,
                                pass_phrase=oci_config.get('pass_phrase'))

        return signer

#    @backoff.on_exception(backoff.expo, ServiceError, max_tries=2)
    def fetch_details_from_endpoint_url(self, reqtype, endpoint):
        self.reqtype = reqtype
        self.endpoint = endpoint
        print(endpoint)
        if self.reqtype == "GET":
            try:
                response = requests.get(self.endpoint, auth=self.signer)
                return response.json()
            except Exception as e:
                message = "Exception in OCI request,  {0}".format(e)
                print(message)

    def get_object_data(self,file_name):

        oss_namespace=globalvariables.dev_tenancy["ns"]
        oss_bucket=globalvariables.dev_tenancy["bn"]
        comp_id=globalvariables.dev_tenancy["comp_id"]
        config = globalvariables.env_dictionary[self.account]['oci_config']

        object_storage = oci.object_storage.ObjectStorageClient(config,id=comp_id)
        try:
            obj = object_storage.get_object(oss_namespace, oss_bucket, file_name).data

            # print(obj.raw)
            # restore_path="/Users/vazad/Desktop/pod_capacity_dashboard/pod_capacity_dashboard/fapod/test.json"
            # streaming it into file in 1 MB chunks
            # print(obj.content)
            # file = "{0}/{1}".format(globalvariables.data_path,file_name)
            # if file:
            #     with open(file, 'wb') as f:
            #         for chunk in obj.raw.stream(1024 * 1024, decode_content=False):
            #             f.write(chunk)
            #     f.close()
            #     return None
            # else:
            #     return obj.content
            #
            return obj.content
        except ServiceError as e:
            message = "Failed to get object!\n{0}{1}".format(
                sys.exc_info()[1:2], e)
            print(message)
            raise
