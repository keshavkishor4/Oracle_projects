module "faops_tf_buckets" {
  source = "../../../tfmodules/faops/faops_buckets/faops_tf_buckets/"
  realm = "${local.realm_enum}"
  tenancy_ocid = "${var.tenancy_ocid}"
  svc_app_compartment_id = "${module.svc_compartments.app_compartment_id}"
}

output "Buckets" {
  value = [
    "${module.faops_tf_buckets.faops_instances_terraform_bucket_name}"
  ]
}
