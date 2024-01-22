import os,sys
# import panda as pd
import oracledb
from sqlalchemy import create_engine
from sqlalchemy import text
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables


user=str(globalvariables.db_cred['db_user'])
password=str(globalvariables.db_cred['db_passwd'])
dsn="fsremwdso_low"
config_dir=str(globalvariables.db_cred['wallet_loc'])
wallet_location=str(globalvariables.db_cred['wallet_loc'])
wallet_password=str(globalvariables.db_cred['wallet_passwd'])


def db_con(df,table):
    engine = create_engine(
        f'oracle+oracledb://:@',
        connect_args={
            "user": user,
            "password": password,
            "dsn": "fsremwdso_low",
            "config_dir": config_dir,
            "wallet_location": wallet_location,
            "wallet_password": wallet_password,
        })
    # df=df[['total_seconds','time','sql_id']]
    # df.rename
    df.to_sql(name=table,con=engine,if_exists='replace',index=False)