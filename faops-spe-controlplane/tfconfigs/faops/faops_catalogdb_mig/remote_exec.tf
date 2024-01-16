module "faops_remote_exec" {
  source = "../../../tfmodules/faops/faops_catalogdb_mig"
  bastion_ssh_private_key_path  ="${var.bastion_ssh_private_key_path}"
  ssh_private_key = "${chomp(file(var.ssh_private_key_path))}"
  bastion_public_ip             ="${var.lcm_bastion_public_ip}"
  bastion_user                  ="${var.bastion_user}"
  faops_19c_private_ip          ="${var.faops_19c_private_ip}"
  faops_12c_private_ip          ="${var.faops_12c_private_ip}"
  faops_cb_mt_private_ips       ="${var.faops_cb_mt_private_ips}"
  faops_cb_db_user_password       ="${var.faops_cb_db_user_password}"
}