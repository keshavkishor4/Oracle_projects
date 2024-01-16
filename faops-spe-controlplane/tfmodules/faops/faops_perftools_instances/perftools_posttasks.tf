resource "null_resource" "faops_perftools_post_install" {
    "count"           = "${length(var.faops_perftools_ad_indices)}"
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${element(module.faops_perftools.private_ip, count.index) }"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${var.bastion_ssh_private_key}"
        }
      source      = "../../../scripts/faops_perftools_post_install.sh"
      destination = "/tmp/faops_perftools_post_install.sh"
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${element(module.faops_perftools.private_ip, count.index) }"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${var.bastion_ssh_private_key}"
        }
     inline = [
       "chmod uga+x /tmp/faops_perftools_post_install.sh",
       "sudo su - root -c \"/tmp/faops_perftools_post_install.sh\""
        ]
    }
}
