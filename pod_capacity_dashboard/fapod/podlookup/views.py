from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.template import loader
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from .models import *
import json
import requests
import sys
import datetime
import oci
import re
import os
import subprocess
sys.path.append("../")
from common import commonutils,data_fetch,podcontent,ociSDK,globalvariables
from sys import platform
#################################### Index Page ####################################
def index_page(request):
    try:
        try:
            account=str(request.session['cred_value'])
        except Exception as e:
            return render(request,'podlookup/cred_value_error_page.html')
        if request.GET:
            pod = str(request.GET['pod_name']).upper()
            is_adpdata = podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))['podAttributes']['isADP']
            commonutils.session_json()
            request.session['pod']=pod
            result = podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))
            #print(result)
            request.session['pod_region_name'] = result['fm_datacenter']
            pod_name=str(request.session['pod'])
            pod_data = podcontent.full_pod_data_method(pod,str(request.session['cred_value']))
            Full_pod_result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
            next_stamp_value = None
            for item in Full_pod_result:
                if item.get('name') == 'next_stamp':
                    next_stamp_value = item.get('value')
                elif item.get('name') == 'stamp':
                    stamp_value = item.get('value')
                elif item.get('name') == 'fusiondb_dbname':
                    fusion_dbname = item.get('value')
                elif item.get('name') == 'fusiondb_dbuniquename':
                    fusion_unique_dbname = item.get('value')       
            if "custom" in stamp_value:
                bespoke_custom = "Yes"
            else:
                bespoke_custom = "No"
            for i in range(len(pod_data)):
                if str(pod_data[i]['name']) == "isFAAAS":
                    is_faas=str(pod_data[i]['value'])
                    request.session['isFaas']=str(is_faas)
                if str(pod_data[i]['name']) == "oci_size":
                    size=str(pod_data[i]['value'])
                if str(pod_data[i]['name']) == "oci_availability_domain":
                    ad_domain=str(pod_data[i]['value'])
                    request.session['ad_domain']=str(ad_domain)
            #print(size,is_faas)
            #print(pod_families)
            try:
                pod_basic_data.objects.all().delete()
                homepage_pod_data={}
                homepage_pod_data['Pod_Name']=str(result['pod_name'])
                homepage_pod_data['dr_role']=str(result['dr_role'])
                homepage_pod_data['physical_pod_name']=str(result['physical_pod_name'])
                homepage_pod_data['service']=str(result['service'])
                homepage_pod_data['last_updated']=str(result['last_updated'])
                homepage_pod_data['datacenter_code']=str(result['datacenter_code'])
                homepage_pod_data['dc_short_name']=str(result['dc_short_name'])
                homepage_pod_data['associated_dr_peer']=str(result['associated_dr_peer'])
                homepage_pod_data['peer_physical_pod_name']=str(result['peer_physical_pod_name'])
                homepage_pod_data['id_name']=str(result['id_name'])
                homepage_pod_data['fusion_service_name']=str(result['fusion_service_name'])
                homepage_pod_data['status']=str(result['status'])
                homepage_pod_data['pod_type']=str(result['type'])
                homepage_pod_data['release']=str(result['release'])
                homepage_pod_data['customer_name']=str(result['customer'])
                homepage_pod_data['golden_gate_enabled']=str(result['golden_gate_enabled'])
                homepage_pod_data['fm_datacenter']=str(result['fm_datacenter'])
                pod_basic_data.objects.create(
                    Pod_Name=str(result['pod_name']),
                    dr_role=str(result['dr_role']),
                    physical_pod_name=str(result['physical_pod_name']),
                    service=str(result['service']),
                    last_updated=str(result['last_updated']),
                    datacenter_code=str(result['datacenter_code']),
                    dc_short_name=str(result['dc_short_name']),
                    associated_dr_peer=str(result['associated_dr_peer']),
                    peer_physical_pod_name=str(result['peer_physical_pod_name']),
                    id_name=str(result['id_name']),
                    fusion_service_name=str(result['fusion_service_name']),
                    status=str(result['status']),
                    pod_type=str(result['type']),
                    release=str(result['release']),
                    customer_name=str(result['customer']),
                    golden_gate_enabled=str(result['golden_gate_enabled']),
                    fm_datacenter=str(result['fm_datacenter'])
                    )
                pod_basic_data_monitoring.objects.create(
                    Pod_Name=str(result['pod_name']),
                    dr_role=str(result['dr_role']),
                    physical_pod_name=str(result['physical_pod_name']),
                    service=str(result['service']),
                    last_updated=str(result['last_updated']),
                    datacenter_code=str(result['datacenter_code']),
                    dc_short_name=str(result['dc_short_name']),
                    associated_dr_peer=str(result['associated_dr_peer']),
                    peer_physical_pod_name=str(result['peer_physical_pod_name']),
                    id_name=str(result['id_name']),
                    fusion_service_name=str(result['fusion_service_name']),
                    status=str(result['status']),
                    pod_type=str(result['type']),
                    release=str(result['release']),
                    customer_name=str(result['customer']),
                    golden_gate_enabled=str(result['golden_gate_enabled']),
                    fm_datacenter=str(result['fm_datacenter'])
                    )
            except Exception as e:
                print(e)
            pod_details_from_cloudmeta=pod_basic_data.objects.all()

            ######################## Pod Family Details ###############################
            """
            pod_families= podcontent.pod_family(pod,str(request.session['cred_value']))
            for i in range(len(pod_families['pods'])):
                print(pod_families['pods'][i]['name'],pod_families['pods'][i]['fm_type'])
                URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs/oci_size".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],str(pod_families['pods'][i]['name']))
                pod_size= podcontent.cloud_meta_genric(URL,account)
                print(pod_size['value']) """
            ######################## Pod Family Details ###############################
            source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
            if is_faas == "true":
                source_url_dop = "http://devops.oci.oraclecorp.com"
                #print("FAAAS Env")
                tt_is="https://prod-ops-fusionapps."+str(result['fm_datacenter'])+".oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName="+pod
                oci_sdk = ociSDK.OciSdk(account)
                tt_is_req = oci_sdk.fetch_details_from_endpoint_url("GET",tt_is)
                #print(tt_is_req[0]['supportedPlatform'])
                return render(request,'podlookup/main.html',{'k':homepage_pod_data,'output_data':homepage_pod_data,'size':size,'is_faas':is_faas,'tt_is_req':tt_is_req,'pod':pod, 'is_adpdata':is_adpdata, 'stamp': stamp_value, 'bespoke_custom': bespoke_custom, 'next_stamp_size': next_stamp_value, 'fusion_dbname': fusion_dbname, 'fusion_unique_dbname': fusion_unique_dbname, 'source_url': source_url, 'source_url_dop': source_url_dop})
            else:
                #print("Gen1 Pod")
                #print(homepage_pod_data)
                return render(request,'podlookup/main.html',{'k':homepage_pod_data,'output_data':homepage_pod_data,'size':size,'is_faas':is_faas,'pod':pod, 'is_adpdata':is_adpdata, 'stamp': stamp_value, 'bespoke_custom': bespoke_custom, 'next_stamp_size': next_stamp_value, 'fusion_dbname': fusion_dbname, 'fusion_unique_dbname': fusion_unique_dbname, 'source_url': source_url})
            """
            #Getting FAAAS pod is resize needed element
            #print(str(result['fm_datacenter']))
            tt_is="https://prod-ops-fusionapps."+str(result['fm_datacenter'])+".oci.oraclecloud.com/20191001/internal/fusionEnvironments?limit=100"
            #print(account)
            oci_sdk = ociSDK.OciSdk(account)
            tt_is_req = oci_sdk.fetch_details_from_endpoint_url("GET",tt_is)
            #print(tt_is_req)
            for i in range(len(tt_is_req)):
                if str(pod) == str(tt_is_req[i]['systemName']):
                    print(tt_is_req[i])
                #print(tt_is_req[i]['displayName'])
                #print("==============")
                #podName
            """
            #amharees@amharees-mac Downloads % ./oci_curl.py --profile fapod_oci_config -X GET "https://prod-ops-fusionapps.us-phoenix-1.oci.oraclecloud.com/20191001/internal/fusionEnvironments?systemName=IAKKQY-TEST" | jq .
            #print(homepage_pod_data)
            #return render(request,'podlookup/main.html',{'k':homepage_pod_data,'output_data':homepage_pod_data,'size':size,'is_faas':is_faas})
            #print(pod_details_from_cloudmeta.get())
            #return render(request,'podlookup/main.html',{'pod_data_from_metadata': homepage_pod_data,'size':size,'is_faas':is_faas})
        return render(request,'podlookup/main_woget.html')
    except Exception as e:
        return render(request,'podlookup/main.html')

def credstore_pageMethod(request):
    query = request.GET.get('data')
    request.session['cred_value']=query
    if platform != "linux":
        if str(query) == "commercial":
            #print(query)
            os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
        elif str(query) == "ukg":
            #print(query)
            os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region uk-gov-london-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region uk-gov-london-1 --auth ${var_OCI_CLI_AUTH};")
        elif str(query) == "eura":
            #print(query)
            os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
        else:
            #print(query)
            os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
        #os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
    try:
        if platform != "linux":
            subprocess.Popen(["python3" , "oci_session_validate.py"])
        else:
            subprocess.Popen(["python3" , "/opt/faops/spe/fapodcapacity/fapod/oci_session_validate.py"])
    except Exception as e:
        print(e)

    oci_sdk=ociSDK.OciSdk(request.session['cred_value'])
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#################################### OCI Session Authentication -- For now not using this and adding it into credstore_pageMethod Page ####################################
def ocisessauthmethod(request):
    os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --no-browser --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
    #os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#################################### LBaas View Method ####################################
def lbaas_id_view_method(request):
    is_faas=str(request.session['isFaas'])
    lbaas_data_table.objects.all().delete()
    lbaas_id=str(request.POST['lbaas_id'])
    #print(lbaas_id)
    region_name=str(request.POST['region'])
    try:
        account=str(request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    config=globalvariables.env_dictionary[account]['oci_config']
    #print(config)
    #print(lbaas_id)
    config["region"]=region_name
    try:
        lb_data={}
        try:
            signer = podcontent.oci_token_code(config)
            load_balancer_client = oci.load_balancer.LoadBalancerClient({'region': config['region']}, signer=signer)
            pod_name=str(request.session['pod'])
            #print(pod_name)
            if is_faas == "true":
                #lbaas_id="pod-"+str(pod_name).upper()+".loadbalancer-pod_loadbalancer_1.loadBalancerLoadBalancer-loadbalancer"
                list_load_balancers_response = load_balancer_client.list_load_balancers(compartment_id='ocid1.compartment.oc1..aaaaaaaargimiyzx7pkw4fqrlckpjjdhnldrnirnhdkhjmba4votujb7754a',display_name=lbaas_id)
            else:
                #lbaas_id=str(pod_name)+"-loadbalancer-1"
                list_load_balancers_response = load_balancer_client.list_load_balancers(compartment_id='ocid1.compartment.oc1..aaaaaaaaedremzszzkluzxvnwlrafigu2sls2sygyvqn2eu5yjikkgvqauyq',display_name=lbaas_id)
                #print(list_load_balancers_response.data)
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        if len(list_load_balancers_response.data) == 0:
            pass
        else:
            lbaas_data_table.objects.create(region_name=str(region_name),display_name=str(list_load_balancers_response.data[0].display_name),lbaas_id=str(list_load_balancers_response.data[0].id), compartment_id=str(list_load_balancers_response.data[0].compartment_id),lifecycle_state=str(list_load_balancers_response.data[0].lifecycle_state),minimum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.minimum_bandwidth_in_mbps), maximum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.maximum_bandwidth_in_mbps),subnet_ids=str(list_load_balancers_response.data[0].subnet_ids), shape_name=str(list_load_balancers_response.data[0].shape_name),ip_address=str(list_load_balancers_response.data[0].ip_addresses[0].ip_address))
            lbaas_data_table_monitoring.objects.create(region_name=str(region_name),display_name=str(list_load_balancers_response.data[0].display_name),lbaas_id=str(list_load_balancers_response.data[0].id), compartment_id=str(list_load_balancers_response.data[0].compartment_id),lifecycle_state=str(list_load_balancers_response.data[0].lifecycle_state),minimum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.minimum_bandwidth_in_mbps), maximum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.maximum_bandwidth_in_mbps),subnet_ids=str(list_load_balancers_response.data[0].subnet_ids), shape_name=str(list_load_balancers_response.data[0].shape_name),ip_address=str(list_load_balancers_response.data[0].ip_addresses[0].ip_address))
    except:
        pass
    #if is_faas=="true":
    #    return render(request,'podlookup/faas_lbaas.html')
    lb_data=lbaas_data_table.objects.all()
    source_url_dop = "http://devops.oci.oraclecorp.com"
    return render(request,'podlookup/lbaas_data.html',{'lbaas_data':lb_data, 'source_url_dop': source_url_dop})

