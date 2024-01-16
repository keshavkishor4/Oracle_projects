from django.contrib import admin

# Register your models here.
from .models import Stamp_Pod_Report
from .models import Stamp_Pod_Report_monitoring
from .models import pod_basic_data
from .models import pod_basic_data_monitoring
from .models import pod_instance_details
from .models import pod_instance_details_monitoring
from .models import region_level_capacity_table
from .models import region_level_capacity_table_monitoring
from .models import no_capacity_region_list
from .models import no_capacity_region_list_monitoring
from .models import unable_to_fetch_region_list
from .models import unable_to_fetch_region_list_monitoring
from .models import capacity_reservation_level_capacity_details
from .models import capacity_reservation_level_capacity_details_monitoring
from .models import Manual_Pod_Report
from .models import Manual_Pod_Report_monitoring
from .models import inst_full_data
from .models import inst_full_data_monitoring
from .models import cap_data
from .models import cap_data_monitoring
from .models import pod_cap_data
from .models import pod_cap_data_monitoring
from .models import exa_data_info
from .models import exa_data_info_monitoring
from .models import lbaas_details_table
from .models import lbaas_details_table_monitoring
from .models import full_pod_data
from .models import full_pod_data_monitoring
from .models import lbaas_data_table
from .models import lbaas_data_table_monitoring
from .models import exanode_info
from .models import exanode_info_monitoring

class exanode_info_admin(admin.ModelAdmin):
    list_display = ('hostname','role','type_of_hw','datacenter_code','uuid','instance_ocid','serial_number','kernel_version','cpu_model','os_version','ip_address','product_name','environment')

class exanode_info_admin_monitoring(admin.ModelAdmin):
    list_display = ('hostname','role','type_of_hw','datacenter_code','uuid','instance_ocid','serial_number','kernel_version','cpu_model','os_version','ip_address','product_name','environment','dtime')

class lbaas_data_table_admin(admin.ModelAdmin):
    list_display = ('region_name','display_name','lbaas_id','compartment_id','lifecycle_state','maximum_bandwidth_in_mbps','minimum_bandwidth_in_mbps','subnet_ids','shape_name','ip_address')

class lbaas_data_table_admin_monitoring(admin.ModelAdmin):
    list_display = ('region_name','display_name','lbaas_id','compartment_id','lifecycle_state','maximum_bandwidth_in_mbps','minimum_bandwidth_in_mbps','subnet_ids','shape_name','ip_address','dtime')

class full_pod_data_admin(admin.ModelAdmin):
    list_display = ('Pod_Name','name','value')

class full_pod_data_admin_monitoring(admin.ModelAdmin):
    list_display = ('Pod_Name','name','value','dtime')

class lbaas_details_table_admin(admin.ModelAdmin):
    list_display = ('region_name','display_name','lbaas_id','compartment_id','Pod_Name','ip_address','lifecycle_state')

class lbaas_details_table_admin_monitoring(admin.ModelAdmin):
    list_display = ('region_name','display_name','lbaas_id','compartment_id','Pod_Name','ip_address','lifecycle_state','dtime')

class stamp_pod_report(admin.ModelAdmin):
    list_display = ('request_data','fm_date','Pod_Name','customer_name','bugs','bug_creation_date','resize_type','execution_type','resize_reason','environment_type','pod_architecture','fresh_p_or_u','next_rel_date','next_rel_version','current_release','data_center','environment_region_name','old_shape','new_shape','pod_size','hw_map')

class stamp_pod_report_monitoring(admin.ModelAdmin):
    list_display = ('request_data','fm_date','Pod_Name','customer_name','bugs','bug_creation_date','resize_type','execution_type','resize_reason','environment_type','pod_architecture','fresh_p_or_u','next_rel_date','next_rel_version','current_release','data_center','environment_region_name','old_shape','new_shape','pod_size','hw_map','dtime')

class pod_basic_dta(admin.ModelAdmin):
    list_display = ('Pod_Name','dr_role','physical_pod_name','service','last_updated','datacenter_code','dc_short_name','associated_dr_peer','peer_physical_pod_name','id_name','fusion_service_name','status','pod_type','release','customer_name','golden_gate_enabled','fm_datacenter')

class pod_basic_dta_monitoring(admin.ModelAdmin):
    list_display = ('Pod_Name','dr_role','physical_pod_name','service','last_updated','datacenter_code','dc_short_name','associated_dr_peer','peer_physical_pod_name','id_name','fusion_service_name','status','pod_type','release','customer_name','golden_gate_enabled','fm_datacenter','dtime')

