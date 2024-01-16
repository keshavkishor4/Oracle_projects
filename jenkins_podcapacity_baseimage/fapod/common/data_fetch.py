import requests
import sys
import datetime
import json
import os
import traceback
import shutil
sys.path.append("../")
from common import globalvariables,ociSDK



class fetch:

    def __init__(self) -> None:
        pass

    def check_file_age(self,filename,td):
        try:
            if os.path.exists(filename):
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(filename))
                # print(file_time)
                nw = datetime.datetime.now()
                lt_file_time = nw - datetime.timedelta(hours=td)
                # print(lt_file_time)
                if file_time > lt_file_time:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            traceback.print_exc()
            print("{0}fun ->check_file_age raised exception {1} ".format(globalvariables.RED,e))

    def vpn_data(self,account):
        try:
            timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            date_time=datetime.datetime.now()
            td = datetime.timedelta(days = 1)
            f_date = date_time - td
            file_date=f_date.strftime("%Y%m%d")
            file_name="fa_vpn_fc_usage_{0}.json".format(file_date)
            vpn_pod_json_file="{0}/{1}".format(globalvariables.raw_vpn,globalvariables.data_files["vpn_data"]["filename"])
            timedelta = globalvariables.data_files["vpn_data"]["timedelta"] # Time delta for no of hours to check how old is file.
            if not self.check_file_age(vpn_pod_json_file,timedelta):
                if os.path.exists(globalvariables.raw_vpn):
                    oci_sdk=ociSDK.OciSdk(account)
                    data = oci_sdk.get_object_data(file_name)
                    data=data.decode()
                    if os.path.exists(vpn_pod_json_file):
                        shutil.copy2(vpn_pod_json_file,vpn_pod_json_file.split('.')[0]+"_"+timestamp+"."+"json")
                    with open(vpn_pod_json_file,'w') as jd:
                        json.dump(data,jd,indent=6)
                    return True, vpn_pod_json_file
                else:
                    print("{0} Given dir PATH ==> \"{1}\" does not exist".format(globalvariables.RED,globalvariables.raw_vpn))
                    return False,vpn_pod_json_file
            else:
                return True, vpn_pod_json_file
        except Exception as e:
            traceback.print_exc()
            print("{0}fun ->vpn_data raised exception {1} ".format(globalvariables.RED,e))

    def manual_psr_data(self):
        try:
            timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            manual_pod_json_file="{0}/{1}".format(globalvariables.raw_psr,globalvariables.data_files["manual_psr_data"]["filename"])
            timedelta=globalvariables.data_files["manual_psr_data"]["timedelta"]
            if not self.check_file_age(manual_pod_json_file,timedelta):
                if os.path.exists(globalvariables.raw_psr):
                    manual_pod_url_result=requests.get(globalvariables.psr_data["manual_pod_url"],verify=True)
                    stamp_pod_content=manual_pod_url_result.json()
                    if os.path.exists(manual_pod_json_file):
                        shutil.copy2(manual_pod_json_file,manual_pod_json_file.split('.')[0]+"_"+timestamp+"."+"json")
                    with open(manual_pod_json_file,'w') as jd:
                        json.dump(stamp_pod_content,jd,indent=6)
                    return True, manual_pod_json_file
                else:
                    print("{0} Given dir PATH ==> \"{1}\" does not exist".format(globalvariables.RED,globalvariables.raw_psr))
                    return False,manual_pod_json_file
            else:
                return True, manual_pod_json_file
        except Exception as e:
            traceback.print_exc()
            print("{0}fun ->manual_psr_data raised exception {1} ".format(globalvariables.RED,e))

    def stamp_psr_data(self):
        try:
            timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            stamp_pod_json_file="{0}/{1}".format(globalvariables.raw_psr,globalvariables.data_files["stamp_psr_data"]["filename"])
            timedelta=globalvariables.data_files["stamp_psr_data"]["timedelta"]
            if not self.check_file_age(stamp_pod_json_file,timedelta):
                if os.path.exists(globalvariables.raw_psr):
                    stamp_pod_url_result=requests.get(globalvariables.psr_data["stamp_pod_url"],verify=True)
                    stamp_pod_content=stamp_pod_url_result.json()
                    if os.path.exists(stamp_pod_json_file):
                        shutil.copy2(stamp_pod_json_file,stamp_pod_json_file.split('.')[0]+"_"+timestamp+"."+"json")
                    with open(stamp_pod_json_file,'w') as jd:
                        json.dump(stamp_pod_content,jd,indent=6)
                    print("stamp pod data " )
                    print(stamp_pod_json_file)
                    return True, stamp_pod_json_file
                else:
                    print("{0} Given dir PATH ==> \"{1}\" does not exist".format(globalvariables.RED,globalvariables.raw_psr))
                    return False,stamp_pod_json_file
            else:
                return True, stamp_pod_json_file
        except Exception as e:
            traceback.print_exc()
            print("{0}fun ->stamp_psr_data raised exception {1} ".format(globalvariables.RED,e))

    def resize_lcm_profile_data(self,account):
        try:
            timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            lcm_resize_profile="{0}/{1}".format(globalvariables.raw_profile,globalvariables.data_files["resize_lcm_profile_data"]["filename"])
            timedelta=globalvariables.data_files["resize_lcm_profile_data"]["timedelta"]
            if not self.check_file_age(lcm_resize_profile,timedelta):
                if os.path.exists(globalvariables.raw_profile):
                    URL = globalvariables.sizing_profile_endpoints["commercial"]
                    oci_sdk=ociSDK.OciSdk(account) #-------> Using account here
                    response = oci_sdk.fetch_details_from_endpoint_url("GET",URL)
                    if os.path.exists(lcm_resize_profile):
                        shutil.copy2(lcm_resize_profile,lcm_resize_profile.split('.')[0]+"_"+timestamp+"."+"json")
                    with open(lcm_resize_profile,'w') as jd:
                        json.dump(response,jd,indent=6)
                    return True, lcm_resize_profile
                else:
                    print("{0} Given dir PATH ==> \"{1}\" does not exist".format(globalvariables.RED,globalvariables.raw_profile))
                    return False,lcm_resize_profile
            else:
                return True, lcm_resize_profile
        except Exception as e:
            traceback.print_exc()
            print("{0}fun ->resize_lcm_profile_data raised exception {1} ".format(globalvariables.RED,e))

    def cloudmeta_podattribute(self,pod_name):
        URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs".format(globalvariables.cloud_meta['url'],pod_name)
        result = self.cloud_meta_genric(URL)
        # print(result)
        return result

    def get_token(self):
        headersAuth = {
            'Authorization': 'Basic',
        }
        payload = {"email": str(globalvariables.cloud_meta['username']),
        "password": str(globalvariables.cloud_meta['password'])}
        URL = "{0}/cloudmeta-api/v2/login".format(globalvariables.cloud_meta['url'])
        try:
            response = requests.post(URL, headers=headersAuth, data=payload, verify=True)
            j = response.json()
            return j['bearer']
        except Exception as e:
            print(e)

    def cloud_meta_genric(self,URL):
        headersAPI = {
                'accept': 'application/json',
                'Authorization': 'Bearer '+str(self.get_token()),
        }
        try:
            response=requests.get(URL,headers=headersAPI,verify=True)
            result=response.json()
            return result
        except Exception as e:
            print(e)