#################################### Get Weekly Report Stamp report and Manual Report ####################################
def get_weekly_report(request):
    #print(request.session['pod'])
    pod=str(request.session['pod'])
    datafetch=data_fetch.fetch()
    version_data=podcontent.maintenance_level_podattr(pod,str(request.session['cred_value']))
    is_adpdata = podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))['podAttributes']['isADP']
    #print(is_adpdata)
    #is_adpdata['podAttributes']['isADP'])
    Stamp_Pod_Report.objects.all().delete()
    status,stampfilepath=datafetch.stamp_psr_data()
    with open(stampfilepath) as f:
        stamp_pod_result=json.load(f)
    status,manualfilename=datafetch.manual_psr_data()
    with open(manualfilename) as f:
        manual_pod_result=json.load(f)
    for i in range(len(stamp_pod_result)):
        Stamp_Pod_Report.objects.create(
            request_data=str(stamp_pod_result[i]['Request Date']),
            fm_date=str(stamp_pod_result[i]['FM Date']),
            Pod_Name=str(stamp_pod_result[i]['POD Name']),
            customer_name=str(stamp_pod_result[i]['Customer Name']),
            bugs=str(stamp_pod_result[i]['Bugs']),
            bug_creation_date=str(stamp_pod_result[i]['BUG Creation Date']),
            resize_type=str(stamp_pod_result[i]['Resize Type']),
            execution_type=str(stamp_pod_result[i]['Execution Type']),
            resize_reason=str(stamp_pod_result[i]['Resize Reason']),
            environment_type=str(stamp_pod_result[i]['Environment Type']),
            pod_architecture=str(stamp_pod_result[i]['POD Architecture']),
            fresh_p_or_u=str(stamp_pod_result[i]['Fresh P Or U']),
            next_rel_date=str(stamp_pod_result[i]['Next Rel Date']),
            next_rel_version=str(stamp_pod_result[i]['Next Rel Version']),
            current_release=str(stamp_pod_result[i]['Current Release']),
            data_center=str(stamp_pod_result[i]['Data Center']),
            environment_region_name=str(stamp_pod_result[i]['Environment Region Name']),
            old_shape=str(stamp_pod_result[i]['Old Shape']),
            new_shape=str(stamp_pod_result[i]['New Shape']),
            pod_size=str(stamp_pod_result[i]['POD Size']),
            hw_map=str(stamp_pod_result[i]['HW Map']))

        Stamp_Pod_Report_monitoring.objects.create(
            request_data=str(stamp_pod_result[i]['Request Date']),
            fm_date=str(stamp_pod_result[i]['FM Date']),
            Pod_Name=str(stamp_pod_result[i]['POD Name']),
            customer_name=str(stamp_pod_result[i]['Customer Name']),
            bugs=str(stamp_pod_result[i]['Bugs']),
            bug_creation_date=str(stamp_pod_result[i]['BUG Creation Date']),
            resize_type=str(stamp_pod_result[i]['Resize Type']),
            execution_type=str(stamp_pod_result[i]['Execution Type']),
            resize_reason=str(stamp_pod_result[i]['Resize Reason']),
            environment_type=str(stamp_pod_result[i]['Environment Type']),
            pod_architecture=str(stamp_pod_result[i]['POD Architecture']),
            fresh_p_or_u=str(stamp_pod_result[i]['Fresh P Or U']),
            next_rel_date=str(stamp_pod_result[i]['Next Rel Date']),
            next_rel_version=str(stamp_pod_result[i]['Next Rel Version']),
            current_release=str(stamp_pod_result[i]['Current Release']),
            data_center=str(stamp_pod_result[i]['Data Center']),
            environment_region_name=str(stamp_pod_result[i]['Environment Region Name']),
            old_shape=str(stamp_pod_result[i]['Old Shape']),
            new_shape=str(stamp_pod_result[i]['New Shape']),
            pod_size=str(stamp_pod_result[i]['POD Size']),
            hw_map=str(stamp_pod_result[i]['HW Map']))
    pod_detail_from_stamp_report={}
    for i in range(len(stamp_pod_result)):
        if str(stamp_pod_result[i]['POD Name']) == str(pod):
            pod_detail_from_stamp_report['request_data']=str(stamp_pod_result[i]['Request Date'])
            pod_detail_from_stamp_report['fm_date']=str(stamp_pod_result[i]['FM Date'])
            pod_detail_from_stamp_report['Pod_Name']=str(stamp_pod_result[i]['POD Name'])
            pod_detail_from_stamp_report['customer_name']=str(stamp_pod_result[i]['Customer Name'])
            pod_detail_from_stamp_report['bugs']=str(stamp_pod_result[i]['Bugs'])
            pod_detail_from_stamp_report['bug_creation_date']=str(stamp_pod_result[i]['BUG Creation Date'])
            pod_detail_from_stamp_report['resize_type']=str(stamp_pod_result[i]['Resize Type'])
            pod_detail_from_stamp_report['execution_type']=str(stamp_pod_result[i]['Execution Type'])
            pod_detail_from_stamp_report['resize_reason']=str(stamp_pod_result[i]['Resize Reason'])
            pod_detail_from_stamp_report['environment_type']=str(stamp_pod_result[i]['Environment Type'])
            pod_detail_from_stamp_report['pod_architecture']=str(stamp_pod_result[i]['POD Architecture'])
            pod_detail_from_stamp_report['fresh_p_or_u']=str(stamp_pod_result[i]['Fresh P Or U'])
            pod_detail_from_stamp_report['next_rel_date']=str(stamp_pod_result[i]['Next Rel Date'])
            pod_detail_from_stamp_report['next_rel_version']=str(stamp_pod_result[i]['Next Rel Version'])
            pod_detail_from_stamp_report['current_release']=str(stamp_pod_result[i]['Current Release'])
            pod_detail_from_stamp_report['data_center']=str(stamp_pod_result[i]['Data Center'])
            pod_detail_from_stamp_report['environment_region_name']=str(stamp_pod_result[i]['Environment Region Name'])
            pod_detail_from_stamp_report['old_shape']=str(stamp_pod_result[i]['Old Shape'])
            pod_detail_from_stamp_report['new_shape']=str(stamp_pod_result[i]['New Shape'])
            pod_detail_from_stamp_report['pod_size']=str(stamp_pod_result[i]['POD Size'])
            pod_detail_from_stamp_report['hw_map']=str(stamp_pod_result[i]['HW Map'])
            break;
    Manual_Pod_Report.objects.all().delete()
    for i in range(len(manual_pod_result)):
        Manual_Pod_Report.objects.create(
            fm_date=str(manual_pod_result[i]['FM Date']),
            Pod_Name=str(manual_pod_result[i]['POD Name']),
            customer_name=str(manual_pod_result[i]['Customer Name']),
            bugs=str(manual_pod_result[i]['Bugs']),
            resize_type=str(manual_pod_result[i]['Resize Type']),
            execution_type=str(manual_pod_result[i]['Execution Type']),
            resize_reason=str(manual_pod_result[i]['Resize Reason']),
            environment_type=str(manual_pod_result[i]['Environment Type']),
            pod_architecture=str(manual_pod_result[i]['POD Architecture']),
            next_rel_date=str(manual_pod_result[i]['Next Rel Date']),
            next_rel_version=str(manual_pod_result[i]['Next Rel Version']),
            current_release=str(manual_pod_result[i]['Current Release']),
            data_center=str(manual_pod_result[i]['Data Center']),
            environment_region_name=str(manual_pod_result[i]['Environment Region Name']),
            old_shape=str(manual_pod_result[i]['Old Shape']),
            new_shape=str(manual_pod_result[i]['New Shape']),
            pod_size=str(manual_pod_result[i]['POD Size']),
            hw_map=str(manual_pod_result[i]['HW Map']))

        Manual_Pod_Report_monitoring.objects.create(
            fm_date=str(manual_pod_result[i]['FM Date']),
            Pod_Name=str(manual_pod_result[i]['POD Name']),
            customer_name=str(manual_pod_result[i]['Customer Name']),
            bugs=str(manual_pod_result[i]['Bugs']),
            resize_type=str(manual_pod_result[i]['Resize Type']),
            execution_type=str(manual_pod_result[i]['Execution Type']),
            resize_reason=str(manual_pod_result[i]['Resize Reason']),
            environment_type=str(manual_pod_result[i]['Environment Type']),
            pod_architecture=str(manual_pod_result[i]['POD Architecture']),
            next_rel_date=str(manual_pod_result[i]['Next Rel Date']),
            next_rel_version=str(manual_pod_result[i]['Next Rel Version']),
            current_release=str(manual_pod_result[i]['Current Release']),
            data_center=str(manual_pod_result[i]['Data Center']),
            environment_region_name=str(manual_pod_result[i]['Environment Region Name']),
            old_shape=str(manual_pod_result[i]['Old Shape']),
            new_shape=str(manual_pod_result[i]['New Shape']),
            pod_size=str(manual_pod_result[i]['POD Size']),
            hw_map=str(manual_pod_result[i]['HW Map']))

    pod_detail_from_manual_report={}
    for i in range(len(manual_pod_result)):
            if str(manual_pod_result[i]['POD Name']) == str(pod):
                pod_detail_from_manual_report['fm_date']=str(manual_pod_result[i]['FM Date'])
                pod_detail_from_manual_report['Pod_Name']=str(manual_pod_result[i]['POD Name'])
                pod_detail_from_manual_report['customer_name']=str(manual_pod_result[i]['Customer Name'])
                pod_detail_from_manual_report['bugs']=str(manual_pod_result[i]['Bugs'])
                pod_detail_from_manual_report['resize_type']=str(manual_pod_result[i]['Resize Type'])
                pod_detail_from_manual_report['execution_type']=str(manual_pod_result[i]['Execution Type'])
                pod_detail_from_manual_report['resize_reason']=str(manual_pod_result[i]['Resize Reason'])
                pod_detail_from_manual_report['environment_type']=str(manual_pod_result[i]['Environment Type'])
                pod_detail_from_manual_report['pod_architecture']=str(manual_pod_result[i]['POD Architecture'])
                pod_detail_from_manual_report['next_rel_date']=str(manual_pod_result[i]['Next Rel Date'])
                pod_detail_from_manual_report['next_rel_version']=str(manual_pod_result[i]['Next Rel Version'])
                pod_detail_from_manual_report['current_release']=str(manual_pod_result[i]['Current Release'])
                pod_detail_from_manual_report['data_center']=str(manual_pod_result[i]['Data Center'])
                pod_detail_from_manual_report['environment_region_name']=str(manual_pod_result[i]['Environment Region Name'])
                pod_detail_from_manual_report['old_shape']=str(manual_pod_result[i]['Old Shape'])
                pod_detail_from_manual_report['new_shape']=str(manual_pod_result[i]['New Shape'])
                pod_detail_from_manual_report['pod_size']=str(manual_pod_result[i]['POD Size'])
                pod_detail_from_manual_report['hw_map']=str(manual_pod_result[i]['HW Map'])
                break;
    source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
    if pod_detail_from_manual_report:
        if pod_detail_from_stamp_report:
            return render(request,'podlookup/resource_data.html',{'pod_stamp_result': pod_detail_from_stamp_report,'pod_manual_result': pod_detail_from_manual_report,'version':version_data,'isadp':is_adpdata, 'source_url':source_url})
        else:
            return render(request,'podlookup/resource_manual_data.html',{'pod_manual_result': pod_detail_from_manual_report,'version':version_data,'isadp':is_adpdata, 'source_url':source_url})
    else:
        return render(request,'podlookup/resource_stamp_data.html',{'pod_stamp_result': pod_detail_from_stamp_report,'version':version_data,'isadp':is_adpdata, 'source_url': source_url})

#################################### Pod Details based on cloud-meta API Call Page ####################################
def PodBasicData(request):
    full_pod_data.objects.all().delete()
    pod_name=str(request.session['pod'])
    result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
    #print("Pod basic result is:-",result)
    try:
        for i in range(len(result)):
            full_pod_data_monitoring.objects.create(Pod_Name=str(pod_name),name=str(result[i]['name']),value=str(result[i]['value']))
            full_pod_data.objects.create(Pod_Name=str(pod_name),name=str(result[i]['name']),value=str(result[i]['value']))
    except Exception as e:
        print(e)
    pod_full_details=full_pod_data.objects.all()
    source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
    return render(request,'podlookup/pod_full_details.html',{'pod_data_from_metadata': pod_full_details, 'source_url':source_url})

#################################### PodFamily View Accordian ####################################
def PodFamilyViewMethod(request):
    pod_name=str(request.session['pod'])
    account=str(request.session['cred_value'])
    pod_families= podcontent.pod_family(pod_name,account)
    pod_family_result=[]
    for i in range(len(pod_families['pods'])):
        pod_result={}
        pod_result['name']=pod_families['pods'][i]['name']
        #pod_result.append(pod_families['pods'][i]['name'])
        try:
            pod_result['fmtype']=pod_families['pods'][i]['fm_type']
            #pod_result.append(pod_families['pods'][i]['fm_type'])
        except Exception as e:
            pod_result['fmtype']=" "
            #pod_result.append(" ")
            pass
        #pod_result.append(pod_families['pods'][i]['fm_type'])
        URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs/oci_size".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],str(pod_families['pods'][i]['name']))
        pod_size= podcontent.cloud_meta_genric(URL,account)
        #print(pod_size['value'])
        pod_result['size']=pod_size['value']
        Full_pod_result = podcontent.full_pod_data_method(pod_families['pods'][i]['name'],request.session['cred_value'])
        for item in Full_pod_result:
            if item.get('name') == 'stamp':
                stamp_value = item.get('value')
        pod_result['stamp'] = stamp_value
        if "custom" in stamp_value:
            bespoke_custom = "Yes"
        else:
            bespoke_custom = "No"
        pod_result['bespoke_custom'] = bespoke_custom
        #pod_result.append(pod_size['value'])
        pod_family_result.append(pod_result)
    ATE = is_production_pod_smaller(pod_family_result)
    source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
    return render(request,'podlookup/pod_family_data.html',{'result':pod_family_result, 'ATE': ATE, 'source_url':source_url})

def get_numeric_value(stamp):
    # Split the stamp value by comma and take the first part
    parts = stamp.split(',')[0]
    
    # Extract the numeric part (excluding any non-numeric characters)
    numeric_value = ''.join(filter(str.isdigit, parts))
    
    return int(numeric_value) if numeric_value else 0

def is_production_pod_smaller(pod_data):
    ATE = False
    # Define the size order
    size_order = {"XS": 1,"S": 2, "M": 3, "L": 4}
    
    # Initialize variables to track the production pod's size
    production_pod_size = None

    # Iterate through the pod_data to find the production pod's size
    for pod in pod_data:
        if pod['fmtype'] == 'Production':
            production_pod_size = pod['size']
            production_pod_numeric_stamp = get_numeric_value(pod['stamp'])
            break
    #print("Size of prd pod:-",production_pod_size)
    # If the production pod size is not found, return False
    if production_pod_size is None:
        return ATE

    # Compare the production pod's size with other pods
    for pod in pod_data:
        #print(pod)
        if pod['fmtype'] != 'Production':
            numeric_stamp = get_numeric_value(pod['stamp'])
            if size_order[pod['size']] == size_order[production_pod_size] and (numeric_stamp > production_pod_numeric_stamp):
                ATE = True
                break
            elif size_order[pod['size']] > size_order[production_pod_size]:
                ATE = True  # Production pod has a smaller size
                break
    return ATE
