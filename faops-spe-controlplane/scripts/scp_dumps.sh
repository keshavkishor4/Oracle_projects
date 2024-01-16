#!/usr/bin/expect -f
set TGT_ADDR [lindex $argv 0];

spawn scp "/u01/app/oracle/expdir/FAOPS_EXP_DMP.zip" oraimp@$TGT_ADDR:/tmp/FAOPS_EXP_DMP.zip
expect "password"
send "welcome@123\r"
interact

spawn scp "/u01/app/oracle/expdir/source_md5.txt" oraimp@$TGT_ADDR:/tmp/source_md5.txt
expect "password"
send "welcome@123\r"
interact
