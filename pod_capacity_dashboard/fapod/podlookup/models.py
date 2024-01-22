from django.db import models

# Create your models here.

########### Pod attr values table ###########
class full_pod_data(models.Model):
    Pod_Name=models.CharField(max_length=255)
    name=models.CharField(max_length=255)
    value=models.CharField(max_length=255)

class full_pod_data_monitoring(models.Model):
    Pod_Name=models.CharField(max_length=255)
    name=models.CharField(max_length=255)
    value=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### ExaNode Host Details table ###########
class exanode_info(models.Model):
    hostname=models.CharField(max_length=255)
    role=models.CharField(max_length=255)
    type_of_hw=models.CharField(max_length=255)
    datacenter_code=models.CharField(max_length=255)
    uuid=models.CharField(max_length=255)
    instance_ocid=models.CharField(max_length=255)
    serial_number=models.CharField(max_length=255)
    kernel_version=models.CharField(max_length=255)
    cpu_model=models.CharField(max_length=255)
    os_version=models.CharField(max_length=255)
    ip_address=models.CharField(max_length=255)
    product_name=models.CharField(max_length=255)
    environment=models.CharField(max_length=255)


class exanode_info_monitoring(models.Model):
    hostname=models.CharField(max_length=255)
    role=models.CharField(max_length=255)
    type_of_hw=models.CharField(max_length=255)
    datacenter_code=models.CharField(max_length=255)
    uuid=models.CharField(max_length=255)
    instance_ocid=models.CharField(max_length=255)
    serial_number=models.CharField(max_length=255)
    kernel_version=models.CharField(max_length=255)
    cpu_model=models.CharField(max_length=255)
    os_version=models.CharField(max_length=255)
    ip_address=models.CharField(max_length=255)
    product_name=models.CharField(max_length=255)
    environment=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

###########  Weekly report StampPod table ###########
class Stamp_Pod_Report(models.Model):
    request_data=models.CharField(max_length=255)
    fm_date=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    bugs=models.CharField(max_length=255)
    bug_creation_date=models.CharField(max_length=255)
    resize_type=models.CharField(max_length=255)
    execution_type=models.CharField(max_length=255)
    resize_reason=models.CharField(max_length=255)
    environment_type=models.CharField(max_length=255)
    pod_architecture=models.CharField(max_length=255)
    fresh_p_or_u=models.CharField(max_length=255)
    next_rel_date=models.CharField(max_length=255)
    next_rel_version=models.CharField(max_length=255)
    current_release=models.CharField(max_length=255)
    data_center=models.CharField(max_length=255)
    environment_region_name=models.CharField(max_length=255)
    old_shape=models.CharField(max_length=255)
    new_shape=models.CharField(max_length=255)
    pod_size=models.CharField(max_length=255)
    hw_map=models.CharField(max_length=255)
    #create_date=models.DateTimeField()

class Stamp_Pod_Report_monitoring(models.Model):
    request_data=models.CharField(max_length=255)
    fm_date=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    bugs=models.CharField(max_length=255)
    bug_creation_date=models.CharField(max_length=255)
    resize_type=models.CharField(max_length=255)
    execution_type=models.CharField(max_length=255)
    resize_reason=models.CharField(max_length=255)
    environment_type=models.CharField(max_length=255)
    pod_architecture=models.CharField(max_length=255)
    fresh_p_or_u=models.CharField(max_length=255)
    next_rel_date=models.CharField(max_length=255)
    next_rel_version=models.CharField(max_length=255)
    current_release=models.CharField(max_length=255)
    data_center=models.CharField(max_length=255)
    environment_region_name=models.CharField(max_length=255)
    old_shape=models.CharField(max_length=255)
    new_shape=models.CharField(max_length=255)
    pod_size=models.CharField(max_length=255)
    hw_map=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### LBaas Instance table ###########
class lbaas_data_table(models.Model):
    region_name=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    lbaas_id=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    maximum_bandwidth_in_mbps=models.CharField(max_length=255,default=None)
    minimum_bandwidth_in_mbps=models.CharField(max_length=255,default=None)
    subnet_ids=models.TextField(default=None)
    shape_name=models.CharField(max_length=255,default=None)
    ip_address=models.CharField(max_length=255,default=None)

class lbaas_data_table_monitoring(models.Model):
    region_name=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    lbaas_id=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    maximum_bandwidth_in_mbps=models.CharField(max_length=255,default=None)
    minimum_bandwidth_in_mbps=models.CharField(max_length=255,default=None)
    subnet_ids=models.TextField(default=None)
    shape_name=models.CharField(max_length=255,default=None)
    ip_address=models.CharField(max_length=255,default=None)
    dtime=models.DateTimeField(auto_now_add=True)

