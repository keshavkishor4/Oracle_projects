import json
import os
import sys
import time
import datetime
import requests
import oci
sys.path.append("../")
from common import globalvariables,ociSDK

#'https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/v2/FUSION/pods?name\[like\]=EEHO%25'
# New Code Adding w.r.t oci session authenticate
def oci_token_code(config):
    token_file = config['security_token_file']
    token = None
    with open(token_file, 'r') as f:
        token = f.read()
        #print(token)
    private_key = oci.signer.load_private_key_from_file(config['key_file'])
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
    #print(client)
    #result = client.list_region_subscriptions(config['tenancy'])
    #print(result.data)
    return signer

def oci_token_code_1(config):
    token_file = config['security_token_file']
    token = None
    with open(token_file, 'r') as f:
        token = f.read()
        #print(token)
    private_key = oci.signer.load_private_key_from_file(config['key_file'])
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    #client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
    return signer

def get_token(account):
    base_path = os.path.dirname(os.getcwd())
    tokenfile="{0}/creds/token.txt".format(base_path)
    if os.path.exists(tokenfile):
        if os.path.getsize(tokenfile) == 0:
            print("File is empty!...")
            with open(tokenfile,"w") as k:
                result=get_token__(account)
                k.write("{0}|{1}".format(datetime.datetime.now(),result))
            return result
        with open(tokenfile) as f:
            data=f.readline().split("|")
            if data[1] == 'None':
                with open(tokenfile,"w") as k:
                    result=get_token__(account)
                    k.write("{0}|{1}".format(datetime.datetime.now(),result))
                return result
            else:
                value=data[0]
                format='%Y-%m-%d %H:%M:%S.%f'
                then=datetime.datetime.strptime(value, format)
                now=datetime.datetime.now()
                difference = now - then
                seconds_in_day = 24 * 60 * 60
                #print(str(divmod(difference.days * seconds_in_day + difference.seconds, 60)[0]) + "Minutes time")
                if divmod(difference.days * seconds_in_day + difference.seconds, 60)[0] > 50 or data[1] is None:
                    with open(tokenfile,"w") as k:
                        result=get_token__(account)
                        k.write("{0}|{1}".format(datetime.datetime.now(),result))
                    return result
                else:
                    return str(data[1])
    else:
        #print("else statement")
        with open(tokenfile,"w") as f:
            result=get_token__(account)
            f.write("{0}|{1}".format(datetime.datetime.now(),result))
        return result
    #print("Startiing---- Ifelse")

def get_token__(account):
    headersAuth = {
        'Authorization': 'Basic',
    }
    payload = {"email": str(globalvariables.env_dictionary[account]["cloud_meta"]['username']),
    "password": str(globalvariables.env_dictionary[account]["cloud_meta"]['password'])}
    URL = "{0}/cloudmeta-api/v2/login".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'])
    try:
        response = requests.post(URL, headers=headersAuth, data=payload, verify=True)
        if response.status_code <= 399:
            j = response.json()
            #print(response.status_code)
        else:
            j['bearer']=None
        return j['bearer']
    except Exception as e:
        j['bearer']=None
        return j['bearer']
        #return e

def full_pod_data_method(pod_name,account):
    URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
    result = cloud_meta_genric(URL,account)
    return result

def exadata_node_data(exanode,account):
    URL="{0}/cloudmeta-api/v2/hostDetails?hostname={1}".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],exanode)
    result = cloud_meta_genric(URL,account)
    return result

def pod_instance_data_values(pod_name,account):
    result = cloud_meta_podattr(pod_name,account)
    return result

def pod_members_details_data(pod_name, account):
    URL = "{0}/cloudmeta-api/v2/FUSION/pods/{1}/members".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
    try:
        result = cloud_meta_genric(URL,account)
        return result
    except Exception as e:
        print(e)

def pod_compute_data(hostname, account):
    URL = "{0}/cloudmeta-api/v2/FUSION/hosts/{1}/fa_servers".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],hostname)
    try:
        result = cloud_meta_genric(URL,account)
        return result
    except Exception as e:
        print(e)
def pod_family(pod,account):
    #print(pod[:4])
    URL="{0}/cloudmeta-api/v2/FUSION/pods?name[like]={1}%25".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod[:4])
    #print(URL)
    try:
        result=cloud_meta_genric(URL,account)
        return result
    except Exception as e:
        print(e)

def cloud_meta_podattr(pod_name,account):
    URL = "{0}/cloudmeta-api/v2/podDetails".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'])
    headersAPI = {
            'accept': 'application/json',
            'Authorization': 'Bearer '+str(get_token(account)),
    }
    params={
        'pod' : str(pod_name),
        'request_type' : 'all'
    }
    try:
        response = requests.get(URL, headers=headersAPI, data=params, verify=True)
        #print(response)
        result=response.json()
        return result
    except Exception as e:
        print(e)

def cloud_meta_genric(URL,account):
    headersAPI = {
            'accept': 'application/json',
            'Authorization': 'Bearer '+str(get_token(account)),
    }
    try:
        response=requests.get(URL,headers=headersAPI,verify=True)
        result=response.json()
        return result
    except Exception as e:
        print(e)

def maintenance_level_podattr(pod_name,account):
    URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs/maintenance_level".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
    result = cloud_meta_genric(URL,account)
    try:
        return result['value'].split('_')[0]
    except Exception as e:
        print(e)