#################################### ExaData Info based on cloud-meta API Call ####################################
def ExaDataFetchMethod(request):
    exa_data_info.objects.all().delete()
    try:
        account=str(request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    pod_name=str(request.session['pod'])
    region_name=str(request.session['pod_region_name'])
    is_adpdata = podcontent.cloud_meta_podattr(pod_name,str(request.session['cred_value']))['podAttributes']['isADP']
    #print(f'\n##is_adpdata -> {is_adpdata}')
    if is_adpdata == "true":
        URL = "{0}/cloudmeta-api/v2/FUSION/pods/{1}/exadatas".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
        Exa_result = podcontent.cloud_meta_genric(URL,account)
        #print(f'##Exa_result -> {Exa_result}')
        result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
        for item in result:
            if item['name'] == 'fusiondb_dbname':
                pod_db_name = item['value'].lower()
        POD_URL="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?podDbname="+ pod_db_name
        #print(f'\n##POD_URL -> {POD_URL}')
        oci_sdk = ociSDK.OciSdk(account)
        pod_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",POD_URL)
        for i in range(len(pod_url_data)):
            P=pod_url_data[i]['facpPodDbProperties']['podName']
            C=pod_url_data[i]['placement']['logicalClusterId']
            #print(f'pod : cluster ->  {P} : {C}')
            if pod_url_data[i]['facpPodDbProperties']['podName']:
                if pod_url_data[i]['facpPodDbProperties']['podName'].upper() == pod_name.upper():
                    logical_cluster_id = pod_url_data[i]['placement']['logicalClusterId']
        logical_cluster_url="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?logicalClusterId=" + logical_cluster_id
        logical_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",logical_cluster_url)
        #print(f'\n##logical_cluster_url -> {logical_cluster_url}')
        #print(f'\n##logical_url_data -> {logical_url_data}')
        modified_json_list = []

        # Mapping of size values
        size_mapping = {
            'X_SMALL': 'XS',
            'SMALL': 'S',
            'MEDIUM': 'M',
            'LARGE': 'L',
        }

        # Iterate through the list and create modified JSON objects
        for item in logical_url_data:
            podName={item['facpPodDbProperties']['podName']}
            #print(f'##POD -> {podName}')
            # Get the pod size and apply the size mapping
            pod_size = size_mapping.get(item['sizeProfile']['podSize'], item['sizeProfile']['podSize'])
            # Create a modified JSON object
            modified_json = {
                'displayName': item['displayName'],
                'podName': item['facpPodDbProperties']['podName'],
                'id': item['id'],
                'podSize': pod_size,
            }

            # Append the modified JSON object to the list
            modified_json_list.append(modified_json)
        #print(f'\n ##modified_json_list -> {modified_json_list}')    
        exa_data = {}
        # Populate the exadata mapping dictionary
        for exadata_item in Exa_result:
            exadata_name = exadata_item['exadata']
            pod_info = []
            for pod_item in modified_json_list:
                pod_info.append({'podName': pod_item['podName'].upper(), 'podSize': pod_item['podSize'], 'id': pod_item['id']})
            exa_data[exadata_name] = pod_info
        #print(f'\n ##exa_data -> {exa_data}')    
        source_url_dop = "http://devops.oci.oraclecorp.com"
        return render(request,'podlookup/exa_data_adp.html',{'exa_data':exa_data, 'region_name':region_name, 'source_url_dop': source_url_dop})
    else:
        URL = "{0}/cloudmeta-api/v2/FUSION/pods/{1}/exadatas".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
        result = podcontent.cloud_meta_genric(URL,account)
        #print(result)
        try:
            exa_data={}
            for i in range(len(result)):
                #print(result[i]['exadata'])
                e_data=get_exa_pod_info(result[i]['exadata'],account,pod_name)
                exa_data[result[i]['exadata']]=e_data
            #print(exa_data)
        except Exception as e:
            print(e)
        source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
        return render(request,'podlookup/exa_data.html',{'exa_data':exa_data, 'source_url': 'source_url'})

def bespoke_data(request):
    try:
        account=str(request.session['cred_value'])
        region_name=str(request.session['pod_region_name'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        Full_pod_result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
        # next_stamp_value = None
        for item in Full_pod_result:
            if item.get('name') == 'stamp':
                stamp_value = item.get('value')     
        if "custom" in stamp_value:
            bespoke_mt = "Yes"
        else:
            bespoke_mt = "No"
        extracted_value = None
        pattern = re.compile(r'customSize=(\w+)-(\d+)')
        matches = pattern.findall(stamp_value)
        if matches:
            extracted_value = matches[0][1]
            print(extracted_value)
        #print("Value of Bespoke custom is:-",bespoke_mt)
        pod_name=str(request.session['pod'])
        is_faas=str(request.session['isFaas'])
        result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
        #print("Value of result is:-",result)
        # for item in result:
        #     if item['name'] == 'fusiondb_dbuniquename':
        #         db_unique_name = item['value']  
        is_adpdata = podcontent.cloud_meta_podattr(pod_name,str(request.session['cred_value']))['podAttributes']['isADP']
        source_url_dop = "http://devops.oci.oraclecorp.com"
        new_json = None
        if is_adpdata == "true":
            result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
            for item in result:
                if item['name'] == 'fusiondb_dbname':
                    pod_db_name = item['value'].lower()
            POD_URL="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?podDbname="+ pod_db_name
            oci_sdk = ociSDK.OciSdk(account)
            pod_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",POD_URL)
            pod_db_id = pod_url_data[0]['id']
            db_parameter_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs/"+pod_db_id+"/actions/listCustomInitConfigs"
            db_parameter_data = oci_sdk.fetch_details_from_endpoint_url("GET",db_parameter_url)
            param_values_list = [{'paramName': d['paramName'], 'currentValue': d['currentValue'], 'state': d['state'], 'customValue': d['customValue']} for d in db_parameter_data]
            #print("Value of param_values_list is :-", param_values_list)
            # Filter rows where customValue is not None
            filtered_rows = [row for row in param_values_list if row['customValue'] is not None]
            # Determine whether bespoke_db should be 'yes' or 'no'
            bespoke_db = 'Yes' if filtered_rows else 'No'
            # Create a new JSON with the filtered rows
            new_json = json.dumps(filtered_rows, indent=2)

            # Print or use the new JSON as needed
            # print("Value of new json is:-",new_json)
            return render(request, 'podlookup/bespoke_data.html', {'data': new_json, 'bespoke_db': bespoke_db, 'bespoke_mt': bespoke_mt, 'is_adpdata': is_adpdata, 'is_faas': is_faas, 'extracted_value':extracted_value, 'source_url_dop':source_url_dop })
        else:
            bespoke_db = "No"
            return render(request, 'podlookup/bespoke_data.html', {'data': new_json, 'bespoke_db': bespoke_db, 'bespoke_mt': bespoke_mt, 'is_adpdata': is_adpdata, 'is_faas': is_faas, 'extracted_value':extracted_value, 'source_url_dop':source_url_dop })
    except Exception as e:
        print(e)
def bespoke_db_data(request):
    try:
        account=str(request.session['cred_value'])
        region_name=str(request.session['pod_region_name'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        pod_name=str(request.session['pod'])
        is_faas=str(request.session['isFaas'])
        result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
        #print("Value of result is:-",result)
        for item in result:
            if item['name'] == 'fusiondb_dbuniquename':
                db_unique_name = item['value']  
        is_adpdata = podcontent.cloud_meta_podattr(pod_name,str(request.session['cred_value']))['podAttributes']['isADP']
        source_url_dop = "http://devops.oci.oraclecorp.com"
        data_list = None
        if is_adpdata == "true":
            result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
            for item in result:
                if item['name'] == 'fusiondb_dbname':
                    pod_db_name = item['value'].lower()
            POD_URL="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?podDbname="+ pod_db_name
            oci_sdk = ociSDK.OciSdk(account)
            pod_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",POD_URL)
            pod_db_id = pod_url_data[0]['id']
            db_parameter_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs/"+pod_db_id+"/actions/listCustomInitConfigs"
            db_parameter_data = oci_sdk.fetch_details_from_endpoint_url("GET",db_parameter_url)
            param_values_list = [{'paramName': d['paramName'], 'currentValue': d['currentValue'], 'state': d['state'], 'customValue': d['customValue']} for d in db_parameter_data]
            # Filter rows where customValue is not None
            filtered_rows = [row for row in param_values_list if row['customValue'] is not None]
            # Determine whether bespoke_db should be 'yes' or 'no'
            bespoke_db = 'Yes' if filtered_rows else 'No'
            # Create a new JSON with the filtered rows
            new_json = json.dumps(filtered_rows)
            data_list = json.loads(new_json)
            return render(request,'podlookup/bespoke_db_data.html', {'data':data_list, 'bespoke_db': bespoke_db,'is_adpdata':is_adpdata, 'is_faas': is_faas, 'source_url_dop':source_url_dop})
        else:
            bespoke_db = "No"
            return render(request,'podlookup/bespoke_db_data.html', {'data':data_list, 'bespoke_db': bespoke_db,'is_adpdata':is_adpdata, 'is_faas': is_faas, 'source_url_dop':source_url_dop})
    except Exception as e:
        print(e)
def get_exa_pod_info(exa_node,account,pod_name):
    URL="{0}/cloudmeta-api/v2/FUSION/exadatas/{1}/pods".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],exa_node)
    result = podcontent.cloud_meta_genric(URL,account)
    try:
        exa_node_data=[]
        for i in range(len(result)):
            v={}
            URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs/oci_size".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],str(result[i]['pod_name']))
            size = podcontent.cloud_meta_genric(URL,account)
            exa_data_info_monitoring.objects.create(Pod_Name=str(result[i]['pod_name']),exa_node=str(exa_node),Shape=str(size['value']))
            exa_data_info.objects.create(Pod_Name=str(result[i]['pod_name']),exa_node=str(exa_node),Shape=str(size['value']))
            #exa_node_data.append(result[i]['pod_name'])
            v[result[i]['pod_name']]=str(size['value'])
            exa_node_data.append(v)
            #print(exa_node_data)
        return exa_node_data
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def save_data_to_json(file_path, data):
    # Save data to a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def backup_json_file(file_path):
    # Create a backup of the existing JSON file with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file_path = f"{file_path}.{timestamp}.bak"
    os.rename(file_path, backup_file_path)
    
def DBInitConfiguration(request):
    try:
        account=str(request.session['cred_value'])
        region_name=str(request.session['pod_region_name'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        pod_name=str(request.session['pod'])
        is_faas=str(request.session['isFaas'])
        result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
        #print("Value of result is:-",result)
        for item in result:
            if item['name'] == 'fusiondb_dbuniquename':
                db_unique_name = item['value']  
        is_adpdata = podcontent.cloud_meta_podattr(pod_name,str(request.session['cred_value']))['podAttributes']['isADP']
        source_url_dop = "http://devops.oci.oraclecorp.com"
        if is_adpdata == "true":
            result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
            for item in result:
                if item['name'] == 'fusiondb_dbname':
                    pod_db_name = item['value'].lower()
            POD_URL="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?podDbname="+ pod_db_name
            oci_sdk = ociSDK.OciSdk(account)
            pod_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",POD_URL)
            pod_db_id = pod_url_data[0]['id']
            db_parameter_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs/"+pod_db_id+"/actions/listCustomInitConfigs"
            db_parameter_data = oci_sdk.fetch_details_from_endpoint_url("GET",db_parameter_url)
            param_values_list = [{'paramName': d['paramName'], 'currentValue': d['currentValue'], 'state': d['state'], 'customValue': d['customValue']} for d in db_parameter_data]
            return render(request, 'podlookup/db_init_conf.html', {'data': param_values_list, 'is_adpdata': is_adpdata, 'is_faas': is_faas, 'source_url_dop':source_url_dop })
        else:
            return render(request, 'podlookup/db_init_conf.html', {'is_adpdata': is_adpdata })
    except Exception as e:
        pass


def ComputeDataMethod(request):
    try:
        account=str(request.session['cred_value'])
        region_name=str(request.session['pod_region_name'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        #hostname = "evzu-dev9l624ku52-fa1.pod341.prd01iad01pod06.oraclevcn.com"
        hostname = str(request.POST['exa_id'])
        pod_name=str(request.session['pod'])
        result = podcontent.pod_members_details_data(pod_name,request.session['cred_value'])
        hostnames = [entry['hostname'] for entry in result]
        compute_result = podcontent.pod_compute_data(hostname,request.session['cred_value'])
        source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
        return render(request, 'podlookup/heap_size_data.html', {'data': compute_result, 'source_url': source_url })
    except Exception as e:
        print(e)
        pass
    
def ExaDataNodeViewMethod(request):
    exanode_info.objects.all().delete()
    try:
        account=str(request.session['cred_value'])
        region_name=str(request.session['pod_region_name'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        result = podcontent.exadata_node_data(str(request.POST['exa_id']),request.session['cred_value'])
        #print(str(request.POST['exa_id']))
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        exanode_info.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
        exanode_info_monitoring.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
    except Exception as e:
        return render(request,'podlookup/error_page.html')
    result=exanode_info.objects.all()
    is_faas=str(request.session['isFaas'])
    #is_adp=str(request.session['isADP'])
    pod=str(request.session['pod'])
    is_adpdata = podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))['podAttributes']['isADP']
    #if is_faas == "true":
    if is_adpdata == "true":
        oci_sdk = ociSDK.OciSdk(account)
        get_dbnode_name = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/dbNodes"
        dbnode_names = oci_sdk.fetch_details_from_endpoint_url("GET", get_dbnode_name)
        # print("Db nodes names:-",dbnode_names)
        exadata_details_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/exadataInfrastructures"
        # https://prod-adp-ops.us-ashburn-1.oci.oraclecloud.com/20191001/internal/dbNodes/ocid1.adpdbnode.oc1.iad.aaaaaaaawrbabwuaymo2i6ulzzrfydywldnmumhgkdgwmh6c242gyspfxtta
        oci_sdk = ociSDK.OciSdk(account)
        exadata_details = oci_sdk.fetch_details_from_endpoint_url_parameter("GET",exadata_details_url)
        vm_cluster_id = ""
        for item in exadata_details:
            if item["displayName"] in str(request.POST['exa_id']):
                vm_cluster_id = item["vmClusterId"]
                availavility_domain = item["availabilityDomain"]
        if not vm_cluster_id:
            fusion_env_url = "https://prod-ops-fusionapps."+str(region_name)+".oci.oraclecloud.com/20191001/internal/fusionEnvironments"
            oci_sdk = ociSDK.OciSdk(account)
            fusion_env_data = oci_sdk.fetch_details_from_endpoint_url_parameter("GET",fusion_env_url)
            #print("pod name is:-",pod_name)
            for item in fusion_env_data:
                #print("Came inside for loop")
                if item["systemName"] == pod:
                    pod_id = item["podDbId"]
            pod_db_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/podDbs/" + pod_id
            pod_db_data = oci_sdk.fetch_details_from_endpoint_url("GET", pod_db_url)
            vm_cluster_id = pod_db_data['placement']['vmClusterId']
            availavility_domain = pod_db_data['placement']['availabilityDomain']
        dbnode_data_value = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/dbNodes?limit=100&vmClusterId=" + vm_cluster_id
        db_node_data = oci_sdk.fetch_details_from_endpoint_url("GET",dbnode_data_value)
        for db in db_node_data:
            if db["shortHostName"] in str(request.POST['exa_id']):
                db_node_id = db["id"]
        data_db_node_based_id_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/dbNodes/" + db_node_id
        data_db_node_based_id = oci_sdk.fetch_details_from_endpoint_url("GET",data_db_node_based_id_url)
        db_host_details={}
        for i in range(len(dbnode_names)):
            db_host_details[str(dbnode_names[i]['fqdn'])]=str(dbnode_names[i]['id'])
        db_host_value=db_host_details[str(dbnode_names[i]['fqdn'])]
        #URL_H = "{0}/cloudmeta-api/v2/hostDetails?hostname={1}".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],str(request.POST['exa_id']))
        #result_h = podcontent.cloud_meta_genric(URL_H,account)
        oci_sdk = ociSDK.OciSdk(account)
        #p_h = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/dbNodes/"+db_host_details[str(request.POST['exa_id'])]
        p_h = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/dbNodes/"+db_host_value
        #print(p_h['logicalClusterId'])
        #print(p_h)
        response_h = oci_sdk.fetch_details_from_endpoint_url("GET",p_h)
        oci_sdk = ociSDK.OciSdk(account)
        ex_data="https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/logicalClusters/capacityManagement?limit=100&capacityState=All"
        response_cap = oci_sdk.fetch_details_from_endpoint_url("GET",ex_data)
        for cap in range(len(response_cap)):
            if str(response_cap[cap]['id']) == str(response_h['logicalClusterId']):
                db_units=response_cap[cap]
        #print(tt_is_req)
        #print(response_h['logicalClusterId'])
        available_huge_pages = int(data_db_node_based_id["healthStatus"]["infos"]["availableHugePages"])
        # asm_reco_total_gb = data_db_node_based_id["healthStatus"]["infos"]["asmRECOTotalGB"]
        # asm_reco_free_gb = data_db_node_based_id["healthStatus"]["infos"]["asmRECOFreeGB"]
        logical_cluster_id = data_db_node_based_id["logicalClusterId"]
        
        health_check={}
        #health_check[response_h['fqdn']]=response_h['healthStatus']
        health_check[response_h['fqdn']]=data_db_node_based_id['healthStatus']
        hugepage_gb = ((int(available_huge_pages)*2048)/1024/1024)
        Total_hugepage = hugepage_gb - 22
        health_check[response_h['fqdn']]['infos']['hugepage_gb']=hugepage_gb
        health_check[response_h['fqdn']]['infos']['Total_hugepage']=Total_hugepage
        health_check[response_h['fqdn']]['lifecycleState']=data_db_node_based_id['lifecycleState']
        health_check[response_h['fqdn']]['lifecycleDetails']=data_db_node_based_id['lifecycleDetails']

        #logical_cluster_url = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/logicalClusters/" + logical_cluster_id
      
        # WORKING
        logical_cluster_url_base = "https://prod-adp-ops."+str(region_name)+".oci.oraclecloud.com/20191001/internal/logicalClusters/capacityManagement?"        
        # Gets First 100 cluster data
        #logical_cluster_url = logical_cluster_url_base + "capacityState=All"
        #logical_cluster_url = logical_cluster_url_base + "limit=100&capacityState=All"

        #logical_cluster_url = logical_cluster_url_base + "limit=All&capacityState=All"     # API Error
        #logical_cluster_url = logical_cluster_url_base + "limit=200&capacityState=All"     # API Error

        # Get data for specifc cluster
        #logical_cluster_url = logical_cluster_url_base + "id=" + logical_cluster_id
        #logical_cluster_url = logical_cluster_url_base + "limit=100&capacityState=All&id=" + logical_cluster_id

        logical_cluster_url = logical_cluster_url_base
        if str(region_name) == "uk-london-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV3SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uY3BPeHp4M1ZPeTEzTE1UNy5hbEM3VTFZR3NNSllGWEE3ZlNDbGxNNndPcjkxZEhvc2Q4U3hGa2ZCMmo4NnZUbUJBZVVnaDNMWXU4cl9MU2h3anQ3bFBVRjdHNGdESThPMWZLaUtNZHVRaE5xZlVxbXp0UHhvR0ZHdkJKV2J4Vmg1TVRYVlpfR3JSOV9TNUVuZWhrU2xaSS1MME5TbS1ZXy12OVpjT0hzQ09VbERweld0U0JIdk1Nby1nQWg1RWxuYmJ0VFUzczczVlRrbVZZMG1ZWV9HdWp0VTZYbjJpZ2VJS0ZIU1ZwVVA4XzFqOWRaRjYyek1qcGphMkV5ZmNXZXRyV3BTNmMwOWlCWjRPdFAxa25IWk5hSW5HcHI4alJuZ2Zrb29JZmM4WWF2NFJ3Qy1laUFIcW9jT0xmNVhtY1NsRjJIdUU1YTE4YUczcjFZSXdWclkxQ1hZdFpERXRiREd0c3RvcmpLa0xmT3JsYTNKNExaVFVtNlNxQ19VNUtsc1NVTVVXNFdlTk1zZ3BZTnB5bFdYSlVZTndkZ28zVy14Tm92bnBrR0dhM0txU1pFZGZvQXM1V1Y4U2c5OWZyWkY0U0FxZDBRWFh2QS5zRGZOdDNIMlZPQW1pNF9hRHlULUl3&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV3SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uMGc5UjVubFRBczZ0X0pXaS45N0JIU0NkckJEemZPbUxvd3ZaNXBMb21KMlBDc0NMNU9FTTVWRnJDdFVkNi1KU2ZqS2szOE50NExOdTlweGxDSFZzZVRYTHNHRTV3SlJ6bVhyS0dyV2xqZzFDVDE3aU44Zmhwdll6ekljVjJVRzZObGktcG1kQXpWSmlmMGZiUHBNVG1lSnJNeUprRllFQVBYN0FTbXNucmR2dnROMFNCUDJrRFNDUGR4MUFwN2RXa1E2M05HQTNHcUdTQXRSYm53WXFxb3ZZc1lub3YzYWlRLWd5MjNVUVlBQVBzMnVGeFFaVGwzekplcEg5ZWxVTHIzVUpEaXoyaF9LcmRSWGJXQkZsUDJvUFV3eWZiQlFjZl8ybDB6UHpBLVVxVnFzTklZdVdCNUZTOHExSUNiMXowem41cEJnc1BGcFA1VjRQbENqV1FoYl9HdXFodnhMb0dQemRPR2pnS3ZjRVlhWlJCcGlSSjV3ZDJGLTB4cFFJNW5tZ2w0WEV0bXBZU1dyYXFraHJmWG1JdGZkWTFpalBucHVGemFEV045Z3hWdG85bGFMSFZUU0ZVUmpwV3AtdkVYV1hPNjZVazJKVS54WGN5dnd2Y3hPMWw1X0g4XzZSaDZR"
        if str(region_name) == "us-ashburn-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uYWxhdzh4VW9YMklySE13Ui5jZDhtcUdXaURieE5Ka0toQ3h4SG01R2IyenEwOHBvV1Q0Ni1OcUxHdUtjSm12d3ZkLTMxYXZ0cFNybnhRcUNmS21wQ1lkejZfWXdOZjhVWVJ6Vmc2TE11Y1M3OXlPSFZtRzNsYVcxUHAwMmtRWXNYOVltczNNSEpEVGI1a2xKTnhEZmZVeW5Yb0ZOT25uMkpkZGk5R0hkWFU5RHVtaVozQ0RPRXNReUZ5b3hnWHpQc0VXNTNuc2tnLXJwTVQ4Sk9YOG92UjdkaHhzNW50WENjTXhFU1AtVTMwWEdHY0dpUDJ5czlGNGR0ZGVpanJtQVR2WGsyeWhVdXpmTDlvZk92eUhGTkU5bzJWc0NPb01Yd0owYXlHMlpjbmlHOEZ0T1R4eEszbGRWSnBhWTF5XzBvaEFxT19FM1ZXQ0Z6amFNRndUMWhIOUJUdGo2dnJvOUFkQWFWZ3U3eUl3SmotTXFCZU51N09JWExZRFNTSC1uMFlKSEVvMzhXbWpoVnNaNVIyRTBzRG9ydlJQTnN1amRCY2pBSmtCUGJxRUFVMGdsV1IwZDV6OGhZRXdEeEMzbkEuQTU5cGlQUklzeXU2STExcGVPZjh5Zw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4ucmtEMXNDMkhBamF2cm9vLS4zRFRfc2ZsU09LdmRWMW9kM2dDb3FucWp4SnNROEdQZVZBWTBJUUdFVUFjV3k4bGh0T0IwNzFiQVVrUkQ4ZkVxVUpjenVqdmo3U1M4cWlMU1FBUWlmTGl4OXNxYmpJME4wMVh3RmZyOENObzhqOXdPblVPV1YxblozY0JaUl9OQWZDVE55NGVWWk5NQmpSRk1ONWlkbVpVa2doUVJHOGZPbThiQTYwSmlLZWFzTXRCbkF2UlJzTVU5Y3hmWDh6WldrbTZMbnlZUWhxdkdSVjB6Vi01djNiU0pPQXlmc0xveEdaazJudEFBTWVQcVNSekxsVzMxRENBa1R4MWZsMXUyTHJXLXgxZVI2ZjdYUDFIMUYzdHdMQndsQndiczM4TlB4bEh5cUJrd0FWNXVOaFNGNVh1Szh2aTV5M0JiUHR1UWxiYWpuTUxzNnhXTHNVSEtPOVpibUtHcTNlN1lDVnN1cEVwaTZ2bnFla0lQdC04RzRzWTAtd3hRaXYtaHRyZ2Fqc3ZSX0FkMXpNZGZzNjd1R0xuN2Nyanc1bHZ4b2VJV2lSZy1jREZLc3pPeUpRUkIuMnNOS0RTM3ZmeGVNUTM2WW5pbU9UQQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uZ0FwQnFzSHlsbVhSczQwMy5EOV9LZjFjVVdKSXg5UE1KTTVFS1h0dVNsWDE0bFRVbzRhbXU1ZHhKQXQ5djR1NnZNYTRDYUlGbWI4NmtwT2FCOVBObm5aTE9ZQklZdnRPRFBGbmNpTXk1cFkzeE1YZ1dMcHdVS25WdHVQTWdyNnJGUlo0SVlIdlZZaTl2c0tuU09hMmc1WG1peEJQazg1QlBnd1NPeWZycjl5dG13TXFOaU1MbmthZEphVEJWUHN2UVp6Um9qazdOaTc1N2RYMjdCanlLSUVXaU9kbHE5ZHowenBkR3k3T04zTnJfbEYzX25zenk4dngzaWFJRlhpRFdZa1I1bldLWXlXYnI0U0NEdkd2VFg1clFJSl9LMFJtS1lSa3k1WHZJN0dObXJvb2FMNEVGY1lZZUpTRlJYZFYwLWs0MmhzNE1XdGx0dWxjMDVOelJ3MGlCUFlaTzVwUlJ3TktDVXlfbjhrX1V4ZFBRSXF6MW1JNmZ0QktRM2l5bUhyWFljMFUwWmh6cTFOZmFxLWNUVHMwREhfZnlBb1U4S0U3V0xhZU9pRlhLQWJWMnE0UVBFLVJJX25BYUJfOHYubHRCX2dFWmIxc0x4Vk0tZEY1bFVfZw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4udGlQbjQ3T0dtWTFuMjNqRi5GMF9oV0tfUmNReVhjQmxuVTlweU9fMjJQMjQtUTJHVllUQlBrVm96OEFGdlBfQ2E3R1g0ODAzN3k2Z0Jjb3VDZzMtRzlESDJxQ3luWnFfaVN1ZWNsUnRldzNrb0lyeG8tQl9lUldUZzZ5N0wtRnZ0eHZodndYbDBuUnlzTGVRcUh5Qm1BeHBDUWU2RlJjVDNBNDlMVUJuSTlzUkhtX05QM0x6dHhpZi1yZ3h4V1IwbkhLUFF1U2gzTURlOEpTX18wZVFteFA2X05oZ3lJYndaM1NMR1ozYV9sWTFvemZFTHZaLXRqMnpLOHhWQjhRbFFWNUJLMVVndWhVb29IaEQ0MlVUVTVXaFRpNUlJTHRYbTdTeDJ1amVfZ3NNWnpRa1dZMjktVTBZNnpnU3hETk8xQUtNc0FTYjdpQmZGUWdtb1U5dGRaUU5CWXUzSjkyMFRIS3JYd0JrQVVTVEJhNWFJNlNkSFoxeUJKLWdDNlc4ZUE4Wm82NmprTjJCVEJZdmVlZS0zM21URUxHcUVWVHBuNzdYcmpRcDVUbm44Y2hLZDNQZ3h6UlkxS1RYQW05SnMuYk15V3ZCRnlYampwcFJ1Q2doRTJOUQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uc3Z1MzlQREQ3NE13dm5zRy5EeUJ3cE1kc1psZHFJWkE4SVB4X2s2aWltb25SbzRXR0h6NWtEYklnNnBLWkc1MlpmLXM2OWlIbDJhSmx6bThkOTU5dXc5aG5mbE16VFN5OFM3V0V1blJuTW1oMS0tT2lUakU2WkhpUjRSQnZ6TWU3QTByRkZGVjcwTkdHdFM5QzJNQjhGTmZZRndRdllPakE5c0Q5c3ZhMHJnNWNldy1lMXJ6Qy13TGY4REFrNW83cklHQjBHZlZSWU9NVFNUdFlmZFh4VjZKa3NteE40dE5wUk96LUZheEFSSEpma0F1S0REQ1duTlQtRmVRWnhjUkxtdDlYOHo4cGdZLXN1RjBpNDBQS21pVWx0NFpNUk00blZ3cE1UUHFxQ0tac01SSWRURjJUWkw3V3BUaXdiSExYcWVOVy12YzFHWl9QV0pqYktHVTBjOVFfMGNfOUNyUEd5UWZvcHNVQTdaZDRCcmowc1p0b2pGYk12Nllqa0k4VDZfWEtGdTRwVm81NXlCaGRySWdhQUh5UHZpaUxWWUlaQmpYMUNEd1JMckwxc1BFTlFzdGRjMXBvSzlWVmZfRlIuVU5pbXVUMTRpT2k0Yjd3Vk9UVHVndw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelkwSWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uSFV4QW5OWXdlcmxuSXFHSy5qdE9QX1lMZDJPcW1VaTRqRzNXam1xZEVZZ2RROUlRdERSNWNHSW1lMjRLdlZwTEEzOFVRaFBpQ1RwcUI3djc3SmxKSERYOFRVRU1zT1VpTFBJSkdidU55STRJaXNYQjZyYk9pVnFPZFQ4ZzhNLTZPZGZwTDZDc24xbTVUZE44ZmVET28tTV9xb1Ffck0xUjZVSFFVYXktalQyWHM4YWExX3BGeDNyNm9OZUNsT2JkSGs3clFiSWZWWjJPenBvZ2FmVTNqdnp1R2FmSmotdFlncmhIZS04Y3hxT0xfQkRya3hzNGs5V3NuUER4NjVFaGdBa2NRSFI4clpjVGtlUzU3RGdGcm1Wc3RwVkJSVk9yM0RlQXdMWGdtWF9wZV9Kckh3Nm52M0U0VXp4aFpYejNmRnRtYXBTUW9OSkZpRE5hblJHeDlGRUtPWFVrX0YwUVVsbGdiNFp3OVRwQU5jUzhzMm9mM3dLeG53ZHBWandKTTg3VGpSRzBYeWhTZHdfa21Nd0pLVWVIeDRMaHdHVWVnRUV0amxQbEdkMXJseUpVRDlxXzBiT3gzZUEwQTkzeE8udUIxcVFGRnp5QVRrVzV5R3hoRk5zUQ%3D%3D"
        if str(region_name) == "us-phoenix-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uMHlMLW5USVFEcnpkVm5NYS4tMUxlR1o1akF6TGNvaGhwM3VTTm4zdW9ETEw0RmIwV010RlBIc2Y3TjFvMVV5SEE5Z1d6N18yTlpCN1F6cTd4Mk1wMTRwOUk1QkFpTU5LZk8xV01iX3pWdENxR0lTbUpYTzNvVEo2dThpdVkycWdzRHo3eXE1NDBWZ2QwSWhEWUtJNUZmY2ZoRGJiN1RpR0VsM1dwOURUV2dVTlYzZFV0X0hIWVJrNEx3QkU3LWFvUU9xVmlhQTlNRlJ6NmZQdmEwVUtodHo5MmNVLUM3UkJabk5nREV0RVBoMnNhQ3IwX2kxU0pISFk0QjZQM3VuUlVNNkZ4Y3lpeGs0LW9HTmtjU2Y1QmFPcHlRVE5NR18xY1k4NzBoT0RPdlFfMkRCLXdTNnVWU3JUakd6eG5PeU9sYWRhRTl6Y3RzcjgxdGxYMVRYTFg4MG9hanhpZzBLVV9pRFZSYUZRVHNIZVk0WFA4OTltX0pUX0J6MS1CS2hLcUFBaW0zeTZCRjRXQlBUZWNPTXdBQWgtMS14UF9GVzV0U3AwVElRY2pjeVJKNVlsSzJ4Z1MwRDZNTTRMMzkwUDkuQXBYdjBWWHAzYlpxTHlrZTRKYjk0dw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4udWFFN2Z1WHJXYmpvb0ZqNC5HRk1NLTZ2NC1ZMDNjcXhhalJHRHMxbm82clo4cnJ4dmZQOV90c1JBWEo5TlFtS3I0bDJERnpFZlZGSXNYcmZwalk2eHFKQjRxbXFoeHhrVTdCWGxrQ2tqalNKN2xRS3BMbUpoaVI5WkFTSm5tdHplNkJYejhrdWxmQmN2MWpaQmdrTURJbl8wbzVtNWVVM3JlMVJYTmJ6by10dkZPYnowZDN1REo1VGR4UUtqTlJDWE1GNXNKNi1Ga0wxRXU1VlR4czdnVVJxVVFHS25TamZmajl0N2ZtYzgtOXkyay0ySkVtQTlUajVESnVsNk9wYmxrQTBIVVlYUGN0T2RsOTVYNHlzZkdrTENuZXhmRnhjLXlZQjJBdE1qcnFDZDRHLVk1aEExV3FuX0tKUmh5Ylo3dkZBNHZxNVFlMUVvbFNibkVFWnlkRHFiVXlFMVlqSkJXUkllamZkZVZqcE94ZXlSYWtnMk03VWtHUWdzbEhudnl6MllrdE44alNrT0IxU2NHcDNaOXZnQ2RCcDVZOGE3cW14OE55V1BDaVdDVXNyaVlmQ0lZR0pJOWstWU9lYTQuRmJXeld0SEY1RHlneDVsUjhkOXp1QQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uenpHeENPaVZyeGdSb00xSC4taVp6WXBKbjg1a1NLOTlOQkZYUk9ZTTg1MlVudVRlR0w5QVlaMkx3MkZmUVM0U3B4S0VHenpEdl9Dc2NELTJUTUlsb0RtcWRlQW9VTmh3ZW9qR05GcXA3dHUtemVJZlRCYkgtV0E4M2dIUmhRcklhNklTWUcxMm5Wa0gzWDlrUENOWXJhVHA0em9DNUhCeEhGSGNicng1ZnZmakdBbjZCUTZWeTluYzVWTjQ1c0ZNOWJrb2VIUmJneF9ybk1HYWlidFU0SUxYUXpUTkpuemFpZGx3cnBNZXZQemstTEdRYjBmc0QweDVPZVlXbjFEUWdXcTV1ZnJyYkFXUHNfTEdHS0RDT0ZjS1ZsbVFYMlVwU05VTXNDU3pBVGJ0cThUeHp6TWVnQXBWUmF6QTZaR3ZPdmZ4ODBkN0VoOVhBVlBwTmdMdUhSVUw5dzZRVy01d3FVTVFXcWpwY2FfcTFWN3lPdzU3Sjg4eFNCdGhHbXZZTF9teUF1SUtNbWNqaHdkV3NQcV90aWd1NC1zdEdDMjE0RG8ybTJpczJGY3hySWVaYWRHSkZGX3pub1VqcnRmVGkuRzNMZEE5ZVBsS2hPZ2ptdjZyYUlKUQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uc0lOci1vOTJldktrM081TS5jWkZ2WlpDQWtoZnBVMFJ4dUEtbzNiZ3Q5bUF2VU5fNE5uQnF6c18zV29FaTRkb1l6aGMxdm1tZDZFeUlxTnl4VEhJLXZwZ01NTzU4VW1sX0tfdm5GQU1jUGVkTmhJWndYcFpFbUJOR3JyYVZiLXhRQkJwcVp2d1UyZVpVOUZuUXFiNy1yOG1KejZ3WXVLb3lzelg2aGdOMTZLMnJkVlE1R1VkODJYTGRsNTh6bjB3MXZVRzQyd00zMTRQd3RKQVlXUnFCOE8tMjJEZGlnWG5oUTJkSld0MmNyalVkRUlSbmtlUGV0NzdvREZVUTkzRllfY1hZejB4N1Z3aUdySDJwWmItSGNDa3JpT3daSVhoYXNVVXQ3dXIxQnpnTXV2bFJMMTQzc3cyNUVUSkhsQVQ1TVhpTHQ0NUdsVzNtcVNyUHNqYmpYcnlzT3JRNE9UQ3RnaU9Sb0ttdGl4VDZEeGV6NWxjcVNLNW0xWDFoQi15QW9yQzNQdzdjejFwYktXRkxhdXBQZzNXb2p5cUliUTZuTi1pTGlkcDY0SHZVQnlhUXh0ZXJFQTFOV1FDZy1KTmsuMWhqaGs0UzFOX0RkaUdmTmJ2a2p0dw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uSFAwRjZyVUR1a0c5elJobC51cnhUQU4wU25ZUThDenN5V2Mxd1F6N0trU2JjV3U0UFpqa3BUY0hwVUE1UDZMZWhYbTlZY2MxS2RWUjlmVWdINGF0TmUxcjJWLVhYZENGbF8xYl9FRnVqbmN5Xy1mR2llNmxsallqd09PU2kxQUVKSFFWeWxvdE1pbE5ZVklJX2dTNkptanZlcWUwZ3JxOEVvTmF3NXl0X2J5ZS1OMU5wUkpzWWtibk1jQjE0Qk9OdXNfWmdtUEwtbTV3cFlFSFNJa1FnWU5YaGhOMXhDWDZCX05Lc1BYN0RXZEJTYnhwTHZaTG81VjJ5bzBRY3E3S0ppaklwbldMTFFsVHlBeVd2NEF1WVY5TEpxTDZVS3l4c0tqMEtEWVRqaDlwUS1nanRYd0laR25SNGR4NlRLWVNoWlVqNmtPMDRLYVIyQWFTdG42WEFqXzQyWlh0bWxRb3ZCd0h2QnhxdmphWUdTcjMzeFNiZ1B5Z0VjRW9NeUpoc3d5OHF6RV9QVFJJUG1ZcXEwX21sWkFfMldrbzJmTWJicl91d1pFUC14aEVjNHlSRk9PbXlFaDJUZElmNTQ1YWkuclkxRnJ1RnJTZWhFUGhEUzk5YjVaUQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4ueWMybzNwblpMVGRmSXdpMS44WW9IalREelVONW1CVVJnU0FOMHpIdlNIb3FSUnlZYktpcnViclNrN3luejFNNjhGVHhnamRDNm5XZzJ5Y1hEMXIyVlJoLUVlQkl4ams1aHc3d2Y2T0tybXZxZ3BzUUNkbWd0VExzaktJYVg1WmdrS01OMHBESWdZcUd0NUhfSG1sQTBKaWtGYzU3RnFHRDVCNXROYkJadGdJLXY3ekFwZk9qRHJKUUhNWTJUTVZIQ2RBQjFtUllWNUZDVEhoakI2Y2RpSFA5SXVHTk9PWHJoc3FNNlNaWXd6eHdQaTY2QXg0YXR0VEVocHd4MUZ0MGNpeGZMUndTcEpnbHRkVmVGSzFPNHJZWVo0ZXBpdjdCTVJObnNZQTNoVVpOR2I1aTRxUXRaNlY0TnNtcUFHZkw4a0hzaUpmdXkwZXNMLWhjYV9wUmdLWmhlOGV0QV9qZUY4OERpNVRBQV9iaHBSMFpKRWJXcmt5clJwSWNyVWMzZDZaZW1rakpjNjdSVmZ1MWZxV3lHLTdsZVVqdFRfNVhnQ21IbVRUZVE4NU0tS0g1VXpYbnZBRTBQU2s5eWFQV08uU3JsSVlWcXhXMWVyTmFfVXpoQmdhdw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE00SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uaTNaTEZ6MEZIRE8wQkNnNS5iY09ha3lHTGlPWHEzeGtIdUpFTGw0UVE2aDM0Wmd1QVY4TExHMUVWRFllcFdOMFZvcGJUVDVtZU8wcmtreDBWWVlWQXlKS2otVjhYeENtTl9neWtDSC10N2QwNTllbTIxY0dUYm5uVllCcEplbUN1a0xLdnpyaEY4OWVEM0NweVJ1LVBXTVE0VFVQTnJMVUlUbmNGRThnei1wUDd5MXhkZGRpUGNrUTVVckpvMjVFUFZXRVU2ODYybTJWV3k0dW5qRmJFbmhQdno2V1AyM1ZSU0gzMzFaTUFrbkQzRmxtUTZKdFpOdXRqX25fMnZsOFBGbjdSNVROOUdMd01ub2N1NTlUb1dybWQwZUJoZjhEa1pQM2JKY3RBc09OTk13Sjg5cGRIVDc4M0J2ekxJRkxwcE0tMFRpbVFwbHNkb3p4ejRXNm95U0YtSV91QVZkMjZXNnNVclYxT1BYYUNTWDhoeWJCRk9UMVNTWlgwVWR5Wll3T05mWTQ5NndlWHZBdGJQaFN5WHcyaVE1TmVJOFJqdHROSW1yV3BvdnpKVDFjX0wtMHkzMi0yQUZIcW9ad2sucDd3SXV5dDFnRVlPLUIzR19tTnJyZw%3D%3D"
        if str(region_name) == "ap-sydney-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhPRE01SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uNF82dEUwTXlZOGVFTlhPMS4zYnR6cWFRa2ZNZzFtRktpbEU4U0dFczRDWWVLbnNWTU1ESGd1dUJNUmtNeXRFQm94RWlGTnN4YXNTMjJuMGVRTTBVTlEyaEt6SVV1VWhOZHVmSWNWY0Q5Z1p1c3dfS1dvTlN0dlNfd1M1TmFtQXFqelppd2dtVkFSeW1jRV9VRl9ZM1otaGl5T2lNWmpoQXkxZlByZUU0cjl2V2IxanNPYTNuYlBlSVFYM2FLUXZrLTE3WFhveHpETVZPYlpuZjFIRzlqeG9tOTc5NndJaEpwMzV6eFp1Wms3OThXejBXb0R2WmJobHpYbWt0Y0UybFNsVEF4NDBTR0lCVzIzYTlkUVExS2V0VU9iOGdYVExIakFJNlZYb3phbHNDaVp4UEliRnJ3TE9tUTdTOGVyYlNneVZSU0QwbHJMbWdRa24zMXZHYU92ZHpTY2JpdlhXVktvRHhrckRWakNMWEVnLWRhVFk0dnJqMTg3bFl0a2R4VlRGak5vRkxZQXVRUjhHeEVsU3JEUmZxMVMxNlk3ZEdxUk0wNEp1N2dyWG1EQWpLVElvS3Rfc1c0VHZvY1B1VzNnQVNlZXRfUDExOC4wQWxTb1FaV3l4bWdiUnBLejk1TG1B"
        if str(region_name) == "ca-toronto-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOell4SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uYUpWaXJBYXZ0OHB3UEdZRC5xZzhodDktUWJFX21VZWR2dWZPS05NZWoyU2ktY09VcXVfSlk1T1FSdE9oem1ycVVHUC11VG5YeWRlUXFPQ2RXa2tQZllFUDZIWUFtWEVQU1pPb2l6T21vM3N1OTlnU29IOGQ5Y2lmem5pME14MmVOWWs4MVhMYkpMbHQzN0daRkthSHBuaEJDdUJ3VV8zYWNrNTZLTFZ0TEh5eHVQZ05zVy1mVldSRFU2Zk9WZXE5Ny1fZ2EtVUJObWl0TElQMnN4dWZqTTdmLWVNUjdGTmhoTno1Nl9yT2E3RFZYMi1feUt3clV1czE2MlRIY29VNVRjcUhLYVNpdjJqdHFnbEtpbjdaUVlLTFlfZG1sVHZWY3p1dzdFTjQ0TnFhOGRvQnRuVVVKRk9KSFRjUGQwZ0xKZ0YxMHh0UGhmQXRLUkstb3QxQlFQcWpRUG93YVhObTEwY0o2Ui1ZR1Jvbk5ISjJSWXo1M2lwWGhnNmRqRzdFTXJtZVlJa2pQd1JESUdfMUY1RkNwOUstTTFZWVZ6OFlRN0FlWXpzTmJUYTZYdmRvWVp0aVNza05pU3RJNzByTWkyZjE3SE11bjJfRDEudnVQd25vVUY4Zm1tMW5ma0VsR1JKZw%3D%3D"
        if str(region_name) == "eu-frankfurt-1":
            logical_cluster_url = logical_cluster_url + "&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV5SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uOUFBcVg5QWI0ZzZZWllXZC56MUVBc01JZmlDS2tyWmlYVVNqN05LZEhlcERzR3c2dnlCaU5nUUE0SDdBdTB3RmJESy1pMEhveWNrblRvXzJKa0hWQnc2emQ3cFVNWnhVc2N4dVpwMmVNZ1VzbUR6NXFDRkVqUHhyZ0l4bFFwQU5kb3VyUW91MjR3OFVZY1Y5UjhFVENOa0NsdkFfSC1QTWxtYkg0dWhBYmdRd3M3Y1JGYmFzT2tURkg2d2JpY1dCNFJhZktqMUppZkw0RnZFZEhjbnl2SUpfSklBSXNsVjllYWpYbVoxRkM3RkVhQXE2VWJNTTZQVkNkYWRTSHYtOFBLZUExVlBGXzlSOEw0S0xlUWNFZVNfWVpWZndjQ3FKYkhaS1dXaXhOUC1WQTRIUkd2ZHJXN1RJUFdFSmJrajdERFFMUm5zZlUtd0w4ckFCdUxyR1RuaV93Rno0OXNkQlA1WUFXdzUwb0Z2NmZNU2JnRGs1ck1hRFM5elladjMyMDN4X01lVDFDa1BlQzkyQlBHcHRBZFRJY0xKOUJlSld3azdKRFlHc0ZUNWVsekFYQ2Itcm9LdnhxQzNyNEdoQ1VrWFIyYjJ2dncyS291cjguWWRFS2lhYUl2QjlGdm9jVjROUHYzQQ%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV5SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uT0wwbXZ3ck1RYVoxQU1pVC5URHI0anhDSi1lU1VDTnlQcGdySUhPbGJmczJUT3lSV3BlSHhsTnV2a0F4dEo3MU5pWFZHSDhVTERoMUJVanVnd1hHVGhXUVBmeE4ycTdzaVI3MzJrODBBSzY3dGJjWjZPaHp0TkJaZUxQU09rSURvLVRfZkRHNk5ENnRvNGlhbVZjdG4yZGJIMFRpVHdJUUlqTEotSmRBeWFyZGNad2NLd0VYZlhYcWtPdHM4X0U4MmpVUUQ2dEc2MVdDMzFPYzVoZ3M2c0pJdnlaVWNPbUNlWnV5T1dPbnlKR29paUJwQ0E5V0dia19tUXFQVmlBeERMMnlQMGdXNU5FNHdPMC1PaGZ6MkdQZ3BmUHF0UGRqZ0RBR3hmclNKZGVxU0lvQUFRVW5wRERRLUhwY0hjV0lYUTNmZEVUTm9vUG14VWpubkxPaFBYVHdJVmVEWXRPeGJjU3VFSGxGcG1adkFsV25NM2RFdE9telZfLWdBMkVDcXQtenI2MGtfR2RxY0g0bl9KU2VMZUdnMThBdXBIakxjem45TWZDVFh3b2xza25EOThpN2Mxa1FDVF9RSjV1SlMwU2Y3OE5pRmU5R0dHOTguYzF1WkdRWkRWajBZTnVibTBXYzlydw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV5SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4ucUp1TTUweFlxSHVucWFLeS5KbGFFLXJRM3pJYmFnNGRYeXlEUVBVZlZFa0FDWGp3TUZMWTlmS1N2cUdqQWMwQ1g1VzQ5bUdSZTJuU19KX0k5WElVUVFrXzRqSmhUTlNkelp5YU1QdkhkV1BwWjUtaEhDNTZxbU5tTGZLbmNTT0VENmx2QWdmeEZCa1NpeF9Fek8taW4tcV91cUI2T2M5Ymx5Z2JtVExNTDVJM1UxdTRoOUl5WXM5bUFMcWxrMHo3Y2hoWVMtQkZNLW56Rk1XdlZjVFZnUjFTNlJ1NUJVd3VCSkNaQWdySTBlX2RyaUlrNDlVSWhYV0swRklDdjR1YWpiWHBGY3l5SlJsMlFzaXpLdmdpUmgtbFFFSm9kU0tST0lsMWUxSW1kbUg3TjB5alZVNFN0Nlg0Z2hUTkRNblF1dVpNN3hxNllLY3FVZ01rSHc0V0k4MHZyZ0kySG9lSWppTnZyelRHMEdFeVJqa25MLVFTTjdBMDhtOTdlOE5uVkd2cWFDZTFNTTlETnFnX2hCbUlFNkV4M0sxUjRxTjN0YTZkMERldUFhWHVSNVZSamVrSWZCMlRvdnVhUHRpMVJBVXZ5amlGNnhvY2RMOXcuYzJZZWdCTF9JTi1fRmVlYVRycHFjdw%3D%3D&page=AAAAAAAAAAJleUpyYVdRaU9pSXhOelV5SWl3aVpXNWpJam9pUVRJMU5rZERUU0lzSW1Gc1p5STZJbVJwY2lKOS4uZUpGNmZDYTdaMG5YSWtFYi5NRmJoT0ktTW42c3Vlc3U1bHBqbVVmX0plbVNLcm9QOHFkTkxCZnhsN3NyQkdqZ3R6azRHSUV0TlBDOXNjNVl4ak8xSGR2bTU2QU1kYUJaV216YlIwZjIycUdJZDlWT3F5WERBanVmYU9uSUx4X1dxSS1UejZ6S1NGWFBUdjBYR2l5RC1oUUtSZWlxUEFzUFNzQVFvMkdVd0JiYTFWeHhENzlTRFNwUjJJc2FWUjBNRzdGR2pkclVWZUxWNl9HMU9YaEZqS2ZiektoZXlyZU1kenRFYVlIM3RqZjd1N19jZFl2WkNsRnlrLUJyM3FaMzJVb3Fjdk14ZVlUdXBxRHhjOGM4UmZLR1hqUWZGSnY4NFZuTEtzOFYwUlRQcU5kblVXN2p6QXM0TDJMd29wdmhaYVJTWElUSXlhN28xRU1TVGJMcmIyS3lEbm9ySm5BWXpEeVBqLXFFOHpSNlhuRnotRktKWHdtQS1idERJZFBORmUzZ184SFk3Sld6Zl9kMjI2SGd6OVE2Ym1qRWlrSE1fS2tjS3ZsanRiUnVUSlJaUm5fNkZocWxxa1lPbFZ4cnlhWE5DakVBSUhNeVI4RzguekstRTFQcHpfX0hGZFY5YnZTWGZjZw%3D%3D"
        logical_cluster_url = logical_cluster_url + "&id=" + logical_cluster_id

        try:
            oci_sdk = ociSDK.OciSdk(account)
            logical_clusters_data = oci_sdk.fetch_details_from_endpoint_url("GET",logical_cluster_url)
            # print(f'logical_clusters_URL -> {logical_cluster_url}')
            # print(f'logical_cluster_id -> {logical_cluster_id}')
            #print(f'\n\nlogical_clusters_data  --> {logical_clusters_data}')

            for i in range(len(logical_clusters_data)):
                cluster_id_i = logical_clusters_data[i]['id']
                #print(f'{i} => A : I -> {logical_cluster_id} : {cluster_id_i}')
                if logical_clusters_data[i]['id'] == logical_cluster_id:
                    logical_cluster_data = logical_clusters_data[i]
                    db_units = logical_cluster_data
                    break
            
                db_units["acforresize"] = float(logical_cluster_data["maximumDbUnits"]) - float(logical_cluster_data["safeDbUnits"]) + float(logical_cluster_data["availableDbUnits"])
                db_units["availabilityDomain"] = availavility_domain
        except Exception as e:
            print(e)
        #print(hugepage_gb,Total_hugepage)
        source_url_dop = "http://devops.oci.oraclecorp.com"
        return render(request,'podlookup/exa_node_data_faaas.html',{'data':result,'health_check':health_check,'db_units':db_units, 'node_id':db_node_id, 'vm_cluster_id':vm_cluster_id, 'source_url_dop': source_url_dop})
    else:
        source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
        return render(request,'podlookup/exa_node_data.html',{'data':result, 'source_url': source_url})

#################################### Pod Instance details ####################################
def HomePodDataDetails(request):
    #print("Test......")
    exanode_info.objects.all().delete()
    #print("Test......")
    try:
        account=str(request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        #print("Hostname value is:-",str(request.POST['exa_id']))
        result = podcontent.exadata_node_data(str(request.POST['exa_id']),request.session['cred_value'])
        oci_availability_domain = result['OK']['value']['extended']['oci']['oci_availability_domain']
        oci_fault_domain = result['OK']['value']['extended']['oci']['oci_fault_domain']
        pod_name=str(result['OK']['value']['pod_name'])
        memory = result['OK']['value']['total_memory']
        compute_shape = result['OK']['value']['extended']['oci']['oci_shape']
        # print(result)
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        exanode_info.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
        exanode_info_monitoring.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
    except Exception as e:
        return render(request,'podlookup/error_page.html')
    result=exanode_info.objects.all()
    return render(request,'podlookup/podinst_node_data.html',{'data':result, 'oci_availability_domain':oci_availability_domain,'oci_fault_domain':oci_fault_domain,'pod_name':pod_name, 'compute_shape': compute_shape, 'memory':memory})

    #is_faas=str(request.session['isFaas'])

#################################### Pod Instance and Capacity Details ####################################
def PodInstanceData(request):
    try:
        result = podcontent.pod_instance_data_values(str(request.session['pod']),request.session['cred_value'])
        #print(result)
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    try:
        pod_instance_details.objects.all().delete()
        for i in range(len(result['podHosts'])):
            pod_instance_details_monitoring.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid']))
            pod_instance_details.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid']))
            ''' print(result['podHosts'][i]['instance_ocid'])
            if result['podHosts'][i]['instance_ocid'] != None:
                pod_instance_details_monitoring.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid']))
                pod_instance_details.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid']))
            else:
                pod_instance_details_monitoring.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid']))
                pod_instance_details.objects.create(Pod_Name=str(result['pod_name']),region_name=str(result['fm_datacenter']),systemtype=str(result['podHosts'][i]['systemType']),pod_host=str(result['podHosts'][i]['podHost']),compartment_id=str(result['podHosts'][i]['compartment_ocid']),instance_id=str(result['podHosts'][i]['instance_ocid'])) '''
    except Exception as e:
        return render(request,'podlookup/error_page.html')
    pod_instance_data=pod_instance_details.objects.all()
    source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
    return render(request,'podlookup/pod_instance_data.html',{'pod_instance_values':pod_instance_data, 'source_url': source_url})

#################################### FAAS Environments Capacity Reservation details - Region level data ####################################
def faascapdetailsMethod(request):
    try:
        account=str(request.session['cred_value'])
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        try:
            #identity_client = oci.identity.IdentityClient(config)
            # New code for OCI Session authenticate
            signer = podcontent.oci_token_code(config)
            identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        rgion=[]
        for region in regions:
            rgion.append(region.region_name)
        rgion.sort()
        if request.GET:
            value=str(request.GET['regions'])
            cid="ocid1.tenancy.oc1..aaaaaaaaqgj4jtr7apjl65fnr5dmerg7zory5qcs7cpd6qcibk2gczefh4qa"
            try:
                result=[]
                oci_sdk=ociSDK.OciSdk(account)
                limits="https://prod-ops-fusionapps."+value+".oci.oraclecloud.com/20191001/internal/limits"
                response = oci_sdk.fetch_details_from_endpoint_url("GET",limits)
                for i in range(len(response)):
                    otpt={}
                    #print(response[i]['serviceName'])
                    if str(response[i]['serviceName'])=="compute":
                        #otpt=response[i]
                        limitvalues="https://limits."+value+".oci.oraclecloud.com/20190729/limitValues?compartmentId="+cid+"&serviceName="+response[i]['serviceName']+"&name="+response[i]['limitName']
                        limitvalues_response = oci_sdk.fetch_details_from_endpoint_url("GET",limitvalues)
                        for j in range(len(limitvalues_response)):
                            if str(response[i]['scopeType']) == "AD" :
                                ravailability_response ="https://limits."+value+".oci.oraclecloud.com/20190729/services/"+response[i]['serviceName']+"/limits/"+response[i]['limitName']+"/resourceAvailability?compartmentId="+cid+"&availabilityDomain="+limitvalues_response[j]['availabilityDomain']
                                ravailability_response_result = oci_sdk.fetch_details_from_endpoint_url("GET",ravailability_response)
                                otpt={}
                                otpt.update(response[i])
                                otpt.update(limitvalues_response[j])
                                otpt.update(ravailability_response_result)
                                result.append(otpt)
                            else:
                                ravailability_response ="https://limits."+value+".oci.oraclecloud.com/20190729/services/"+response[i]['serviceName']+"/limits/"+response[i]['limitName']+"/resourceAvailability?compartmentId="+cid
                                ravailability_response_result = oci_sdk.fetch_details_from_endpoint_url("GET",ravailability_response)
                                otpt={}
                                otpt.update(response[i])
                                otpt.update(limitvalues_response[j])
                                otpt.update(ravailability_response_result)
                                result.append(otpt)

                for i in range(len(result)):
                    #print(result[i])
                    if 'used' in result[i].keys():
                        if result[i]['value'] != 0:
                            result[i]['percentage']=str((result[i]['used']/result[i]['value'])*100)
                            print((result[i]['used']/result[i]['value'])*100)
                        else:
                            result[i]['percentage']="-"
                            print("Value empty")
                return render(request,'podlookup/faas_cap_view_dashbard.html',{'region':rgion,'value':value,'result':result})
            except Exception as e:
                exce="Exception Case"
                return render(request,'podlookup/faas_cap_view_dashbard.html',{'region':rgion,'exce':exce,'value':value})
                print(e)
        return render(request,'podlookup/faas_cap_view_dashbard.html',{'region':rgion})
    except Exception as e:
        pass

#################################### FAAS Environments DataBase details - Region level data ####################################
def faasdbMethod(request):
    try:
        account=str(request.session['cred_value'])
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        try:
            #identity_client = oci.identity.IdentityClient(config)
            # New code for OCI Session authenticate
            signer = podcontent.oci_token_code(config)
            identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        rgion=[]
        for region in regions:
            rgion.append(region.region_name)
        rgion.sort()
        if request.GET:
            value=str(request.GET['regions'])
            try:
                oci_sdk=ociSDK.OciSdk(account)
                ex_data="https://prod-adp-ops."+value+".oci.oraclecloud.com/20191001/internal/logicalClusters/capacityManagement?limit=100&capacityState=All"
                response = oci_sdk.fetch_details_from_endpoint_url("GET",ex_data)
                return render(request,'podlookup/faas_db_data.html',{'region':rgion,'result':response,'value':value})
            except Exception as e:
                print(e)
        return render(request,'podlookup/faas_db_data.html',{'region':rgion})
    except Exception as e:
        paas

        """
./oci_curl.py --profile boat_login -X GET "https://prod-adp-ops.ap-hyderabad-1.oci.oraclecloud.com/20191001/internal/logicalClusters/capacityManagement?limit=100&capacityState=All" | jq .

./oci_curl.py --profile boat_login -X GET "https://prod-adp-ops.ap-hyderabad-1.oci.oraclecloud.com/20191001/internal/dbNodes?limit=100&logicalClusterId=ocid1.adplogicalcluster.oc1..aaaaaaaajyhvvidcynz6hhp7khyzzokpyrhenw32rjagfouevdkd5kgt7kda" | jq .

/cloudmeta-api/v2/{tenant}/exadatas/{reference}/pods

        """

def faasexadataMethod(request):
    try:
        account=str(request.session['cred_value'])
        config=globalvariables.env_dictionary[account]['oci_config']
        l_cluster=str(request.POST['exa_id'])
        region_name=str(request.POST['region'])
        #print(l_cluster,region_name)
        oci_sdk=ociSDK.OciSdk(account)
        htname="https://prod-adp-ops."+region_name+".oci.oraclecloud.com/20191001/internal/dbNodes?limit=100&logicalClusterId="+l_cluster
        response = oci_sdk.fetch_details_from_endpoint_url("GET",htname)
        ht=[]
        for i in range(len(response)):
            ht.append(response[i]['fqdn'])
            #print(response[i]['healthStatus'])
        otput={}
        for i in ht:
            URL="{0}/cloudmeta-api/v2/FUSION/exadatas/{1}/pods".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],i)
            result = podcontent.cloud_meta_genric(URL,account)
            pd_lst=[]
            for j in range(len(result)):
                v={}
                #pd_lst.append(result[j]['pod_name'])
                URL="{0}/cloudmeta-api/v2/FUSION/pods/{1}/attrs/oci_size".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],str(result[j]['pod_name']))
                size = podcontent.cloud_meta_genric(URL,account)
                v[str(result[j]['pod_name'])]=str(size['value'])
                pd_lst.append(v)
                #print(size['value'],result[j]['pod_name'])
            otput[i]=pd_lst
        #print(otput)

        return render(request,'podlookup/faas_exa_node.html',{'data':otput})
    except Exception as e:
        print(e)
        paas

#################################### Capacity Reservation details - Region level data ####################################
def CapacityReservationMethod(request):
    try:
        account=str(request.session['cred_value'])
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        #print(config)
        #print(compartment_id)
        podcontent.oci_token_code(config)

        """
        # New Code Adding w.r.t oci session authenticate
        token_file = config['security_token_file']
        token = None
        with open(token_file, 'r') as f:
            token = f.read()
            print(token)
        private_key = oci.signer.load_private_key_from_file(config['key_file'])
        signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
        client = oci.identity.IdentityClient({'region': region}, signer=signer)
        result = client.list_region_subscriptions(config['tenancy'])
        """
        try:
            #identity_client = oci.identity.IdentityClient(config)
            # New Code Adding w.r.t oci session authenticate
            signer = podcontent.oci_token_code(config)
            #print(signer)
            identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
            #print(regions)
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        rgion=[]
        for region in regions:
            rgion.append(region.region_name)
        rgion.sort()
        if request.GET:
            account=str(request.session['cred_value'])
            config=globalvariables.env_dictionary[account]['oci_config']
            compartment_id = globalvariables.env_dictionary[account]['ten_id']
            # New code for OCI Session authenticate
            signer = podcontent.oci_token_code(config)
            identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
            #identity_client = oci.identity.IdentityClient(config)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
            rgion=[]
            for region in regions:
                rgion.append(region.region_name)
            rgion.sort()
            region_level_capacity_table.objects.all().delete()
            no_capacity_region_list.objects.all().delete()
            unable_to_fetch_region_list.objects.all().delete()
            capacity_reservation_level_capacity_details.objects.all().delete()
            regin = str(request.GET['regions'])
            pod_type = str(request.GET['pod_type'])
            account=str(request.session['cred_value'])
            config=globalvariables.env_dictionary[account]['oci_config']
            if pod_type == "FAAAS":
                compartment_id = globalvariables.faas_tenancy
                #compartment_id = "ocid1.tenancy.oc1..aaaaaaaaqgj4jtr7apjl65fnr5dmerg7zory5qcs7cpd6qcibk2gczefh4qa"
            else:
                compartment_id = globalvariables.env_dictionary[account]['ten_id']
            config['region']=regin
            #core_client = oci.core.ComputeClient(config)
            #print(config)
            #identity_client = podcontent.oci_token_code(config)
            #print(identity_client)
            #signer = pod_content.oci_token_code(config)
            #print(signer)
            core_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
            #print(core_client)
            try:
                #print("insert")
                list_compute_capacity_reservations_ids = core_client.list_compute_capacity_reservations(compartment_id)
                #print(list_compute_capacity_reservations_ids.data)
                if len(list_compute_capacity_reservations_ids.data) >= 1:
                    for i in range(len(list_compute_capacity_reservations_ids.data)):
                        try:
                            dashboard_result=core_client.get_compute_capacity_reservation(capacity_reservation_id=list_compute_capacity_reservations_ids.data[i].id)
                            #print(dashboard_result.data)
                            free_count=dashboard_result.data.reserved_instance_count - dashboard_result.data.used_instance_count
                            pecentage_data=(dashboard_result.data.used_instance_count/dashboard_result.data.reserved_instance_count)*100
                            pecentage_data="{:.2f}".format(pecentage_data)
                            region_level_capacity_table.objects.create(region_name=str(regin),free_count=str(free_count),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                            region_level_capacity_table_monitoring.objects.create(region_name=str(regin),free_count=str(free_count),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                            if len(dashboard_result.data.instance_reservation_configs) >= 1:
                                free_cnt = 0
                                for i in range(len(dashboard_result.data.instance_reservation_configs)):
                                    free_cnt=dashboard_result.data.instance_reservation_configs[i].reserved_count - dashboard_result.data.instance_reservation_configs[i].used_count
                                    if dashboard_result.data.instance_reservation_configs[i].reserved_count == 0 and dashboard_result.data.instance_reservation_configs[i].used_count == 0:
                                        percnt = 0
                                    else:
                                        percnt=(dashboard_result.data.instance_reservation_configs[i].used_count/dashboard_result.data.instance_reservation_configs[i].reserved_count)*100
                                    percnt="{:.2f}".format(percnt)
                                    capacity_reservation_level_capacity_details.objects.create(region_name=str(regin),free_count=str(free_cnt),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),instance_shape=str(dashboard_result.data.instance_reservation_configs[i].instance_shape),reserved_count=str(dashboard_result.data.instance_reservation_configs[i].reserved_count),memory=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.ocpus),used_count=str(dashboard_result.data.instance_reservation_configs[i].used_count),percentage=percnt)
                        except Exception as e:
                            print("Error while fetching data from below Cap data")
                            print(e)
                            #print(dashboard_result.data)

                        """
                        dashboard_result=core_client.get_compute_capacity_reservation(capacity_reservation_id=list_compute_capacity_reservations_ids.data[i].id)
                        print(dashboard_result.data)
                        free_count=dashboard_result.data.reserved_instance_count - dashboard_result.data.used_instance_count
                        pecentage_data=(dashboard_result.data.used_instance_count/dashboard_result.data.reserved_instance_count)*100
                        pecentage_data="{:.2f}".format(pecentage_data)
                        region_level_capacity_table.objects.create(region_name=str(regin),free_count=str(free_count),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        region_level_capacity_table_monitoring.objects.create(region_name=str(regin),free_count=str(free_count),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        if len(dashboard_result.data.instance_reservation_configs) >= 1:
                            for i in range(len(dashboard_result.data.instance_reservation_configs)):
                                free_cnt=dashboard_result.data.instance_reservation_configs[i].reserved_count - dashboard_result.data.instance_reservation_configs[i].used_count
                                percnt=(dashboard_result.data.instance_reservation_configs[i].used_count/dashboard_result.data.instance_reservation_configs[i].reserved_count)*100
                                percnt="{:.2f}".format(percnt)
                                capacity_reservation_level_capacity_details.objects.create(region_name=str(regin),free_count=str(free_cnt),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),instance_shape=str(dashboard_result.data.instance_reservation_configs[i].instance_shape),reserved_count=str(dashboard_result.data.instance_reservation_configs[i].reserved_count),memory=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.ocpus),used_count=str(dashboard_result.data.instance_reservation_configs[i].used_count),percentage=percnt)
                        """
                    region_wise_data=region_level_capacity_table.objects.all()
                    pod_capacity_data=capacity_reservation_level_capacity_details.objects.all()
                    return render(request,'podlookup/cap_view_dashboard.html',{'region':rgion,'region_wise_data':region_wise_data,'pod_capacity_data':pod_capacity_data})
                else:
                    #no_capacity_region_list.objects.create(region=str(region.region_name),result=str('no_capacity_details'))
                    #no_capacity_region_list_monitoring.objects.create(region=str(region.region_name),result=str('no_capacity_details'))
                    #no_capacity_data=no_capacity_region_list.objects.all()
                    region_name=regin
                    data='no_capacity_details'
                    return render(request,'podlookup/cap_view_dashboard.html',{'data':data,'region_name':region_name,'region':rgion})
            except:
                #unable_to_fetch_region_list_monitoring.objects.create(region=str(regin),result=str('issue_while_fetching_data'))
                #unable_to_fetch_region_list.objects.create(region=str(regin),result=str('issue_while_fetching_data'))
                #unable_to_fetch_data=unable_to_fetch_region_list.objects.all()
                region_name=regin
                data='issue_while_fetching_data'
                return render(request,'podlookup/cap_view_dashboard.html',{'data':data,'region_name':region_name,'region':rgion})
        source_url_dop = "http://devops.oci.oraclecorp.com"
        return render(request,'podlookup/cap_view_dashboard.html',{'region':rgion, 'source_url_dop':source_url_dop})
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

#################################################capacity details in home page pod instance Details#################################################
def CapViewMethod(request):
    try:
        pod=str(request.session['pod'])
        account=str(request.session['cred_value'])
        instance_id=str(request.POST['instance_id'])
        region_name=str(request.POST['region'])
        is_faas=str(request.session['isFaas'])
        ad_domain=str(request.session['ad_domain'])
        #print(ad_domain)
        if is_faas == "true":
            compartment_id = globalvariables.faas_tenancy
            #compartment_id = "ocid1.tenancy.oc1..aaaaaaaaqgj4jtr7apjl65fnr5dmerg7zory5qcs7cpd6qcibk2gczefh4qa"
        else:
            compartment_id = globalvariables.env_dictionary[account]['ten_id']
        config=globalvariables.env_dictionary[account]['oci_config']
        config['region']=region_name
        signer = podcontent.oci_token_code(config)
        cmp_client= oci.core.ComputeClient({'region': config['region']}, signer=signer)
        #cmp_client= oci.core.ComputeClient(config)
        inst_data=cmp_client.get_instance(instance_id)
        #print(inst_data.data)
        if inst_data.data.capacity_reservation_id is None:
            insta_data = 'None'
            return render(request,'podlookup/cap_view_none.html',{'inst_info':insta_data})
        else:
            cap_data.objects.all().delete()
            pod_cap_data.objects.all().delete()
            cap_id=str(inst_data.data.capacity_reservation_id)
            #commented old one added new one acc to oci session auth
            #core_client = oci.core.ComputeClient(config)
            core_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
            cmd_output=core_client.get_compute_capacity_reservation(capacity_reservation_id=cap_id)
            #print(cmd_output.data)
            free_count=cmd_output.data.reserved_instance_count - cmd_output.data.used_instance_count
            pecentage_data=(cmd_output.data.used_instance_count/cmd_output.data.reserved_instance_count)*100
            pecentage_data="{:.2f}".format(pecentage_data)
            #print(str(pod),str(free_count),str(region_name),str(cmd_output.data.availability_domain),str(cmd_output.data.display_name),str(cmd_output.data.id),str(cmd_output.data.reserved_instance_count),str(cmd_output.data.used_instance_count),pecentage_data)
            cap_data.objects.create(Pod_Name=str(pod),free_count=str(free_count),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
            cap_data_monitoring.objects.create(Pod_Name=str(pod),free_count=str(free_count),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
            if len(cmd_output.data.instance_reservation_configs) >= 1:
                for i in range(len(cmd_output.data.instance_reservation_configs)):
                    free_cnt = cmd_output.data.instance_reservation_configs[i].reserved_count - cmd_output.data.instance_reservation_configs[i].used_count
                    percnt=(cmd_output.data.instance_reservation_configs[i].used_count/cmd_output.data.instance_reservation_configs[i].reserved_count)*100
                    percnt="{:.2f}".format(percnt)
                    pod_cap_data.objects.create(region_name=str(region_name),free_count=str(free_cnt),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
                    pod_cap_data_monitoring.objects.create(region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
            cap_dta=cap_data.objects.all()
            pod_cap_dta=pod_cap_data.objects.all()
            source_url_dop = "http://devops.oci.oraclecorp.com"
            return render(request,'podlookup/capview.html',{'cap_data':cap_dta,'pod_cap_data':pod_cap_dta, 'source_url_dop':source_url_dop})
        """
        if is_faas == "true":
            # Pod Capacity data
            #value=str(request.POST['region'])
            #compartment_id = globalvariables.faas_tenancy

            value=str(request.POST['region'])
            cid="ocid1.tenancy.oc1..aaaaaaaaqgj4jtr7apjl65fnr5dmerg7zory5qcs7cpd6qcibk2gczefh4qa"
            try:
                result=[]
                oci_sdk=ociSDK.OciSdk(account)
                limits="https://prod-ops-fusionapps."+value+".oci.oraclecloud.com/20191001/internal/limits"
                response = oci_sdk.fetch_details_from_endpoint_url("GET",limits)
                for i in range(len(response)):
                    otpt={}
                    #print(response[i]['serviceName'])
                    if str(response[i]['serviceName'])=="compute":
                        #otpt=response[i]
                        limitvalues="https://limits."+value+".oci.oraclecloud.com/20190729/limitValues?compartmentId="+cid+"&serviceName="+response[i]['serviceName']+"&name="+response[i]['limitName']
                        limitvalues_response = oci_sdk.fetch_details_from_endpoint_url("GET",limitvalues)
                        for j in range(len(limitvalues_response)):
                            if str(response[i]['scopeType']) == "AD" :
                                ravailability_response ="https://limits."+value+".oci.oraclecloud.com/20190729/services/"+response[i]['serviceName']+"/limits/"+response[i]['limitName']+"/resourceAvailability?compartmentId="+cid+"&availabilityDomain="+limitvalues_response[j]['availabilityDomain']
                                ravailability_response_result = oci_sdk.fetch_details_from_endpoint_url("GET",ravailability_response)
                                otpt={}
                                otpt.update(response[i])
                                otpt.update(limitvalues_response[j])
                                otpt.update(ravailability_response_result)
                                result.append(otpt)
                            else:
                                ravailability_response ="https://limits."+value+".oci.oraclecloud.com/20190729/services/"+response[i]['serviceName']+"/limits/"+response[i]['limitName']+"/resourceAvailability?compartmentId="+cid
                                ravailability_response_result = oci_sdk.fetch_details_from_endpoint_url("GET",ravailability_response)
                                otpt={}
                                otpt.update(response[i])
                                otpt.update(limitvalues_response[j])
                                otpt.update(ravailability_response_result)
                                result.append(otpt)
                #print(result)
                for i in range(len(result)):
                    #print(result[i])
                    if 'used' in result[i].keys():
                        if result[i]['value'] != 0:
                            result[i]['percentage']=str((result[i]['used']/result[i]['value'])*100)
                            #print((result[i]['used']/result[i]['value'])*100)
                        else:
                            result[i]['percentage']="-"
                            #print("Value empty")
                data=[]
                for i in range(len(result)):
                    if str(result[i]['availabilityDomain']) == str(ad_domain):
                        data.append(result[i])
                #print(result)

                return render(request,'podlookup/faas_pod_cap_data.html',{'result':data})
            except Exception as e:
                exce="Exception Case"
                return render(request,'podlookup/faas_pod_cap_data.html',{'exce':exce})
                print(e)
        else:
            #print("Gen1 pod")
            #config=globalvariables.oci_config
            config=globalvariables.env_dictionary[account]['oci_config']
            compartment_id = globalvariables.tenancy_id
            config['region']=region_name
            signer = podcontent.oci_token_code(config)
            cmp_client= oci.core.ComputeClient({'region': config['region']}, signer=signer)
            #cmp_client= oci.core.ComputeClient(config)
            inst_data=cmp_client.get_instance(instance_id)
            #print(inst_data.data)
            if inst_data.data.capacity_reservation_id is None:
                insta_data = 'None'
                return render(request,'podlookup/cap_view_none.html',{'inst_info':insta_data})
            else:
                cap_data.objects.all().delete()
                pod_cap_data.objects.all().delete()
                cap_id=str(inst_data.data.capacity_reservation_id)
                #commented old one added new one acc to oci session auth
                #core_client = oci.core.ComputeClient(config)
                core_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
                cmd_output=core_client.get_compute_capacity_reservation(capacity_reservation_id=cap_id)
                #print(cmd_output.data)
                free_count=cmd_output.data.reserved_instance_count - cmd_output.data.used_instance_count
                pecentage_data=(cmd_output.data.used_instance_count/cmd_output.data.reserved_instance_count)*100
                pecentage_data="{:.2f}".format(pecentage_data)
                #print(str(pod),str(free_count),str(region_name),str(cmd_output.data.availability_domain),str(cmd_output.data.display_name),str(cmd_output.data.id),str(cmd_output.data.reserved_instance_count),str(cmd_output.data.used_instance_count),pecentage_data)
                cap_data.objects.create(Pod_Name=str(pod),free_count=str(free_count),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
                cap_data_monitoring.objects.create(Pod_Name=str(pod),free_count=str(free_count),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
                if len(cmd_output.data.instance_reservation_configs) >= 1:
                    for i in range(len(cmd_output.data.instance_reservation_configs)):
                        free_cnt = cmd_output.data.instance_reservation_configs[i].reserved_count - cmd_output.data.instance_reservation_configs[i].used_count
                        percnt=(cmd_output.data.instance_reservation_configs[i].used_count/cmd_output.data.instance_reservation_configs[i].reserved_count)*100
                        percnt="{:.2f}".format(percnt)
                        pod_cap_data.objects.create(region_name=str(region_name),free_count=str(free_cnt),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
                        pod_cap_data_monitoring.objects.create(region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
                cap_dta=cap_data.objects.all()
                pod_cap_dta=pod_cap_data.objects.all()
                return render(request,'podlookup/capview.html',{'cap_data':cap_dta,'pod_cap_data':pod_cap_dta})
                """
    except Exception as e:
        return render(request,'podlookup/oci_config_error_page.html')

def CapacityReservationMainMethod(request):
    try:
        account=str(request.session['cred_value'])
        pod_name=str(request.session['pod'])
        RegionWise_Capacity_Reservation_method(pod_name,account)
        region_wise_data=region_level_capacity_table.objects.all()
        no_capacity_data=no_capacity_region_list.objects.all()
        unable_to_fetch_data=unable_to_fetch_region_list.objects.all()
        pod_capacity_data=capacity_reservation_level_capacity_details.objects.all()
        return render(request,'podlookup/capacity_reservation_main_page.html',{'region_wise_result':region_wise_data,'no_capacity_result':no_capacity_data,'unable_to_fetch_result':unable_to_fetch_data,'region_level_pod_capacity':pod_capacity_data})
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def test(request):
    pod_capacity_data=capacity_reservation_level_capacity_details.objects.all()
    return render(request,'podlookup/regionwise_podcapacity_details.html',{'region_level_pod_capacity':pod_capacity_data})

def RegionWise_Capacity_Reservation_method(pod_name,account):
    try:
        region_level_capacity_table.objects.all().delete()
        no_capacity_region_list.objects.all().delete()
        unable_to_fetch_region_list.objects.all().delete()
        capacity_reservation_level_capacity_details.objects.all().delete()
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        #identity_client = oci.identity.IdentityClient(config)
        # New code for OCI Session authenticate
        signer = podcontent.oci_token_code(config)
        identity_client = oci.identity.IdentityClient({'region': config['region']}, signer=signer)
        response = identity_client.list_region_subscriptions(config["tenancy"])
        regions = response.data
        for region in regions:
            config['region']=region.region_name
            #signer=pod_content.get_token_signer(config)
            core_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
            #core_client = oci.core.ComputeClient(config)
            try:
                list_compute_capacity_reservations_ids = core_client.list_compute_capacity_reservations(compartment_id)
                if len(list_compute_capacity_reservations_ids.data) >= 1:
                    for i in range(len(list_compute_capacity_reservations_ids.data)):
                        dashboard_result=core_client.get_compute_capacity_reservation(capacity_reservation_id=list_compute_capacity_reservations_ids.data[i].id)
                        pecentage_data=(dashboard_result.data.used_instance_count/dashboard_result.data.reserved_instance_count)*100
                        region_level_capacity_table.objects.create(region_name=str(region.region_name),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        region_level_capacity_table_monitoring.objects.create(region_name=str(region.region_name),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        if len(dashboard_result.data.instance_reservation_configs) >= 1:
                            for i in range(len(dashboard_result.data.instance_reservation_configs)):
                                percnt=(dashboard_result.data.instance_reservation_configs[i].used_count/dashboard_result.data.instance_reservation_configs[i].reserved_count)*100
                                capacity_reservation_level_capacity_details.objects.create(region_name=str(region.region_name),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),instance_shape=str(dashboard_result.data.instance_reservation_configs[i].instance_shape),reserved_count=str(dashboard_result.data.instance_reservation_configs[i].reserved_count),used_count=str(dashboard_result.data.instance_reservation_configs[i].used_count),percentage=percnt)
                else:
                    no_capacity_region_list.objects.create(region=str(region.region_name),result=str('no_capacity_details'))
                    no_capacity_region_list_monitoring.objects.create(region=str(region.region_name),result=str('no_capacity_details'))
            except:
                unable_to_fetch_region_list_monitoring.objects.create(region=str(region.region_name),result=str('issue_while_fetching_data'))
                unable_to_fetch_region_list.objects.create(region=str(region.region_name),result=str('issue_while_fetching_data'))
    except Exception as e:
        return render(request,'podlookup/oci_config_error_page.html')

#################################### Fetch Instance Details ####################################
def InstDataMethod(request):
    try:
        #print("Instance details")
        pod=str(request.session['pod'])
        account=str(request.session['cred_value'])
        get_inst_full_data(request.POST['instance_id'],request.POST['region'],pod,account)
        insta_data=inst_full_data.objects.all()
        return render(request,'podlookup/instance_info.html',{'inst_info':insta_data})
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def get_inst_full_data(instance_id,region_name,pod,account):
    try:
        inst_full_data.objects.all().delete()
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        config['region']=region_name
        signer = podcontent.oci_token_code(config)
        cmp_client= oci.core.ComputeClient({'region': config['region']}, signer=signer)
        inst_data=cmp_client.get_instance(instance_id)
        inst_full_data.objects.create(Pod_Name=str(pod),region_name=str(region_name),instance_id=str(instance_id),availability_domain=str(inst_data.data.availability_domain),capacity_reservation_id=str(inst_data.data.capacity_reservation_id),dedicated_vm_host_id=str(inst_data.data.dedicated_vm_host_id),display_name=str(inst_data.data.display_name),fault_domain=str(inst_data.data.fault_domain),lifecycle_state=str(inst_data.data.lifecycle_state),shape=str(inst_data.data.shape),ocpus=str(inst_data.data.shape_config.ocpus))
        inst_full_data_monitoring.objects.create(Pod_Name=str(pod),region_name=str(region_name),instance_id=str(instance_id),availability_domain=str(inst_data.data.availability_domain),capacity_reservation_id=str(inst_data.data.capacity_reservation_id),dedicated_vm_host_id=str(inst_data.data.dedicated_vm_host_id),display_name=str(inst_data.data.display_name),fault_domain=str(inst_data.data.fault_domain),lifecycle_state=str(inst_data.data.lifecycle_state),shape=str(inst_data.data.shape),ocpus=str(inst_data.data.shape_config.ocpus))
    except Exception as e:
        return render(request,'podlookup/oci_config_error_page.html')

def PodSizeAnalyseMethod(request):
    print("Method:  PodSizeAnalyseMethod")
    #if len(request.session['cred_value']) == 0 :
    #    print("account empty")
    if request.GET:
        pod=str(request.GET['podname']).upper()
        size=str(request.GET['size']).upper()
        s_arc=str(request.GET['source_arc']).upper()
        t_arc=str(request.GET['target_arc']).upper()
        account=str(request.session['cred_value'])
        input_data={}
        input_data['pod']=pod
        input_data['size']=size
        input_data['s_arc']=s_arc
        input_data['t_arc']=t_arc

        Full_pod_result = podcontent.full_pod_data_method(pod,account)
        for item in Full_pod_result:
            if item.get('name') == 'stamp':
                stamp = item.get('value')     
        # print(f'STAMP-> {stamp}') 
        bespoke_mt = None
        bespoke_db = None   
        if "custom" in stamp:
            bespoke_mt = stamp
        # print(f'bespoke_mt-> {bespoke_mt}')     

        cloud_attr=podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))
        fass_var=cloud_attr['podAttributes']['isFAAAS']
        pod_region_name=cloud_attr['fm_datacenter']
        for item in Full_pod_result:
            if item['name'] == 'fusiondb_dbname':
                pod_db_name = item['value'].lower()
        POD_URL="https://prod-adp-ops."+str(pod_region_name)+".oci.oraclecloud.com/20191001/internal/podDbs?podDbname="+ pod_db_name
        oci_sdk = ociSDK.OciSdk(account)
        pod_url_data = oci_sdk.fetch_details_from_endpoint_url("GET",POD_URL)
        pod_db_id = pod_url_data[0]['id']
        db_parameter_url = "https://prod-adp-ops."+str(pod_region_name)+".oci.oraclecloud.com/20191001/internal/podDbs/"+pod_db_id+"/actions/listCustomInitConfigs"
        db_parameter_data = oci_sdk.fetch_details_from_endpoint_url("GET",db_parameter_url)
        param_values_list = [{'paramName': d['paramName'], 'currentValue': d['currentValue'], 'state': d['state'], 'customValue': d['customValue']} for d in db_parameter_data]
        filtered_rows = [row for row in param_values_list if row['customValue'] is not None]
        bespoke_db = 'Yes' if filtered_rows else 'No'
        # print(f'bespoke_db-> {bespoke_db}')

        try:
            #print(" ****** Function: commonutils.pod_capacity_analysis: START")
            current, result=commonutils.pod_capacity_analysis(pod,size,s_arc,t_arc,account)
            #print(" ****** Function: commonutils.pod_capacity_analysis: END")
            source_size = current['pod_current_size']
            resize_type = commonutils.compare_sizes(size,source_size)
            #print("# ============= #")
            #print(f'result -> {result}')
            faas_result={}
            # Process Current Uses Data
            cu_data=[]
            for i in result['current_uses']:
                ocpu=0
                memory=0
                for j in range(len(result['current_uses'][i])):
                    ocpu=ocpu+(result['current_uses'][i][j]['ocpus']*result['current_uses'][i][j]['count'])
                    memory=memory+(result['current_uses'][i][j]['memoryInGBs']*result['current_uses'][i][j]['count'])
                om={}
                om['ocpus']=ocpu
                om['memoryInGBs']=memory
                mos={}
                if i == "VM.Standard.E4.Flex":
                    mos['standard-e4-core-reserved-count']=om
                if i == "VM.Standard.E3.Flex":
                    mos['standard-e3-core-reserved-count']=om
                if i == "VM.Standard.A1.Flex":
                    mos['standard-a1-core-reserved-count']=om
                cu_data.append(mos)
            faas_result['current_uses']=cu_data
            #Process for capacity_require data
            cr_data=[]
            for i in result['capacity_require']:
                ocpu=0
                memory=0
                for j in range(len(result['capacity_require'][i])):
                    ocpu=ocpu+(result['capacity_require'][i][j]['ocpus']*result['capacity_require'][i][j]['count'])
                    memory=memory+(result['capacity_require'][i][j]['memoryInGBs']*result['capacity_require'][i][j]['count'])
                om={}
                om['ocpus']=ocpu
                om['memoryInGBs']=memory
                mos={}
                if i == "VM.Standard.E4.Flex":
                    mos['standard-e4-core-reserved-count']=om
                if i == "VM.Standard.E3.Flex":
                    mos['standard-e3-core-reserved-count']=om
                if i == "VM.Standard.A1.Flex":
                    mos['standard-a1-core-reserved-count']=om
                cr_data.append(mos)
            faas_result['capacity_require']=cr_data
            #print(faas_result)
            #Commented 1050 - 1052 line for getting capacity details for FAAAS environments also same as Gen1 Environments
            #if str(fass_var) == "true":
            #print(pod_region_name)
            #    return render(request,'podlookup/podsizeanalyse_faas_pod.html',{'faas_result':faas_result,'result':result,'pod':pod,'input':input_data,'pod_region_name':pod_region_name})
            if 'error' in current.keys():
                return render(request,'podlookup/podsizeanalyse_error.html')
            else:
                source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
                return render(request,'podlookup/podsizeanalyse.html',{'result':result,'pod':pod,'input':input_data,'pod_region_name':pod_region_name,'fass_var':fass_var,'source_size':source_size,'resize_type': resize_type, 'source_url': source_url,'bespoke_mt': bespoke_mt,'bespoke_db': bespoke_db})
                #return render(request,'podlookup/podsizeanalyse.html',{'result':result,'pod':pod,'input':input_data,'pod_region_name':pod_region_name,'fass_var':fass_var,'source_size':source_size,'resize_type': resize_type, 'source_url': source_url})
        except Exception as e:
            return render(request,'podlookup/podsizeanalyse_error.html',{'output':e,'input':input_data})
            #return render(request,'podlookup/cred_value_error_page.html')
        #return render(request,'podlookup/podsizeanalyse.html')
    return render(request,'podlookup/podsizeanalyse.html')

#################################### PSR Analysis Report #################################################################
def psrpagecapviewMethod(request):
    try:
        pod=str(request.POST['podname'])
        region_name=str(request.POST['region'])
        account=str(request.session['cred_value'])
        #is_Faaas=str(request.session['fass_var'])
        cloud_attr=podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))
        is_Faaas=cloud_attr['podAttributes']['isFAAAS']
        #print(is_Faaas)
        result = podcontent.pod_instance_data_values(str(pod),request.session['cred_value'])
        #print(result)
        instance_data=[]
        cap_data=[]
        try:
            for i in range(len(result['podHosts'])):
                instance_data.append(str(result['podHosts'][i]['instance_ocid']))
            for j in instance_data:
                instance_id=j
                #config=globalvariables.oci_config
                config=globalvariables.env_dictionary[account]['oci_config']
                if is_Faaas == "true":
                    compartment_id = globalvariables.faas_tenancy
                else:
                    compartment_id = globalvariables.tenancy_id
                #print(compartment_id)
                config['region']=region_name
                signer = podcontent.oci_token_code(config)
                cmp_client= oci.core.ComputeClient({'region': config['region']}, signer=signer)
                #cmp_client= oci.core.ComputeClient(config)
                inst_data=cmp_client.get_instance(instance_id)
                #print(inst_data.data)
                if inst_data.data.capacity_reservation_id is None:
                    insta_data = 'None'
                    print('NO Capacity')
                else:
                    cap_id=str(inst_data.data.capacity_reservation_id)
                    cap_data.append(cap_id)
            result={}
            for k in set(cap_data):
                if k is None:
                    print("hello")
                else:
                    core_client = oci.core.ComputeClient({'region': config['region']}, signer=signer)
                    cmd_output=core_client.get_compute_capacity_reservation(capacity_reservation_id=k)
                    pecentage_data=(cmd_output.data.used_instance_count/cmd_output.data.reserved_instance_count)*100
                    pecentage_data="{:.2f}".format(pecentage_data)
                    frr_cnt=cmd_output.data.reserved_instance_count - cmd_output.data.used_instance_count
                    v={}
                    v['availability_domain']=str(cmd_output.data.availability_domain)
                    v['cap_id']=str(cmd_output.data.id)
                    v['display_name']=str(cmd_output.data.display_name)
                    v['reserved_instance_count']=str(cmd_output.data.reserved_instance_count)
                    v['used_instance_count']=str(cmd_output.data.used_instance_count)
                    v['frr_cnt'] = str(frr_cnt)
                    v['percentage']=pecentage_data
                    c=[]
                    if len(cmd_output.data.instance_reservation_configs) >= 1:
                        for i in range(len(cmd_output.data.instance_reservation_configs)):
                            percnt=(cmd_output.data.instance_reservation_configs[i].used_count/cmd_output.data.instance_reservation_configs[i].reserved_count)*100
                            percnt="{:.2f}".format(percnt)
                            fee_cnt=cmd_output.data.instance_reservation_configs[i].reserved_count - cmd_output.data.instance_reservation_configs[i].used_count
                            r={}
                            r['display_name']=str(cmd_output.data.display_name)
                            r['instance_shape']=str(cmd_output.data.instance_reservation_configs[i].instance_shape)
                            r['memory']=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs)
                            r['ocpus']=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus)
                            r['reserved_count']=str(cmd_output.data.instance_reservation_configs[i].reserved_count)
                            r['used_count']=str(cmd_output.data.instance_reservation_configs[i].used_count)
                            r['free_count']=str(fee_cnt)
                            r['percentage']=percnt
                            c.append(r)
                    reser={}
                    reser['cap']=v
                    reser['pod_cap']=c
                    result[k]=reser
                #print(result)
                return render(request,'podlookup/psranalysis_capdata.html',{'cmd_output':result})
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def psr_analysis_report(request):
    try:
        try:
            account=str(request.session['cred_value'])
        except Exception as e:
            return render(request,'podlookup/cred_value_error_page.html')
        datafetch=data_fetch.fetch()
        source_url_dop = "http://devops.oci.oraclecorp.com"
        status,stampfilepath=datafetch.stamp_psr_data()
        with open(stampfilepath) as f:
            stamp_pod_result=json.load(f)

        status,manualfilename=datafetch.manual_psr_data()
        with open(manualfilename) as f:
            manual_pod_result=json.load(f)
        manu_date=''
        #Stamp data Validation
        Req_stamp='<option value=\'item0\'>Select Option</option>'
        s_fmdata='<option value=\'item0\'>Select Option</option>'
        s_data=[]
        s_fm_data=[]
        reg_stamp=''
        reg_man=''
        for i in range(len(stamp_pod_result)):
            if stamp_pod_result[i]['Request Date']:
                s_data=commonutils.datelist_stamp('Request Date')
            if stamp_pod_result[i]['FM Date']:
                s_fm_data=commonutils.datelist_stamp('fmdate')

        stamp_reg_reqdata={}
        stamp_reg_fmdata={}
        for date_value in set(s_data):
            l_list=[]
            for i in range(len(stamp_pod_result)):
                if stamp_pod_result[i]['Request Date'] == date_value:
                    l_list.append(stamp_pod_result[i]['Data Center'])
            l_list.sort()
            stamp_reg_reqdata[date_value]=list(set(l_list))

        for date_value in set(s_fm_data):
            l_list=[]
            for i in range(len(stamp_pod_result)):
                if stamp_pod_result[i]['FM Date'] == date_value:
                    l_list.append(stamp_pod_result[i]['Data Center'])
            l_list.sort()
            stamp_reg_fmdata[date_value]=list(set(l_list))
        stamp_reg_reqdata = json.dumps(stamp_reg_reqdata)
        stamp_reg_fmdata=json.dumps(stamp_reg_fmdata)
        #print(stamp_reg_fmdata.keys())
        #print("Stamp data")
        # Sorting dates order wise
        x_s_data=list(set(s_data))
        x_s_data.sort(key = lambda date: datetime.datetime.strptime(date, '%d-%b-%y'))
        x_s_fm_data=list(set(s_fm_data))
        x_s_fm_data.sort(key = lambda date: datetime.datetime.strptime(date, '%d-%b-%y'))
        #print(x_s_fm_data)
        for i in x_s_data:
            Req_stamp=str(Req_stamp)+"<option value=\'"+i+"\'>"+i+"</option>"
        for i in x_s_fm_data:
            s_fmdata=str(s_fmdata)+"<option value=\'"+i+"\'>"+i+"</option>"
        # Manual data Validation
        m_fm_data=[]
        m_fmdata='<option value=\'item0\'>Select Option</option>'
        for i in range(len(manual_pod_result)):
            if manual_pod_result[i]['FM Date']:
                m_fm_data=commonutils.datelist_manual()
                #m_fm_data.append(manual_pod_result[i]['FM Date'])
        manual_reg_fmdata={}
        for date_value in set(m_fm_data):
            l_list=[]
            for i in range(len(manual_pod_result)):
                if manual_pod_result[i]['FM Date'] == date_value:
                    l_list.append(manual_pod_result[i]['Data Center'])
            l_list.sort()
            manual_reg_fmdata[date_value]=list(set(l_list))
        """
        n=list(manual_reg_fmdata.keys())
        n.sort(key = lambda date: datetime.datetime.strptime(date, '%d-%b-%y'))
        manual_data={}
        for i in range(len(n)):
            manual_data[n[i]]=manual_reg_fmdata[n[i]]
        manual_reg_fmdata = manual_data
        print(manual_reg_fmdata) """
        manual_reg_fmdata=json.dumps(manual_reg_fmdata)
        #myKeys = list(manual_reg_fmdata.keys())
        #myKeys.sort()
        #sorted_dict = {i: manual_reg_fmdata[i] for i in myKeys}
        #print(sorted_dict)
        #print("manual data")
        #for i in set(reg_man_list):
        #    reg_man=str(reg_man)+"<option value=\'"+i+"\'>"+i+"</option>"

        #Sorting dates Ascending order
        x_m_fm_data=list(set(m_fm_data))
        x_m_fm_data.sort(key = lambda date: datetime.datetime.strptime(date, '%d-%b-%y'))
        for i in x_m_fm_data:
            m_fmdata=str(m_fmdata)+"<option value=\'"+i+"\'>"+i+"</option>"

        if request.GET:
            result_date=str(request.GET['ChooseDate'])
            req_type=str(request.GET['size'])
            req_region=str(request.GET['region'])
        #    print(result_date,req_type)
            if str(req_type) == 'FMDate':
                psr_req_type='FM Date'
            if str(req_type) == 'ReqDate':
                psr_req_type='Request Date'
        #    print(result_date,req_type)

            if str(request.GET['items']) == "Stamp":
                psr_stamp_output={}
                reg_list=set()
                for i in range(len(stamp_pod_result)):
                    if stamp_pod_result[i][str(psr_req_type)] == str(result_date) :
                        if stamp_pod_result[i]['Data Center'] == "":
                            psr_pod=str(stamp_pod_result[i]['POD Name'])
                            psr_pod_result=podcontent.cloud_meta_podattr(psr_pod,str(request.session['cred_value']))
                            reg_list.add(psr_pod_result['fm_datacenter'])
                        else:
                            reg_list.add(stamp_pod_result[i]['Data Center'])
                for rgion in reg_list:
                    pd_list=[]
                    for i in range(len(stamp_pod_result)):
                        if stamp_pod_result[i][str(psr_req_type)] == str(result_date) :
                            if stamp_pod_result[i]['Data Center'] == rgion:
                                pd_list.append(str(stamp_pod_result[i]['POD Name']))
                    psr_stamp_output[rgion]=pd_list
                psr_page_region_op={}
                for key_region in psr_stamp_output:
                    response,values=commonutils.region_stamp_psr_data(str(result_date),str(key_region),account,str(request.GET['size']))
                    psr_page_region_op[key_region]=values
                pod_content={}
                for i in psr_page_region_op:
                    for j in psr_page_region_op[i]:
                        if j!='current_uses' and j!='capacity_require':
                            for k in range(len(psr_page_region_op[i][j])):
                                for o in psr_page_region_op[i][j][k]:
                                    pod_content[o]=psr_page_region_op[i][j][k][o]
                                    is_faasdata=podcontent.cloud_meta_podattr(o,str(request.session['cred_value']))['podAttributes']['isFAAAS']
                                    pod_content[o]['isFAAAS']=str(is_faasdata)

                #response,values=commonutils.stamp_resize_capacity_check(str(result_date),str(request.GET['size']))
                response,values=commonutils.region_stamp_psr_data(str(result_date),str(req_region),account,str(request.GET['size']))
                #print(values)
                #print("Datewise report")
                response_date,values_date =commonutils.region_stamp_psr_data(str(result_date),"",account,str(request.GET['size']))
                #print(values_date)
                report_type="Stamp"
                return render(request,'podlookup/psranalysis_data.html',{'pod_content':pod_content,'all_reg_data':psr_page_region_op,'values_date':values_date,'regin':str(req_region),'dat':result_date,'data':values,'report':report_type,'r_type':req_type,'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data), "source_url_dop":source_url_dop})
            elif str(request.GET['items']) == "Manual":
                psr_man_output={}
                reg_list=set()
                for i in range(len(manual_pod_result)):
                    if manual_pod_result[i][str(psr_req_type)] == str(result_date) :
                        if manual_pod_result[i]['Data Center'] == "":
                            psr_pod=str(manual_pod_result[i]['POD Name'])
                            psr_pod_result=podcontent.cloud_meta_podattr(psr_pod,str(request.session['cred_value']))
                            reg_list.add(psr_pod_result['fm_datacenter'])
                        else:
                            reg_list.add(manual_pod_result[i]['Data Center'])
                for rgion in reg_list:
                    pd_list=[]
                    for i in range(len(manual_pod_result)):
                        if manual_pod_result[i][str(psr_req_type)] == str(result_date) :
                            if manual_pod_result[i]['Data Center'] == rgion:
                                pd_list.append(str(manual_pod_result[i]['POD Name']))
                    psr_man_output[rgion]=pd_list
                psr_page_region_op={}
                for key_region in psr_man_output:
                    response,values=commonutils.region_manual_psr_data(str(result_date),account,str(key_region))
                    psr_page_region_op[key_region]=values
                pod_content={}
                for i in psr_page_region_op:
                    for j in psr_page_region_op[i]:
                        if j!='current_uses' and j!='capacity_require':
                            for k in range(len(psr_page_region_op[i][j])):
                                for o in psr_page_region_op[i][j][k]:
                                    pod_content[o]=psr_page_region_op[i][j][k][o]
                                    is_faasdata=podcontent.cloud_meta_podattr(o,str(request.session['cred_value']))['podAttributes']['isFAAAS']
                                    pod_content[o]['isFAAAS']=str(is_faasdata)

                #response_date,values_date=commonutils.manual_resize_capacity_check(str(result_date),account,"")
                response,values=commonutils.region_manual_psr_data(str(result_date),account,str(req_region))
                #print(values)
                response_date,values_date=commonutils.region_manual_psr_data(str(result_date),account,"")
                report_type="Manual"
                source_url = "https://cloudmeta.itpa.cyf.oraclecloud.com/cloudmeta-api/swagger-ui/#/default"
                return render(request,'podlookup/psranalysis_data.html',{'pod_content':pod_content,'all_reg_data':psr_page_region_op,'values_date':values_date,'regin':str(req_region),'dat':result_date,'data':values,'report':report_type,'r_type':req_type,'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data), 'source_url': source_url})
            else:
                print("No input")
            return render(request,'podlookup/psranalysis_mainpage.html')
        return render(request,'podlookup/psranalysis_mainpage.html',{'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data),'manual_pod_result':manual_pod_result})
    except Exception as e:
        return render(request,'podlookup/psranalysis_mainpage_error.html')

#commonutils.capacity_check()