########### Weekly manual pod report table ###########
class Manual_Pod_Report(models.Model):
    next_rel_date=models.CharField(max_length=255)
    new_shape=models.CharField(max_length=255)
    fm_date=models.CharField(max_length=255)
    old_shape=models.CharField(max_length=255)
    execution_type=models.CharField(max_length=255)
    environment_type=models.CharField(max_length=255)
    hw_map=models.CharField(max_length=255)
    bugs=models.CharField(max_length=255)
    data_center=models.CharField(max_length=255)
    resize_reason=models.CharField(max_length=255)
    pod_architecture=models.CharField(max_length=255)
    current_release=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    environment_region_name=models.CharField(max_length=255)
    pod_size=models.CharField(max_length=255)
    next_rel_version=models.CharField(max_length=255)
    resize_type=models.CharField(max_length=255)

class Manual_Pod_Report_monitoring(models.Model):
    next_rel_date=models.CharField(max_length=255)
    new_shape=models.CharField(max_length=255)
    fm_date=models.CharField(max_length=255)
    old_shape=models.CharField(max_length=255)
    execution_type=models.CharField(max_length=255)
    environment_type=models.CharField(max_length=255)
    hw_map=models.CharField(max_length=255)
    bugs=models.CharField(max_length=255)
    data_center=models.CharField(max_length=255)
    resize_reason=models.CharField(max_length=255)
    pod_architecture=models.CharField(max_length=255)
    current_release=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    environment_region_name=models.CharField(max_length=255)
    pod_size=models.CharField(max_length=255)
    next_rel_version=models.CharField(max_length=255)
    resize_type=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### Instance id fulle details table ###########
class inst_full_data(models.Model):
    Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    instance_id=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    capacity_reservation_id=models.CharField(max_length=255)
    dedicated_vm_host_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
   # storage_type=models.CharField(max_length=255)
    fault_domain=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    shape=models.CharField(max_length=255)
    ocpus=models.CharField(max_length=255)

class inst_full_data_monitoring(models.Model):
    Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    instance_id=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    capacity_reservation_id=models.CharField(max_length=255)
    dedicated_vm_host_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
   # storage_type=models.CharField(max_length=255)
    fault_domain=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    shape=models.CharField(max_length=255)
    ocpus=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### Pod Level Instance details ###########
class Instance_details(models.Model):
    Region_Name=models.CharField(max_length=255)
    Instance_ID=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    capacity_reservation_id=models.CharField(max_length=255)
    dedicated_vm_host_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    storage_type=models.CharField(max_length=255)
    fault_domain=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    region=models.CharField(max_length=255)
    shape=models.CharField(max_length=255)

class Instance_details_monitoring(models.Model):
    Region_Name=models.CharField(max_length=255)
    Instance_ID=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    capacity_reservation_id=models.CharField(max_length=255)
    dedicated_vm_host_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    storage_type=models.CharField(max_length=255)
    fault_domain=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    region=models.CharField(max_length=255)
    shape=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

###########  Pod Basic Data table ###########
class pod_basic_data(models.Model):
    Pod_Name=models.CharField(max_length=255)
    dr_role=models.CharField(max_length=255)
    physical_pod_name=models.CharField(max_length=255)
    service=models.CharField(max_length=255)
    last_updated=models.CharField(max_length=255)
    datacenter_code=models.CharField(max_length=255)
    dc_short_name=models.CharField(max_length=255)
    associated_dr_peer=models.CharField(max_length=255)
    peer_physical_pod_name=models.CharField(max_length=255)
    id_name=models.CharField(max_length=255)
    fusion_service_name=models.CharField(max_length=255)
    status=models.CharField(max_length=255)
    pod_type=models.CharField(max_length=255)
    release=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    golden_gate_enabled=models.CharField(max_length=255)
    fm_datacenter=models.CharField(max_length=255)

class pod_basic_data_monitoring(models.Model):
    Pod_Name=models.CharField(max_length=255)
    dr_role=models.CharField(max_length=255)
    physical_pod_name=models.CharField(max_length=255)
    service=models.CharField(max_length=255)
    last_updated=models.CharField(max_length=255)
    datacenter_code=models.CharField(max_length=255)
    dc_short_name=models.CharField(max_length=255)
    associated_dr_peer=models.CharField(max_length=255)
    peer_physical_pod_name=models.CharField(max_length=255)
    id_name=models.CharField(max_length=255)
    fusion_service_name=models.CharField(max_length=255)
    status=models.CharField(max_length=255)
    pod_type=models.CharField(max_length=255)
    release=models.CharField(max_length=255)
    customer_name=models.CharField(max_length=255)
    golden_gate_enabled=models.CharField(max_length=255)
    fm_datacenter=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### Pod Instance details ###########
