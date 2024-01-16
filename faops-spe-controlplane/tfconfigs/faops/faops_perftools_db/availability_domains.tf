data "oci_identity_availability_domains" "ad" {
  compartment_id = "${var.tenancy_ocid}"
}

// The template file allows the AD names of all ADs to be passed as a list variable
// using: ${data.template_file.ad_names.*.rendered}
data "template_file" "ad_names" {
  count = "${length(data.oci_identity_availability_domains.ad.availability_domains)}"
  template = "${lookup(data.oci_identity_availability_domains.ad.availability_domains[count.index], "name")}"
}
