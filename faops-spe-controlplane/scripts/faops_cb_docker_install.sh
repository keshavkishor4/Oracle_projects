#!/bin/bash -x
#
echo "########## FAOPS CB Docker Post Tasks START #############"
LOG="/tmp/faops_cbdb_docker_$(hostname)_$(date "+%Y%m%d%H%M%S").log"
#Enable require repos
sudo yum install -y oraclelinux-release-el7 | tee -a $LOG
#run post task
sudo /usr/bin/ol_yum_configure.sh | tee -a $LOG
sudo yum -y install yum-utils | tee -a $LOG
sudo yum-config-manager --enable ol7_developer ol7_developer_epel | tee -a $LOG
#Install certified ssvcs -- Review the latest version and repo for this
sudo yum -y install https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/rpm-sharedservices-virtual/repos/oracle/7Server/x86_64/cdaas-ssvcs-bootstrap-2.1-07.el7.x86_64.rpm | tee -a $LOG
sudo yum -y install oracle-instantclient18.3-sqlplus oracle-database-preinstall-18c | tee -a $LOG
echo '########## Setting FW rules for FAOPS CBDB #########'
firewall-offline-cmd --add-port=8080/tcp
firewall-offline-cmd --add-port=8203/tcp
firewall-offline-cmd --add-port=8202/tcp
firewall-offline-cmd --add-port=5555/tcp
firewall-offline-cmd --add-port=7001/tcp
firewall-offline-cmd --add-port=5555/udp
systemctl daemon-reload
systemctl enable firewalld
systemctl restart firewalld
firewall-cmd --list-all | tee -a $LOG

echo '########## Docker registry logins #############' | tee -a $LOG

mkdir ~/.docker

echo '{
                  "auths": {
                          "iad.ocir.io": {
                                  "auth": "c2Fhc2ZhcHJvZDEvcHJkX2ZhX3JlYWRvbmx5LlBlcmZVc2VyOjFEV0dWN3tVOTB6Qk1oekF9TD5Y"
                          }
                  }
         }
' | sudo tee ~/.docker/config.json

echo "#########  Setting up config to use overlay2 storage drivers" | tee -a $LOG
mkdir /etc/docker
mkdir -p /u01/faops/docker
echo "
{
 \"storage-driver\": \"overlay2\",
 \"data-root\": \"/u01/faops/docker\"
}
" | sudo tee /etc/docker/daemon.json

echo "######### Remove unneeded config files ###########" | tee -a $LOG
rm /etc/systemd/system/docker.service.d/docker-sysconfig.conf

echo "########## Start docker #############"
service docker restart | tee -a $LOG

echo "########## Autoenable to start docker on restart #############" | tee -a $LOG
systemctl status docker
systemctl enable docker
systemctl status docker | tee -a $LOG