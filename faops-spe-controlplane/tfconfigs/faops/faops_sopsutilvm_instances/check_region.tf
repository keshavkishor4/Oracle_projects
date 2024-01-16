resource "null_resource" "check_region" {
  count = "${local.region_check}"
  "ERROR: you cannot run this module in ${var.region}" = true
}
