import time
import os
def oci_session_refresh():
    time_hour=72
    for i in range(time_hour):
        os.system("var_OCI_CONFIG_FILE=~/.oci/config;var_OCI_CLI_PROFILE=fapod_oci_config;oci session refresh --config-file ${var_OCI_CONFIG_FILE}  --profile ${var_OCI_CLI_PROFILE}")
        time.sleep(1800)

def main():
    oci_session_refresh()

if __name__ == "__main__":
    main()
