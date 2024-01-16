resource "oci_core_instance" "linux_instance" {

  "availability_domain" = "${var.ad_list[var.ad_indices[count.index]]}"
  "compartment_id"      = "${var.compartment_id}"
  "display_name"        = "${var.instance_display_name}_${count.index+1}"
  "source_details"      = {
    "source_id"   = "${var.image_id}"
    "source_type" = "image"
  }
  "shape"               = "${var.shape}"
  "count"               = "${length(var.ad_indices)}"

  "create_vnic_details" {
    "subnet_id"              = "${var.subnet_ids[var.ad_indices[count.index]]}"
    "skip_source_dest_check" = "${var.skip_source_dest_check}"
    "hostname_label"      = "${lower(format("%.15s", format("%s%d", var.instance_hostname_label, count.index+1)))}"
    "assign_public_ip"       = "${var.assign_public_ip}"
  }

  "metadata" = {
    "ssh_authorized_keys" = "${var.ssh_public_key}"
    "user_data"           = "${base64encode(file(var.user_data_file)) }"
  }

  "extended_metadata" = {
    "EnableIDCS" = "${var.is_idcs_enabled}"
    "idcs_host" = "${var.idcs_host}"
    "idcs_apppass" = "${var.idcs_apppass}"
    "idcs_appid" = "${var.idcs_appid}"
    "EnablePB" = "${var.is_pb_enabled}"
    "pb_lb_addr" = "${var.pb_lb_addr}"
    "access_conf" = "${var.pb_access_conf}"
  }

  "timeouts" = {
    "create" = "60m"
  }
}

resource "oci_core_volume" "linux_blocks" {
  "availability_domain" = "${var.ad_list[var.ad_indices[count.index]]}"
  "compartment_id"      = "${var.compartment_id}"
  "count"               = "${length(var.volume_mount_directory) > 1 ? length(var.ad_indices) : 0 }"
  "display_name"        = "${var.volume_mount_directory}"
  "size_in_gbs"         = "${var.volume_size_in_gbs}"
}

resource "oci_core_volume_attachment" "linux_blocks_attach" {
  "attachment_type" = "iscsi"
  "count"           = "${length(var.volume_mount_directory) > 1 ? length(var.ad_indices) : 0 }"
  # "compartment_id"  = "${var.compartment_id}"
  "instance_id"     = "${element(oci_core_instance.linux_instance.*.id, count.index)}"
  "volume_id"       = "${element(oci_core_volume.linux_blocks.*.id, count.index)}"
     /*
      * This is a temporary workaround for environments where remote-exec cannot be used.
      */
  provisioner "local-exec" {
     command = "bash ../../../scripts/create_drive.sh"

     environment {
        PRIVATE_KEY = "${var.ssh_private_key_path}"
        BASTION_PRIVATE_KEY = "${var.bastion_ssh_private_key_path}"
        BASTION_HOST = "${var.bastion_public_ip}"
        BASTION_USER = "${var.bastion_user}"
        REMOTE_HOST = "${element(oci_core_instance.linux_instance.*.private_ip, count.index)}"
        IQN = "${self.iqn}"
        IPV4 = "${self.ipv4}"
        PORT = "${self.port}"
        MOUNT = "${var.volume_mount_directory}"
     }
  }

/*
  provisioner "remote-exec" {
    connection = {
      timeout      = "5m"_
      host         = "${length(var.bastion_public_ip) > 7 ? element(oci_core_instance.linux_instance.*.private_ip, count.index) : element(oci_core_instance.linux_instance.*.public_ip, count.index)}"
      private_key = "${var.ssh_private_key}"
      bastion_host = "${var.bastion_public_ip}"
      bastion_user = "${var.bastion_user}"
      bastion_private_key = "${var.bastion_ssh_private_key}"
      user         = "opc"
      agent        = false
    }

    inline = [
      "sudo -s bash -c 'iscsiadm -m node -o new -T ${self.iqn} -p ${self.ipv4}:${self.port}'",
      "sudo -s bash -c 'iscsiadm -m node -o update -T ${self.iqn} -n node.startup -v automatic '",
      "sudo -s bash -c 'iscsiadm -m node -T ${self.iqn} -p ${self.ipv4}:${self.port} -l '",
      "sudo -s bash -c 'mkfs.ext4 -F /dev/sdb'",
      "sudo -s bash -c 'mkdir -p ${var.volume_mountdirectory}'",
      "sudo -s bash -c 'mount -t ext4 /dev/sdb ${var.volume_mount_directory} '",
      "echo '/dev/sdb  ${var.volume_mount_directory} ext4 defaults,noatime,_netdev,nofail    0   2' | sudo tee --append /etc/fstab > /dev/null",
    ]
  }
*/
}
