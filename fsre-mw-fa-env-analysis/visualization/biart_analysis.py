import pandas as pd
import seaborn as scn
import json,os,sys,traceback
from pprint import pprint
BASE_DIR = os.path.abspath(__file__ +"/../../../")
sys.path.append(BASE_DIR)
from common import globalvariables

def bi_art_analysis(bi_art_json_file: dict=None)-> dict:
    """ Do the ess art analysis  
        Args:
            ess_art_json_file (file): file path for json file
        Returns:
            agg_df (dataframe/json): return df 
        Raises:
            Exception: value error  
        """
    try:
        if not bi_art_json_file:
            bi_art_json_file="{0}/EINO_bi_art_perf_data_2023-11-02:00.json".format(globalvariables.dart_data)
        with open(bi_art_json_file,"r") as db_art:
            j_data=json.loads(db_art.read())
        df_bip_job_details=bip_report_details(j_data)
        bip_running_job_details=bip_running_job_analysis(j_data,df_bip_job_details)
        bi_job_summery=bi_jobs_summery(j_data)
        # df_max_total_sec, df_max_per_exec_time, df_max_aas=top_sql_analysis(j_data,instance_id)
        # df_event_with_high_elapsed_time=top_event_with_high_elapsed_time(j_data,instance_id)
        # df_db_contention=db_contention(j_data,instance_id)
        # df_db_load_details=db_load_info(j_data,instance_id)
        # df_db_blocking_session_analysis=db_blocking_session_analysis(j_data)
        # return df_max_total_sec,df_max_per_exec_time,df_max_aas,df_event_with_high_elapsed_time,df_db_contention,df_db_load_details,df_db_blocking_session_analysis
        return df_bip_job_details,bip_running_job_details,bi_job_summery
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting high per execution time func - top_sql_with_total_elepsed_time {1}".format(globalvariables.RED,e)
        print(message)

