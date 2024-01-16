
data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_sopsutilvm" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_sopsutilvm"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_sopsutilvm_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_sopsutilvm.id}"
}

output "faops_sopsutilvm_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_sopsutilvm.name}"
}

resource "oci_objectstorage_bucket" "faops_sopsutilvm_archive" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_sopsutilvm_ARCHIVE"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
  storage_tier = "Archive"
}

output "faops_sopsutilvm_archive_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_sopsutilvm_archive.id}"
}

output "faops_sopsutilvm_archive_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_sopsutilvm_archive.name}"
}
