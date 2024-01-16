#!/bin/bash -x
#Perform Post tasks for PSRtoolsVM
#
echo "########## PSRtools Post Tasks START #############"
LOG="/tmp/psrtoolsvm_$(hostname)_$(date "+%Y%m%d%H%M%S").log"
#Enable require repos
sudo yum install -y oraclelinux-release-el7 | tee -a $LOG
#run post task
sudo /usr/bin/ol_yum_configure.sh | tee -a $LOG
sudo yum -y install yum-utils | tee -a $LOG
sudo yum-config-manager --enable ol7_developer ol7_developer_epel | tee -a $LOG
#Install certified ssvcs -- Review the latest version and repo for this
#sudo yum -y install https://artifactory-phx-prod.cdaas.oraclecloud.com/artifactory/rpm-sharedservices-virtual/repos/oracle/7Server/x86_64/cdaas-ssvcs-bootstrap-2.1-07.el7.x86_64.rpm | tee -a $LOG
#Install server with GUI
sudo yum groupinstall "Server with GUI" -y | tee -a $LOG
sudo systemctl set-default graphical.target | tee -a $LOG
sudo systemctl get-default | tee -a $LOG
sudo systemctl isolate graphical.target | tee -a $LOG
sudo cp -P /etc/ssh/sshd_config /etc/ssh/sshd_config.bkpPSRvm | tee -a $LOG
sudo sed -i 's/^#X11Forwarding yes/X11Forwarding yes/' /etc/ssh/sshd_config | tee -a $LOG
sudo systemctl restart sshd | tee -a $LOG
sudo yum install -y gcc libffi-devel python-devel openssl-devel | tee -a $LOG
#review this for other regions when rollout
sudo yum -y install python-oci-sdk python-oci-cli
#Docker


echo "#########  Setting up config to use overlay2 storage drivers"
sudo mkdir /etc/docker
sudo mkdir -p /u01/psrtools/docker
sudo echo "
{
 \"storage-driver\": \"overlay2\",
 \"data-root\": \"/u01/psrtools/docker\"
}
" | sudo tee /etc/docker/daemon.json

sudo systemctl enable docker | tee -a $LOG
sudo systemctl start docker | tee -a $LOG
sudo chmod 777 /var/run/docker.sock | tee -a $LOG

echo "########## PSRtools Post Tasks Complete #############"
