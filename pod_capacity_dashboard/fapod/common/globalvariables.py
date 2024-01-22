from dotenv import load_dotenv
import os
import sys
import datetime
import oci

# color codes
RED='\033[31m'
AMBER='\033[33m'
GREEN='\033[32m'
RESET='\033[0m'

# os.chdir("/Users/amharees/Desktop/hareesh/project/vipin_scripts/pod_capacity_dashboard/fapod")
# os.chdir("/Users/vazad/Desktop/pod_capacity_dashboard/pod_capacity_dashboard/fapod")
base_path = os.path.dirname(os.getcwd())
# print("base path-> {0}".format(base_path))
dotenv_path="{0}/creds/.env".format(base_path)
env_temp="{0}/creds/env_temp".format(base_path)
raw_psr="{0}/fapod/outdir_log/raw_psr_data".format(base_path)
if not os.path.exists(raw_psr):
    os.makedirs(raw_psr)
raw_profile="{0}/fapod/outdir_log/raw_profile_data".format(base_path)
if not os.path.exists(raw_profile):
    os.makedirs(raw_profile)
processed_psr="{0}/fapod/outdir_log/processed_psr_data".format(base_path)
if not os.path.exists(processed_psr):
    os.makedirs(processed_psr)
raw_vpn="{0}/fapod/outdir_log/raw_vpn_data".format(base_path)
if not os.path.exists(raw_vpn):
    os.makedirs(raw_vpn)
    
all_poddb_data = "{0}/fapod/outdir_log/all_poddb_data".format(base_path)
if not os.path.exists(all_poddb_data):
    os.makedirs(all_poddb_data)

size_template="{0}/fapod/common/size_template.json".format(base_path)
session_json="{0}/fapod/outdir_log/session.json".format(base_path)

if not os.path.exists(dotenv_path):
    print("{0}#".format(RED)*127)
    print("{0}# Please make sure to create '.env' file under :{1} #".format(RED,dotenv_path))
    print("{0}# .env template can be found  => {1}            #".format(RED,env_temp))
    print("{0}#".format(RED)*127)
    print(RESET)
    sys.exit(1)

oci_config_path="{0}/creds/config".format(base_path)

############################################################


if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    oci_com_key="../creds/{0}".format(os.getenv("oci_oc1_comm_boat_key_file"))
    oci_ukg_key="../creds/{0}".format(os.getenv("oci_oc4_ukg_boat_key_file"))
    oci_eura_key="../creds/{0}".format(os.getenv("oci_oc1_eura_boat_key_file"))
    oci_ppd_key="../creds/{0}".format(os.getenv("oci_oc1_ppd_boat_key_file"))
    fapod_confing_file=oci.config.from_file(profile_name="fapod_oci_config")
    env_dictionary={"commercial":{"oci_config":fapod_confing_file,"cloud_meta":{"url" : os.getenv("JC_COMM_URL"),"username" : os.getenv("JC_COMM_USER_NAME"),"password" : os.getenv("JC_COMM_USER_PASS")},"ten_name":os.getenv("oci_oc1_comm_tenancy_name"),"ten_id":os.getenv("oci_oc1_comm_tenancy_ocid")},"ukg":{"oci_config":fapod_confing_file,"cloud_meta":{"url" : os.getenv("JC_UKG_URL"),"username" : os.getenv("JC_UKG_USER_NAME"),"password" : os.getenv("JC_UKG_USER_PASS")},"ten_name":os.getenv("oci_oc4_ukg_tenancy_name"),"ten_id":os.getenv("oci_oc4_ukg_tenancy_ocid")},"eura":{"oci_config":fapod_confing_file,"ten_name":os.getenv("oci_oc1_eura_tenancy_name"),"ten_id":os.getenv("oci_oc1_eura_tenancy_ocid")},"ppd":{"oci_config":fapod_confing_file}}
    #env_dictionary={"commercial":{"oci_config":{"user": os.getenv("oci_oc1_comm_boat_user"),"key_file": oci_com_key,"fingerprint": os.getenv("oci_oc1_comm_boat_fingerprint"),"tenancy": os.getenv("oci_oc1_comm_boat_tenancy_ocid"),"region": os.getenv("oci_oc1_comm_region")},"cloud_meta":{"url" : os.getenv("JC_COMM_URL"),"username" : os.getenv("JC_COMM_USER_NAME"),"password" : os.getenv("JC_COMM_USER_PASS")},"ten_name":os.getenv("oci_oc1_comm_tenancy_name"),"ten_id":os.getenv("oci_oc1_comm_tenancy_ocid")},"ukg":{"oci_config":{"user": os.getenv("oci_oc4_ukg_boat_user"),"key_file": oci_ukg_key,"fingerprint": os.getenv("oci_oc4_ukg_boat_fingerprint"),"tenancy": os.getenv("oci_oc4_ukg_boat_tenancy_ocid"),"region": os.getenv("oci_oc4_ukg_region")},"cloud_meta":{"url" : os.getenv("JC_UKG_URL"),"username" : os.getenv("JC_UKG_USER_NAME"),"password" : os.getenv("JC_UKG_USER_PASS")},"ten_name":os.getenv("oci_oc4_ukg_tenancy_name"),"ten_id":os.getenv("oci_oc4_ukg_tenancy_ocid")},"eura":{"oci_config":{"user": os.getenv("oci_oc1_eura_boat_user"),"key_file": oci_eura_key,"fingerprint": os.getenv("oci_oc1_eura_boat_fingerprint"),"tenancy": os.getenv("oci_oc1_eura_boat_tenancy_ocid"),"region": os.getenv("oci_oc1_eura_region")},"ten_name":os.getenv("oci_oc1_eura_tenancy_name"),"ten_id":os.getenv("oci_oc1_eura_tenancy_ocid")},"ppd":{"oci_config":{"user": os.getenv("oci_oc1_ppd_boat_user"),"key_file": oci_ppd_key,"fingerprint": os.getenv("oci_oc1_ppd_boat_fingerprint"),"tenancy": os.getenv("oci_oc1_ppd_boat_tenancy_ocid"),"region": os.getenv("oci_oc1_ppd_region")}}}
    oci_pem_loc="../creds/{0}".format(os.getenv("oci_oc1_comm_boat_key_file"))
    # print(oci_pem_loc)
    oci_config = {
        "user": os.getenv("oci_oc1_comm_boat_user"),
        "key_file": oci_pem_loc,
        "fingerprint": os.getenv("oci_oc1_comm_boat_fingerprint"),
        "tenancy": os.getenv("oci_oc1_comm_boat_tenancy_ocid"),
        "region": os.getenv("oci_oc1_comm_region")
    }

    # create config file
