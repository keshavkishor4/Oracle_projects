#!/bin/bash -x

echo '################### Common install begins #####################'
touch /tmp/bastiondata.`date +%s`.start

echo '###### Enable firewalld ########'
systemctl enable  firewalld
systemctl restart firewalld

touch /tmp/bastiondata.`date +%s`.stop