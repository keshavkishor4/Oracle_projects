module "faops_sopsutilvm_buckets" {
  source = "../../../tfmodules/faops/faops_buckets/faops_sopsutilvm_buckets"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  server = "FAOPS"
  svc_app_compartment_id = "${module.svc_compartments.app_compartment_id}"
}

output "Buckets" {
  value = [
    "${module.faops_sopsutilvm_buckets.faops_sopsutilvm_bucket_name}",
    "${module.faops_sopsutilvm_buckets.faops_sopsutilvm_archive_bucket_name}",
  ]
}