class Pod_Instance_Details(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','systemtype','pod_host','compartment_id','instance_id')

class Pod_Instance_Details_monitoring(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','systemtype','pod_host','compartment_id','instance_id','dtime')

class region_level_capacity_list(admin.ModelAdmin):
    list_display = ('region_name','availability_domain','display_name','cap_id','reserved_instance_count','used_instance_count','percentage')

class region_level_capacity_list_monitoring(admin.ModelAdmin):
    list_display = ('region_name','availability_domain','display_name','cap_id','reserved_instance_count','used_instance_count','percentage','dtime')

class no_capacity_region_list_data(admin.ModelAdmin):
    list_display = ('region','result')

class no_capacity_region_list_data_monitoring(admin.ModelAdmin):
    list_display = ('region','result','dtime')

class unable_to_fetch_region_list_data(admin.ModelAdmin):
    list_display = ('region','result')

class unable_to_fetch_region_list_data_monitoring(admin.ModelAdmin):
    list_display = ('region','result','dtime')

class capacity_reservation_level_capacity_details_data(admin.ModelAdmin):
    list_display = ('region_name','cap_id','display_name','instance_shape','reserved_count','used_count','memory','ocpus','percentage')

class capacity_reservation_level_capacity_details_data_monitoring(admin.ModelAdmin):
    list_display = ('region_name','cap_id','display_name','instance_shape','reserved_count','used_count','memory','ocpus','percentage','dtime')

class manual_pod_report_data(admin.ModelAdmin):
    list_display = ('fm_date','Pod_Name','customer_name','bugs','resize_type','execution_type','resize_reason','environment_type','pod_architecture','next_rel_date','next_rel_version','current_release','data_center','environment_region_name','old_shape','new_shape','pod_size','hw_map')

class manual_pod_report_data_monitoring(admin.ModelAdmin):
    list_display = ('fm_date','Pod_Name','customer_name','bugs','resize_type','execution_type','resize_reason','environment_type','pod_architecture','next_rel_date','next_rel_version','current_release','data_center','environment_region_name','old_shape','new_shape','pod_size','hw_map','dtime')

class instance_full_data_admin(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','instance_id','availability_domain','capacity_reservation_id','dedicated_vm_host_id','display_name','fault_domain','lifecycle_state','shape')

class instance_full_data_admin_monitoring(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','instance_id','availability_domain','capacity_reservation_id','dedicated_vm_host_id','display_name','fault_domain','lifecycle_state','shape','dtime')

class cap_data_admin(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','availability_domain','display_name','cap_id','reserved_instance_count','used_instance_count','percentage')

class cap_data_admin_monitoring(admin.ModelAdmin):
    list_display = ('Pod_Name','region_name','availability_domain','display_name','cap_id','reserved_instance_count','used_instance_count','percentage','dtime')

class pod_cap_data_admin(admin.ModelAdmin):
    list_display = ('region_name','cap_id','display_name','instance_shape','reserved_count','used_count','memory','ocpus','percentage')

class pod_cap_data_admin_monitoring(admin.ModelAdmin):
    list_display = ('region_name','cap_id','display_name','instance_shape','reserved_count','used_count','memory','ocpus','percentage','dtime')

class exa_data_info_admin(admin.ModelAdmin):
    list_display = ('exa_node','Pod_Name')

class exa_data_info_monitoring_admin(admin.ModelAdmin):
    list_display = ('exa_node','Pod_Name','dtime')



admin.site.register(exanode_info,exanode_info_admin)
admin.site.register(exanode_info_monitoring,exanode_info_admin_monitoring)
admin.site.register(full_pod_data,full_pod_data_admin)
admin.site.register(full_pod_data_monitoring,full_pod_data_admin_monitoring)
admin.site.register(pod_instance_details,Pod_Instance_Details)
admin.site.register(pod_instance_details_monitoring,Pod_Instance_Details_monitoring)
admin.site.register(Stamp_Pod_Report,stamp_pod_report)
admin.site.register(Stamp_Pod_Report_monitoring,stamp_pod_report_monitoring)
admin.site.register(pod_basic_data,pod_basic_dta)
admin.site.register(pod_basic_data_monitoring,pod_basic_dta_monitoring)
admin.site.register(region_level_capacity_table,region_level_capacity_list)
admin.site.register(region_level_capacity_table_monitoring,region_level_capacity_list_monitoring)
admin.site.register(no_capacity_region_list,no_capacity_region_list_data)
admin.site.register(no_capacity_region_list_monitoring,no_capacity_region_list_data_monitoring)
admin.site.register(unable_to_fetch_region_list,unable_to_fetch_region_list_data)
admin.site.register(unable_to_fetch_region_list_monitoring,unable_to_fetch_region_list_data_monitoring)
admin.site.register(capacity_reservation_level_capacity_details,capacity_reservation_level_capacity_details_data)
admin.site.register(capacity_reservation_level_capacity_details_monitoring,capacity_reservation_level_capacity_details_data_monitoring)
admin.site.register(Manual_Pod_Report,manual_pod_report_data)
admin.site.register(Manual_Pod_Report_monitoring,manual_pod_report_data_monitoring)
admin.site.register(cap_data,cap_data_admin)
admin.site.register(cap_data_monitoring,cap_data_admin_monitoring)
admin.site.register(pod_cap_data,pod_cap_data_admin)
admin.site.register(pod_cap_data_monitoring,pod_cap_data_admin_monitoring)
admin.site.register(exa_data_info,exa_data_info_admin)
admin.site.register(exa_data_info_monitoring,exa_data_info_monitoring_admin)
admin.site.register(lbaas_details_table,lbaas_details_table_admin)
admin.site.register(lbaas_data_table,lbaas_data_table_admin)
admin.site.register(lbaas_details_table_monitoring,lbaas_details_table_admin_monitoring)
admin.site.register(lbaas_data_table_monitoring,lbaas_data_table_admin_monitoring)
