#!/usr/bin/expect 
Basion="$1"
ip="$2"
url="$3"
workspace="/scratch/src/oci/fig/fig_develop/fasaasservicemgr"
#echo "$workspace/modules/common/src/test/resources/ssh/id_rsa -t -o ProxyCommand="ssh -i $workspace/modules/common/src/test/resources/ssh/id_rsa opc@$Basion -W %h:%p %r" opc@$ip"
ssh -i $workspace/modules/common/src/test/resources/ssh/id_rsa -t -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ProxyCommand="ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $workspace/modules/common/src/test/resources/ssh/id_rsa opc@$Basion -W %h:%p %r" opc@$ip << EOF
sudo su -
/opt/jetty/latest/bin/jetty.sh restart
curl $url -m 20
exit

EOF

