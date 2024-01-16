module "network" {
  source = "../compartment"
  tenancy_ocid = "${var.tenancy_ocid}"
  compartment_name = "${local.network_compartment_name}"
  compartment_description = "Networking resources for ${var.service_identifier}, ${var.realm} realm"
  read_only = "${var.read_only}"
}

output "network_compartment_id" {
  value = "${module.network.compartment_id}"
}

output "network_compartment_name" {
  value = "${local.network_compartment_name}"
}

module "app" {
  source = "../compartment"
  tenancy_ocid = "${var.tenancy_ocid}"
  compartment_name = "${local.app_compartment_name}"
  compartment_description = "App resources for ${var.service_identifier}, ${var.realm} realm"
  read_only = "${var.read_only}"
}

output "app_compartment_id" {
  value = "${module.app.compartment_id}"
}

output "app_compartment_name" {
  value = "${local.app_compartment_name}"
}

module "data" {
  source = "../compartment"
  tenancy_ocid = "${var.tenancy_ocid}"
  compartment_name = "${local.data_compartment_name}"
  compartment_description = "Data resources for ${var.service_identifier}, ${var.realm} realm"
  read_only = "${var.read_only}"
}

output "data_compartment_id" {
  value = "${module.data.compartment_id}"
}

output "data_compartment_name" {
  value = "${local.data_compartment_name}"
}

output "compartments" {
  value = [
    "${module.network.compartment_name}=\"${module.network.compartment_id}\"",
    "${module.app.compartment_name}=\"${module.app.compartment_id}\"",
    "${module.data.compartment_name}=\"${module.data.compartment_id}\"",
  ]
}


