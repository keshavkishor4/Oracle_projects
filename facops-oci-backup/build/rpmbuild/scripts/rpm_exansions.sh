%pre -e
# upgrade
/usr/bin/systemctl stop faocibkp.service >/dev/null 2>&1 ||:

%post -e 
%systemd_post faocibkp.service
/usr/bin/systemctl daemon-reload
/usr/bin/systemctl start faocibkp.service 

%preun -e 
%systemd_preun faocibkp.service 
#uninstall
/usr/bin/systemctl --no-reload disable faocibkp.service
/usr/bin/systemctl stop faocibkp.service >/dev/null 2>&1 ||:
/usr/bin/systemctl disable faocibkp.service
