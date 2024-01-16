data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_provutilvm" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_provutilvm"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_provutilvm_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_provutilvm.id}"
}

output "faops_provutilvm_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_provutilvm.name}"
}

resource "oci_objectstorage_bucket" "faops_provutilvm_archive" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_provutilvm_ARCHIVE"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
  storage_tier = "Archive"
}

output "faops_provutilvm_archive_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_provutilvm_archive.id}"
}

output "faops_provutilvm_archive_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_provutilvm_archive.name}"
}
