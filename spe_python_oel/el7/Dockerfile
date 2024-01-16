FROM container-registry.oracle.com/os/oraclelinux:7-slim
ENV http_proxy http://www-proxy.us.oracle.com:80 
ENV https_proxy http://www-proxy.us.oracle.com:80 
# RUN yum install -y libffi-devel make net-tools openssh openssh-server openssh-clients findutils which gzip zip unzip gcc openssl-devel bzip2-devel sqlite-devel wget tar vi gawk git locate tcl-devel tk-devel
COPY fresh_install.sh /usr/local/bin 
RUN chmod 755 /usr/local/bin/fresh_install.sh
RUN /usr/local/bin/fresh_install.sh
RUN sed 's/session\s*required\s*pam_loginuid.so/session optional pam_loginuid.so/g' -i /etc/pam.d/sshd
RUN source ~/.bashrc
RUN echo 'updating packages'
COPY update_install_python_packages.sh /usr/local/bin 
RUN chmod 755 /usr/local/bin/update_install_python_packages.sh
RUN /usr/local/bin/update_install_python_packages.sh
RUN yum clean all
# RUN python --version
CMD tail -f /dev/null
