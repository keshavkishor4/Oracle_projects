
variable "region" {}
variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "ssh_private_key_path" {}
variable "bastion_ssh_private_key_path" {}
variable "private_key_path" {}
variable "lcm_bastion_public_ip" {}
variable "bastion_user" {}
variable "faops_19c_private_ip" {}
variable "faops_12c_private_ip" {}
variable "faops_cb_db_user_password" {}
variable "faops_cb_mt_private_ips" {
    type = "list"
}

// Must be one of: prd, ppd, dev, tst
variable "realm" {
  default = "dev"
}

locals {
  realm_map = {
    prd="prd"
    ppd="ppd"
    dev="dev"
    tst="tst"
  }

  realm_enum = "${local.realm_map[var.realm]}"
}