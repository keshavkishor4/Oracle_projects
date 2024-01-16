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
import os
sys.path.append("../")
from common import commonutils,data_fetch,podcontent,ociSDK,globalvariables


#################################### Index Page ####################################
def index_page(request):
    if request.GET:
        pod = str(request.GET['pod_name']).upper()
        request.session['pod']=pod

        result = podcontent.cloud_meta_podattr(pod,str(request.session['cred_value']))
        print(result)
        try:
            pod_basic_data.objects.all().delete()
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
        return render(request,'podlookup/main.html',{'pod_data_from_metadata': pod_details_from_cloudmeta})
    return render(request,'podlookup/main_woget.html')

def credstore_pageMethod(request):
    query = request.GET.get('data')
    request.session['cred_value']=query
    oci_sdk=ociSDK.OciSdk(request.session['cred_value'])
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

#################################### LBaas View Method ####################################
def lbaas_id_view_method(request):
    lbaas_data_table.objects.all().delete()
    lbaas_id=str(request.POST['lbaas_id'])
    region_name=str(request.POST['region'])
    try:
        account=str(request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    config=globalvariables.env_dictionary[account]['oci_config']
    config["region"]=region_name
    try:
        lb_data={}
        try:
            load_balancer_client = oci.load_balancer.LoadBalancerClient(config)
            list_load_balancers_response = load_balancer_client.list_load_balancers(compartment_id='ocid1.compartment.oc1..aaaaaaaaedremzszzkluzxvnwlrafigu2sls2sygyvqn2eu5yjikkgvqauyq',display_name=lbaas_id)
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        if len(list_load_balancers_response.data) == 0:
            pass
        else:
            lbaas_data_table.objects.create(region_name=str(region_name),display_name=str(list_load_balancers_response.data[0].display_name),lbaas_id=str(list_load_balancers_response.data[0].id), compartment_id=str(list_load_balancers_response.data[0].compartment_id),lifecycle_state=str(list_load_balancers_response.data[0].lifecycle_state),minimum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.minimum_bandwidth_in_mbps), maximum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.maximum_bandwidth_in_mbps),subnet_ids=str(list_load_balancers_response.data[0].subnet_ids), shape_name=str(list_load_balancers_response.data[0].shape_name),ip_address=str(list_load_balancers_response.data[0].ip_addresses[0].ip_address))
            lbaas_data_table_monitoring.objects.create(region_name=str(region_name),display_name=str(list_load_balancers_response.data[0].display_name),lbaas_id=str(list_load_balancers_response.data[0].id), compartment_id=str(list_load_balancers_response.data[0].compartment_id),lifecycle_state=str(list_load_balancers_response.data[0].lifecycle_state),minimum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.minimum_bandwidth_in_mbps), maximum_bandwidth_in_mbps=str(list_load_balancers_response.data[0].shape_details.maximum_bandwidth_in_mbps),subnet_ids=str(list_load_balancers_response.data[0].subnet_ids), shape_name=str(list_load_balancers_response.data[0].shape_name),ip_address=str(list_load_balancers_response.data[0].ip_addresses[0].ip_address))
    except:
        pass
    lb_data=lbaas_data_table.objects.all()
    return render(request,'podlookup/lbaas_data.html',{'lbaas_data':lb_data})

#################################### Get Weekly Report Stamp report and Manual Report ####################################
def get_weekly_report(request):
    #print(request.session['pod'])
    pod=str(request.session['pod'])
    datafetch=data_fetch.fetch()
    version_data=podcontent.maintenance_level_podattr(pod,str(request.session['cred_value']))
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
    if pod_detail_from_manual_report:
        if pod_detail_from_stamp_report:
            return render(request,'podlookup/resource_data.html',{'pod_stamp_result': pod_detail_from_stamp_report,'pod_manual_result': pod_detail_from_manual_report,'version':version_data})
        else:
            return render(request,'podlookup/resource_manual_data.html',{'pod_manual_result': pod_detail_from_manual_report,'version':version_data})
    else:
        return render(request,'podlookup/resource_stamp_data.html',{'pod_stamp_result': pod_detail_from_stamp_report,'version':version_data})

