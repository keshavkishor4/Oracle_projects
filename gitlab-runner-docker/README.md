# Instructions to make gitlab-runner slave using OEL 7.9 image
## Configure Proxy
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
## Run the docker compose
```
git clone git@orahub.oci.oraclecorp.com:faops-ocibackup-dev/gitlab-runner-docker.git
cd gitlab-runner-docker
docker-compose up -d
```
## Register the runner
```
docker exec gitlab-runner-oel /usr/local/bin/gitlab-runner register --non-interactive \
  --url "https://orahub.oci.oraclecorp.com/" \
  --registration-token "<PROJECT_TOKEN" \
  --executor "shell" \
  --description "docker-runner for faoci-backup - $(hostname -f)" \
  --maintenance-note "Free-form maintainer notes about this runner" \
  --tag-list "faocibkp" \
  --run-untagged="true" \
  --locked="false" \
  --access-level="not_protected"
```