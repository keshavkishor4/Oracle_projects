#!/bin/bash
unset https_proxy
unset http_proxy
unset HTTP_PROXY
unset HTTPS_PROXY
/usr/local/bin/gitlab-runner run --user=gitlab-runner --working-directory=/home/gitlab-runner
