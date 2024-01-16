
resource "oci_database_db_system" "faops_catalogtools_catalogdb_system" {
  availability_domain = "${var.ad_list[var.faops_cb_catalogdb_ad]}"
  compartment_id = "${var.faops_db_compartment_id}"
  cpu_core_count = "2"
  database_edition = "ENTERPRISE_EDITION_EXTREME_PERFORMANCE"
  db_home {
    database {
      "admin_password" = "${var.faops_cb_db_admin_password}"
      "db_name" = "${var.catalogdb_name}"
      "db_workload" = "OLTP"
      "pdb_name" = "${var.pdb_name}"

      db_backup_config {
        auto_backup_enabled     = true
        recovery_window_in_days = 10
      }
    }
    db_version = "19.14.0.0"
    display_name = "FAOPS_CATALOG_DB_MANAGEMENT"
  }
  disk_redundancy = "HIGH"
  shape = "${var.faops_catalog_db_shape}"
  subnet_id = "${var.faops_catalogdb_frontend_subnet_ids[var.faops_cb_catalogdb_ad]}"
  ssh_public_keys = ["${var.ssh_public_key}"]
  display_name = "${var.server}_catalog_db_management"
  hostname = "${var.server}catalogdbhost"
  data_storage_percentage = "80"
  data_storage_size_in_gb = "1024"
  node_count = "1"
}


# Get DB node list
data "oci_database_db_nodes" "catalogdb_node_list" {
  compartment_id = "${var.faops_db_compartment_id}"
  db_system_id = "${oci_database_db_system.faops_catalogtools_catalogdb_system.id}"
}

# Gets the OCID of the first (default) vNIC
data "oci_core_vnic" "catalogdb_node_vnic" {
  vnic_id = "${data.oci_database_db_nodes.catalogdb_node_list.db_nodes.0.vnic_id}"
}

# Get OCI Database entries
data "oci_database_db_homes" "catalogdb_homes" {
  compartment_id = "${var.faops_db_compartment_id}"
  db_system_id   = "${oci_database_db_system.faops_catalogtools_catalogdb_system.id}"
}

data "oci_database_databases" "faops_dbs" {
  compartment_id = "${var.faops_db_compartment_id}"
  # system_id   = "${oci_database_db_system.faops_cb_catalogdb_system.id}"
  db_home_id     = "${data.oci_database_db_homes.catalogdb_homes.db_homes.0.db_home_id}"
}

output "dbs" {
 value = "${join(",",data.oci_core_vnic.catalogdb_node_vnic.*.private_ip_address)}"
}

output "service_name" {
#  value = ["${formatlist("%s.%s)", oci_database_db_system.management.catalogdb_home.*.database.*.pdb_name,oci_database_db_system.management.*.domain)}",]
  value = "${element(concat(oci_database_db_system.faops_catalogtools_catalogdb_system.*.domain, list("")), 0)}"
}
output "cdb_name" {
  value = "${data.oci_database_databases.faops_dbs.databases.0.db_unique_name}"
}

output "ez_connect" {
  value = "${data.oci_database_databases.faops_dbs.databases.0.connection_strings}"
}

output "db_ip" {
 value = "${data.oci_core_vnic.catalogdb_node_vnic.private_ip_address}"
}