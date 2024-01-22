FROM phx.ocir.io/axxyy35wuycx/oel:7-slim
#FROM container-registry.oracle.com/os/oraclelinux:7-slim
ENV http_proxy www-proxy.us.oracle.com:80
ENV https_proxy www-proxy.us.oracle.com:80
ENV NO_PROXY "*.oci.oraclecorp.com,*.falcm.ocs.oraclecloud.com,*.oraclecorp.com,*.falcm.ocs.oc-test.com"
RUN yum-config-manager --enable ol7_optional_latest -y
RUN yum install oraclelinux-release-el7 -y
RUN /usr/bin/ol_yum_configure.sh
RUN yum install -y oracle-softwarecollection-release-el7
RUN yum-config-manager --enable ol7_latest ol7_optional_latest
RUN yum install rh-ruby26 rh-ruby26-ruby-devel gcc make rpm-build rubygems createrepo which mlocate hostname vi gcc rpm-build rpm-devel rpmlint make python bash coreutils diffutils patch rpmdevtools ca-certificates openssl jq git -y
#RUN echo "scl enable rh-ruby23 bash" >> ~/.bash_profile
#RUN echo "scl enable rh-ruby23 bash" >> ~/.bashrc
SHELL [ "/usr/bin/scl", "enable", "rh-ruby26" ]
RUN ruby -v
RUN gem install --no-document fpm
#
RUN curl -L --output /usr/local/bin/gitlab-runner https://gitlab-runner-downloads.s3.amazonaws.com/latest/binaries/gitlab-runner-linux-amd64
RUN chmod +x /usr/local/bin/gitlab-runner
RUN useradd --comment 'GitLab Runner' --create-home gitlab-runner --shell /bin/bash
RUN mkdir -p /home/gitlab-runner/.gitlab-runner/certs /repo
RUN chown -Rh gitlab-runner:gitlab-runner /home/gitlab-runner/.gitlab-runner 
RUN chown -Rh gitlab-runner:gitlab-runner /repo
#/usr/bin/gitlab-runnerRUN gitlab-runner install --user=gitlab-runner --working-directory=/home/gitlab-runner
#RUN gitlab-runner start
#RUN curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.rpm.sh" | bash
#RUN yes | yum install gitlab-runner -y
RUN yum clean all
ENV http_proxy ""
ENV https_proxy ""
#COPY https_server_run.py ./
#CMD tail -f /dev/null
#CMD /usr/bin/gitlab-runner run --user=gitlab-runner --working-directory=/home/gitlab-runner
COPY scripts/gitlab-runner_run.sh /opt/gitlab-runner_run.sh
RUN chmod 755 /opt/gitlab-runner_run.sh
#ENTRYPOINT [ "/usr/local/bin/gitlab-runner", "run", "--user=gitlab-runner", "--working-directory=/home/gitlab-runner" ]
ENTRYPOINT ["/opt/gitlab-runner_run.sh"]
