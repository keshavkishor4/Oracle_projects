#!/bin/bash -x

echo '################### Common install begins #####################'
touch ~opc/userdata.`date +%s`.start

echo '###### Enable port 8080 ########
firewall-offline-cmd --add-port=8080/tcp
echo '###### Enable port 3872 - 3875 for EM ########'
firewall-offline-cmd --add-port=3872/tcp
firewall-offline-cmd --add-port=3873/tcp
firewall-offline-cmd --add-port=3874/tcp
firewall-offline-cmd --add-port=3875/tcp
firewall-offline-cmd --service=https
systemctl daemon-reload
systemctl enable  firewalld
systemctl restart firewalld

touch ~opc/userdata.`date +%s`.stop