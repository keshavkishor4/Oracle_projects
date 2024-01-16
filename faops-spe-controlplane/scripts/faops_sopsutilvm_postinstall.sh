echo "Setting firewall rules for EL7"
sudo firewall-offline-cmd --add-port=8203/tcp
sudo firewall-offline-cmd --add-port=8080/tcp
sudo systemctl daemon-reload
sudo systemctl enable firewalld
sudo systemctl restart firewalld
sudo firewall-cmd --list-all
# Enable require repos
sudo yum install -y oraclelinux-release-el7
sudo /usr/bin/ol_yum_configure.sh
sudo yum-config-manager --enable ol7_developer ol7_developer_epel
sudo yum -y install python3 python3-pip python-oci-sdk python-oci-cli oracle-database-preinstall-19c
# Post actions
sudo mkdir -p /u01/software