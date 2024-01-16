#!/bin/bash -x

echo '################### Common install begins #####################'
touch /tmp/bastiondata.`date +%s`.start

echo '###### Enable port 7777 and 10663 ########'
firewall-offline-cmd --add-port=7777/tcp
firewall-offline-cmd --add-port=10663/tcp
systemctl daemon-reload
systemctl enable  firewalld
systemctl restart firewalld

touch /tmp/bastiondata.`date +%s`.stop