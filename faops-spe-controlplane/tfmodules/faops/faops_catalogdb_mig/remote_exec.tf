resource "null_resource" "remote-exec_stop_container" {
    count = "${length(var.faops_cb_mt_private_ips)}"
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${element(var.faops_cb_mt_private_ips, count.index)}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/stop_mt_container.sh"
      destination = "/tmp/stop_mt_container.sh"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${element(var.faops_cb_mt_private_ips, count.index)}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/stop_mt_container.sh",
       "sudo /tmp/stop_mt_container.sh"
        ]
    }
}

resource "null_resource" "remote-exec_pre_clean_up" {
    depends_on = ["null_resource.remote-exec_stop_container"]
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/pre_clean_up.sh"
      destination = "/tmp/pre_clean_up.sh"
    }

    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/pre_clean_up.sh"
      destination = "/tmp/pre_clean_up.sh"
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/pre_clean_up.sh",
       "sudo /tmp/pre_clean_up.sh"
        ]
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/pre_clean_up.sh",
       "sudo /tmp/pre_clean_up.sh"
        ]
    }
}

resource "null_resource" "remote-exec_file_place" {
    depends_on = ["null_resource.remote-exec_pre_clean_up"]
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/db_tasks.zip"
      destination = "/tmp/db_tasks.zip"
    }

    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/db_tasks.zip"
      destination = "/tmp/db_tasks.zip"
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "cd /tmp",
       "unzip /tmp/db_tasks.zip",
       "chmod uga+x /tmp/pre_export_tasks.sh",
       "sudo /tmp/pre_export_tasks.sh"
        ]
    }

    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "cd /tmp",
       "unzip /tmp/db_tasks.zip",
       "chmod uga+x /tmp/pre_export_tasks.sh",
       "sudo /tmp/pre_export_tasks.sh"
        ]
    }
}

resource "null_resource" "remote-exec_cleanup_reco" {
    depends_on = ["null_resource.remote-exec_file_place"]
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/cleanup_reco.sh"
      destination = "/tmp/cleanup_reco.sh"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/cleanup_reco.sh",
       "sudo su - grid -c /tmp/cleanup_reco.sh",
        ]
    }
}

resource "null_resource" "remote-exec_export" {
    depends_on = ["null_resource.remote-exec_cleanup_reco"]
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/export_scripts.zip"
      destination = "/tmp/export_scripts.zip"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_12c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "cd /tmp",
       "unzip /tmp/export_scripts.zip",
       "chmod uga+x /tmp/export_faops_v2.sh",
       "chmod uga+x /tmp/scp_dumps.sh",
       "sudo su oracle -c /tmp/export_faops_v2.sh",
       "/tmp/scp_dumps.sh ${var.faops_19c_private_ip}"
        ]
    }
}

resource "null_resource" "remote-exec_import" {
    depends_on = ["null_resource.remote-exec_export"]
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/import_faops_v2.sh"
      destination = "/tmp/import_faops_v2.sh"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${var.faops_19c_private_ip}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/import_faops_v2.sh",
       "sudo su oracle -c '/tmp/import_faops_v2.sh apexpdb apexadmin ${var.faops_cb_db_user_password} T3JhY2xlIzEyM18='",
        "sudo cp -P /etc/ssh/sshd_config /etc/ssh/sshd_config.premig19c",
        "sudo systemctl restart sshd",
        "sudo pkill -u oraimp",
        "sudo userdel -f oraimp"
        ]
    }
}


resource "null_resource" "remote-exec_start_container" {
    depends_on = ["null_resource.remote-exec_import"]
    count = "${length(var.faops_cb_mt_private_ips)}"
    provisioner "file" {
      connection {
        user = "opc"
        agent = false
        private_key = "${var.ssh_private_key}"
        timeout = "10m"
        host = "${element(var.faops_cb_mt_private_ips, count.index)}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
      source      = "../../../scripts/start_mt_container.sh"
      destination = "/tmp/start_mt_container.sh"
    }

   
    provisioner "remote-exec" {
     connection {
        user = "opc"
        agent = false
        timeout = "10m"
        private_key = "${var.ssh_private_key}"
        host = "${element(var.faops_cb_mt_private_ips, count.index)}"
        bastion_host = "${var.bastion_public_ip}"
        bastion_user = "${var.bastion_user}"
        bastion_private_key = "${chomp(file(var.bastion_ssh_private_key_path))}"
        }
     inline = [
       "chmod uga+x /tmp/start_mt_container.sh",
       "sudo /tmp/start_mt_container.sh",
       "sudo docker exec faopscbapi cp /u01/faopscbnode/public/scripts/db_tasks.sh /u01/faopscbnode/public/scripts/db_tasks.sh_backup",
       "sudo docker exec faopscbapi sed -i -e 's#faopscbdbhost#faopscatalogdbhost#g' /u01/faopscbnode/public/scripts/db_tasks.sh",
       "sudo /tmp/stop_mt_container.sh",
       "sudo /tmp/start_mt_container.sh"
        ]
    }
}