#################################### Pod Details based on cloud-meta API Call Page ####################################
def PodBasicData(request):
    full_pod_data.objects.all().delete()
    pod_name=str(request.session['pod'])
    result = podcontent.full_pod_data_method(str(request.session['pod']),request.session['cred_value'])
    try:
        for i in range(len(result)):
            full_pod_data_monitoring.objects.create(Pod_Name=str(pod_name),name=str(result[i]['name']),value=str(result[i]['value']))
            full_pod_data.objects.create(Pod_Name=str(pod_name),name=str(result[i]['name']),value=str(result[i]['value']))
    except Exception as e:
        print(e)
    pod_full_details=full_pod_data.objects.all()
    return render(request,'podlookup/pod_full_details.html',{'pod_data_from_metadata': pod_full_details})

#################################### ExaData Info based on cloud-meta API Call ####################################
def ExaDataFetchMethod(request):
    exa_data_info.objects.all().delete()
    try:
        account=str(request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')
    pod_name=str(request.session['pod'])
    URL = "{0}/cloudmeta-api/v2/FUSION/pods/{1}/exadatas".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],pod_name)
    result = podcontent.cloud_meta_genric(URL,account)
    try:
        exa_data={}
        for i in range(len(result)):
            e_data=get_exa_pod_info(result[i]['exadata'],account,pod_name)
            exa_data[result[i]['exadata']]=e_data
    except Exception as e:
        print(e)
    return render(request,'podlookup/exa_data.html',{'exa_data':exa_data})

def get_exa_pod_info(exa_node,account,pod_name):
    URL="{0}/cloudmeta-api/v2/FUSION/exadatas/{1}/pods".format(globalvariables.env_dictionary[account]["cloud_meta"]['url'],exa_node)
    result = podcontent.cloud_meta_genric(URL,account)
    try:
        exa_node_data=[]
        for i in range(len(result)):
            exa_data_info_monitoring.objects.create(Pod_Name=str(result[i]['pod_name']),exa_node=str(exa_node))
            exa_data_info.objects.create(Pod_Name=str(result[i]['pod_name']),exa_node=str(exa_node))
            exa_node_data.append(result[i]['pod_name'])
        return exa_node_data
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def ExaDataNodeViewMethod(request):
    exanode_info.objects.all().delete()
    try:
        result = podcontent.exadata_node_data(str(request.POST['exa_id']),request.session['cred_value'])
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

    try:
        exanode_info.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
        exanode_info_monitoring.objects.create(hostname=str(result['OK']['value']['hostname']),role=str(result['OK']['value']['role']),type_of_hw=str(result['OK']['value']['type']),datacenter_code=str(result['OK']['value']['datacenter_code']),uuid=str(result['OK']['value']['uuid']),instance_ocid=str(result['OK']['value']['instance_ocid']),serial_number=str(result['OK']['value']['serial_number']),kernel_version=str(result['OK']['value']['kernel_version']),cpu_model=str(result['OK']['value']['cpu_model']),os_version=str(result['OK']['value']['os_version']),ip_address=str(result['OK']['value']['ip_address']),product_name=str(result['OK']['value']['product_name']),environment=str(result['OK']['value']['environment']))
    except Exception as e:
        return render(request,'podlookup/error_page.html')
    result=exanode_info.objects.all()
    return render(request,'podlookup/exa_node_data.html',{'data':result})

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
    return render(request,'podlookup/pod_instance_data.html',{'pod_instance_values':pod_instance_data})

