#!/bin/bash -x
#Perform Post tasks for PERFToolsVM
#
echo "########## PERFTools Post Tasks START #############"
LOG="/tmp/PERFToolsvm_$(hostname)_$(date "+%Y%m%d%H%M%S").log"
#Enable require repos
 yum install -y oraclelinux-release-el7 | tee -a $LOG
#run post task
 /usr/bin/ol_yum_configure.sh | tee -a $LOG
 yum -y install yum-utils | tee -a $LOG
 yum-config-manager --enable ol7_developer ol7_developer_epel | tee -a $LOG
#Install certified ssvcs -- Review the latest version and repo for this
#yum -y install https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/rpm-sharedservices-virtual/repos/oracle/7Server/x86_64/cdaas-ssvcs-bootstrap-2.1-07.el7.x86_64.rpm | tee -a $LOG
#Install server with GUI
 yum groupinstall "Server with GUI" -y | tee -a $LOG
 systemctl set-default graphical.target | tee -a $LOG
 systemctl get-default | tee -a $LOG
 systemctl isolate graphical.target | tee -a $LOG
 cp -P /etc/ssh/sshd_config /etc/ssh/sshd_config.bkpPSRvm | tee -a $LOG
 sed -i 's/^#X11Forwarding yes/X11Forwarding yes/' /etc/ssh/sshd_config | tee -a $LOG
 systemctl restart sshd | tee -a $LOG
 yum install -y gcc libffi-devel python-devel openssl-devel | tee -a $LOG
#review this for other regions when rollout
 yum -y install python-oci-sdk python-oci-cli
#Docker


echo "#########  Setting up config to use overlay2 storage drivers"
 mkdir /etc/docker
 mkdir -p /u01/PERFTools/docker
 echo "
{
 \"storage-driver\": \"overlay2\",
 \"data-root\": \"/u01/PERFTools/docker\"
}
" | sudo tee /etc/docker/daemon.json

 systemctl enable docker | tee -a $LOG
 systemctl start docker | tee -a $LOG
 chmod 777 /var/run/docker.sock | tee -a $LOG

echo "########## PERFTools Post Tasks Complete #############"
