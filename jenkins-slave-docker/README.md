# Instructions to make Jenkins Slave slave using OEL 7.9 image
## Install docker and docker-compose
### Install docker engine as "root" user
```
yum -y update
yum install -y docker-engine docker-cli 
```

### Install docker-compose
1. Pickup the latest release from https://github.com/docker/compose/releases
2. Download the binary and perform steps
```
export http_proxy=www-proxy.us.oracle.com:80
export https_proxy=www-proxy.us.oracle.com:80
mkdir ~/bin
curl -o ~/bin/docker-compose -L https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-linux-aarch64
chmod +x ~/bin/docker-compose
echo 'export PATH=$PATH:~/bin' | tee -a ~/.bashrc
```
Verify the version
```
docker-compose --version
```
## Configure Proxy

```
mkdir -p ~/.docker/
```

Ensure proxies are set correct in `~/.docker/config.json`

example:
```
"proxies": {
		"default": {
			"httpProxy": "http://www-proxy.us.oracle.com:80",
			"httpsProxy": "http://www-proxy.us.oracle.com:80",
			"noProxy": "*.oci.oraclecorp.com,*.falcm.ocs.oraclecloud.com,*.oraclecorp.com,*.falcm.ocs.oc-test.com"
		}
	}
```

## Clone the repo
```
git clone git@orahub.oci.oraclecorp.com:faops-ocibackup-dev/jenkins-slave-docker.git
cd jenkins-slave-docker 
```

### Prepare the environment
#### Set Docker ROOT_PASS under .env 
```
echo "export ROOT_PASS=<root_password_for_docker_container>" >> .env
```
## Bring up the docker
```
docker-compose up -d
```

## To Start communication between jenkins and docker
```
Modify configuration of file "/lib/systemd/system/docker.service" and add configuration:-
ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:4243 -H unix:///var/run/docker.sock

Note:- Port can be change as per requirement
```
