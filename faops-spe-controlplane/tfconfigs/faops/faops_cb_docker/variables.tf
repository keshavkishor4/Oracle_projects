variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "region" {}
variable "region_key" {}
variable "ssh_private_key_path" {}
variable "bastion_ssh_private_key_path" {}
variable "faops_docker_repo" {}
variable "faops_docker_release_version" {}
variable "faops_apex_internal_port" { default = "8080"}
variable "faops_apex_external_port" { default = "8080" }
variable "faops_api_internal_port" { default = "8023"}
variable "faops_api_external_port" { default = "8023" }
variable "faops_cb_mt_private_ips" { type = "list" }
variable "lcm_bastion_public_ip" {}

variable "use_local_exec_workaround" {
  default = false
}
// Must be one of: prd, ppd, dev, tst
variable "realm" {
  default = "dev"
}

variable "bastion_user" { default = "opc" }