
data "oci_objectstorage_namespace" "ns" {}

resource "oci_objectstorage_bucket" "faops_perftools_db" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_PERFTOOLS_DB"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
}

output "faops_perftools_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_perftools_db.id}"
}

output "faops_perftools_db_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_perftools_db.name}"
}

resource "oci_objectstorage_bucket" "faops_perftools_archive" {
  compartment_id = "${var.svc_app_compartment_id}"
  name = "${upper(var.realm)}_${upper(var.server)}_PERFTOOLS_DB_ARCHIVE"
  namespace = "${data.oci_objectstorage_namespace.ns.namespace}"
  storage_tier = "Archive"
}

output "faops_perftools_db_archive_bucket_id" {
  value = "${oci_objectstorage_bucket.faops_perftools_archive.id}"
}

output "faops_perftools_db_archive_bucket_name" {
  value = "${oci_objectstorage_bucket.faops_perftools_archive.name}"
}
