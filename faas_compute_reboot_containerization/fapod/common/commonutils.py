import json
import sys
import datetime
import requests
import traceback
import os
import re
import copy
sys.path.append("../")
from common import globalvariables,ociSDK,data_fetch,podcontent



#oci_sdk=ociSDK.OciSdk()
datafetch=data_fetch.fetch()

####################################################################PODSIZE COMP####################################################################
def current_size_temp(profile_data,release,arc,pod_size):
    try:
        size=""
        cur_scaling_no = ""
        if 'XS' in pod_size.split(',')[0]:
            cur_scaling_no = pod_size.split(',')[0][2:]
            size=pod_size.split(',')[0][:2]
        else:
            cur_scaling_no = pod_size.split(',')[0][1:]
            size=pod_size.split(',')[0][0]
        current_temp={"pod_current_size": pod_size.split(',')[0],"release":release,"auxvm_count":cur_scaling_no}
        vmdic = {}
        shape=""
        for profile in profile_data:
            if profile["podSizeType"] == size and profile["faRelease"] == release and profile["profileType"] == "INFRASTRUCTURE":
                for vmtype in json.loads(profile["sizeProfileJsonData"])["topology"]["vmHosts"]:
                    if "ocpus" in vmtype["ociVMShapeHwInfo"][arc]:
                        vmdic.update({vmtype["vmType"]:{"arc":arc,"shape":vmtype["ociVMShapeHwInfo"][arc]["shape"],"ocpus":vmtype["ociVMShapeHwInfo"][arc]["ocpus"],"memoryInGBs":vmtype["ociVMShapeHwInfo"][arc]["memoryInGBs"]}})
                        shape=vmtype["ociVMShapeHwInfo"][arc]["shape"]
                    else:
                        vmdic.update({vmtype["vmType"]:{"arc":arc,"shape":vmtype["ociVMShapeHwInfo"][arc]["shape"]}})
                        shape=vmtype["ociVMShapeHwInfo"][arc]["shape"]
                for auxvm in json.loads(profile["sizeProfileJsonData"])["topology"]["extensionDefinitions"]:
                    if "ocpus" in auxvm ["ociVMShapeHwInfo"][arc]:
                            vmdic.update({auxvm["vmType"]:{"arc":arc,"shape":auxvm["ociVMShapeHwInfo"][arc]["shape"],"ocpus":auxvm["ociVMShapeHwInfo"][arc]["ocpus"],"memoryInGBs":vmtype["ociVMShapeHwInfo"][arc]["memoryInGBs"]}})
                    else:
                        vmdic.update({auxvm["vmType"]:{"arc":arc,"shape":auxvm["ociVMShapeHwInfo"][arc]["shape"]}})

                vmdic.update({"AUXVM_LIMIT":json.loads(profile["sizeProfileJsonData"])["topology"]["extensionInstances"]})
        current_temp.update({"vmshape":shape,"vmtype":vmdic})
        return current_temp
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))

