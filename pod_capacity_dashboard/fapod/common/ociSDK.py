#!/usr/bin/env python3
import os
import sys
import requests
import oci
import json
sys.path.append("../")
from common import globalvariables,podcontent

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
        # print(self.signer)
    def __get_oci_auth_signer(self, oci_config):
        #print(oci_config)
        #Adding OCI Session Suth Script
        token_file = oci_config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
            token = f.read()
        private_key = oci.signer.load_private_key_from_file(oci_config['key_file'])
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        client = oci.identity.IdentityClient({'region': oci_config['region']}, signer=signer)
        #Commenting Old Script below
        #print("inside oci SDK function")
        #key_file_loc = "{0}".format(oci_config.get('key_file'))
        #commenting key_file_loc for new authentication approach
        #key_file_loc = "../creds/{0}".format(oci_config.get('key_file'))
        #signer = podcontent.oci_token_code(config)
        """
        signer = oci.Signer(tenancy=oci_config.get('tenancy'), user=oci_config.get('user'),
                                fingerprint=oci_config.get('fingerprint'),
                                #private_key_file_location=oci_config.get('key_file'),
                                private_key_file_location=key_file_loc,
                                pass_phrase=oci_config.get('pass_phrase'))
        """
        #print(signer)

        return signer

#    @backoff.on_exception(backoff.expo, ServiceError, max_tries=2)
    def fetch_details_from_endpoint_url(self, reqtype, endpoint):
        self.reqtype = reqtype
        self.endpoint = endpoint
        #print(endpoint)
        if self.reqtype == "GET":
            try:
                response = requests.get(self.endpoint, auth=self.signer)
                return response.json()
            except Exception as e:
                message = "Exception in OCI request,  {0}".format(e)
                print(message)

    def fetch_details_from_endpoint_url_parameter(self,reqtype,endpoint):
        self.reqtype = reqtype
        self.endpoint = endpoint
        # Initialize a variable to store the opc-next-page token
        opc_next_page_token = None
        all_data = []
        try:
            while True:
                parameter = {
                    "limit": "100",
                    "page": opc_next_page_token  # Set the page token for pagination
                }
                
                response = requests.get(self.endpoint, auth=self.signer, params=parameter)
                #print(response.status_code)
                
                # Check if the response has the opc-next-page header
                if 'opc-next-page' in response.headers:
                    opc_next_page_token = response.headers['opc-next-page']
                else:
                    # If opc-next-page is not found in headers, break out of the loop
                    break
                
                json_obj = json.loads(response.text)
                
                # Append the current page of data to the list
                all_data.extend(json_obj)
            
            return all_data
        except Exception as e:
            message = "Exception in OCI request,  {0}".format(e)
            print(message)

    def get_object_data(self,file_name):

        oss_namespace=globalvariables.dev_tenancy["ns"]
        oss_bucket=globalvariables.dev_tenancy["bn"]
        comp_id=globalvariables.dev_tenancy["comp_id"]
        config = globalvariables.env_dictionary[self.account]['oci_config']
        token_file = config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
            token = f.read()
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)

        object_storage = oci.object_storage.ObjectStorageClient(config=config,signer=signer,id=comp_id)
        """
        config = globalvariables.env_dictionary[self.account]['oci_config']
        token_file = config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
            token = f.read()
        print(config)
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        object_storage = oci.object_storage.ObjectStorageClient(config=config,signer=signer,id=comp_id )
        try:
            obj = object_storage.get_object(oss_namespace, oss_bucket, file_name).data

        """
        try:
            obj = object_storage.get_object(oss_namespace, oss_bucket, file_name).data

            #print(obj.raw)
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
