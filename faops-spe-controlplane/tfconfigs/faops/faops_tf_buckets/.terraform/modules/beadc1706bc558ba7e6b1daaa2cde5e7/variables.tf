variable "tenancy_ocid" {}
variable "compartment_name" {}

// The description is only used if read_only = false.
variable "compartment_description" {
  default = ""
}

// If true, data will be returned about the compartment if it exists, and the user is only required to have
// read permissions. If not found, then an empty string will be returned for the compartment ID.
// If false, the compartment will be managed by this module, and the user must have write permissions to
// the compartment.
variable "read_only" {
  default = true
}