def target_size_temp(profile_data,target_size,release,tar_arc):
    try:
        trg_scaling_no=""
        trg_base_size=""
        if 'XS' in target_size:
            trg_scaling_no = target_size[2:]
            trg_base_size = 'XS'
        else:
            trg_scaling_no = target_size[1:]
            trg_base_size = target_size[0]
        if not trg_scaling_no:
            trg_scaling_no=0
        target_temp={"pod_target_size": target_size,"release":release,"auxvm_count":trg_scaling_no}
        vmdic = {}
        shape=""
        #print(trg_base_size,release)
        for profile in profile_data:
            if profile["podSizeType"] == trg_base_size and profile["faRelease"] == release and profile["profileType"] == "INFRASTRUCTURE":
                for vmtype in json.loads(profile["sizeProfileJsonData"])["topology"]["vmHosts"]:
                    if "ocpus" in vmtype["ociVMShapeHwInfo"][tar_arc]:
                        vmdic.update({vmtype["vmType"]:{"arc":tar_arc,"shape":vmtype["ociVMShapeHwInfo"][tar_arc]["shape"],"ocpus":vmtype["ociVMShapeHwInfo"][tar_arc]["ocpus"],"memoryInGBs":vmtype["ociVMShapeHwInfo"][tar_arc]["memoryInGBs"]}})
                        shape=vmtype["ociVMShapeHwInfo"][tar_arc]["shape"]
                    else:
                        vmdic.update({vmtype["vmType"]:{"arc":tar_arc,"shape":vmtype["ociVMShapeHwInfo"][tar_arc]["shape"]}})
                        shape=vmtype["ociVMShapeHwInfo"][tar_arc]["shape"]
                for auxvm in json.loads(profile["sizeProfileJsonData"])["topology"]["extensionDefinitions"]:
                    if "ocpus" in auxvm ["ociVMShapeHwInfo"][tar_arc]:
                            vmdic.update({auxvm["vmType"]:{"arc":tar_arc,"shape":auxvm["ociVMShapeHwInfo"][tar_arc]["shape"],"ocpus":auxvm["ociVMShapeHwInfo"][tar_arc]["ocpus"],"memoryInGBs":vmtype["ociVMShapeHwInfo"][tar_arc]["memoryInGBs"]}})
                    else:
                        vmdic.update({auxvm["vmType"]:{"arc":tar_arc,"shape":auxvm["ociVMShapeHwInfo"][tar_arc]["shape"]}})

                vmdic.update({"AUXVM_LIMIT":json.loads(profile["sizeProfileJsonData"])["topology"]["extensionInstances"]})

        target_temp.update({"vmshape":shape,"vmtype":vmdic})
        return target_temp
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))


def pod_sizing_comp(pod,target_size,src_arc,tar_arc,account,release=None,pod_size=None):
    try:
        if not release :
            data = podcontent.full_pod_data_method(pod,account)
            # print(type(data))
            if type(data) == list:
                # current_size = '' # sample value -> L (T-shirt sizing)
                release = ''  # sample value -> 11.13.22.10.0
                pod_size = '' # sample value -> L41,VCP=1,BIP=1,CustomVM_CRMAP=33,BGKM=true,CustomVM_Service3=5,GRC=1,customSize=EEHO-29477109,ES=0
                # print(type(data))
                for i in data:
                    if i["name"] == "pod_size":
                        pod_size = i["value"]
                    elif i["name"] == "maintenance_level":
                        release = i["value"]
                    # elif i["name"] == "size":
                    #     current_size = i["value"]
                release = release.split('_')[0]
                # print(pod,pod_size,release,current_size)
        status,file_name=datafetch.resize_lcm_profile_data(account)
        if status:
            with open(file_name,'r') as j_data:
                response=json.load(j_data)
            current_temp=current_size_temp(response,release,src_arc,pod_size)
            targate_temp=target_size_temp(response,target_size,release,tar_arc)
            return current_temp,targate_temp
        else:
            print("{0}error occured in file generation : check the function - stamp_psr_data".format(globalvariables.RED))
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))
####################################################################PODSIZE COMP####################################################################
def check_hw(hw_map):
    try:
        if hw_map:
            if "AMD" in hw_map.upper() and "E3" in hw_map.upper():
                return "AMD"
            elif "AMD" in hw_map.upper() and "E4" in hw_map.upper():
                return "AMDE4FULL"
            elif "X6" in hw_map.upper():
                return "X6"
            elif "X7" in hw_map.upper():
                return "X7"
            elif "X9" in hw_map.upper():
                return "X9"
            elif "ARM" in hw_map.upper():
                return "ARMA1"
            else:
                traceback.print_exc()
                print("{0}check_HW -> invalide HW MAP recieve in manual/stamp data {1}".format(globalvariables.RED,hw_map))
        else:
            return hw_map
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))

