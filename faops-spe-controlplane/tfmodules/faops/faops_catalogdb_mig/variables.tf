variable "ssh_private_key" {}
variable "bastion_ssh_private_key_path" {}
variable "bastion_public_ip" {}
variable "bastion_user" {}
variable "faops_19c_private_ip" {}
variable "faops_12c_private_ip" {}
variable "faops_cb_db_user_password" {}
variable "faops_cb_mt_private_ips" {
    type = "list"
}