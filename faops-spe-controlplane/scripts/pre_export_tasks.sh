#!/bin/bash
#to be executed as root user
EXP_BASE_DIR='/u01/app/oracle/expdir'
FAOPS_SCRIPTS='/opt/faops/scripts'
FAOPS_LOGS='/opt/faops/logs'

function pre_tasks() {
  mkdir -p ${EXP_BASE_DIR} ${FAOPS_SCRIPTS} ${FAOPS_LOGS}
  chown oracle:oinstall ${EXP_BASE_DIR}
  cp /tmp/db_tasks.sh /opt/faops/scripts/
  chmod 755 /opt/faops/scripts/db_tasks.sh
  cp /tmp/faops_db_tasks /etc/cron.d/
  chmod 644 /etc/cron.d/faops_db_tasks
}

function execute_db_tasks() {
if [[ -f "/opt/faops/scripts/db_tasks.sh" ]]; then
  /opt/faops/scripts/db_tasks.sh
fi
}

pre_tasks
execute_db_tasks
