resource "null_resource" "remote-exec" {
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${module.faops_provutilvm.private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${var.bastion_ssh_private_key}"
        }
      source      = "../../../scripts/faops_provutilvm_postinstall.sh"
      destination = "/tmp/faops_postinstall.sh"
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${module.faops_provutilvm.private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${var.bastion_ssh_private_key}"
        }
     inline = [
       "chmod uga+x /tmp/faops_postinstall.sh",
       "/tmp/faops_postinstall.sh"
        ]
    }
}
