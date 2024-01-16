#!/bin/bash
BACKUP_BASE_DIR="/opt/faops/spe/ocifabackup"
JQ_TOOL="${BACKUP_BASE_DIR}/utils/jq"
chmod 755 ${JQ_TOOL}
METADATA=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/metadata 2>/dev/null)
INST=$(curl -H "Authorization: Bearer Oracle" -L http://169.254.169.254/opc/v2/instance/ 2>/dev/null)
REGION=$(echo "${INST}"| "${JQ_TOOL}" -r '.canonicalRegionName')
# 
HOST_TYPE=$(echo "${METADATA}" | "${JQ_TOOL}" -r '.dbSystemShape')
case "$HOST_TYPE" in
    *"Exa"*) 
        # %systemd_preun faocibkp.service
        # #uninstall
        # /usr/bin/systemctl --no-reload disable faocibkp.service
        # /usr/bin/systemctl stop faocibkp.service >/dev/null 2>&1 ||:
        # /usr/bin/systemctl disable faocibkp.service
        echo ""
        ;;
    *"VM.Standard"*) 
        # %systemd_preun faocibkp.service
        # #uninstall
        # /usr/bin/systemctl --no-reload disable faocibkp.service
        # /usr/bin/systemctl stop faocibkp.service >/dev/null 2>&1 ||:
        # /usr/bin/systemctl disable faocibkp.service
        echo ""
        ;;
    *)
        :
        ;;
esac
