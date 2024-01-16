
data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_sopsvm" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_sopsvm"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_sopsvm_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_sopsvm.id}"
}

output "faops_sopsvm_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_sopsvm.name}"
}

resource "oci_objectstorage_bucket" "faops_sopsvm_archive" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_sopsvm_ARCHIVE"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
  storage_tier = "Archive"
}

output "faops_sopsvm_archive_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_sopsvm_archive.id}"
}

output "faops_sopsvm_archive_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_sopsvm_archive.name}"
}
