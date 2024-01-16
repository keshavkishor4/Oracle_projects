
module "faops_sopsutilvm" {
  source = "../../../tfmodules/linux_instance_faops/psr"
  compartment_id= "${var.app_compartment_id}"
  instance_display_name = "${var.server}_sopsutilvm"
  instance_hostname_label = "${var.server}sopsutilvm"
  ad_list = "${var.ad_list}"
  subnet_ids = "${var.faops_mt_subnet_ids}"
  ad_indices = "${var.faops_sopsutilvm_ad_indices}"
  volume_mount_directory = "/u01"
  volume_size_in_gbs = "${var.faops_sopsutilvm_local_volume_size_in_gbs}"
  shape = "${var.faops_cb_mt_instance_shape}"
  image_id = "${var.faops_cb_mt_instance_custom_image_id}"
  skip_source_dest_check = false
  assign_public_ip = false
  bastion_public_ip = "${var.bastion_public_ip}"
  user_data_file = "../../../resources/common_user_data.tpl"
  ssh_public_key = "${var.ssh_public_key}"
  ssh_private_key = "${var.ssh_private_key}"
  ssh_private_key_path = "${var.ssh_private_key_path}"
  bastion_ssh_private_key = "${var.bastion_ssh_private_key}"
  bastion_ssh_private_key_path = "${var.bastion_ssh_private_key_path}"
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

output "faops_sopsutilvm" {
  value = ["${formatlist("%s: %s (%s)", module.faops_sopsutilvm.display_name, module.faops_sopsutilvm.private_ip, module.faops_sopsutilvm.availability_domain)}",]
}

output "faops_sopsutilvm_private_ips" {
  value = "${module.faops_sopsutilvm.private_ip}"
}
