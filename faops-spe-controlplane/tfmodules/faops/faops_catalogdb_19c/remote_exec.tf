resource "null_resource" "remote-exec" {
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${data.oci_core_vnic.catalogdb_node_vnic.private_ip_address}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/faops_catalogdb_configuration.sh"
      destination = "/tmp/faops_catalogdb_configuration.sh"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${data.oci_core_vnic.catalogdb_node_vnic.private_ip_address}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "sudo chmod 755 /tmp/faops_catalogdb_configuration.sh",
       "sudo chown oracle:oinstall /tmp/faops_catalogdb_configuration.sh",
       "sudo /tmp/faops_catalogdb_configuration.sh ${var.catalogdb_name} ${var.faops_cb_db_admin_password} ${var.recovery_file_dest_size}",
        ]
    }
}
