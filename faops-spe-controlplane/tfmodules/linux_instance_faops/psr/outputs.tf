output "instance_ids" {
  value = ["${oci_core_instance.linux_instance.*.id}"]
}

output "public_ip" {
  value = ["${oci_core_instance.linux_instance.*.public_ip}"]
}

output "private_ip" {
  value = ["${oci_core_instance.linux_instance.*.private_ip}"]
}

output "display_name" {
  value = ["${oci_core_instance.linux_instance.*.display_name}"]
}

output "availability_domain" {
  value = ["${oci_core_instance.linux_instance.*.availability_domain}"]
}