class pod_instance_details(models.Model):
    Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    systemtype=models.CharField(max_length=255)
    pod_host=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    instance_id=models.CharField(max_length=255)

class pod_instance_details_monitoring(models.Model):
    Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    systemtype=models.CharField(max_length=255)
    pod_host=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    instance_id=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### Region Level Capacity Details ###########
class region_level_capacity_table(models.Model):
    #Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    display_name=models.CharField(max_length=255)
    cap_id=models.CharField(max_length=255)
    reserved_instance_count=models.CharField(max_length=255)
    used_instance_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)

class region_level_capacity_table_monitoring(models.Model):
    #Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    display_name=models.CharField(max_length=255)
    cap_id=models.CharField(max_length=255)
    reserved_instance_count=models.CharField(max_length=255)
    used_instance_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)
    dtime=models.DateTimeField(auto_now_add=True)

########### Region with no capacity reservation ###########
class no_capacity_region_list(models.Model):
    region=models.CharField(max_length=255)
    result=models.CharField(max_length=255)

class no_capacity_region_list_monitoring(models.Model):
    region=models.CharField(max_length=255)
    result=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### regions unable to fetch info ###########
class unable_to_fetch_region_list(models.Model):
    region=models.CharField(max_length=255)
    result=models.CharField(max_length=255)

class unable_to_fetch_region_list_monitoring(models.Model):
    region=models.CharField(max_length=255)
    result=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

########### Complete Pod Capaicty details ###########
class capacity_reservation_level_capacity_details(models.Model):
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    cap_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    instance_shape=models.CharField(max_length=255)
    reserved_count=models.CharField(max_length=255)
    used_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    memory=models.CharField(max_length=255,default='')
    ocpus=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)

class capacity_reservation_level_capacity_details_monitoring(models.Model):
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    cap_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    instance_shape=models.CharField(max_length=255)
    reserved_count=models.CharField(max_length=255)
    used_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    memory=models.CharField(max_length=255,default='')
    ocpus=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)
    dtime=models.DateTimeField(auto_now_add=True)

########### ExaData Info ###########
class exa_data_info(models.Model):
    exa_node=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    Shape=models.CharField(max_length=255,default='')

class exa_data_info_monitoring(models.Model):
    exa_node=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    Shape=models.CharField(max_length=255,default='')
    dtime=models.DateTimeField(auto_now_add=True)

############### LBaas Details ################################
class lbaas_details_table(models.Model):
    region_name=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    lbaas_id=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    ip_address=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)

class lbaas_details_table_monitoring(models.Model):
    region_name=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    lbaas_id=models.CharField(max_length=255)
    compartment_id=models.CharField(max_length=255)
    Pod_Name=models.CharField(max_length=255)
    ip_address=models.CharField(max_length=255)
    lifecycle_state=models.CharField(max_length=255)
    dtime=models.DateTimeField(auto_now_add=True)

############### Instance level Capacity details ################################
class cap_data(models.Model):
    Pod_Name=models.CharField(max_length=255)
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    cap_id=models.CharField(max_length=255)
    reserved_instance_count=models.CharField(max_length=255)
    used_instance_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)

class cap_data_monitoring(models.Model):
    Pod_Name=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    cap_id=models.CharField(max_length=255)
    reserved_instance_count=models.CharField(max_length=255)
    used_instance_count=models.CharField(max_length=255)
    percentage=models.FloatField(default=0)
    dtime=models.DateTimeField(auto_now_add=True)

########### Instance level Pod capacity details ###########
class pod_cap_data(models.Model):
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    cap_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    instance_shape=models.CharField(max_length=255)
    reserved_count=models.CharField(max_length=255)
    used_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    memory=models.CharField(max_length=255,default='')
    ocpus=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)

class pod_cap_data_monitoring(models.Model):
    region_name=models.CharField(max_length=255)
    availability_domain=models.CharField(max_length=255,default='')
    cap_id=models.CharField(max_length=255)
    display_name=models.CharField(max_length=255)
    instance_shape=models.CharField(max_length=255)
    reserved_count=models.CharField(max_length=255)
    used_count=models.CharField(max_length=255)
    free_count=models.CharField(max_length=255,default='')
    memory=models.CharField(max_length=255,default='')
    ocpus=models.CharField(max_length=255,default='')
    percentage=models.FloatField(default=0)
    dtime=models.DateTimeField(auto_now_add=True)