#################################### Capacity Reservation details - Region level data ####################################
def CapacityReservationMethod(request):
    try:
        account=str(request.session['cred_value'])
        config=globalvariables.env_dictionary[account]['oci_config']
        compartment_id = globalvariables.env_dictionary[account]['ten_id']
        try:
            identity_client = oci.identity.IdentityClient(config)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
        rgion=[]
        for region in regions:
            rgion.append(region.region_name)
        if request.GET:
            account=str(request.session['cred_value'])
            config=globalvariables.env_dictionary[account]['oci_config']
            compartment_id = globalvariables.env_dictionary[account]['ten_id']
            identity_client = oci.identity.IdentityClient(config)
            response = identity_client.list_region_subscriptions(config["tenancy"])
            regions = response.data
            rgion=[]
            for region in regions:
                rgion.append(region.region_name)
            region_level_capacity_table.objects.all().delete()
            no_capacity_region_list.objects.all().delete()
            unable_to_fetch_region_list.objects.all().delete()
            capacity_reservation_level_capacity_details.objects.all().delete()
            regin = str(request.GET['regions'])
            account=str(request.session['cred_value'])
            config=globalvariables.env_dictionary[account]['oci_config']
            compartment_id = globalvariables.env_dictionary[account]['ten_id']
            config['region']=regin
            core_client = oci.core.ComputeClient(config)
            try:
                list_compute_capacity_reservations_ids = core_client.list_compute_capacity_reservations(compartment_id)
                if len(list_compute_capacity_reservations_ids.data) >= 1:
                    for i in range(len(list_compute_capacity_reservations_ids.data)):
                        dashboard_result=core_client.get_compute_capacity_reservation(capacity_reservation_id=list_compute_capacity_reservations_ids.data[i].id)
                        pecentage_data=(dashboard_result.data.used_instance_count/dashboard_result.data.reserved_instance_count)*100
                        region_level_capacity_table.objects.create(region_name=str(regin),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        region_level_capacity_table_monitoring.objects.create(region_name=str(regin),availability_domain=str(dashboard_result.data.availability_domain),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),reserved_instance_count=str(dashboard_result.data.reserved_instance_count),used_instance_count=str(dashboard_result.data.used_instance_count),percentage=pecentage_data)
                        if len(dashboard_result.data.instance_reservation_configs) >= 1:
                            for i in range(len(dashboard_result.data.instance_reservation_configs)):
                                percnt=(dashboard_result.data.instance_reservation_configs[i].used_count/dashboard_result.data.instance_reservation_configs[i].reserved_count)*100
                                capacity_reservation_level_capacity_details.objects.create(region_name=str(regin),display_name=str(dashboard_result.data.display_name),cap_id=str(dashboard_result.data.id),instance_shape=str(dashboard_result.data.instance_reservation_configs[i].instance_shape),reserved_count=str(dashboard_result.data.instance_reservation_configs[i].reserved_count),memory=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(dashboard_result.data.instance_reservation_configs[i].instance_shape_config.ocpus),used_count=str(dashboard_result.data.instance_reservation_configs[i].used_count),percentage=percnt)
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
        return render(request,'podlookup/cap_view_dashboard.html',{'region':rgion})
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')


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
        identity_client = oci.identity.IdentityClient(config)
        response = identity_client.list_region_subscriptions(config["tenancy"])
        regions = response.data
        for region in regions:
            config['region']=region.region_name
            core_client = oci.core.ComputeClient(config)
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
        cmp_client= oci.core.ComputeClient(config)
        inst_data=cmp_client.get_instance(instance_id)
        inst_full_data.objects.create(Pod_Name=str(pod),region_name=str(region_name),instance_id=str(instance_id),availability_domain=str(inst_data.data.availability_domain),capacity_reservation_id=str(inst_data.data.capacity_reservation_id),dedicated_vm_host_id=str(inst_data.data.dedicated_vm_host_id),display_name=str(inst_data.data.display_name),fault_domain=str(inst_data.data.fault_domain),lifecycle_state=str(inst_data.data.lifecycle_state),shape=str(inst_data.data.shape))
        inst_full_data_monitoring.objects.create(Pod_Name=str(pod),region_name=str(region_name),instance_id=str(instance_id),availability_domain=str(inst_data.data.availability_domain),capacity_reservation_id=str(inst_data.data.capacity_reservation_id),dedicated_vm_host_id=str(inst_data.data.dedicated_vm_host_id),display_name=str(inst_data.data.display_name),fault_domain=str(inst_data.data.fault_domain),lifecycle_state=str(inst_data.data.lifecycle_state),shape=str(inst_data.data.shape))
    except Exception as e:
        return render(request,'podlookup/oci_config_error_page.html')

