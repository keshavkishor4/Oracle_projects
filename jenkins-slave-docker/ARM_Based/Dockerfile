FROM phx.ocir.io/axxyy35wuycx/oel7_python_arm:1
#FROM phx.ocir.io/axxyy35wuycx/oel:7-slim
#FROM container-registry.oracle.com/os/oraclelinux:7-slim
ENV http_proxy www-proxy.us.oracle.com:80
ENV https_proxy www-proxy.us.oracle.com:80
RUN yum-config-manager --enable ol7_optional_latest -y
RUN yum install oraclelinux-release-el7 -y
RUN /usr/bin/ol_yum_configure.sh
RUN yum install -y oracle-softwarecollection-release-el7
RUN yum-config-manager --enable ol7_latest ol7_optional_latest
RUN yum install rh-ruby26 rh-ruby26-ruby-devel gcc make rpm-build rubygems createrepo which mlocate hostname vi gcc rpm-build rpm-devel rpmlint make python bash coreutils diffutils patch rpmdevtools openssh-server java-11-openjdk-devel git -y
SHELL [ "/usr/bin/scl", "enable", "rh-ruby26" ]
RUN ruby -v
RUN gem install --no-document fpm
RUN yum clean all
RUN mkdir -p /repo
# RUN chown -Rh gitlab-runner:gitlab-runner /repo
ENV http_proxy ""
ENV https_proxy ""
RUN mkdir -p /var/run/sshd
RUN ssh-keygen -A
ADD ./conf/sshd_config /etc/ssh/sshd_config
ARG ROOT_PASS
ENV ROOT_PASS=$ROOT_PASS
RUN echo root:$ROOT_PASS | chpasswd
RUN echo "export JAVA_HOME=/usr/lib/jvm/java" >> ~/.bash_profile
RUN echo "export JRE_HOME=/usr/lib/jvm/jre" >> ~/.bash_profile
RUN echo 'export PATH=$JAVA_HOME/bin:$PATH'  >> ~/.bash_profile
RUN env
CMD ["/usr/sbin/sshd", "-D"]