#     with open(oci_config_path,'w+') as config:
#         config_contents = """
# [boat_login]
# user={0}
# fingerprint={1}
# tenancy={2}
# key_file={4}
#         """.format(os.getenv("oci_user"),os.getenv("oci_fingerprint"),os.getenv("oci_tenancy"),os.getenv("oci_region"),os.getenv("oci_key_file"),)
#         config.writelines(config_contents)



    #
    cloud_meta = {
        "url" : os.getenv("JC_COMM_URL"),
        "username" : os.getenv("JC_COMM_USER_NAME"),
        "password" : os.getenv("JC_COMM_USER_PASS")
    }
    tenancy_id=os.getenv("oci_oc1_comm_tenancy_ocid")
    # print(oci_config)
else:
    oci_config = None
    cloud_meta = None
    print(".env file not present on {0}".format(dotenv_path))


############################################################
faas_tenancy = "ocid1.tenancy.oc1..aaaaaaaaqgj4jtr7apjl65fnr5dmerg7zory5qcs7cpd6qcibk2gczefh4qa"

sizing_profile_endpoints = {
  "commercial":"https://prod-ops-fusionapps.us-phoenix-1.oci.oraclecloud.com/20191001/podSizeProfile"
}

dev_tenancy={
    "comp_id":"ocid1.tenancy.oc1..aaaaaaaack5ncdw275e6cffsinab575lw3vnzewarcuvwq7zbv2yn5bvdrka",
    "ns":"axxyy35wuycx",
    "bn":"fsremw-artifacts"
}
# data_path="{0}/fapod/common/data/".format(base_path)
arc_map=["AMDE4FULL","AMD","X6","X7","X9","ARMA1"]


date_time=datetime.datetime.now()
today_date=date_time.strftime("%Y%m%d")

psr_data={
    "stamp_pod_url":"https://objectstorage.us-ashburn-1.oraclecloud.com/p/k5mw50Vb0sYMvgK1z6dwqN54DFrGu3N4-8TcTyaKEgCQCXh69IoS1tLEPUBbgra2/n/idfl2ow6j7cl/b/ResizingTracker/o/Weekly_Upcoming_Stamp_POD_Report_"+today_date+".json",
    "manual_pod_url": "https://objectstorage.us-ashburn-1.oraclecloud.com/p/k5mw50Vb0sYMvgK1z6dwqN54DFrGu3N4-8TcTyaKEgCQCXh69IoS1tLEPUBbgra2/n/idfl2ow6j7cl/b/ResizingTracker/o/Weekly_Upcoming_Manual_POD_Report_"+today_date+".json"
}

data_files={
    "vpn_data":{"filename":"vpn_pod_data.json",
              "timedelta":4},
    "manual_psr_data":{"filename":"manual_pod_data.json",
              "timedelta":24},
    "stamp_psr_data":{"filename":"stamp_pod_data.json",
              "timedelta":24},
    "resize_lcm_profile_data":{"filename":"lcm_resize_profile.json",
              "timedelta":24},
    "manual_resize_capacity":{"filename":"manual_resize_capacity.json",
              "timedelta":4},
    "stamp_resize_capacity":{"filename":"stamp_resize_capacity.json",
              "timedelta":4}

}

resize_type=["T-Shirt","Scaleout"]
x_shape=["VM.Standard2.4","VM.Standard2.1","VM.Standard2.8","VM.Standard2.2","VM.Standard2.16","VM.Standard.B1.8","VM.Standard.B1.16"]

post_session_url="https://g6a07596b28be13-fsremwdso.adb.us-phoenix-1.oraclecloudapps.com/ords/fsrepodcapacity/data/session"
