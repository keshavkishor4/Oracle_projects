from django.shortcuts import render,redirect
import pandas as pd
from plotly.offline import plot
import plotly.express as px
from .form import podform
import os,sys,json,traceback
BASE_DIR = os.path.abspath(__file__ +"/../../../")
sys.path.append(BASE_DIR)
from common import globalvariables
from data_analysis import pod_analysis
from visualization import dbart_analysis
# Create your views here.

def index(request):
    try:
        pod=podform()
        data={'form':pod}
        # exa_data=''
        # if request.GET:
        #     POD_Name=request.GET.get("pod_name")
        #     Start_time=request.GET.get("start_time")
        #     Start_time=str(Start_time) + ':00'
        #     End_time=request.GET.get("end_time")
        #     End_time=str(End_time) + ':00'
        #     # django_time=request.GET.get('starttimedjango')
        #     # print(django_time)
            
        #     if POD_Name:
        #         print(f'{POD_Name},{Start_time},{End_time}')
        #         exa_data=pod_analysis.pod_analysis(POD_Name,Start_time,End_time)
        #         return render(request,'exa_table.html',{'exa_data':exa_data})
        return render(request,'index.html',data) 
    except Exception as e:
        message = "Error in func submit_form ".format(e)
        print(message)
def submit_form(request):
    # exa_data=pod_analysis.pod_analysis(POD_Name,Start_time,End_time)    
    # return render(request,'exa_table.html',{'exa_data':exa_data})
    try:
        j_data=[]
        if request.method=='POST':
            POD_Name=request.POST.get("pod_name")
            Start_time=request.POST.get("start_time")
            Start_time=str(Start_time) + ':00'
            End_time=request.POST.get("end_time")
            End_time=str(End_time) + ':00'
            # django_time=request.GET.get('starttimedjango')
            # print(django_time)
            
            # if POD_Name:
            print(f'{POD_Name},{Start_time},{End_time}')
            exa_data=pod_analysis.pod_analysis(POD_Name,Start_time,End_time)
            # print(exa_data)
            exa_data=json.loads(exa_data)
            j_data=pod_analysis.exa_view_frame(exa_data)
            # print(j_data)
            # j_data=json.loads(j_data)
            # print(j_data)
        #     dict_data={}
        # for key in exa_data:
        #     dict_data.update({key:[pod['pod_name'] for pod in exa_data[key]['databases']]})

        return render(request,'exa_table.html',{'exa_data':j_data})
    except Exception as e:
        message = "Error in func submit_form ".format(e)
        print(message)


def db_dash(request):
    try:
        db_art_file=request.POST.get("dart_url")
        exadata=request.POST.get("exa_node")
        pod=request.POST.get("pod_name")
        db_name=request.POST.get("db_name")
        db_name=db_name.upper()
        pod_size=request.POST.get("pod_size")
        exa_name=exadata.split('.')[0].upper()
        exadata=exadata.split('.')[0].split('-')[1][-1]
        
        print(f'exadata -> {exadata} db_art_url -> {db_art_file} exa_name {exa_name}')
    
        db_art_json_file="{0}/{1}".format(globalvariables.dart_data,db_art_file)
        with open(db_art_json_file,"r") as db_art:
                j_data=json.loads(db_art.read())
        # print(f'file path {j_data}')
        if j_data:
            df_max_total_sec,df_max_per_exec_time,df_max_aas,df_event_with_high_elapsed_time,df_db_contention,df_db_load_details,df_db_blocking_session_analysis=dbart_analysis.db_art_analysis(exadata,pod,db_art_file)
            print(df_max_total_sec)
            print(df_max_per_exec_time)
            print(df_db_blocking_session_analysis)
            fig=px.line(df_max_total_sec,x="time",y="total_time_min",hover_name="sql_details",title="Top sql with Elapsed time in min",color="sql_id")
            total_sec = plot(fig, output_type="div")
            # context = {'total_sec': total_sec}

            fig1=px.line(df_max_per_exec_time,x="time",y="per_exec_time",hover_name="sql_details",title="Top sql with per exec time in sec",color="sql_id")
            per_exe = plot(fig1, output_type="div")

            fig2=px.line(df_max_aas,x="time",y="aas",hover_name="sql_details",title="Top sql with Average Active Sessions (AAS)",color="sql_id")
            aas_sql = plot(fig2, output_type="div")

            fig3=px.scatter(df_event_with_high_elapsed_time,x="time",y="total_seconds",hover_name="event_2",title="Top Event with high Elapsed time",color="event_2")
            top_event = plot(fig3, output_type="div")
            context = {'total_sec': total_sec,
            'per_exe': per_exe,
            'aas_sql':aas_sql,
            'top_event':top_event,
            'pod_name':pod,
            'db_name':db_name,
            'pod_size':pod_size,
            'exa_name':exa_name
            }
            return render(request,'chart.html',context)
        else:
            context = {
            'pod_name':pod,
            'db_name':db_name,
            'pod_size':pod_size,
            'exa_name':exa_name
            }
            return render(request,'Dart_unavailable.html',context)
    except Exception as e:
        traceback.print_exc()
        message="{0}Error in getting dataframes func - db_dash {1}".format(globalvariables.RED,e)
        print(message)
        context = {
           'pod_name':pod,
           'db_name':db_name,
           'pod_size':pod_size,
           'exa_name':exa_name
           }
        return render(request,'Dart_unavailable.html',context)

       
    

def test(request):
    return render(request,'Dart_unavailable.html')