
data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_psrtools" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_PSRTOOLS"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_psrtools_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_psrtools.id}"
}

output "faops_psrtools_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_psrtools.name}"
}

resource "oci_objectstorage_bucket" "faops_psrtools_archive" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_PSRTOOLS_ARCHIVE"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
  storage_tier = "Archive"
}

output "faops_psrtools_archive_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_psrtools_archive.id}"
}

output "faops_psrtools_archive_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_psrtools_archive.name}"
}
