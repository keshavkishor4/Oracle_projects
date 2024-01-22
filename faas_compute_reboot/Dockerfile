FROM phx.ocir.io/axxyy35wuycx/oel7_python_fliprtbaseimage_arm:5
COPY setup.sh /opt/faops/spe/fliprt
COPY src /opt/faops/spe/fliprt
COPY creds /opt/faops/spe/fliprt/creds
WORKDIR  /opt/faops/spe/fliprt
CMD [  "./setup.sh" ]
