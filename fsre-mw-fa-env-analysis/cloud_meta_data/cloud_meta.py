import requests
import sys
import traceback
import os
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables

def get_token():
        headersAuth = {
            'Authorization': 'Basic',
        }
        url = "https://cloudmeta.itpa.cyf.oraclecloud.com"
        payload = { "email": str(globalvariables.cloud_meta['username']),
        "password": str(globalvariables.cloud_meta['password'])}
        URL = "{0}/cloudmeta-api/v2/login".format(url)
        try:
            response = requests.post(URL, headers=headersAuth, data=payload, verify=True)
            j = response.json()
            return j['bearer']
        except Exception as e:
            print(e)

def get_pod_size(pod_name):
    try:
        pod_name=pod_name.upper()
        URL="{0}/cloudmeta-api/v2/podDetails?pod={1}&request_type=Attributes".format(str(globalvariables.cloud_meta['url']),pod_name)
        data=get_cloud_meta_data(URL)
        for item in data:
            if 'pod_size' in item:
                return item['pod_size'].split(',')[0]
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting pod size info for pod  -> {0}{1}".format(pod_name,e)
        print(message)

def get_db_name(pod_name):
    try:
        pod_name=pod_name.upper()
        URL="{0}/cloudmeta-api/v2/podDetails?pod={1}&request_type=Attributes".format(str(globalvariables.cloud_meta['url']),pod_name)
        data=get_cloud_meta_data(URL)
        for item in data:
            if 'fusiondb_dbname' in item:
                return(item['fusiondb_dbname'])
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting pod db name  pod  -> {0}{1}".format(pod_name,e)
        print(message)
        
def get_exadata_details(pod_name):
    try:
        pod_name=pod_name.upper()
        URL="{0}/cloudmeta-api/v2/{1}/pods/{2}/exadatas".format(str(globalvariables.cloud_meta['url']),"FUSION",pod_name)
        data=get_cloud_meta_data(URL)
        return [exa["exadata"]  for exa in data ]
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting exadata details for  pod  -> {0}{1}".format(pod_name,e)
        print(message)

def get_pod_details(exadata_name):
    try:
        URL="{0}/cloudmeta-api/v2/{1}/exadatas/{2}/pods".format(str(globalvariables.cloud_meta['url']),"FUSION",exadata_name)
        data=get_cloud_meta_data(URL)
        return [pod["pod_name"]  for pod in data ]
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting pods details for exadata  -> {0}{1}".format(exadata_name,e)
        print(message)



def get_cloud_meta_data(URL):
    headersAPI = {
            'accept': 'application/json',
            'Authorization': 'Bearer '+str(get_token()),
    }
    try:
        response=requests.get(URL,headers=headersAPI,verify=True)
        result=response.json()
        return result
    except Exception as e:
        traceback.print_exc()
        message = "Error in getting data from cloud meta -> {0}{1}".format(URL,e)
        print(message)


# print(get_exadata_details("EDYG"))

# print(get_pod_details("epxa1a031-y4y3r7.pod2dbfrontend.prd01phx01lcm01.oraclevcn.com"))