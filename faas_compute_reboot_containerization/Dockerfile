FROM phx.ocir.io/axxyy35wuycx/oraclelinux_arm:7-slim as base
COPY python_install.sh /python_install.sh
COPY requirements.txt /requirements.txt
ENV http_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
ENV https_proxy="http://www-proxy-hqdc.us.oracle.com:80/"
ENV no_proxy="localhost,127.0.0.1,us.oracle.com,oraclecorp.com,oraclevcn.com,.oraclecloud.com"
RUN  chmod 755 /python_install.sh && /python_install.sh\
               source ~/.bashrc \
               && /opt/faops/spe/fliprt/utils/python3/el7/bin/pip3 install --upgrade pip \
                && /opt/faops/spe/fliprt/utils/python3/el7/bin/pip3 install virtualenv \
                && /opt/faops/spe/fliprt/utils/python3/el7/bin/pip3 install oci-cli

RUN /opt/faops/spe/fliprt/utils/python3/el7/bin/pip3 install -r /requirements.txt
FROM phx.ocir.io/axxyy35wuycx/oraclelinux_arm:7-slim
RUN mkdir -p /opt/faops/spe/fliprt/utils/ && mkdir -p /opt/faops/spe/fliprt/utils/sqllite && mkdir -p /opt/faops/spe/fliprt/creds 
COPY --from=base /opt/faops/spe/fliprt/utils /opt/faops/spe/fliprt/utils

