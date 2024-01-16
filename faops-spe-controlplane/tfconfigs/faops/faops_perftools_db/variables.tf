variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "private_key_password" {}

variable "bastion_ssh_private_key_path" {}
variable "bastion_user" {}

variable "lcm_bastion_public_ip" {}

variable "local_work_dir" {}

variable "ssh_public_key_path" {}
variable "ssh_private_key_path" {}

variable "faops_perf_db_shape" {
  default = "VM.Standard2.8"
}

variable "faops_cb_db_admin_password" {}
variable "faops_cb_db_user_password" {}

variable "faops_db_frontend_subnet_ids" {
  type = "list"
}
variable "faops_db_backend_subnet_ids" {
  type = "list"
}

variable "faops_cb_db_ad" {
  default = 0
}

variable "region" {}

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

variable "recovery_file_dest_size" {
    default = "100G"
}