def CapViewMethod(request):
    try:
        pod=str(request.session['pod'])
        instance_id=str(request.POST['instance_id'])
        region_name=str(request.POST['region'])
        config=globalvariables.oci_config
        compartment_id = globalvariables.tenancy_id
        config['region']=region_name
        cmp_client= oci.core.ComputeClient(config)
        inst_data=cmp_client.get_instance(instance_id)
        if inst_data.data.capacity_reservation_id is None:
            insta_data = 'None'
            return render(request,'podlookup/cap_view_none.html',{'inst_info':insta_data})
        else:
            cap_data.objects.all().delete()
            pod_cap_data.objects.all().delete()
            cap_id=str(inst_data.data.capacity_reservation_id)
            core_client = oci.core.ComputeClient(config)
            cmd_output=core_client.get_compute_capacity_reservation(capacity_reservation_id=cap_id)
            #print(cmd_output.data)
            pecentage_data=(cmd_output.data.used_instance_count/cmd_output.data.reserved_instance_count)*100
            cap_data.objects.create(Pod_Name=str(pod),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
            cap_data_monitoring.objects.create(Pod_Name=str(pod),region_name=str(region_name),availability_domain=str(cmd_output.data.availability_domain),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),reserved_instance_count=str(cmd_output.data.reserved_instance_count),used_instance_count=str(cmd_output.data.used_instance_count),percentage=pecentage_data)
            if len(cmd_output.data.instance_reservation_configs) >= 1:
                for i in range(len(cmd_output.data.instance_reservation_configs)):
                    percnt=(cmd_output.data.instance_reservation_configs[i].used_count/cmd_output.data.instance_reservation_configs[i].reserved_count)*100
                    pod_cap_data.objects.create(region_name=str(region_name),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
                    pod_cap_data_monitoring.objects.create(region_name=str(region_name),display_name=str(cmd_output.data.display_name),cap_id=str(cmd_output.data.id),instance_shape=str(cmd_output.data.instance_reservation_configs[i].instance_shape),memory=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs),ocpus=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus),reserved_count=str(cmd_output.data.instance_reservation_configs[i].reserved_count),used_count=str(cmd_output.data.instance_reservation_configs[i].used_count),percentage=percnt)
            cap_dta=cap_data.objects.all()
            pod_cap_dta=pod_cap_data.objects.all()
            return render(request,'podlookup/capview.html',{'cap_data':cap_dta,'pod_cap_data':pod_cap_dta})
    except Exception as e:
        return render(request,'podlookup/oci_config_error_page.html')

def PodSizeAnalyseMethod(request):
    #if len(request.session['cred_value']) == 0 :
    #    print("account empty")
    if request.GET:
        try:
            pod=str(request.GET['podname']).upper()
            size=str(request.GET['size']).upper()
            s_arc=str(request.GET['source_arc']).upper()
            t_arc=str(request.GET['target_arc']).upper()
            account=str(request.session['cred_value'])
            print(pod,size,s_arc,t_arc)
            current,target=commonutils.pod_sizing_comp(pod,size,s_arc,t_arc,account)
            result=commonutils.pod_capacity_analysis(pod,size,s_arc,t_arc,account)
            print(result)
            if 'error' in current.keys():
                return render(request,'podlookup/podsizeanalyse_error.html')
            else:
                return render(request,'podlookup/podsizeanalyse.html',{'result':result,'pod':pod})
        except Exception as e:
            return render(request,'podlookup/cred_value_error_page.html')
        #return render(request,'podlookup/podsizeanalyse.html')
    return render(request,'podlookup/podsizeanalyse.html')

