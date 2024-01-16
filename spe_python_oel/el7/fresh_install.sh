#!/bin/bash
# 
BASE_DIR="/opt/faops/spe/ocifabackup"
PYTHON_BASE_REL="3.11"
PYTHON_REL="${PYTHON_BASE_REL}.5"
PYTHON_REL_FILE="Python-${PYTHON_REL}.tgz"
# 
OPENSSL_REL="openssl-1.1.1t"
OPENSSL_REL_FILE="${OPENSSL_REL}.tar.gz"
SSL_INSTALL_DIR=$BASE_DIR/utils/python3/openssl/el7
# 

# BASE_DIR="/opt/faops/spe/ocifabackup"

# Set Proxy
#export https_proxy=http://www-proxy.us.oracle.com:80 | tee -a ~/.bashrc
#export http_proxy=http://www-proxy.us.oracle.com:80 | tee -a ~/.bashrc
echo "Exporting environment variables"
# export PROXY_HOST="130.35.131.138"
# export PROXY_PORT=80
# export PROXY="$PROXY_HOST:$PROXY_PORT"
# export PROXY_URL="http://$PROXY"
# export ALL_PROXY=$PROXY_URL
# export http_proxy=$PROXY_URL
# export https_proxy=$PROXY_URL
# export HTTP_PROXY=$PROXY_URL
# export HTTPS_PROXY=$PROXY_URL

export http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"


function install_packages() {
    echo "Initiating yum installations"
    yum install -q -y libffi-devel make net-tools openssh openssh-server openssh-clients findutils which gzip zip unzip gcc openssl-devel bzip2-devel sqlite-devel wget tar vi gawk git locate tcl-devel tk-devel
    # curl -L "https://github.com/docker/compose/releases/download/1.26.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    # chmod +x /usr/local/bin/docker-compose
    # yum install -y yum-utils device-mapper-persistent-data lvm2
    # yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    # yum install docker
    # systemctl start docker
    # systemctl enable docker
}

# yum-config-manager --disable ol7_latest
# yum-config-manager --save --setopt=ol7_optional_latest.skip_if_unavailable=true
function install_ssl() {
    mkdir -p ${SSL_INSTALL_DIR}
    curl -L -o /usr/src/${OPENSSL_REL_FILE} https://www.openssl.org/source/${OPENSSL_REL_FILE}
    tar xzf /usr/src/${OPENSSL_REL_FILE} -C /usr/src
    cd /usr/src/${OPENSSL_REL} && ./config --prefix=${SSL_INSTALL_DIR} --openssldir=${SSL_INSTALL_DIR} && make && make install 
    export PATH=$SSL_INSTALL_DIR/bin:$PATH
    export LD_LIBRARY_PATH=$SSL_INSTALL_DIR/lib
    export LDFLAGS="-L${LD_LIBRARY_PATH} -Wl,-rpath,${LD_LIBRARY_PATH}"
    ${SSL_INSTALL_DIR}/bin/openssl version
}
function install_python() {
    export PATH=$SSL_INSTALL_DIR/bin:$PATH
    export LD_LIBRARY_PATH=$SSL_INSTALL_DIR/lib
    export LDFLAGS="-L${LD_LIBRARY_PATH} -Wl,-rpath,${LD_LIBRARY_PATH}"
    curl -L -o /usr/src/Python-${PYTHON_REL}.tgz https://www.python.org/ftp/python/${PYTHON_REL}/Python-${PYTHON_REL}.tgz
    mkdir -p /usr/local/python3/el7
    mkdir -p ~/.ssh
    mkdir -p ${BASE_DIR}/utils/python3/el7
    tar xzf /usr/src/${PYTHON_REL_FILE} -C /usr/src
    cd /usr/src/Python-${PYTHON_REL} && ./configure --prefix=${BASE_DIR}/utils/python3/el7  --with-openssl=$SSL_INSTALL_DIR
    cd /usr/src/Python-${PYTHON_REL} && make && make altinstall
    cd $BASE_DIR/utils/python3/el7/bin && ln -s python${PYTHON_BASE_REL} python3
    cd $BASE_DIR/utils/python3/el7/bin && ln -s python3 python
    cd $BASE_DIR/utils/python3/el7/bin && ln -s pip${PYTHON_BASE_REL} pip3
    cd $BASE_DIR/utils/python3/el7/bin && ln -s pip3 pip
    echo "export PYTHONPATH=\"${BASE_DIR}/utils/python3/el7\"" >> ~/.bashrc
    echo 'export PATH="$PYTHONPATH/bin:$PATH"' >> ~/.bashrc
    echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDfwIAf7/5mLQtd9pkMGZC4CHbz2RZmb8CfPz+otrgkEtODKBj2OjNE0CHOXz3Ry9dqZG62kq66sm3UgN5bET2W5epjJsINVhjblIDFhXEOCibEwEK0yk9W3Q0dajjr1cDV55rSSrnVGfy9W9uHn+0gxbJUtFWPXdZ7yXSVljumFTbpqkAHthyCRg3t0WxLudVmwjEwUm9XAZYYli1HTZokGg3wZ9P/+j1LXpW2ZorN/NJxYGe4dfb3YuG5/r4hfOaIHUrmOjTDbCX0kjBG17YIZuwcdXdSttoO5SBo6GHYPr4Q5xVlU02Joqex/sjhPE4bI7xTfrbVDdFXmjViokEV Key for saasfareadiness1' >> ~/.ssh/authorized_keys
    source ~/.bashrc
    python --version
    rm -rf /usr/src/Python-${PYTHON_REL}*
}

install_packages
install_ssl
install_python
# 