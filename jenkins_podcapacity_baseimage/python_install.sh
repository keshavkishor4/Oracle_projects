#!/bin/bash
#
BASE_DIR="/opt/faops/spe/fapodcapacity"
PYTHON_BASE_REL="3.10"
PYTHON_REL="${PYTHON_BASE_REL}.7"
PYTHON_REL_FILE="Python-${PYTHON_REL}.tgz"
#
OPENSSL_REL="openssl-1.1.1q"
OPENSSL_REL_FILE="${OPENSSL_REL}.tar.gz"
SSL_INSTALL_DIR=$BASE_DIR/utils/python3/openssl/el7
#

# BASE_DIR="/opt/faops/spe/ocifabackup"

# Set Proxy
# export https_proxy=http://www-proxy.us.oracle.com:80 | tee -a ~/.bashrc
# export http_proxy=http://www-proxy.us.oracle.com:80 | tee -a ~/.bashrc
export http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
export no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"

function install_packages() {
    yum install -q -y libffi-devel make net-tools openssh openssh-server openssh-clients findutils which gzip zip unzip gcc openssl-devel bzip2-devel sqlite-devel wget tar vi gawk git locate tcl-devel tk-devel
}

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
    export C_INCLUDE_PATH=/opt/faops/spe/fapodcapacity/utils/sqllite/include
    export CPLUS_INCLUDE_PATH=/opt/faops/spe/fapodcapacity/utils/sqllite/include 
    export LD_RUN_PATH=/opt/faops/spe/fapodcapacity/utils/sqllite/lib
    export PATH=$SSL_INSTALL_DIR/bin:$PATH
    export LD_LIBRARY_PATH=$SSL_INSTALL_DIR/lib:/opt/faops/spe/fapodcapacity/utils/sqllite/lib
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
function sqllite(){
    mkdir -p /opt/faops/spe/fapodcapacity/utils/sqllite
    export sqlite="/opt/faops/spe/fapodcapacity/utils/sqllite"
    curl -L -o /opt/faops/spe/fapodcapacity/utils/sqllite/sqlite-autoconf-3410200.tar.gz https://www.sqlite.org/2023/sqlite-autoconf-3410200.tar.gz
    cd /opt/faops/spe/fapodcapacity/utils/sqllite/
    tar zxvf sqlite-autoconf-3410200.tar.gz
    cd sqlite-autoconf-3410200
    ./configure --prefix=$sqlite
    make && make install
    export PATH=$sqlite/bin:$PATH
    export LD_LIBRARY_PATH=$sqlite/lib
    export LD_RUN_PATH=$HOME/lib

}

install_packages
install_ssl
sqllite
install_python
