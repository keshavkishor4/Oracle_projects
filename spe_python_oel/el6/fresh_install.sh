#!/bin/bash
# 
BASE_DIR="/opt/faops/spe/ocifabackup"
PYTHON_BASE_REL="3.11"
PYTHON_REL="${PYTHON_BASE_REL}.5"
PYTHON_REL_FILE="Python-${PYTHON_REL}.tgz"
# 
OPENSSL_REL="openssl-1.1.1t"
OPENSSL_REL_FILE="${OPENSSL_REL}.tar.gz"
SSL_INSTALL_DIR=$BASE_DIR/utils/python3/openssl/el6
# 
# BASE_DIR="/opt/faops/spe/ocifabackup"
export PROXY_HOST="130.35.131.138"
export PROXY_PORT=80
export PROXY="$PROXY_HOST:$PROXY_PORT"
export PROXY_URL="http://$PROXY"
export ALL_PROXY=$PROXY_URL
export http_proxy=$PROXY_URL
export https_proxy=$PROXY_URL
export HTTP_PROXY=$PROXY_URL
export HTTPS_PROXY=$PROXY_URL

function install_os_packages() {
    yum install -y make net-tools openssh openssh-server openssh-clients findutils which gzip zip unzip gcc openssl-devel bzip2-devel sqlite-devel wget tar vi gawk createrepo
}
function install_python() {
    
    curl -L -o /usr/src/Python-${PYTHON_REL}.tgz https://www.python.org/ftp/python/${PYTHON_REL}/Python-${PYTHON_REL}.tgz
    mkdir -p /usr/local/python3/el6
    mkdir -p ~/.ssh
    mkdir -p ${BASE_DIR}/utils/python3/el6
    tar xzf /usr/src/${PYTHON_REL_FILE} -C /usr/src
    cd /usr/src/Python-${PYTHON_REL} && ./configure --prefix=${BASE_DIR}/utils/python3/el6  --with-openssl=/usr/bin/openssl 
    cd /usr/src/Python-${PYTHON_REL} && make && make altinstall
    cd $BASE_DIR/utils/python3/el6/bin && ln -s python${PYTHON_BASE_REL} python3
    cd $BASE_DIR/utils/python3/el6/bin && ln -s python3 python
    cd $BASE_DIR/utils/python3/el6/bin && ln -s pip${PYTHON_BASE_REL} pip3
    cd $BASE_DIR/utils/python3/el6/bin && ln -s pip3 pip
    echo "export PYTHONPATH=\"${BASE_DIR}/utils/python3/el6\"" >> ~/.bashrc
    echo 'export PATH="$PYTHONPATH/bin:$PATH"' >> ~/.bashrc
    echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDfwIAf7/5mLQtd9pkMGZC4CHbz2RZmb8CfPz+otrgkEtODKBj2OjNE0CHOXz3Ry9dqZG62kq66sm3UgN5bET2W5epjJsINVhjblIDFhXEOCibEwEK0yk9W3Q0dajjr1cDV55rSSrnVGfy9W9uHn+0gxbJUtFWPXdZ7yXSVljumFTbpqkAHthyCRg3t0WxLudVmwjEwUm9XAZYYli1HTZokGg3wZ9P/+j1LXpW2ZorN/NJxYGe4dfb3YuG5/r4hfOaIHUrmOjTDbCX0kjBG17YIZuwcdXdSttoO5SBo6GHYPr4Q5xVlU02Joqex/sjhPE4bI7xTfrbVDdFXmjViokEV Key for saasfareadiness1' >> ~/.ssh/authorized_keys
    source ~/.bashrc
    python --version
    rm -rf /usr/src/Python-${PYTHON_REL}*
}

install_os_packages
install_python
# 