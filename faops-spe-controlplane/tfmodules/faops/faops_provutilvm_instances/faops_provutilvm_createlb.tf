locals {
  single_ad_lb = "${var.svc_lb_subnet_ids[var.mgmt_lb_ad_index_1]}"
  multi_ad_lb  = "${var.svc_lb_subnet_ids[var.mgmt_lb_ad_index_1]},${var.svc_lb_subnet_ids[var.mgmt_lb_ad_index_2]}"
}

resource "oci_load_balancer" "management" {
  shape          = "${var.management_load_balancer_shape}"
  compartment_id = "${var.dmz_compartment_id}"
  subnet_ids     = ["${split(",", (length(var.ad_list)>2)?local.multi_ad_lb:local.single_ad_lb)}"]
  display_name   = "${var.server}_provutilvm_lb"
}

resource "oci_load_balancer_certificate" "provutilvm_lb_certificate" {
  load_balancer_id   = "${oci_load_balancer.management.id}"
  ca_certificate     = "${var.faops_cb_ssl_ca_certificate}"

  /*
   * Note: When rotating certs, certificate_name should always be updated.
   */
  certificate_name   = "${var.faops_cb_self_signed_certificate_name}"
  private_key        = "${var.faops_cb_ssl_private_key}"
  public_certificate = "${var.faops_cb_ssl_public_certificate}"

  lifecycle {
    create_before_destroy = true
  }
}

resource "oci_load_balancer_backendset" "provutilvm_8080" {
  name             = "provutilvm_8080"
  load_balancer_id = "${oci_load_balancer.management.id}"
  policy           = "WEIGHTED_ROUND_ROBIN"

  health_checker {
    port     = "8080"
    protocol = "TCP"
    response_body_regex = ".*"
    retries = "3"
    interval_ms = "30000"
    timeout_in_millis = "15000"
    url_path = "${var.faops_provutilvm_8080_health_checker_url}"
  }
  session_persistence_configuration {
     disable_fallback = "false"
     cookie_name = "*"
  }
  ssl_configuration {
    certificate_name        = "${oci_load_balancer_certificate.provutilvm_lb_certificate.certificate_name}"
    verify_peer_certificate = false
    verify_depth            = "1"
  }
}

resource "oci_load_balancer_backend" "provutilvm_8080" {
  count            = "${length(var.faops_provutilvm_ad_indices)}"
  load_balancer_id = "${oci_load_balancer.management.id}"
  backendset_name  = "${oci_load_balancer_backendset.provutilvm_8080.name}"
  ip_address       = "${element(module.faops_provutilvm.private_ip, count.index)}"
  port             = 8080
  backup           = false
  drain            = false
  offline          = false
  weight           = 1
}

resource "oci_load_balancer_backendset" "provutilvm_8203" {
  name             = "provutilvm_8203"
  load_balancer_id = "${oci_load_balancer.management.id}"
  policy           = "WEIGHTED_ROUND_ROBIN"

  health_checker {
    port     = "8203"
    protocol = "TCP"
    retries = "2"
    interval_ms = "30000"
    timeout_in_millis = "15000"
    response_body_regex = ".*"
    url_path = "${var.faops_provutilvm_8203_health_checker_url}"
  }
  ssl_configuration {
    certificate_name        = "${oci_load_balancer_certificate.provutilvm_lb_certificate.certificate_name}"
    verify_peer_certificate = false
    verify_depth            = "1"
  }
}



resource "oci_load_balancer_backend" "provutilvm_8203" {
  count            = "${length(var.faops_provutilvm_ad_indices)}"
  load_balancer_id = "${oci_load_balancer.management.id}"
  backendset_name  = "${oci_load_balancer_backendset.provutilvm_8203.name}"
  ip_address       = "${element(module.faops_provutilvm.private_ip, count.index)}"
  port             = 8203
  backup           = false
  drain            = false
  offline          = false
  weight           = 1
}

resource "oci_load_balancer_path_route_set" "provutilvm_https_jenkins_path_route_set" {
  #Required
  load_balancer_id = "${oci_load_balancer.management.id}"
  name             = "provutilvm_https_jenkins"

  path_routes {
    #Required
    backend_set_name = "${oci_load_balancer_backendset.provutilvm_8203.name}"
    path             = "/login"

    path_match_type {
      #Required
      match_type = "PREFIX_MATCH"
    }
  }
}

