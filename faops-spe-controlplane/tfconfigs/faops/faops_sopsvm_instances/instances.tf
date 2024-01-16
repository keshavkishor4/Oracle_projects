module "faops_sopsvm_instances" {
  source = "../../../tfmodules/faops/faops_sopsvm_instances"
  # region = "${var.region}"
  region = "${var.faops_sopsvm_region != "" ? var.faops_sopsvm_region : local.faops_sopsvm_region_map[var.realm]}"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  ssh_public_key = "${chomp(file(var.ssh_public_key_path))}"
  ssh_private_key = "${chomp(file(var.ssh_private_key_path))}"
  ssh_private_key_path = "${var.ssh_private_key_path}"
  bastion_ssh_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
  bastion_ssh_private_key_path = "${var.bastion_ssh_private_key_path}"
  bastion_public_ip = "${var.lcm_bastion_public_ip}"


  local_work_dir = "${var.local_work_dir}"
  is_dev_realm = "${var.is_dev_realm}"

  http_proxy = "${var.http_proxy}"
  https_proxy = "${var.https_proxy}"
# 
//LB
  faops_cb_ssl_ca_certificate = "${chomp(file(var.faops_cb_ssl_ca_certificate_path))}"
  faops_cb_ssl_private_key = "${chomp(file(var.faops_cb_ssl_private_key_path))}"
  faops_cb_ssl_public_certificate = "${chomp(file(var.faops_cb_ssl_public_certificate_path))}"
  faops_cb_self_signed_certificate_name = "${var.faops_cb_self_signed_certificate_name}"
  faops_sopsvm_8203_health_checker_url = "${var.faops_sopsvm_8203_health_checker_url}"
  faops_sopsvm_8080_health_checker_url = "${var.faops_sopsvm_8080_health_checker_url}"

  local_work_dir = "${var.local_work_dir}"
  is_dev_realm = "${var.is_dev_realm}"

  http_proxy = "${var.http_proxy}"
  https_proxy = "${var.https_proxy}"

  # management_load_balancer_shape = "${var.lcm_management_load_balancer_shape != "" ? var.lcm_management_load_balancer_shape : local.load_balancer_shapes_map[var.realm]}"
  management_load_balancer_shape = "${var.faops_sops_lb_shape}"

  svc_lb_subnet_ids = "${var.lcm_svc_lb_subnet_ids}"
  faops_mt_subnet_ids = "${var.faops_mt_subnet_ids}"
  mgmt_lb_ad_index_1 = "${length(data.template_file.ad_names.*.rendered)>2?2:0}"
  mgmt_lb_ad_index_2 = "${length(data.template_file.ad_names.*.rendered)>2?1:0}"
# 

  dmz_compartment_id = "${module.svc_compartments.app_compartment_id}"
  app_compartment_id = "${module.svc_compartments.app_compartment_id}"

  svc_lb_subnet_ids = "${var.lcm_svc_lb_subnet_ids}"
  faops_mt_subnet_ids = "${var.faops_mt_subnet_ids}"

  ad_list = "${data.template_file.ad_names.*.rendered}"

  faops_sopsvm_ad_indices = ["${split(",", length(var.faops_sopsvm_ad_indices) == 0 ? join(",", local.faops_sopsvm_ad_indices_map[var.realm]) : join(",", var.faops_sopsvm_ad_indices))}"]
  faops_cb_mt_instance_shape = "${var.faops_cb_mt_instance_shape != "" ? var.faops_cb_mt_instance_shape : local.faops_cb_mt_instance_shapes_map[var.realm]}"

  faops_cb_mt_instance_custom_image_id = "${var.faops_cb_mt_instance_custom_image_id}"
  faops_sopsvm_local_volume_size_in_gbs = "${var.faops_sopsvm_local_volume_size_in_gbs != "" ? var.faops_sopsvm_local_volume_size_in_gbs :  local.volume_size_in_gbs_map[var.realm]}"

  server="FAOPS"

  bastion_user = "${var.bastion_user}"
  // Powerbroker
  is_idcs_enabled = "${var.is_idcs_enabled}"
  idcs_host= "${var.idcs_host}"
  idcs_apppass = "${var.idcs_apppass}"
  idcs_appid = "${var.idcs_appid}"
  is_pb_enabled = "${var.is_pb_enabled}"
  pb_lb_addr = "${var.pb_lb_addr}"
  pb_access_conf = "${var.pb_access_conf}"
}

output "FAOPS SOPS VM IP Address" {
  value = "${module.faops_sopsvm_instances.faops_sopsvm}"
}


output "FAOPS SOPS LB Public IP Address" {
  value = "${module.faops_sopsvm_instances.management_load_balancer_public_ip_address}"
}