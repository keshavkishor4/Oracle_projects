# Location of file system to mount. If left empty,
# no mount will be attempted and no disk will be allocated.
# NOTE: If a volume is requested for the VM, a private key must be provided.
variable "volume_mount_directory" {
  default = ""
}

variable "volume_size_in_gbs" {
  default = "50"
}

variable "shape" {}

variable "skip_source_dest_check" {
  default = false
}

variable "image_id" {}

variable "assign_public_ip" {
  default = "false"
}

variable "bastion_public_ip" {
  default = ""
}

variable "user_data_file" {
  default = ""
}

variable "ad_list" {
  type    = "list"
  default = []
}

variable "ad_indices" {
  type = "list"
}

variable "ssh_public_key" {}
variable "ssh_private_key" {}
variable "ssh_private_key_path" {}
variable "bastion_ssh_private_key" {}
variable "bastion_ssh_private_key_path" {}


// Powerbroker
variable "is_idcs_enabled" { default = false }
variable "idcs_host" {}
variable "idcs_apppass" {}
variable "idcs_appid" {}
variable "is_pb_enabled" { default = false }
variable "pb_lb_addr" {}
variable "pb_access_conf" {}

variable "compartment_id" {}

variable "instance_display_name" {}

variable "instance_hostname_label" {}

variable "subnet_ids" {
  type    = "list"
  default = []
}

variable "bastion_user" {}