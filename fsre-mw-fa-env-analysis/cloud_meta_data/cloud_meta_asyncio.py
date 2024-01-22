import requests
import sys
import traceback
import os
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
import time,asyncio,aiohttp

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

async def get_cloud_meta_response(session: str,URL: str,pod_name: str) -> dict:
    try:
        async with session.get(URL) as response:
            result=await response.json()
            for item in result:
                pod_size={}
                if 'pod_size' in item:
                    pod_size.update({pod_name:item['pod_size'].split(',')[0]})
                    return pod_size
    except Exception as e:
        traceback.print_exc()
        message = "{2}Error in getting data from cloud meta -> {0}{1}".format(URL,e,globalvariables.RED)
        print(message)

async def get_pods_size(pod_names: list) -> list:
    try:
        headersAPI = {
            'accept': 'application/json',
            'Authorization': 'Bearer '+str(get_token()),
        }
        async with aiohttp.ClientSession(headers=headersAPI) as session:
            tasks=[]
            for pod_name in pod_names:
                pod_name=pod_name.upper()
                URL="{0}/cloudmeta-api/v2/podDetails?pod={1}&request_type=Attributes".format(str(globalvariables.cloud_meta['url']),pod_name)
                task = asyncio.create_task(get_cloud_meta_response(session,URL,pod_name))
                tasks.append(task)
            
            pod_size_list= await asyncio.gather(*tasks)
            return pod_size_list
    except Exception as e:
        traceback.print_exc()
        message = "{2}Error in getting pod size info for pods  -> {0}{1}".format(pod_names,e,globalvariables.RED)
        print(message)

# start=time.time()
# print(asyncio.run(get_pods_size(["eeho","eino"])))
# end=time.time()
# print(f"Total time {(end - start)}sec")
# print(get_exadata_details("EDYG"))

# print(get_pod_details("epxa1a031-y4y3r7.pod2dbfrontend.prd01phx01lcm01.oraclevcn.com"))