def manual_resize_capacity_check(input_date):
    date_time=datetime.datetime.now()
    today_date=date_time.strftime("%Y%m%d")
    try:
        processed_manual_json="{0}/manual_{1}.json".format(globalvariables.processed_psr,input_date)
        age_time=globalvariables.data_files["manual_resize_capacity"]["timedelta"]
        with open(globalvariables.size_template,'r') as size_temp:
            size_template=json.load(size_temp)
        if os.path.exists(processed_manual_json) and datafetch.check_file_age(processed_manual_json,age_time):
            with open(processed_manual_json,'r') as jdata:
                manual_data=json.load(jdata)
            return True, manual_data
        else:
            dict1={}
            status,filename=datafetch.manual_psr_data()
            # print(status,filename)
            if status :
                with open(filename,'r') as data:
                    jdata=json.load(data)
                    for i in jdata:
                        base_size=re.sub(r'[0-9]','',i["Old Shape"])
                        if i["FM Date"] == input_date and i["FM Date"] not in dict1:
                            dict1.update({i["FM Date"]: []})
                        if i["FM Date"] == input_date and base_size in size_template:
                            hw_map=check_hw(i['HW Map'])
                            account="commercial"
                            #print(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                            current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                            dict1[i["FM Date"]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Manual','timestamp':today_date}})
                    with open(processed_manual_json,'w') as data:
                        json.dump(dict1,data,indent=6)
                # print(dict1)
                return True, dict1
            else:
                print("{0}error occured in file generation : check the function - manual_psr_data".format(globalvariables.RED))
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))

def stamp_resize_capacity_check(input_date,flag=""):
    date_type=""
    if flag.lower() == "fmdate" :
        date_type="FM Date"
    else:
        date_type="Request Date"
    try:
        date_time=datetime.datetime.now()
        today_date=date_time.strftime("%Y%m%d")
        processed_stamp_json="{0}/stamp_{1}_{2}.json".format(globalvariables.processed_psr,input_date,flag)
        age_time=globalvariables.data_files["stamp_resize_capacity"]["timedelta"]
        with open(globalvariables.size_template,'r') as size_temp:
            size_template=json.load(size_temp)
        if os.path.exists(processed_stamp_json) and datafetch.check_file_age(processed_stamp_json,age_time):
            with open(processed_stamp_json,'r') as jdata:
                stamp_data=json.load(jdata)
            return True, stamp_data
        else:
            dict1={}
            status,filename=datafetch.stamp_psr_data()
            #print(status,filename)
            if status :
                with open(filename,'r') as data:
                    jdata=json.load(data)
                    for i in jdata:
                        #print(i[date_type],input_date)
                        base_size=re.sub(r'[0-9]','',i["Old Shape"])
                        if i[date_type] == input_date and i[date_type] not in dict1:
                            dict1.update({i[date_type]: []})
                        if i[date_type] == input_date and base_size in size_template:
                            hw_map=check_hw(i['HW Map'])
                            account="commercial"
                            #print(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                            current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                            dict1[i[date_type]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Manual','timestamp':today_date}})
                    with open(processed_stamp_json,'w') as data:
                        json.dump(dict1,data,indent=6)
                return True, dict1
            else:
                print("{0}error occured in file generation : check the function - stamp_psr_data{1}".format(globalvariables.RED,globalvariables.RESET))
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}{2}".format(globalvariables.RED,e,globalvariables.RESET))

def vpn_check(pod_name,account):
    try:
        status,filename=datafetch.vpn_data(account)
        if status:
            with open(filename,'r') as jd:
                j_data=json.load(jd)
                count=0
                # print(type(json.loads(j_data)))
                for pod in json.loads(j_data):
                    if pod["POD_NAME"].lower() == pod_name.lower():
                        count += 1
                        return True
                if count == 0:
                    return False
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))

def stamp_region_data(input_date,flag):
    date_type=""
    if flag.lower() == "fmdate" :
        date_type="FM Date"
    else:
        date_type="Request Date"
    region=[]
    status,filename=datafetch.stamp_psr_data()
    if status:
        with open(filename,'r') as data:
            jdata=json.load(data)
            for i in jdata:
                if i[date_type] == input_date:
                    region.append(i["Data Center"])
    return region


def manual_region_data(input_date):
    region=[]
    status,filename=datafetch.manual_psr_data()
    if status:
        with open(filename,'r') as data:
            jdata=json.load(data)
            for i in jdata:
                if i["FM Date"] == input_date:
                    region.append(i["Data Center"])
    return region


