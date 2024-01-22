import pandas as pd
# import seaborn as scn
import json,os,sys,traceback
from pprint import pprint
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
from db_module import db_con,db_sql_con

def db_art_analysis(instance_id: str,pod:str,db_art_json_file:dict=None)-> dict:
    """ Do the db art analysis  
        Args:
            db_art_json_file (file): file path for json file
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return df for . 
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json_file:
            # print("not condition")
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
        else:
            db_art_json_file="{0}/{1}".format(globalvariables.dart_data,db_art_json_file)
        print(db_art_json_file)
        with open(db_art_json_file,"r") as db_art:
            j_data=json.loads(db_art.read())
        if j_data:
            df_max_total_sec, df_max_per_exec_time, df_max_aas=top_sql_analysis(j_data,pod,instance_id)
            df_event_with_high_elapsed_time=top_event_with_high_elapsed_time(j_data,pod,instance_id)
            df_db_contention=db_contention(j_data,pod,instance_id)
            df_db_load_details=db_load_info(j_data,pod,instance_id)
            df_db_blocking_session_analysis=db_blocking_session_analysis(j_data)
            return df_max_total_sec,df_max_per_exec_time,df_max_aas,df_event_with_high_elapsed_time,df_db_contention,df_db_load_details,df_db_blocking_session_analysis
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting db art analysis func - db_art_analysis {1}".format(globalvariables.RED,e)
        print(message)

def top_sql_with_total_elapsed_time(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ get the sql with high elapsed time in time series 
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return panda dataframe with sql having high elapsed time over the time. 
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "top_sql_id" in db_table:
                test=[]
                for j_data in db_table["top_sql_id"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)
        df=df[df.instance_id == instance_id][["total_seconds","time","sql_id"]].astype({'total_seconds': 'int', 'sql_id': 'object'})
        df.loc[:,["new_val"]]=df.groupby("time")["total_seconds"].transform("max")
        df=df.loc[df["total_seconds"] == df["new_val"]][["time","sql_id","total_seconds"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        # scn.barplot(x="time",y="total_seconds",data=df,orient="x",hue="sql_id",legend="full")
        return df
        # scn.lineplot(x="time",y="total_seconds",data=test_type,hue="sql_id",legend="full",palette='pastel')
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id")
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id",style="sql_id",size="sql_id",sizes=(100,40),palette="plasma")
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting high per execution time func - top_sql_with_total_elepsed_time {1}".format(globalvariables.RED,e)
        print(message)

def top_sql_with_high_per_execution_time(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ get the sql with high per execution time in time series 
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return panda dataframe with sql having high per execution time over the time. 
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "top_sql_id" in db_table:
                test=[]
                for j_data in db_table["top_sql_id"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)
        df=df[df.instance_id == str(instance_id)][["time","total_seconds","sql_id","distinct_sql_executions"]].astype({'total_seconds': 'int', 'distinct_sql_executions': 'int'})
        df["per_exe_time"]=df["total_seconds"]/df["distinct_sql_executions"]
        df=df[["time","sql_id","per_exe_time"]]
        df.loc[:,["new_val"]]=df.groupby(["time"])["per_exe_time"].transform("max")
        df=df.loc[df["per_exe_time"] == df["new_val"]][["time","sql_id","per_exe_time"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        # scn.scatterplot(x="per_exe_time",y="time",data=df,hue="sql_id",legend="full")# plt.show()
        return df
        # scn.lineplot(x="time",y="total_seconds",data=test_type,hue="sql_id",legend="full",palette='pastel')
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id")
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id",style="sql_id",size="sql_id",sizes=(100,40),palette="plasma")
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in sql with high per execution func - top_sql_with_high_per_execution_time {1}".format(globalvariables.RED,e)
        print(message)

def top_sql_with_high_aas(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ get the sql with high aas in time series 
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return panda dataframe with sql having high aas over the time. 
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "top_sql_id" in db_table:
                test=[]
                for j_data in db_table["top_sql_id"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)
        df=df[df.instance_id == str(instance_id)][["time","aas","sql_id"]].astype({'aas': 'float'})
        df.loc[:,["new_val"]]=df.groupby(["time"])["aas"].transform("max")
        df=df.loc[df["aas"] == df["new_val"]][["time","sql_id","aas"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        # scn.scatterplot(x="aas",y="time",data=df,hue="sql_id",legend="full")# plt.show()
        return df
        # scn.lineplot(x="time",y="total_seconds",data=test_type,hue="sql_id",legend="full",palette='pastel')
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id")
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id",style="sql_id",size="sql_id",sizes=(100,40),palette="plasma")
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting sql with high aas func - top_sql_with_high_aas {1}".format(globalvariables.RED,e)
        print(message)

def top_event_with_high_elapsed_time(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ get the top event with high elapsed time in time series 
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return  dataframe with event having high elapsed time. 
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "top_event" in db_table:
                test=[]
                for j_data in db_table["top_event"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)
        df=df[df.instance_id == str(instance_id)][["time","total_seconds","event_2"]].astype({'total_seconds': 'int'})
        df.loc[:,["new_val"]]=df.groupby("time")["total_seconds"].transform("max")
        df=df.loc[df["total_seconds"] == df["new_val"]][["time","event_2","total_seconds"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        # scn.scatterplot(x="total_seconds",y="time",data=df,hue="event_2",legend="full")
        # scn.scatterplot(x="aas",y="time",data=df,hue="sql_id",legend="full")# plt.show()
        return df
        # scn.lineplot(x="time",y="total_seconds",data=test_type,hue="sql_id",legend="full",palette='pastel')
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id")
        # scn.scatterplot(x="time",y="total_seconds",data=test_type,hue="sql_id",style="sql_id",size="sql_id",sizes=(100,40),palette="plasma")
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting top event with high elapsed time func - top_event_with_high_elapsed_time {1}".format(globalvariables.RED,e)
        print(message)

def top_sql_analysis(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ get the top sql analysis  
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df_max_total_sec (dataframe/json): return dataframe for top sql having high total sec. 
            df_max_per_exec_time (dataframe/json): return dataframe for top sql having per exection time.
            df_max_aas (dataframe/json): return dataframe for top sql having high aas.
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "top_sql_id" in db_table:
                test=[]
                for j_data in db_table["top_sql_id"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        print(data)
        df_max_total_sec=''
        df_max_per_exec_time=''
        df_max_aas=''
        if data:
            df=pd.DataFrame(data)
            df=df[df.instance_id == str(instance_id)][["total_seconds","aas","distinct_sql_executions","time","sql_id","module"]].astype({'total_seconds': 'int','aas':'float','distinct_sql_executions':'int','sql_id': 'str','module':'str'})
            df.loc[:,["per_exec_time"]]=df["total_seconds"]/df["distinct_sql_executions"]
            df.loc[:,["max_total_Sec"]]=df.groupby("time")["total_seconds"].transform("max")
            df.loc[:,["max_per_exc_time"]]=df.groupby("time")["per_exec_time"].transform("max")
            df.loc[:,["max_aas"]]=df.groupby("time")["aas"].transform("max")
            df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
            df.loc[:,["sql_details"]]=df["sql_id"] +":"+ df["module"]
            # df=df.loc[(df["total_seconds"] == df["max_total_Sec"]) & (df["per_exec_time"] == df["max_per_exc_time"]) & (df["aas"] == df["max_aas"]) ]
            # print(df)

            df_max_total_sec=df.loc[df["total_seconds"] == df["max_total_Sec"]][["time","sql_details","total_seconds","sql_id"]]
            df_max_total_sec["total_time_min"]=df_max_total_sec["total_seconds"]/60
            df_max_per_exec_time=df.loc[df["per_exec_time"] == df["max_per_exc_time"]][["time","sql_details","per_exec_time","sql_id"]]
            df_max_aas=df.loc[df["aas"] == df["max_aas"]][["time","sql_details","aas","sql_id"]]
            df=df.loc[(df["total_seconds"] == df["max_total_Sec"]) & (df["per_exec_time"] == df["max_per_exc_time"]) & (df["aas"] == df["max_aas"]) ]
            df=df[['total_seconds', 'aas', 'distinct_sql_executions', 'time', 'sql_id','module', 'per_exec_time', 'sql_details']]
            # print([tuple(x) for x in df.values ])
            df.loc[:,["pod"]]=pod
            # print(df)
            # db_con.df_to_db(df)
            # df=
            # db_sql_con.db_con(df,'test1234')
            return df_max_total_sec, df_max_per_exec_time, df_max_aas
        else:
            return df_max_total_sec, df_max_per_exec_time, df_max_aas
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting top sql analysis func - top_sql_analysis {1}".format(globalvariables.RED,e)
        print(message)

def db_contention(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ do the db contention analysis  
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return dataframe for db_contention over the time.
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "db_contention" in db_table:
                test=[]
                for j_data in db_table["db_contention"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)

        return df
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in db contention analysis func - db_contention {1}".format(globalvariables.RED,e)
        print(message)

def db_load_info(db_art_json:dict,pod:str,instance_id: str)-> dict:
    """ do the db load analysis  
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            df (dataframe/json): return dataframe for db load info over the time.
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EODR_db_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        data=[]
        for db_table in db_art_json:
            if "db_load_information_as_of_now" in db_table:
                test=[]
                for j_data in db_table["db_load_information_as_of_now"]:
                    j_data.update({"time":db_table["collected_time"]})
                    test.append(j_data)
                data.extend(test)
        df=pd.DataFrame(data)
        df=df[df.instance_id == str(instance_id)][["host","aas_cpu_pct","aas_io_pct","time"]].astype({'aas_cpu_pct': 'float','aas_io_pct':'float'})
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        return df
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in db contention analysis func - db_contention {1}".format(globalvariables.RED,e)
        print(message)