resource "oci_load_balancer_path_route_set" "provutilvm_https_inv_path_route_set" {
  #Required
  load_balancer_id = "${oci_load_balancer.management.id}"
  name             = "provutilvm_https_inv"

  path_routes {
    #Required
    backend_set_name = "${oci_load_balancer_backendset.provutilvm_8080.name}"
    path             = "/ords"

    path_match_type {
      #Required
      match_type = "PREFIX_MATCH"
    }
  }
}

resource "oci_load_balancer_rule_set" "provutilvm_https_jenkins_ruleset" {
  items {
    action = "ADD_HTTP_RESPONSE_HEADER"
    header = "Strict-Transport-Security"
    value = "max-age=31536000; includeSubDomains"
    description = "provutilvm_https_jenkins_ruleset ruleset"
  }
  name = "provutilvm_https_jenkins_ruleset"
  load_balancer_id = "${oci_load_balancer.management.id}"
}
resource "oci_load_balancer_rule_set" "provutilvm_https_inv_ruleset" {
  items {
    action = "ADD_HTTP_RESPONSE_HEADER"
    header = "Strict-Transport-Security"
    value = "max-age=31536000; includeSubDomains"
    description = "provutilvm_https_inv_ruleset ruleset"
  }
  name = "provutilvm_https_inv_ruleset"
  load_balancer_id = "${oci_load_balancer.management.id}"
}

resource "oci_load_balancer_hostname" "provutilvm_https_jenkins_hostname" {
    #Required
    hostname = "${var.faops_provutilvm_jenkins_hostname}"
    load_balancer_id = "${oci_load_balancer.management.id}"
    name = "provutilvm_https_jenkins_hostname"
    #Optional
    lifecycle {
        create_before_destroy = true
    }
}

resource "oci_load_balancer_hostname" "provutilvm_https_inv_hostname" {
    #Required
    hostname = "${var.faops_provutilvm_inv_hostname}"
    load_balancer_id = "${oci_load_balancer.management.id}"
    name = "provutilvm_https_inv_hostname"
    #Optional
    lifecycle {
        create_before_destroy = true
    }
}

resource "oci_load_balancer_listener" "provutilvm_https_jenkins" {
  load_balancer_id         = "${oci_load_balancer.management.id}"
  name                     = "provutilvm_https_jenkins"
  default_backend_set_name = "${oci_load_balancer_backendset.provutilvm_8203.name}"
  port                     = 443
  protocol                 = "HTTP"
  hostname_names           = ["${oci_load_balancer_hostname.provutilvm_https_jenkins_hostname.name}"]
  path_route_set_name      = "${oci_load_balancer_path_route_set.provutilvm_https_jenkins_path_route_set.name}"
  rule_set_names           = ["${oci_load_balancer_rule_set.provutilvm_https_jenkins_ruleset.name}"]


  ssl_configuration {
    certificate_name        = "${oci_load_balancer_certificate.provutilvm_lb_certificate.certificate_name}"
    verify_peer_certificate = false
    verify_depth            = "1"
  }
}


resource "oci_load_balancer_listener" "provutilvm_https_inv" {
  load_balancer_id         = "${oci_load_balancer.management.id}"
  name                     = "provutilvm_https_inv"
  default_backend_set_name = "${oci_load_balancer_backendset.provutilvm_8080.name}"
  port                     = 443
  protocol                 = "HTTP"
  hostname_names           = ["${oci_load_balancer_hostname.provutilvm_https_inv_hostname.name}"]
  path_route_set_name      = "${oci_load_balancer_path_route_set.provutilvm_https_inv_path_route_set.name}"
  rule_set_names           = ["${oci_load_balancer_rule_set.provutilvm_https_inv_ruleset.name}"]

  ssl_configuration {
    certificate_name        = "${oci_load_balancer_certificate.provutilvm_lb_certificate.certificate_name}"
    verify_peer_certificate = false
    verify_depth            = "1"
  }
}


output "management_load_balancer_public_ip_address" {
  value = ["${oci_load_balancer.management.ip_addresses}"]
}

