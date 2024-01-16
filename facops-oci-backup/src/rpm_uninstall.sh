#!/bin/bash
BASE_DIR="/opt/faops/spe/ocifabackup"
HOST=$(hostname -s)
INST_META_FILE=$BASE_DIR/config/${HOST}_inst_meta.json

echo "uninstall of old rpm, clearing out old files"
# if old cron exist
if [[ -f "/etc/cron.d/ocifsbackup" ]];then
    rm -f /etc/cron.d/ocifsbackup
fi
# 
if [[ -f "/etc/cron.d/ocifsbackupv2" ]];then
    rm -f /etc/cron.d/ocifsbackupv2
fi
# 
if [[ -f "/etc/cron.d/ocifsbkpvalidate" ]];then
    rm -f /etc/cron.d/ocifsbkpvalidate
fi
# wallet configs 
if [[ -d "$BASE_DIR/wallet/" ]]; then
    rm -rf $BASE_DIR/wallet/*
fi
# clean up old python
if [[ -d "$BASE_DIR/utils/python3" ]]; then
    rm -rf $BASE_DIR/utils/python3/
fi
#clean up heavy artifacts
if [[ -f $BASE_DIR/config/.artifacts_db.txt ]];then
    for FILE in $(cat $BASE_DIR/config/.artifacts_db.txt);do
        if [ -f $FILE ];then
            rm -f $BASE_DIR/$FILE
        fi
    done
fi
# 
if [[ -f $BASE_DIR/config/.artifacts_mt.txt ]];then
    for FILE in $(cat $BASE_DIR/config/.artifacts_mt.txt);do
        if [ -f $FILE ];then
            rm -f $BASE_DIR/$FILE
        fi
    done
fi
# 
if [[ -f $INST_META_FILE ]];then
    rm -f $INST_META_FILE
fi
# 
if [[ -f /tmp/.faocibkp.tmp ]];then
    rm -f /tmp/.faocibkp.tmp
fi