def region_manual_psr_data(input_date,account,region):
    date_time=datetime.datetime.now()
    today_date=date_time.strftime("%Y%m%d")
    #account="commercial"
    try:
        release_list=psr_release_validation(account)
        processed_manual_json="{0}/manual_{1}_{2}.json".format(globalvariables.processed_psr,region,input_date)
        capacity_analysis="{0}/capacity_analysis_manual_{1}_{2}.json".format(globalvariables.processed_psr,region,input_date)
        age_time=globalvariables.data_files["manual_resize_capacity"]["timedelta"]
        with open(globalvariables.size_template,'r') as size_temp:
            size_template=json.load(size_temp)
        if os.path.exists(processed_manual_json) and datafetch.check_file_age(processed_manual_json,age_time):
            with open(processed_manual_json,'r') as jdata:
                manual_data=json.load(jdata)
            return True, manual_data
        else:
            dict1={}
            capacity_needed={}
            capacity_current={}
            status,filename=datafetch.manual_psr_data()
            # print(status,filename)
            if status :
                with open(filename,'r') as data:
                    jdata=json.load(data)
                    for i in jdata:
                        base_size=re.sub(r'[0-9]','',i["Old Shape"])
                        hw_map=check_hw(i['HW Map'])
                        if hw_map:
                            if i["FM Date"] == input_date and i["FM Date"] not in dict1:
                                dict1.update({i["FM Date"]: []})
                            if ( region and  i["FM Date"] == input_date and i["Data Center"] == region ) or ( not region and  i["FM Date"] == input_date ):
                                if base_size in size_template and i["Current Release"] in release_list:
                                    if i["Resize Type"] in globalvariables.resize_type :
                                        #print(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                                        current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                                        dict1[i["FM Date"]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Manual','timestamp':today_date,"Resize Type":i["Resize Type"],"Resize Reason":i["Resize Reason"],"Bugs":i["Bugs"],"POD Architectur":i["POD Architecture"]}})
                                        if targate_temp["vmshape"] in capacity_needed.keys():
                                            vm_num=capacity_needed[targate_temp["vmshape"]]
                                            newvm=vm_num + int(targate_temp["auxvm_count"])
                                            capacity_needed.update({targate_temp["vmshape"]:newvm})
                                        else:
                                            capacity_needed.update({targate_temp["vmshape"]: int(targate_temp["auxvm_count"])})
                                        if current_temp["vmshape"] in capacity_current.keys():
                                            vm_num=capacity_current[current_temp["vmshape"]]
                                            newvm=vm_num + int(current_temp["auxvm_count"])
                                            capacity_current.update({current_temp["vmshape"]:newvm})
                                        else:
                                            capacity_current.update({current_temp["vmshape"]: int(current_temp["auxvm_count"])})
                                elif i["Resize Type"] in globalvariables.resize_type :
                                    current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,"",i["Old Shape"])
                                    dict1[i["FM Date"]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Manual','timestamp':today_date,"Resize Type":i["Resize Type"],"Resize Reason":i["Resize Reason"],"Bugs":i["Bugs"],"POD Architectur":i["POD Architecture"]}})
                                    if targate_temp["vmshape"] in capacity_needed.keys():
                                        vm_num=capacity_needed[targate_temp["vmshape"]]
                                        newvm=vm_num + int(targate_temp["auxvm_count"])
                                        capacity_needed.update({targate_temp["vmshape"]:newvm})
                                    else:
                                        capacity_needed.update({targate_temp["vmshape"]: int(targate_temp["auxvm_count"])})
                                    if current_temp["vmshape"] in capacity_current.keys():
                                        vm_num=capacity_current[current_temp["vmshape"]]
                                        newvm=vm_num + int(current_temp["auxvm_count"])
                                        print(newvm)
                                        capacity_current.update({current_temp["vmshape"]:newvm})
                                    else:
                                        capacity_current.update({current_temp["vmshape"]: int(current_temp["auxvm_count"])})
                    if len(dict1) != 0:
                        current_uses,capacity_require=capacity_calculate_v1(dict1[input_date])
                        dict1.update({"current_uses":current_uses,"capacity_require":capacity_require})
                        with open(capacity_analysis,'w') as cap_req:
                            json.dump({"current_uses":current_uses,"capacity_require":capacity_require},cap_req,indent=6)
                        with open(processed_manual_json,'w') as data:
                            json.dump(dict1,data,indent=6)
                    else:
                        return False,dict1
                # print(dict1)
                return True, dict1
            else:
                print("{0}error occured in file generation : check the function - manual_psr_data".format(globalvariables.RED))
    except Exception as e:
        traceback.print_exc()
        print("{0}{1}".format(globalvariables.RED,e))

def psr_release_validation(account):
    try:
        status,file=datafetch.resize_lcm_profile_data(account)
        if status:
            with open(file,'r') as p_data:
                profile_data=json.load(p_data)
            release_list=[]
            for data in profile_data:
                if data["faRelease"]:
                    release_list.append(data["faRelease"])
            return release_list
    except Exception as e:
        traceback.print_exc()
        print("{0} error in psr_release_validation {1}".format(globalvariables.RED,e))

def capacity_calculate(dict1,dict2):
    try:
        dict3={}
        dict1_len=len(dict1)
        if dict1_len >0 :
            for key,value in dict1.items():
                dict3.update({key:int(dict2[key]) - int(value)})
        else:
            dict3=dict2
        return dict3
    except Exception as e:
        traceback.print_exc()
        print("{0} error in capacity_calculate {1}".format(globalvariables.RED,e))

def check_release(rel):
    # print(len(rel))
    if len(rel) == 8:
        return "11" + "." + rel + "." + "0"
    else:
        return rel



def check_shape_v1(value,array):
    status=False
    shape=""
    for val in array:
        if value["ocpus"] == val["ocpus"] and value["memoryInGBs"] == val["memoryInGBs"]:
            status=True
            shape=val
    return status,shape

def check_dict_format(dict1):
    dict2={}
    for shape,shape_val in dict1.items():
        if type(shape_val) is not list:
            dict2.update({shape:[{"ocpus":0,"memoryInGBs":0,"count":shape_val}]})
        else:
            dict2.update({shape:shape_val})
    return dict2

def capacity_calculate_v1(dict1):
    try:
        # print(dict1)
        old_dict1={}
        new_dict={}
        #old/current capacity calculation
        for pod_data in dict1:
            for pod in pod_data.values():
                # base_size=re.sub(r'[0-9]','',str(pod["Old Shape"]["pod_current_size"]))
                vmshape=pod["Old Shape"]["vmshape"]
                auxvm=int(pod["Old Shape"]["auxvm_count"])
                # if vmshape in old_dict1:
                #processing AMD shapes
                if vmshape not in globalvariables.x_shape:
                    for key,value in pod["Old Shape"]["vmtype"].items():
                        if key != "AUXVM" and "ocpus" in list(value):
                            check={"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"]}
                            if vmshape not in old_dict1:
                                old_dict1.update({vmshape: []})
                            status,av_shape=check_shape_v1(check,old_dict1[vmshape])
                            if status:#checking if shape already exist in json
                                ind=old_dict1[vmshape].index(av_shape)
                                newcount=av_shape["count"] + 1
                                old_dict1[vmshape][ind].update({"ocpus":av_shape["ocpus"],"memoryInGBs":av_shape["memoryInGBs"],"count":newcount})
                            else:
                                old_dict1[vmshape].append({"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"],"count":1})
                        if key == "AUXVM" and auxvm >0:
                                for i in range(auxvm):
                                    check={"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"]}
                                    if vmshape not in old_dict1:
                                        old_dict1.update({vmshape: []})
                                    status,aux_shape=check_shape_v1(check,old_dict1[vmshape])
                                    if status:#checking if shape already exist in json
                                        ind=old_dict1[vmshape].index(aux_shape)
                                        newcount=aux_shape["count"] + 1
                                        old_dict1[vmshape][ind].update({"ocpus":aux_shape["ocpus"],"memoryInGBs":aux_shape["memoryInGBs"],"count":newcount})
                                    else:
                                        old_dict1[vmshape].append({"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"],"count":1})
                #Handling intel type shapes where prior entry present in old_dict1
                else:
                    for key,value in pod["Old Shape"]["vmtype"].items():
                        if key != "AUXVM" and "shape" in list(value):
                            if value["shape"] in old_dict1:
                                newcount=old_dict1[value["shape"]] + 1
                                old_dict1[value["shape"]] = newcount
                            else:
                                old_dict1.update({value["shape"]:1})
                        if key == "AUXVM" and auxvm >0:
                            if value["shape"] in old_dict1 :
                                newcount=old_dict1[value["shape"]] + auxvm
                                old_dict1[value["shape"]] =  newcount
                            else:
                                old_dict1.update({value["shape"]:auxvm})
            # print(old_dict1)
        # print(old_dict1)
        #new capacity calculation
        old_dict=copy.deepcopy(old_dict1)


        for pod_data in dict1:
            for pod_req in pod_data.values():
                # base_size=re.sub(r'[0-9]','',str(pod["New Shape"]["pod_target_size"]))
                pod=pod_req["New Shape"]
                vmshape=pod["vmshape"]
                auxcount=int(pod["auxvm_count"])
                #AMD type processing
                if vmshape not in globalvariables.x_shape:
                    for key,value in pod["vmtype"].items():
                        if key != "AUXVM" and "ocpus" in list(value):
                            vmshape_1=value["shape"]
                            check={"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"]}
                            status_old=""
                            shape_del=""
                            if vmshape_1 in old_dict:
                                status_old,shape_del = check_shape_v1(check,old_dict[vmshape_1])
                            if not status_old:
                                if vmshape not in new_dict:
                                    new_dict.update({vmshape: []})
                                status_new,shape_update = check_shape_v1(check,new_dict[vmshape])
                                if status_new:
                                            ind=new_dict[vmshape].index(shape_update)
                                            newcount=shape_update["count"] + 1
                                            new_dict[vmshape][ind].update({"ocpus":shape_update["ocpus"],"memoryInGBs":shape_update["memoryInGBs"],"count":newcount})
                                else:
                                    new_dict[vmshape].append({"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"],"count":1})
                            elif shape_del["count"] == 1:
                                old_dict[vmshape].remove(shape_del)
                            else:
                                ind=old_dict[vmshape].index(shape_del)
                                new_count=shape_del["count"] - 1
                                old_dict[vmshape][ind].update({"ocpus":shape_del["ocpus"],"memoryInGBs":shape_del["memoryInGBs"],"count":new_count})
                        #AUXVM count processing
                        if key == "AUXVM" and auxcount >0:
                            for i in range(auxcount):
                                auxvmshape_1=value["shape"]
                                check_aux={"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"]}
                                # print(check_aux)
                                aux_status_old=""
                                aux_shape_del=""
                                if auxvmshape_1 in old_dict:
                                    aux_status_old,aux_shape_del = check_shape_v1(check_aux,old_dict[auxvmshape_1])
                                # aux_status_new,aux_shape_update = check_shape_v1(check_aux,new_dict[vmshape])
                                if not aux_status_old:
                                    if vmshape not in new_dict:
                                        new_dict.update({vmshape: []})
                                    aux_status_new,aux_shape_update = check_shape_v1(check_aux,new_dict[vmshape])
                                    if aux_status_new:#checking if shape already exist in json
                                                ind=new_dict[vmshape].index(aux_shape_update)
                                                newcount=aux_shape_update["count"] + 1
                                                new_dict[vmshape][ind].update({"ocpus":aux_shape_update["ocpus"],"memoryInGBs":aux_shape_update["memoryInGBs"],"count":newcount})
                                                # print(newcount)
                                    else:
                                        new_dict[vmshape].append({"ocpus":value["ocpus"],"memoryInGBs":value["memoryInGBs"],"count":1})
                                elif aux_shape_del["count"] == 1:
                                    old_dict[vmshape].remove(aux_shape_del)
                                else:
                                    ind=old_dict[vmshape].index(aux_shape_del)
                                    new_count=aux_shape_del["count"] - 1
                                    old_dict[vmshape][ind].update({"ocpus":aux_shape_del["ocpus"],"memoryInGBs":aux_shape_del["memoryInGBs"],"count":new_count})
                #intel type processing
                else:
                    for intel_key,intel_value in pod["vmtype"].items():
                        if intel_key != "AUXVM" and "shape" in list(value):
                            if intel_value["shape"] not in old_dict:
                                if intel_value["shape"] in new_dict:
                                    newcount=new_dict[intel_value["shape"]] + 1
                                    new_dict[intel_value["shape"]] = newcount
                                else:
                                    new_dict.update({intel_value["shape"]:1})
                            elif old_dict[intel_value["shape"]] == 1:
                                old_dict.pop(intel_value["shape"])
                            else:
                                new_count=old_dict[intel_value["shape"]] - 1
                                old_dict[intel_value["shape"]] = new_count
                        if intel_key == "AUXVM" and auxcount >0:#AUXVM processing
                            if intel_value["shape"] not in old_dict :
                                if intel_value["shape"] in new_dict:
                                    newcount=new_dict[intel_value["shape"]] + auxcount
                                    new_dict[intel_value["shape"]] =  newcount
                                else:
                                    new_dict.update({intel_value["shape"]:auxcount})
                            elif old_dict[intel_value["shape"]] == 1:
                                old_dict.pop(intel_value["shape"])
                            else:
                                new_count=old_dict[intel_value["shape"]] - 1
                                old_dict[intel_value["shape"]] = new_count

        old_dict1=check_dict_format(old_dict1)
        new_dict=check_dict_format(new_dict)
        return old_dict1,new_dict
        # print old_dict
    except Exception as e:
        traceback.print_exc()
        print("{0} error in capacity_calculate {1}".format(globalvariables.RED,e))


