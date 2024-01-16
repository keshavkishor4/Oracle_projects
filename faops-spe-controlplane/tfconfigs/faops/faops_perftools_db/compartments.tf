locals {
  service_identifier = "fa"
}

module "svc_compartments" {
  source = "../../../tfmodules/compartment_stack"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  service_identifier = "${local.service_identifier}"
  read_only = true
  stack_name = "svc"
}