def db_blocking_session_analysis(db_art_json:dict)-> dict:
    """ do the db blocking session analysis  
        Args:
            db_art_json (dict): json data
            instance_id (str): instance id for which data need to be parsed
        Returns:
            blocker_details (dataframe/json): return dataframe for db blocking session analysis.
        Raises:
            Exception: value error  
        """
    try:
        if not db_art_json:
            db_art_json_file="{0}/EUBP_db_art_perf_data_2023-10-17:00.json".format(globalvariables.dart_data)
            with open(db_art_json_file,"r") as db_art:
                db_art_json=json.loads(db_art.read())
        blocking_sessions_data=[]
        most_waiters=[]
        db_contention=[]
        for db_table in db_art_json:
            if "hang_analysis" in db_table:
                for key in db_table["hang_analysis"]:
                    if key == "blocking_sessions" :
                        test=[]
                        for j_data in db_table["hang_analysis"]["blocking_sessions"]:
                            j_data.update({"time":db_table["collected_time"]})
                            test.append(j_data)
                        blocking_sessions_data.extend(test)
                    if key == "chains_with_most_waiters":
                        test=[]
                        for j_data in db_table["hang_analysis"]["chains_with_most_waiters"]:
                            j_data.update({"time":db_table["collected_time"]})
                            test.append(j_data)
                        most_waiters.extend(test)
        
            if "db_contention" in db_table:
                        test=[]
                        for j_data in db_table["db_contention"]:
                            j_data.update({"time":db_table["collected_time"]})
                            test.append(j_data)
                        db_contention.extend(test)
            
        #1st dataframe to get session details
        df=pd.DataFrame(blocking_sessions_data)
        df=df[["time","blocker_instance","blocker_sid","blocker_osid","module","num_waiters","longest","waiting_on"]]
        df.loc[:,["max_waiters"]]=df.groupby("time")["num_waiters"].transform("max")
        df=df.loc[df["max_waiters"] == df["num_waiters"]]
        df.drop(columns=["max_waiters"],inplace=True)
        #2nd dataframe to get most waiters and "sess_serial#"
        if most_waiters:
            df_most_Waiter=pd.DataFrame(most_waiters)
            print(df_most_Waiter)
            df_most_Waiter=df_most_Waiter[["chain_signature","osid","pid","sid","sess_serial#","pdb_name","in_wait_secs","time","num_waiters"]]
            df_most_Waiter.loc[:,["max_waiters"]]=df_most_Waiter.groupby("time")["num_waiters"].transform("max")
            df_most_Waiter=df_most_Waiter.loc[df_most_Waiter["max_waiters"] == df_most_Waiter["num_waiters"]]
            df_most_Waiter.drop(columns=["max_waiters"],inplace=True)

            #merging dataframes 
            result=pd.merge(df, df_most_Waiter, on='time', how='inner')
            # result

            # 3rd dataframe to get sql details
            if db_contention:
                df_db_con=pd.DataFrame(db_contention)

                # df_db_con
                #merging sql dataframe with blocking session dataframe
                blocker_details=pd.merge(result, df_db_con, on=['time','module'], how='inner')
                blocker_details=blocker_details.astype({"blocker_instance":"str","blocker_sid":"str","blocker_osid":"str","sess_serial#":"str","sql_id":"str","event":"str","module":"str"})

            #concatenating multiple column data to get session details.

            blocker_details.loc[:,["session_details"]]=blocker_details["sql_id"] + ":"+ blocker_details["module"] + ":" + blocker_details["event"]+ ":" + blocker_details["blocker_instance"] +":"+blocker_details["blocker_sid"] +":"+blocker_details["blocker_osid"] +":"+blocker_details["sess_serial#"]

            #converting datatypes string -> datetime and string -> int

            blocker_details.loc[:,["time"]]=pd.to_datetime(blocker_details["time"].str.replace("_"," "))
            blocker_details=blocker_details.astype({"num_waiters_x":"int"})
            print(blocker_details)
        # print(blocker_details)
        # blocker_details
        # fig=px.scatter(blocker_details,x="num_waiters_x",y="time",color="session_details",hover_name="waiting_on")
        # fig.show()
            return blocker_details
        
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in db blocking session analysis func - db_blocking_session_analysis {1}".format(globalvariables.RED,e)
        print(message)
def main():
    db_art_analysis("4","EINO-TEST","EINO-TEST_db_art_perf_data_2023-11-23:07.json")
    # print(df_max_per_exec_time)
# /Users/vazad/Desktop/fsre-mw-fa-env-analysis/fsre-mw-fa-env-analysis/out_data/dart_data/EUBP_db_art_perf_data_2023-10-17:00.json
#/Users/vazad/Desktop/fsre-mw-fa-env-analysis/fsre-mw-fa-env-analysis/out_data/dart_data/EINO-TEST_db_art_perf_data_2023-11-23:07.json
if __name__ == "__main__":
    main()
