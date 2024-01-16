FROM phx.ocir.io/axxyy35wuycx/oraclelinux_arm:7-slim as base
COPY python_install.sh /python_install.sh
ENV DJANGO_HOME /opt/faops/spe/fapodcapacity
ENV http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
ENV https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
ENV no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"
COPY requirements.txt /opt/faops/spe/fapodcapacity/requirements.txt
RUN  chmod 755 /python_install.sh && /python_install.sh\
               source ~/.bashrc \
               && /opt/faops/spe/fapodcapacity/utils/python3/el7/bin/pip3 install --upgrade pip \
                && /opt/faops/spe/fapodcapacity/utils/python3/el7/bin/pip3 install virtualenv \
                && /opt/faops/spe/fapodcapacity/utils/python3/el7/bin/pip3 install oci-cli

WORKDIR $DJANGO_HOME
RUN /opt/faops/spe/fapodcapacity/utils/python3/el7/bin/python3 -m venv django
RUN /bin/bash -c "source $DJANGO_HOME/django/bin/activate && pip3 install -r $DJANGO_HOME/requirements.txt"
FROM phx.ocir.io/axxyy35wuycx/oraclelinux_arm:7-slim
RUN mkdir -p /opt/faops/spe/fapodcapacity/utils/ && mkdir -p /opt/faops/spe/fapodcapacity/utils/sqllite && mkdir -p /opt/faops/spe/fapodcapacity/creds 
COPY --from=base /opt/faops/spe/fapodcapacity/utils /opt/faops/spe/fapodcapacity/utils
COPY --from=base /opt/faops/spe/fapodcapacity/django /opt/faops/spe/fapodcapacity/django
