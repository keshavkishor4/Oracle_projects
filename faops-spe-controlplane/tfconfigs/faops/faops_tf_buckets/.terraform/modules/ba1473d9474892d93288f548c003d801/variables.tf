variable "tenancy_ocid" {}

// Examples: prd, ppd, dev, tst
variable "realm" {
  default = "dev"
}

variable "stack_name" {}

variable "service_identifier" {}

// If true, data will be returned about the compartments if they exists, and the user is only required to have
// read permissions. If not found, then an empty string will be returned for the compartment IDs.
// If false, the compartments will be managed by this module, and the user must have write permissions.
variable "read_only" {
  default = true
}

locals {
  app_compartment_name = "${lower(var.realm)}_${lower(var.service_identifier)}_${lower(var.stack_name)}_app"
  data_compartment_name = "${lower(var.realm)}_${lower(var.service_identifier)}_${lower(var.stack_name)}_data"
}
