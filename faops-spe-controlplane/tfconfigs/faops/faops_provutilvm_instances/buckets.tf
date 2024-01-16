module "faops_provutilvm_buckets" {
  source = "../../../tfmodules/faops/faops_buckets/faops_provutilvm_buckets"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  server = "FAOPS"
  svc_app_compartment_id = "${module.svc_compartments.app_compartment_id}"
}

output "Buckets" {
  value = [
    "${module.faops_provutilvm_buckets.faops_provutilvm_bucket_name}",
    "${module.faops_provutilvm_buckets.faops_provutilvm_archive_bucket_name}",
  ]
}