#################################### PSR Analysis Report #################################################################
def psrpagecapviewMethod(request):
    try:
        pod=str(request.POST['podname'])
        region_name=str(request.POST['region'])
        result = podcontent.pod_instance_data_values(str(pod),request.session['cred_value'])
        #print(result)
        instance_data=[]
        cap_data=[]
        try:
            for i in range(len(result['podHosts'])):
                instance_data.append(str(result['podHosts'][i]['instance_ocid']))
            for j in instance_data:
                instance_id=j
                config=globalvariables.oci_config
                compartment_id = globalvariables.tenancy_id
                config['region']=region_name
                cmp_client= oci.core.ComputeClient(config)
                inst_data=cmp_client.get_instance(instance_id)
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
                    core_client = oci.core.ComputeClient(config)
                    cmd_output=core_client.get_compute_capacity_reservation(capacity_reservation_id=k)
                    pecentage_data=(cmd_output.data.used_instance_count/cmd_output.data.reserved_instance_count)*100
                    v={}
                    v['availability_domain']=str(cmd_output.data.availability_domain)
                    v['cap_id']=str(cmd_output.data.id)
                    v['display_name']=str(cmd_output.data.display_name)
                    v['reserved_instance_count']=str(cmd_output.data.reserved_instance_count)
                    v['used_instance_count']=str(cmd_output.data.used_instance_count)
                    v['percentage']=pecentage_data
                    c=[]
                    if len(cmd_output.data.instance_reservation_configs) >= 1:
                        for i in range(len(cmd_output.data.instance_reservation_configs)):
                            percnt=(cmd_output.data.instance_reservation_configs[i].used_count/cmd_output.data.instance_reservation_configs[i].reserved_count)*100
                            r={}
                            r['display_name']=str(cmd_output.data.display_name)
                            r['instance_shape']=str(cmd_output.data.instance_reservation_configs[i].instance_shape)
                            r['memory']=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.memory_in_gbs)
                            r['ocpus']=str(cmd_output.data.instance_reservation_configs[i].instance_shape_config.ocpus)
                            r['reserved_count']=str(cmd_output.data.instance_reservation_configs[i].reserved_count)
                            r['used_count']=str(cmd_output.data.instance_reservation_configs[i].used_count)
                            r['percentage']=percnt
                            c.append(r)
                    reser={}
                    reser['cap']=v
                    reser['pod_cap']=c
                    result[k]=reser
                return render(request,'podlookup/psranalysis_capdata.html',{'cmd_output':result})
        except Exception as e:
            return render(request,'podlookup/oci_config_error_page.html')
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')

