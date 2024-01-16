module "faops_psrtools_instances" {
  source = "../../../tfmodules/faops/faops_psrtools_instances"
  region = "${var.region}"
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


  dmz_compartment_id = "${module.svc_compartments.app_compartment_id}"
  app_compartment_id = "${module.svc_compartments.app_compartment_id}"

  svc_lb_subnet_ids = "${var.lcm_svc_lb_subnet_ids}"
  faops_mt_subnet_ids = "${var.faops_mt_subnet_ids}"

  ad_list = "${data.template_file.ad_names.*.rendered}"

  faops_psrtools_ad_indices = ["${split(",", length(var.faops_psrtools_ad_indices) == 0 ? join(",", local.faops_psrtools_ad_indices_map[var.realm]) : join(",", var.faops_psrtools_ad_indices))}"]
  faops_cb_mt_instance_shape = "${var.faops_cb_mt_instance_shape != "" ? var.faops_cb_mt_instance_shape : local.faops_cb_mt_instance_shapes_map[var.realm]}"

  faops_cb_mt_instance_custom_image_id = "${var.faops_cb_mt_instance_custom_image_id}"
  faops_psrtools_local_volume_size_in_gbs = "${var.faops_psrtools_local_volume_size_in_gbs != "" ? var.faops_psrtools_local_volume_size_in_gbs :  local.volume_size_in_gbs_map[var.realm]}"

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

output "FAOPS PSR TOOLS VM" {
  value = "${module.faops_psrtools_instances.faops_psrtools}"
}
