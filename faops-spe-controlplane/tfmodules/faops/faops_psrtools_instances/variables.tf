variable "tenancy_ocid" {}

variable "dmz_compartment_id" {}
variable "app_compartment_id" {}

variable "faops_cb_mt_instance_custom_image_id" {}

variable "svc_lb_subnet_ids" {
  type = "list"
}

variable "faops_mt_subnet_ids" {
  type = "list"
}

variable "realm" {}
variable "region" {}
variable "local_work_dir" {}
variable "is_dev_realm" {}
variable "faops_psrtools_local_volume_size_in_gbs" {}

// A list of AD names, which should usually correspond to the
// oci_identity_availability_domains data source.
variable "ad_list" {
  type = "list"
}

variable "ssh_public_key" {}
variable "ssh_private_key" {}
variable "ssh_private_key_path" {}

variable "bastion_user" {}
variable "bastion_ssh_private_key" {}
variable "bastion_ssh_private_key_path" {}
variable "bastion_public_ip" {}


variable "faops_cb_mt_instance_shape" {}

variable "faops_psrtools_ad_indices" {
  type = "list"
}

variable "http_proxy" {}
variable "https_proxy" {}

variable "server" {}
// Powerbroker
variable "is_idcs_enabled" { default = false }
variable "idcs_host" {}
variable "idcs_apppass" {}
variable "idcs_appid" {}
variable "is_pb_enabled" { default = false }
variable "pb_lb_addr" {}
variable "pb_access_conf" {}
