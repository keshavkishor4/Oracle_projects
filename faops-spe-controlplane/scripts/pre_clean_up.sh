#!/bin/bash

cd /tmp
if [[ -f scp_dump.sh ]] 
  then
    echo "Removing scp_dump.sh"
    rm scp_dumps.sh
fi
if [[ -f pre_export_tasks.sh ]] 
  then
    echo "Removing pre_export_tasks.sh"
    rm pre_export_tasks.sh
fi
if [[ -f db_tasks.zip ]] 
  then
    echo "Removing db_tasks.zip"
    rm db_tasks.zip
fi
if [[ -f export_scripts.zip ]] 
  then
    echo "Removing export_scripts.zip"
    rm export_scripts.zip
fi
if [[ -f import_faops_v2.sh ]] 
  then
    echo "Removing import_faops_v2.sh"
    rm import_faops_v2.sh
fi
if [[ -f db_tasks.sh ]] 
  then
    echo "Removing db_tasks.sh"
    rm db_tasks.sh
fi
if [[ -f faops_db_tasks ]] 
  then
    echo "Removing faops_db_tasks"
    rm faops_db_tasks
fi
if [[ -f /u01/app/oracle/expdir/faops* ]]
  then
    cd /u01/app/oracle/expdir
    rm *
fi  