def region_stamp_psr_data(input_date,region,account,flag=""):
    date_type=""
    if flag.lower() == "fmdate" :
        date_type="FM Date"
    else:
        date_type="Request Date"
    #account="commercial"
    try:
        release_list=psr_release_validation(account)
        date_time=datetime.datetime.now()
        today_date=date_time.strftime("%Y%m%d")
        processed_stamp_json="{0}/stamp_{1}_{2}_{3}.json".format(globalvariables.processed_psr,region,input_date,flag)
        capacity_analysis="{0}/capacity_analysis_{1}_{2}_{3}.json".format(globalvariables.processed_psr,region,input_date,flag)
        age_time=globalvariables.data_files["stamp_resize_capacity"]["timedelta"]
        with open(globalvariables.size_template,'r') as size_temp:
            size_template=json.load(size_temp)
        if os.path.exists(processed_stamp_json) and datafetch.check_file_age(processed_stamp_json,age_time):
            with open(processed_stamp_json,'r') as jdata:
                stamp_data=json.load(jdata)
            return True, stamp_data
        else:
            dict1={}
            capacity_needed={}
            capacity_current={}
            status,filename=datafetch.stamp_psr_data()
            #print(status,filename)
            if status :
                with open(filename,'r') as data:
                    jdata=json.load(data)
                    for i in jdata:
                        #print(i[date_type],input_date)
                        if i['HW Map']:
                            hw_map=check_hw(i['HW Map'])
                            base_size=re.sub(r'[0-9]','',i["Old Shape"])
                            if i[date_type] == input_date and i[date_type] not in dict1:
                                dict1.update({i[date_type]: []})
                            release=check_release(i["Current Release"])
                            # print(release)
                            if ( region and  i[date_type] == input_date and i["Data Center"] == region ) or ( not region and  i[date_type] == input_date ):
                                if base_size in size_template and release in release_list:#old shape and curren release validation
                                    #print(i['POD Name'],i['New Shape'],hw_map,hw_map,account,i["Current Release"],i["Old Shape"])
                                    if i["Resize Type"] in globalvariables.resize_type:
                                        current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,release,i["Old Shape"])
                                        dict1[i[date_type]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Stamp','timestamp':today_date,"Resize Type":i["Resize Type"],"Resize Reason":i["Resize Reason"],"Bugs":i["Bugs"],"POD Architectur":i["POD Architecture"]}})
                                        if targate_temp["vmshape"] in capacity_needed.keys():
                                            vm_num=capacity_needed[targate_temp["vmshape"]]
                                            newvm=vm_num + int(targate_temp["auxvm_count"])
                                            capacity_needed.update({targate_temp["vmshape"]:newvm})
                                        else:
                                            capacity_needed.update({targate_temp["vmshape"]: int(targate_temp["auxvm_count"])})

                                        if current_temp["vmshape"] in capacity_current.keys():
                                            vm_num=capacity_current[current_temp["vmshape"]]
                                            newvm=vm_num + int(current_temp["auxvm_count"])
                                            capacity_current.update({current_temp["vmshape"]:newvm})
                                        else:
                                            capacity_current.update({current_temp["vmshape"]: int(current_temp["auxvm_count"])})
                                elif i["Resize Type"] in globalvariables.resize_type:
                                    current_temp,targate_temp=pod_sizing_comp(i['POD Name'],i['New Shape'],hw_map,hw_map,account,"",i["Old Shape"])
                                    dict1[i[date_type]].append({i['POD Name']:{'Old Shape': current_temp, 'New Shape': targate_temp,'region':i['Data Center'],'resize_type':'Stamp','timestamp':today_date,"Resize Type":i["Resize Type"],"Resize Reason":i["Resize Reason"],"Bugs":i["Bugs"],"POD Architectur":i["POD Architecture"]}})
                                    if targate_temp["vmshape"] in capacity_needed.keys():
                                        vm_num=capacity_needed[targate_temp["vmshape"]]
                                        newvm=vm_num + int(targate_temp["auxvm_count"])
                                        capacity_needed.update({targate_temp["vmshape"]:newvm})
                                    else:
                                        capacity_needed.update({targate_temp["vmshape"]: int(targate_temp["auxvm_count"])})
                                    if current_temp["vmshape"] in capacity_current.keys():
                                        vm_num=capacity_current[current_temp["vmshape"]]
                                        newvm=vm_num + int(current_temp["auxvm_count"])
                                        capacity_current.update({current_temp["vmshape"]:newvm})
                                    else:
                                        capacity_current.update({current_temp["vmshape"]: int(current_temp["auxvm_count"])})
                    if len(dict1) != 0:
                        current_uses,capacity_require=capacity_calculate_v1(dict1[input_date])
                        dict1.update({"current_uses":current_uses,"capacity_require":capacity_require})
                        with open(processed_stamp_json,'w') as data:
                            json.dump(dict1,data,indent=6)
                        with open(capacity_analysis,'w') as cap_req:
                            json.dump({"current_uses":current_uses,"capacity_require":capacity_require},cap_req,indent=6)
                        return True, dict1
                    else:
                        return False,dict1
            else:
                print("{0}error occured in file generation : check the function - stamp_psr_data{1}".format(globalvariables.RED,globalvariables.RESET))
    except Exception as e:
        traceback.print_exc()
        print("{0}error in region_stamp_psr_data {1}{2}".format(globalvariables.RED,e,globalvariables.RESET))

def datelist_stamp(flag):
    date_type=""
    if flag.lower() == "fmdate" :
        date_type="FM Date"
    else:
        date_type="Request Date"
    date_list=[]
    status,filename=datafetch.stamp_psr_data()
    if status:
        with open(filename,'r') as data:
            jdata=json.load(data)
            for i in jdata:
                    datestring=i[date_type]
                    try:
                        date=datetime.datetime.strptime(datestring,"%d-%b-%y")
                        date_list.append(i[date_type])
                    except ValueError as e:
                        print("{0}{1} skipping".format(globalvariables.AMBER,e))
    return date_list

def datelist_manual():
    date_list=[]
    status,filename=datafetch.manual_psr_data()
    if status:
        with open(filename,'r') as data:
            jdata=json.load(data)
            for i in jdata:
                    datestring=i["FM Date"]
                    try:
                        date=datetime.datetime.strptime(datestring,"%d-%b-%y")
                        date_list.append(i["FM Date"])
                    except ValueError as e:
                        print("{0}{1} skipping".format(globalvariables.AMBER,e))
    return  date_list

def pod_capacity_analysis(pod,target_size,src_arc,tar_arc,account):
    pod_list=[]
    pod_dict={}
    current,target=pod_sizing_comp(pod,target_size,src_arc,tar_arc,account)
    # print(target)
    pod_list.append({pod:{"Old Shape":current,
                       "New Shape":target}})
    if len(pod_list) != 0:
        current_uses,capacity_require=capacity_calculate_v1(pod_list)
        pod_dict.update({"pod_current_size":pod_list[0][pod]["Old Shape"],"pod_target_size":pod_list[0][pod]["New Shape"],"current_uses":current_uses,"capacity_require":capacity_require})
        # print(pod_dict)
    return pod_dict

# region_manual_psr_data("28-APR-23","commercial","ap-mumbai-1")

# data = podcontent.full_pod_data_method("EEHO","commercial")
# print(data)