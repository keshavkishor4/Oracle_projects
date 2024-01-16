

resource "null_resource" "configure_docker" {
  count = "${length(var.faops_cb_mt_private_ips)}"
  provisioner "file" {
       connection {
              user = "opc"
              agent = false
              private_key = "${chomp(file(var.ssh_private_key_path))}"
              timeout = "10m"
              host = "${element(var.faops_cb_mt_private_ips, count.index)}"
              bastion_host = "${var.lcm_bastion_public_ip}"
              bastion_user = "${var.bastion_user}"
              bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
       }
      source      = "../../../scripts/faops_cb_docker_install.sh"
      destination = "/tmp/faops_cb_docker_install.sh"
  }
  provisioner "remote-exec" {
        connection {
              user = "opc"
              agent = false
              private_key = "${chomp(file(var.ssh_private_key_path))}"
              timeout = "10m"
              host = "${element(var.faops_cb_mt_private_ips, count.index)}"
              bastion_host = "${var.lcm_bastion_public_ip}"
              bastion_user = "${var.bastion_user}"
              bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
       }
         inline = [
           "chmod uga+x /tmp/faops_cb_docker_install.sh",
           "sudo su - root -c \"/tmp/faops_cb_docker_install.sh \"",
            ]
  }
}

resource null_resource "download_containers" {
  depends_on = ["null_resource.configure_docker"]
  count = "${length(var.faops_cb_mt_private_ips)}"
  provisioner "file" {
       connection {
              user = "opc"
              agent = false
              private_key = "${chomp(file(var.ssh_private_key_path))}"
              timeout = "10m"
              host = "${element(var.faops_cb_mt_private_ips, count.index)}"
              bastion_host = "${var.lcm_bastion_public_ip}"
              bastion_user = "${var.bastion_user}"
              bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
       }
      source      = "../../../scripts/faops_cb_docker_initiate.sh"
      destination = "/tmp/faops_cb_docker_initiate.sh"
  }
  provisioner "remote-exec" {
        connection {
              user = "opc"
              agent = false
              private_key = "${chomp(file(var.ssh_private_key_path))}"
              timeout = "10m"
              host = "${element(var.faops_cb_mt_private_ips, count.index)}"
              bastion_host = "${var.lcm_bastion_public_ip}"
              bastion_user = "${var.bastion_user}"
              bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
       }
         inline = [
           "sudo su - root -c \"chmod uga+x /tmp/faops_cb_docker_initiate.sh\"",
           "sudo su - root -c \"docker ps\"",
           "sudo su - root -c \"sh /tmp/faops_cb_docker_initiate.sh ${var.faops_docker_repo} ${var.faops_docker_release_version} ${var.faops_apex_external_port} ${var.faops_apex_internal_port} ${var.faops_api_external_port} ${var.faops_api_internal_port} \"",
           "sudo su - root -c \"docker ps\""
            ]
  }
}