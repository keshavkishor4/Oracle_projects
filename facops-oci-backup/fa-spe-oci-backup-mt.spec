%global __os_install_post %(echo '%{__os_install_post}' | sed -e 's!/usr/lib[^[:space:]]*/brp-python-bytecompile[[:space:]].*$!!g')
%define     PNAME fa-peo-oci-backup-slim
Name:		%PNAME
Version:	2.0.0.0
Release:	200120
Summary:	Utility for FA SaaS OCI Backup and Restore
Group:		Applications/System
License:	GPL
URL:		https://confluence.rightnowtech.com/display/SPTA/FA+on+OCI+backup+Restore+Package+Release+Notes
Source0:	%PNAME-%{version}.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)
BuildArch:  x86_64
Vendor:		Oracle PEO
Packager:	saas_perf_oci_ww_grp@oracle.com

#BuildRequires:	
#Requires:	dmidecode >= 2.0
#Requires:	oracle-hmp-tools
#Requires:	oracle-hmp-libs

%description
Utility for FA SaaS OCI Backup and Restore 

%prep
rm -rf $RPM_BUILD_DIR/%PNAME-%{version}
rm -rf $RPM_BUILD_ROOT

%setup -q

#%build

%install
install -d $RPM_BUILD_ROOT/usr/bin
install -d $RPM_BUILD_ROOT/etc/cron.d
install -d $RPM_BUILD_ROOT/etc
install -d $RPM_BUILD_ROOT/var/log
install -d $RPM_BUILD_ROOT/opt/faops/spe/
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/mt
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/wallet
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/key_archive
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils/db
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/bin
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/lib
#Setup for v2
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/mt/backup_config
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/db
install -d $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils/stage

#Setup for v2
cp -a src/config/* $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/config/
cp -a src/common/* $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/common
cp -a src/lib/* $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/lib
cp -a src/bin/db_main/* $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/bin
cp -a src/bin/mt_main/* $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/bin

#rm -f $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils/db/nfs_backup/rman.scripts.20180801.1.tar.gz
#rm -f $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils/db/nfs_backup/rman_multi_from_fpcldx0009_05Jun2018.tar.gz
#rm -f $RPM_BUILD_ROOT/opt/faops/spe/ocifabackup/utils/db/nfs_backup/temp2/rman_multi_from_fpcldx0009_05Jun2018.tar.gz

#touch $RPM_BUILD_ROOT/var/log/fa-peo-oci-backup.log

#%clean

%files
%defattr(-,root,root)
%attr(0755,root,root) /opt/faops/spe/ocifabackup/config
%attr(0755,root,root) /opt/faops/spe/ocifabackup/config/mt
%attr(0755,root,root) /opt/faops/spe/ocifabackup/config/mt/backup_config
%attr(0755,root,root) /opt/faops/spe/ocifabackup/config/wallet
%attr(0755,root,root) /opt/faops/spe/ocifabackup/config/key_archive
%attr(0755,root,root) /opt/faops/spe/ocifabackup/utils
%attr(0755,root,root) /opt/faops/spe/ocifabackup/utils/jq
%attr(0755,oracle,root) /opt/faops/spe/ocifabackup/utils/db
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin
%attr(0755,root,root) /opt/faops/spe/ocifabackup/lib
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/db_wallet_backup.py
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/db_artifacts_backup.py
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/ocifsbackup.py
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/ocifsbackupv2_eura.py
#Setup for v2
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/db_tasks.py
%attr(0755,root,root) /opt/faops/spe/ocifabackup/bin/db_download_obj.py

%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-cleanup.json_template
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-file-patterns.json
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-fs-list.json_template
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-oci.json
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-restore-exclude-list.json_template
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-retention-policy.json
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-retention-policy_v2.json
#Setup for v2
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/config-oci_v2.json
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/db/housekeeping-db_v2.json

%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/key_archive/oci_api_key.pem
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/key_archive/oci_api_key_public.pem
%config(noreplace) %attr(644,root,root) /opt/faops/spe/ocifabackup/config/mt/oci_api_key.pem

%config(noreplace) %attr(644,oracle,root) /opt/faops/spe/ocifabackup/config/db/Readme_all_pod_info.txt
%config(noreplace) %attr(644,oracle,root) /opt/faops/spe/ocifabackup/config/common/faops-backup-ver.json

#%config(noreplace) %attr(644,root,root) /etc/cron.d/fa-peo-oci-backup
#%config(noreplace) %attr(644,root,root) /etc/fa-peo-oci-backup.conf

#%ghost /var/log/fa-peo-oci-backup.log

# 
%pre
#%post
#/usr/bin/fa-peo-oci-backup -c install -v > /dev/null 2>&1 &
#printf "%s\n" "Post Install."

#%preun

#%postun

%changelog

* Mon Jan 14 2019 Luhua Wang <luhua.wang@oracle.com> - 1.0.0.0-190114
- Initial version with new spec file
