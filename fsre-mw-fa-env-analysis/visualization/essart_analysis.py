import pandas as pd
import seaborn as scn
import json,os,sys,traceback
from pprint import pprint
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables


def ess_art_analysis(ess_art_json_file: dict=None)-> dict:
    """ Do the ess art analysis  
        Args:
            ess_art_json_file (file): file path for json file
        Returns:
            agg_df (dataframe/json): return df 
        Raises:
            Exception: value error  
        """
    try:
        if not ess_art_json_file:
            ess_art_json_file="{0}/EODR_ess_art_perf_data_2023-10-10:19.json".format(globalvariables.dart_data)
        with open(ess_art_json_file,"r") as db_art:
            j_data=json.loads(db_art.read())
        df_ess_cancelling_jobs=ess_cancelling_jobs(j_data)
        # df_max_total_sec, df_max_per_exec_time, df_max_aas=top_sql_analysis(j_data,instance_id)
        # df_event_with_high_elapsed_time=top_event_with_high_elapsed_time(j_data,instance_id)
        # df_db_contention=db_contention(j_data,instance_id)
        # df_db_load_details=db_load_info(j_data,instance_id)
        # df_db_blocking_session_analysis=db_blocking_session_analysis(j_data)
        # return df_max_total_sec,df_max_per_exec_time,df_max_aas,df_event_with_high_elapsed_time,df_db_contention,df_db_load_details,df_db_blocking_session_analysis
        return df_ess_cancelling_jobs
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting high per execution time func - top_sql_with_total_elepsed_time {1}".format(globalvariables.RED,e)
        print(message)

def ess_cancelling_jobs(ess_art_json:dict)-> dict:
    """ Do the ess cancelling jon analysis 
        Args:
            ess_art_json (dict): json data
        Returns:
            agg_df (dataframe/json): return panda dataframe with ess cancelling jobs. 
        Raises:
            Exception: value error  
        """
    try:
        if not ess_art_json:
            ess_art_json_file="{0}/ECGY_ess_art_perf_data_2023-10-24:11.json".format(globalvariables.dart_data)
            with open(ess_art_json_file,"r") as db_art:
                ess_art_json=json.loads(db_art.read())
        ess_cancelling_data=[]
        for ess_table in ess_art_json:
            if "the_details_of_top_100_cancelling_jobs" in ess_table:
                test=[]
                for data in ess_table["the_details_of_top_100_cancelling_jobs"]:
                    data.update({"time":ess_table["collected_time"]})
                    test.append(data)
                ess_cancelling_data.extend(test)
        df=pd.DataFrame(ess_cancelling_data)
        df=df.astype({"ellapsed_minutes":"int"})
        agg_df=df.groupby(["time","definition","job_type"])["ellapsed_minutes"].aggregate(["count","mean","max"]).reset_index()
        agg_df.loc[:,["max_avg"]]=round(agg_df.groupby("time")["mean"].transform("max"),2)
        agg_df=agg_df[agg_df["mean"]==agg_df["max_avg"]]
        agg_df.loc[:,["time"]]=pd.to_datetime(agg_df["time"].str.replace("_"," "))
        agg_df=agg_df.astype({"definition":"str","job_type":"str","max_avg":"str","max":"int","count":"int"})
        # print(agg_df.dtypes)
        agg_df.loc[:,["job_details"]]=agg_df["definition"] + ":" + agg_df["job_type"] + ":" + "Avg Ellapsed minutes - " +agg_df["max_avg"]
        # fig=px.scatter(agg_df,x="count",y="time",color="job_details",hover_name="max",size="max")
        # fig.show()
        return agg_df
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in doing ess cancelling job analysis func - ess_cancelling_jobs {1}".format(globalvariables.RED,e)
        print(message)

def main():
    pprint(ess_art_analysis())
# /Users/vazad/Desktop/fsre-mw-fa-env-analysis/fsre-mw-fa-env-analysis/out_data/dart_data/EUBP_db_art_perf_data_2023-10-17:00.json
if __name__ == "__main__":
    main()
