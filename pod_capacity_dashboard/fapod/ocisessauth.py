import os
os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;var_OCI_CLI_AUTH=security_token;oci session authenticate --profile-name ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --tenancy-name bmc_operator_access;oci session validate --profile ${var_OCI_CLI_PROFILE} --region us-phoenix-1 --auth ${var_OCI_CLI_AUTH};")
