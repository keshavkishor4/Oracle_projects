variable "tenancy_ocid" {}

variable "faops_db_compartment_id" {}

variable "faops_catalogdb_frontend_subnet_ids" {
  type = "list"
}
variable "faops_catalogdb_backend_subnet_ids" {
  type = "list"
}

variable "realm" {}
variable "region" {}
variable "local_work_dir" {}

// A list of AD names, which should usually correspond to the
// oci_identity_availability_domains data source.
variable "ad_list" {
  type = "list"
}

variable "ssh_public_key" {}
variable "ssh_private_key" {}
variable "bastion_ssh_private_key" {}
variable "bastion_ssh_private_key_path" {}

variable "ssh_private_key_path" {}

variable "bastion_public_ip" {}
variable "bastion_user" {}

// 0-based index into var.ad_list
variable "faops_cb_catalogdb_ad" {
  default = 0
}

variable "faops_cb_db_admin_password" {}
variable "faops_cb_db_user_password" {}

variable "faops_catalog_db_shape" {}

variable "catalogdb_name" {
    default = "opscdb"
}

variable "pdb_name" {
    default = "pdbName"
}

variable "recovery_file_dest_size" {}
variable "is_rac" {
    default = true
}

variable "server" {}
