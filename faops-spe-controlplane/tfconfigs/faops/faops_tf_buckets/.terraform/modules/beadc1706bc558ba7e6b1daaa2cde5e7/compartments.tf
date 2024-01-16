resource "oci_identity_compartment" "this" {
  count = "${var.read_only ? 0 : 1}"
  name        = "${var.compartment_name}"
  description = "${var.compartment_description}"
}

data "oci_identity_compartments" "this" {
  count = "${var.read_only ? 1 : 0}"
  compartment_id = "${var.tenancy_ocid}"
  filter {
    name   = "name"
    values = ["${var.compartment_name}"]
  }
}

locals {
  compartment_ids = "${concat(flatten(data.oci_identity_compartments.this.*.compartments), list(map("id", "")))}"
}

output "compartment_id" {
  // This allows the compartment ID to be retrieved from the resource if it exists, and if not to use the data source.
  value = "${var.read_only ? lookup(local.compartment_ids[0], "id") : element(concat(oci_identity_compartment.this.*.id, list("")), 0)}"
}

output "compartment_name" {
  value = "${var.compartment_name}"
}