def bip_report_details(bi_art_json:dict)-> dict:
    """ Do the bip long running report analysis 
        Args:
            bi_art_json (dict): json data
        Returns:
            agg_df (dataframe/json): return panda dataframe with bip art analysis jobs. 
        Raises:
            Exception: value error  
        """
    try:
        if not bi_art_json:
                ess_art_json_file="{0}/EINO_bi_art_perf_data_2023-11-02:00.json".format(globalvariables.dart_data)
                with open(ess_art_json_file,"r") as db_art:
                    bi_art_json=json.loads(db_art.read())
        all_bi_data=[]
        for bi_table in bi_art_json:
            if "bip_job_details_in_the_last_4_hours,_that_are_taking_more_than_5_mins_with_min,_max_and_avg_times_of_each_report_in_last_7_days" in bi_table:
                test=[]
                for data in bi_table["bip_job_details_in_the_last_4_hours,_that_are_taking_more_than_5_mins_with_min,_max_and_avg_times_of_each_report_in_last_7_days"]:
                    data.update({"time":bi_table["collected_time"]})
                    test.append(data)
                all_bi_data.extend(test)

        # #1st dataframe to get ess_cancelling_data 

        df=pd.DataFrame(all_bi_data)
        df=df[["time","report_name","total_dur_min","sqlid_list","number_rows","sql_exec_time_secs"]]
        df['report_type'] = df['report_name'].str.split('/').str[1]
        df['report'] = df['report_name'].str.split('/').str[-1]
        df.drop(["report_name"],axis=1)
        df=df[["time","report_type","report","sqlid_list","number_rows","sql_exec_time_secs","total_dur_min"]]
        df=df.assign(sqlid_list=df.sqlid_list.str.split(','),number_rows=df.number_rows.str.split(','),sql_exec_time_secs=df.sql_exec_time_secs.str.split(','))
        def func_sql(x):
            sql_len = len(x["sqlid_list"])
            rows_len = len(x["number_rows"])
            if sql_len != rows_len:
                for i in range(sql_len - rows_len):
                    x["number_rows"].append(0)
            return x
        df[["sqlid_list","number_rows"]]=df[["sqlid_list","number_rows"]].apply(func_sql,axis=1)
        df=df.explode(["sqlid_list","sql_exec_time_secs","number_rows"])
        def sql_exc(x):
            try:
                for i in str(x):
                    res=''
                    if i.isdigit():
                        res += x
                return int(res)
            except Exception as e:
                return int(0)
        def check_report_type(x):
            if x == "custom":
                return "custom"
            else:
                return "seeded"
        df["report_type"]=df["report_type"].apply(check_report_type)
        df["sql_exec_time_secs"]=df["sql_exec_time_secs"].apply(sql_exc)
        df=df.astype({"sql_exec_time_secs":"int"})
        df["sql_time"]=df.groupby(["time","report"])["sql_exec_time_secs"].transform("max")
        df=df.loc[df["sql_exec_time_secs"] == df["sql_time"]]
        df.reset_index()
        df=df.astype({"report_type":"str","report":"str","sqlid_list":"str","number_rows":"str"})
        df.loc[:,["report_details"]]=df["report_type"] + ":" + df["report"]+ ":" + df["sqlid_list"]+ ":" + df["number_rows"]
        # print(df.dtypes)
        df=df[["time","sql_exec_time_secs","report_details","report_type","sqlid_list","report","total_dur_min"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        
        # fig=px.scatter(df,x="sql_exec_time_secs",y="time",hover_name="report_details",size="sql_exec_time_secs",color="report_type")
        # fig.show()  
        # # fig=px.treemap(df,x="sql_exec_time_secs",y="report_details",color="time")
        # fig=px.treemap(names=df["sql_exec_time_secs"],parents=df["report_details"])
        # fig.show()\
        return df
    except Exception as e:
            traceback.print_exc()
            message="{0}Error in doing bip   job analysis func - bip_job_details {1}".format(globalvariables.RED,e)
            print(message)

def bip_running_job_analysis(j_data: dict,bi_report_data:dict)->dict:
    """ Do the bip_running_job_analysis 
        Args:
            j_data (dict): bi json data
            bi_report_data (dict): get the bi report analysis data frame
        Returns:
            result (dataframe/json): return panda dataframe with bip job analysis. 
        Raises:
            Exception: value error  
        """
    try:
        all_bi_data=[]
        for bi_table in j_data:
            if "bip_running_jobs_that_are_triggred_in_last_3_days:" in bi_table:
                test=[]
                for data in bi_table["bip_running_jobs_that_are_triggred_in_last_3_days:"]:
                    data.update({"time":bi_table["collected_time"]})
                    test.append(data)
                all_bi_data.extend(test)

        df=pd.DataFrame(all_bi_data)
        def check_report_type(x):
            if x == "custom":
                return "custom"
            else:
                return "seeded"
        df['report_type'] = df['report_url'].str.split('/').str[1].apply(check_report_type)
        df['report'] = df['report_url'].str.split('/').str[-1]
        # df["report_type"]=df["report_type"].apply(check_report_type)
        df=df.drop(["report_url"],axis=1)
        df=df[["time","report_type","report","bip_job_id","elapsed_minutes","ess_request_id"]]
        df.loc[:,["time"]]=pd.to_datetime(df["time"].str.replace("_"," "))
        #join two dataframe to get bipjob and respective sql/report detail
        result=pd.merge(df, bi_report_data, on=['time','report'],how='inner')
    #     print(result.columns)
        result=result[["time","bip_job_id","report_type_x","report","sql_exec_time_secs","sqlid_list","report_details","total_dur_min"]]
    #     print(result)
        def duration_exc(x):
            try:
                for i in str(x):
                    res=''
                    if i.isdigit():
                        res += x
                return int(round(float(res)))*60
            except Exception as e:
                return int(round(float(0)))
        result.loc[:,["total_dur_sec"]]=result["total_dur_min"].apply(duration_exc)
        return result
        # print(result)
        # report_data=result[result["report"] == "jpmc_r_or052_applicants_reporting_report.xdo"]
        # fig=px.bar(report_data,x="time",y=["sql_exec_time_secs","total_dur_sec"],hover_name="report_details",barmode='group')
        # fig.show()
    #     print(report_data)
    #     fig=px.scatter(result,x="sql_exec_time_secs",y="time",hover_name="report_details",size="sql_exec_time_secs",color="bip_job_id")
    #     fig.show()
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting high per execution time func - bip_running_job_analysis {1}".format(globalvariables.RED,e)
        print(message)

def bi_jobs_summery(j_data):
    all_bi_data=[]
    for bi_table in j_data:
        if "overall_pod_job_details" in bi_table:
            test=[]
            for data in bi_table["overall_pod_job_details"]:
                data.update({"time":bi_table["collected_time"]})
                test.append(data)
            all_bi_data.extend(test)

    # #1st dataframe to get ess_cancelling_data 

    df=pd.DataFrame(all_bi_data)
    df=df.astype({"bip_waiting_jobs":"int","bi_ess_jobs":"int","bip_online_running_jobs":"int"})
    df["time"]=pd.to_datetime(df["time"].str.replace("_"," "))
#     print(df)
#     print(pd.to_datetime(df["time"].str.replace("_"," ")))
    df.sort_values('time')
    return df
    # fig = px.bar(df, x='time', y=["bi_ess_jobs","bip_online_running_jobs","bip_waiting_jobs"],barmode='group',hover_data="max_bi_ess_threads")
#     fig.update_traces(width=1000000)
    # fig.show()
def main():
    df1,df2,df3=bi_art_analysis("")
    print(df3.columns)
    # print(df2.columns)

if __name__ == "__main__":
    main()






         