def psr_analysis_report(request):
    try:
        account=str(request.session['cred_value'])
        datafetch=data_fetch.fetch()
        status,stampfilepath=datafetch.stamp_psr_data()

        with open(stampfilepath) as f:
            stamp_pod_result=json.load(f)
        status,manualfilename=datafetch.manual_psr_data()
        with open(manualfilename) as f:
            manual_pod_result=json.load(f)
        manu_date=''
        Req_stamp='<option value=\'item0\'>Select Option</option>'
        s_fmdata='<option value=\'item0\'>Select Option</option>'
        s_data=[]
        s_fm_data=[]
        reg_stamp=''
        reg_man=''
        for i in range(len(stamp_pod_result)):
            if stamp_pod_result[i]['Request Date']:
                s_data=commonutils.datelist_stamp('Request Date')
                print(s_data)
                #s_data.append(stamp_pod_result[i]['Request Date'])
            if stamp_pod_result[i]['FM Date']:
                s_fm_data=commonutils.datelist_stamp('fmdate')
                print(s_fm_data)
                #s_fm_data.append(stamp_pod_result[i]['FM Date'])
        stamp_reg_reqdata={}
        stamp_reg_fmdata={}
        for date_value in set(s_data):
            l_list=[]
            for i in range(len(stamp_pod_result)):
                if stamp_pod_result[i]['Request Date'] == date_value:
                    l_list.append(stamp_pod_result[i]['Data Center'])
            stamp_reg_reqdata[date_value]=list(set(l_list))

        for date_value in set(s_fm_data):
            l_list=[]
            for i in range(len(stamp_pod_result)):
                if stamp_pod_result[i]['FM Date'] == date_value:
                    l_list.append(stamp_pod_result[i]['Data Center'])
            stamp_reg_fmdata[date_value]=list(set(l_list))
        stamp_reg_reqdata = json.dumps(stamp_reg_reqdata)
        stamp_reg_fmdata=json.dumps(stamp_reg_fmdata)
        for i in set(s_data):
            Req_stamp=str(Req_stamp)+"<option value=\'"+i+"\'>"+i+"</option>"
        for i in set(s_fm_data):
            s_fmdata=str(s_fmdata)+"<option value=\'"+i+"\'>"+i+"</option>"
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
            manual_reg_fmdata[date_value]=list(set(l_list))
        manual_reg_fmdata=json.dumps(manual_reg_fmdata)
        #for i in set(reg_man_list):
        #    reg_man=str(reg_man)+"<option value=\'"+i+"\'>"+i+"</option>"
        for i in set(m_fm_data):
            m_fmdata=str(m_fmdata)+"<option value=\'"+i+"\'>"+i+"</option>"

        if request.GET:
            result_date=str(request.GET['ChooseDate'])
            req_type=str(request.GET['size'])
            req_region=str(request.GET['region'])
            if str(request.GET['items']) == "Stamp":
                #response,values=commonutils.stamp_resize_capacity_check(str(result_date),str(request.GET['size']))
                response,values=commonutils.region_stamp_psr_data(str(result_date),str(req_region),account,str(request.GET['size']))
                print(values)
                print("Datewise report")
                response_date,values_date =commonutils.region_stamp_psr_data(str(result_date),"",account,str(request.GET['size']))
                print(values_date)
                report_type="Stamp"
                return render(request,'podlookup/psranalysis_data.html',{'values_date':values_date,'regin':str(req_region),'dat':result_date,'data':values,'report':report_type,'r_type':req_type,'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data)})
            elif str(request.GET['items']) == "Manual":
                #response_date,values_date=commonutils.manual_resize_capacity_check(str(result_date),account,"")
                response,values=commonutils.region_manual_psr_data(str(result_date),account,str(req_region))
                print(values)
                response_date,values_date=commonutils.region_manual_psr_data(str(result_date),account,"")
                #region_manual_psr_data(
                report_type="Manual"
                return render(request,'podlookup/psranalysis_data.html',{'values_date':values_date,'regin':str(req_region),'dat':result_date,'data':values,'report':report_type,'r_type':req_type,'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data)})
            else:
                print("No input")
            return render(request,'podlookup/psranalysis_mainpage.html')
        return render(request,'podlookup/psranalysis_mainpage.html',{'Req_stamp':Req_stamp,'s_fmdata':s_fmdata,'m_fmdata':m_fmdata,'reg_stamp':reg_stamp,'reg_man':reg_man,'stamp_reg_reqdata':stamp_reg_reqdata,'stamp_reg_fmdata':stamp_reg_fmdata,'manual_reg_fmdata':manual_reg_fmdata,'m_fm_data':set(m_fm_data),'manual_pod_result':manual_pod_result})
    except Exception as e:
        return render(request,'podlookup/cred_value_error_page.html')


#commonutils.capacity_check()
