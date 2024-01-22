from dotenv import load_dotenv
import os
import sys
import time
# base_path = os.path.dirname(os.getcwd())

# color codes
RED='\033[31m'
AMBER='\033[33m'
GREEN='\033[32m'
RESET='\033[0m'

BASE_DIR = os.path.abspath(__file__ +"/../../")
# sys.path.append(BASE_DIR)
dotenv_path="{0}/cred/.env".format(BASE_DIR)
print(dotenv_path)
if not os.path.exists(dotenv_path):
    print("{0}#".format(RED)*127)
    print("{0}# Please make sure to create '.env' file under :{1} #".format(RED,dotenv_path))
    print("{0}# .env template can be found  =>             #".format(RED))
    print("{0}#".format(RED)*127)
    print(RESET)
    sys.exit(1)
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    cloud_meta= {"url" : os.getenv("JC_COMM_URL"),"username" : os.getenv("JC_COMM_USER_NAME"),"password" : os.getenv("JC_COMM_USER_PASS")}
    db_cred={"db_user":os.getenv("db_user"),"db_passwd":os.getenv("db_password"),"wallet_passwd":os.getenv("wallet_password"),"wallet_loc":os.getenv("wallet_loc")}
    

odin_dashboard="https://dashboards.odin.oraclecloud.com/DART/"
odib_base_url="https://dashboards.odin.oraclecloud.com"
dart_base_url="https://dashboards.odin.oraclecloud.com/cgi-bin/dart_dashboard?"
dart_data="{0}/out_data/dart_data".format(BASE_DIR)
full_dart_data="{0}/out_data/full_dart_data".format(BASE_DIR)
exa_octo_data="{0}/out_data/octo_exa_data".format(BASE_DIR)
db_art_config_file="{0}/config/db_art/db_art_table.json".format(BASE_DIR)
prom_file="{0}/config/promql.txt".format(BASE_DIR)

#web scrapping for hanganalysis in db art - Defined the table names as per table column len in hanganalysis dashboard. 
table_name_json={
    27: "chains_details",
    13: "chains_with_most_waiters",
    5: ["top_Sessions","sessions_with_high_wait_time"],
    3: "chains_with_longest_wait",
    11:"blocking_sessions"
}

#exa cpu peak value to check noisy naighbour
# 
exa_cpu_peak=80 #int value
per_hour_count=5


exa_test_sample=["esia15-0z1dn4.pod2dbfrontend.prd01sin01lcm01.oraclevcn.com","epxa3a030-r27rm3.pod2dbfrontend.prd01phx01lcm01.oraclevcn.com"]
#dart configuration 
dart_config="{0}/config/dart_config.json".format(BASE_DIR)

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print("Finished {0} in {1} secs".format(repr(func.__name__), round(run_time, 3)))
        return value
    return wrapper