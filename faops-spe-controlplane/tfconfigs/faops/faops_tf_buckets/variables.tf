variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "private_key_password" {}

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
variable "is_dev_realm" {}
