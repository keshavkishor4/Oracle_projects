module "faops_cb_db" {
  source = "../../../tfmodules/faops/faops_catalogdb_19c"
  region = "${var.region}"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  ssh_public_key = "${chomp(file(var.ssh_public_key_path))}"
  ssh_private_key = "${chomp(file(var.ssh_private_key_path))}"
  ssh_private_key_path = "${var.ssh_private_key_path}"
  bastion_ssh_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
  bastion_ssh_private_key_path = "${var.bastion_ssh_private_key_path}"

  faops_catalog_db_shape = "${var.faops_cb_db_shape}"
  local_work_dir = "${var.local_work_dir}"

  bastion_public_ip = "${var.lcm_bastion_public_ip}"

  faops_db_compartment_id = "${module.svc_compartments.data_compartment_id}"
  faops_catalogdb_backend_subnet_ids = "${var.faops_db_backend_subnet_ids}"
  faops_catalogdb_frontend_subnet_ids = "${var.faops_db_frontend_subnet_ids}"
  ad_list = "${data.template_file.ad_names.*.rendered}"
  faops_cb_db_admin_password = "${var.faops_cb_db_admin_password}"
  faops_cb_db_user_password = "${var.faops_cb_db_user_password}"
  recovery_file_dest_size = "${var.recovery_file_dest_size}"
  server="FAOPS"
  bastion_user = "${var.bastion_user}"
}

output "FAOPS CB DB Node" {
  value = ["${module.faops_cb_db.dbs}"]
}

output "FAOPS CB DBNode Domain Name" {
  value = ["${module.faops_cb_db.service_name}"]
}