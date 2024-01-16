
data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_instances_terraform" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_faops_instances_terraform"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_instances_terraform_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_instances_terraform.name}"
}
