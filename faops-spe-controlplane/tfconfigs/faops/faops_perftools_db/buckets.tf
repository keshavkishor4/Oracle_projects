module "faops_perftoolsdb_buckets" {
  source = "../../../tfmodules/faops/faops_buckets/faops_perftoolsdb_buckets"
  realm = "${local.realm_enum}"
  server = "FAOPS"
  tenancy_ocid = "${var.tenancy_ocid}"
  svc_app_compartment_id = "${module.svc_compartments.app_compartment_id}"
}

output "Buckets" {
  value = [
    "${module.faops_perftoolsdb_buckets.faops_perftools_db_bucket_name}",
    "${module.faops_perftoolsdb_buckets.faops_perftools_db_archive_bucket_name}",
  ]
}
