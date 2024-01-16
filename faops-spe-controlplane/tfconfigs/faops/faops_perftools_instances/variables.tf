variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "private_key_password" {}

variable "local_work_dir" {}

variable "ssh_public_key_path" {}
variable "ssh_private_key_path" {}
variable "bastion_ssh_private_key_path" {}

variable "lcm_bastion_public_ip" {}


variable "is_dev_realm" {}

variable "lcm_svc_lb_subnet_ids" {
  type = "list"
}
variable "faops_mt_subnet_ids" {
  type = "list"
}

variable "faops_cb_mt_instance_shape" {
  default = ""
}

variable "faops_perftools_ad_indices" {
  type = "list"
  default = [0,1,2]
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

  faops_perftools_ad_indices_map = {
    prd = [0,1]
    ppd = [1]
    dev = [1]
    tst = [1]
  }

  faops_cb_mt_instance_shapes_map = {
    prd = "VM.Standard2.16"
    ppd = "VM.Standard2.2"
    dev = "VM.Standard2.2"
    tst = "VM.Standard2.2"
  }
  volume_size_in_gbs_map = {
    prd = "2048"
    ppd = "500"
    dev = "500"
    tst = "500"
  }
  # load_balancer_shapes_map = {
  #   prd = "400Mbps"
  #   ppd = "100Mbps"
  #   dev = "100Mbps"
  #   tst = "100Mbps"
  # }
}

variable "faops_perftools_lb_shape" {
  default = "100Mbps"
}

variable "lcm_management_load_balancer_shape" {
    default = ""
}
variable "faops_cb_ssl_ca_certificate_path" {}
variable "faops_cb_ssl_private_key_path" {}
variable "faops_cb_ssl_public_certificate_path" {}
variable "faops_cb_self_signed_certificate_name" {}

#This would need a change when the final health check url is finalized
variable "faops_perftools_8203_health_checker_url" {
    default = "/"
}
#This would need a change when the final health check url is finalized
variable "faops_perftools_8080_health_checker_url" {
    default = "/"
}
variable "faops_perftools_local_volume_size_in_gbs"  {
    default = ""
}
variable "faops_cb_mt_instance_custom_image_id" { default = "" }
variable "http_proxy" {}
variable "https_proxy" {}



variable "bastion_user" {}
variable "lcm_vcn_cidr" {}

module "lcm_network_ranges" {
  source = "../../../tfmodules/lcm_network_ranges"
  lcm_vcn_cidr = "${var.lcm_vcn_cidr}"
  is_dev_realm = "${var.is_dev_realm}"
}

locals {
  faops_mt_subnet_family_prefix = "${module.lcm_network_ranges.faops_mt_subnet_family_prefix}"
}

# variable "em_oms_9851_health_checker_url" { default = "/xmlpserver/services" }
# variable "em_oms_9851_response_regex" { default = "And now... Some Services" }

// Powerbroker
variable "is_idcs_enabled" { default = false }
variable "idcs_host" {}
variable "idcs_apppass" {}
variable "idcs_appid" {}
variable "is_pb_enabled" { default = false }
variable "pb_lb_addr" {}
variable "pb_access_conf" {}
