
variable "is_dev_realm" {}

variable "lcm_vcn_cidr" {}

locals {
  // Assuming that the VCN is /16
  // Each tier has /19, with a possibility for 8 tiers.
  dmz_tier_prefix = "${cidrsubnet(var.lcm_vcn_cidr, 3, 0)}"
  app_tier_prefix = "${cidrsubnet(var.lcm_vcn_cidr, 3, 1)}"
  mgmt_db_tier_prefix = "${cidrsubnet(var.lcm_vcn_cidr, 3, 2)}"
  pod_db_tier_prefix = "${cidrsubnet(var.lcm_vcn_cidr, 3, 3)}"
  svc_db_tier_prefix = "${cidrsubnet (var.lcm_vcn_cidr, 3, 4)}"
  svc_app_tier_prefix = "${cidrsubnet (var.lcm_vcn_cidr, 3, 5)}"
  sandbox_tier_prefix = "${cidrsubnet (var.lcm_vcn_cidr, 3, 6)}"


  // Each DMZ subnet family has /22, with option for 9 subnet families.
  // Each subnet family usually has one subnet per AD.
  // If using the default subnet_family_cidr_offset of 3, then
  // each subnet will get /25 (128 addresses).
  lb_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 0)}"
  bastion_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 1)}"
  scanner_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 2)}"
  svc_lb_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 3)}"
  proxy_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 4)}"
  proxy_lb_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 5)}"
  ops_bastion_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 6)}"
  security_proxy_subnet_family_prefix = "${cidrsubnet(local.dmz_tier_prefix, 3, 7)}"



  em_db_frontend_subnet_family_prefix = "${cidrsubnet(local.svc_db_tier_prefix, 5, 0)}"
  em_db_backend_subnet_family_prefix = "${cidrsubnet(local.svc_db_tier_prefix, 5, 1)}"

  em_oms_subnet_family_prefix = "${cidrsubnet(local.svc_app_tier_prefix, 5, 0)}"

  //--start-- faops subnet entries - BUG 28633474 -- 07Feb2019
  faops_db_frontend_subnet_family_prefix = "${cidrsubnet(local.svc_db_tier_prefix, 5, 3)}"
  faops_db_backend_subnet_family_prefix = "${cidrsubnet(local.svc_db_tier_prefix, 5, 4)}"
  faops_mt_subnet_family_prefix = "${cidrsubnet(local.svc_app_tier_prefix, 5, 3)}"
  // --end-- faops subnet entries - BUG 28633474 -- 07Feb2019

  mcollective_subnet_family_prefix = "${cidrsubnet(local.svc_app_tier_prefix, 5, 1)}"

  jenkins_oci_instances_subnet_family_prefix = "${cidrsubnet(local.sandbox_tier_prefix, 2, 0)}"

  pod_manager_subnet_family_prefix = "${cidrsubnet(local.app_tier_prefix, 3, 0)}"

  mgmt_db_frontend_subnet_family_prefix = "${var.is_dev_realm ? cidrsubnet(local.mgmt_db_tier_prefix, 2, 0) : cidrsubnet(local.mgmt_db_tier_prefix, 4, 0)}"
  mgmt_db_backend_subnet_family_prefix = "${var.is_dev_realm ? cidrsubnet(local.mgmt_db_tier_prefix, 2, 1) : cidrsubnet(local.mgmt_db_tier_prefix, 4, 1)}"

  pod_db_frontend_subnet_family_prefix = "${cidrsubnet(local.pod_db_tier_prefix, 1, 0)}"
  pod_db_backend_subnet_family_prefix = "${cidrsubnet(local.pod_db_tier_prefix, 1, 1)}"
}

output "em_db_frontend_subnet_family_prefix" {
  value = "${local.em_db_frontend_subnet_family_prefix}"
}

output "em_db_backend_subnet_family_prefix" {
  value = "${local.em_db_backend_subnet_family_prefix}"
}

// --start-- faops output entries - BUG 28633474 -- 07Feb2019
output "faops_db_frontend_subnet_family_prefix" {
  value = "${local.faops_db_frontend_subnet_family_prefix}"
}
output "faops_db_backend_subnet_family_prefix" {
  value = "${local.faops_db_backend_subnet_family_prefix}"
}
output "faops_mt_subnet_family_prefix" {
  value = "${local.faops_mt_subnet_family_prefix}"
}
// --end-- faops output entries - BUG 28633474 -- 07Feb2019

output "mcollective_subnet_family_prefix" {
  value = "${local.mcollective_subnet_family_prefix}"
}

output "jenkins_oci_instances_subnet_family_prefix" {
  value = "${local.jenkins_oci_instances_subnet_family_prefix}"
}

output "em_oms_subnet_family_prefix" {
  value = "${local.em_oms_subnet_family_prefix}"
}

output "proxy_subnet_family_prefix" {
  value = "${local.proxy_subnet_family_prefix}"
}

output "proxy_lb_subnet_family_prefix" {
  value = "${local.proxy_lb_subnet_family_prefix}"
}

output "svc_lb_subnet_family_prefix" {
  value = "${local.svc_lb_subnet_family_prefix}"
}

output "lb_subnet_family_prefix" {
  value = "${local.lb_subnet_family_prefix}"
}

output "bastion_subnet_family_prefix" {
  value = "${local.bastion_subnet_family_prefix}"
}

output "ops_bastion_subnet_family_prefix" {
  value = "${local.ops_bastion_subnet_family_prefix}"
}

output "security_proxy_subnet_family_prefix" {
  value = "${local.security_proxy_subnet_family_prefix}"
}

output "scanner_subnet_family_prefix" {
  value = "${local.scanner_subnet_family_prefix}"
}

output "pod_manager_subnet_family_prefix" {
  value = "${local.pod_manager_subnet_family_prefix}"
}

output "mgmt_db_frontend_subnet_family_prefix" {
  value = "${local.mgmt_db_frontend_subnet_family_prefix}"
}

output "mgmt_db_backend_subnet_family_prefix" {
  value = "${local.mgmt_db_backend_subnet_family_prefix}"
}

output "pod_db_frontend_subnet_family_prefix" {
  value = "${local.pod_db_frontend_subnet_family_prefix}"
}

output "pod_db_backend_subnet_family_prefix" {
  value = "${local.pod_db_backend_subnet_family_prefix}"
}
