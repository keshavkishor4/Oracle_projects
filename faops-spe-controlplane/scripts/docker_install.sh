#!/bin/bash -x

IS_DEV=$1
HTTP_PROXY=$2
HTTPS_PROXY=$3

if [ "$IS_DEV" == "true" ]; then
  echo '########## Setup proxy #################'
  export http_proxy=${HTTP_PROXY}
  export https_proxy=${HTTPS_PROXY}
fi

echo '########## Docker registry logins #############'

mkdir ~/.docker

echo '{
                  "auths": {
                          "container-registry.oracle.com": {
                                  "auth": "bGNtLWJ1aWxkX3VzQG9yYWNsZS5jb206TGNtT3BzNzMzNw=="
                          },
                          "fra.ocir.io": {
                                  "auth": "b3JhY2xlZmFvbmJtL2F1cmVsaXVzLmZpZ3VlcmVkb0BvcmFjbGUuY29tOiQzU1Z3XTtjYi4+PDJ7Yy05X0NK"
                          },
                          "phx.ocir.io": {
                                  "auth": "b3JhY2xlZmFvbmJtL2xjbS5wcm92aXNpb25pbmc6MSl6SyskUkNUOnQuTGNtRDFiTSE="
                          }
                  }
         }
' > ~/.docker/config.json

echo "#########  Add proxy for proxied connections"
if [ "$IS_DEV" == "true" ]; then
    echo "[Service]
Environment=${HTTP_PROXY}
" > /etc/systemd/system/docker.service.d/http-proxy.conf
fi

echo "#########  Setting up config to use overlay2 storage drivers"
mkdir /etc/docker
echo "
{
 \"storage-driver\": \"overlay2\"
}
" >  /etc/docker/daemon.json

echo "######### Remove unneeded config files ###########"
rm /etc/systemd/system/docker.service.d/docker-sysconfig.conf

echo "########## Start docker #############"
service docker start

echo "########## Autoenable to start docker on restart #############"
systemctl status docker
systemctl enable docker
systemctl status docker