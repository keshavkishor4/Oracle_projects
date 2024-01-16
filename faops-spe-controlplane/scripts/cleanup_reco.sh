#!/bin/bash
OLDDATE=$(date +%d -d "-15 days")
sqlplus -s / as sysasm << EOF
  spool /tmp/asm_dg.txt;
  SELECT name, free_mb, total_mb, free_mb/total_mb*100 as percentage FROM v\$asm_diskgroup;
  spool off;
EOF
RECO_PER=$(grep -i RECO /tmp/asm_dg.txt | awk '{print $4}' | cut -d . -f1)

if [[ "$RECO_PER" > "20" ]]; then
  echo "Enough free space is available on ASM storage"
else
  echo "RECO Diskgroup is running low on space. Cleaning up some old backups"
  ARCHIVE_LIST=$(asmcmd ls +RECO/OPSCBDB*/ARCHIVELOG | head -n 5 | sed 's,/,,g')
  for BACKUP_DATE in $ARCHIVE_LIST ; do
      asmcmd -p rm -rf +RECO/OPSCBDB*/ARCHIVELOG/${BACKUP_DATE}/*
  done;
fi