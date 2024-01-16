Script that reads all-pod-info_<host name>.txt and calls rman_oss:-
1) rman_wrapper_oratab_20190103.sh (Wrapper script that parses all-pod-info_<host name>.txt and calls main backup script rman_oss.sh)

Script that parses /etc/oratab and generates all-pod-info_<host name>.txt
1) all_pod_oratab_modify.sh (Shell script that parses /etc/oratab file and live/active instances from server to generate all-pod-info_<host name>.txt file)

Script that updates backup needed flag from "y" to "n"
1) update_flag_driver.sh (This is main script that calls update_flag_oratab_yn.sh)
2) update_flag_oratab_yn.sh (This script reads database defined in configuration file db_backup_exceptions.txt and changes backup needed flag from "y" to "n")

Script that schedule's Rman backup and generation of all-pod-info_<host name>.txt file
1) cron.sh (Scripts read backup schedule defined in configuration file backup_schedule.txt and creates cronjob for backups and all-pod-info generation on Database  compute node)

Script that updates /etc/oratab with missing active oracle's SID
1) sid_add_oratab.sh (This file need to be run as root user)

Script that needs to be run as root to configure database for rman backup
1) database_config.sh (This file need to be run as root user)

Configuration files:-
1) backup_schedule.txt (Contains backup schdules of L0,L1, archivelog and allpod info generation)
2) db_backup_exceptions.txt (This file contains names of the databases for which backups are not needed)
3) database_config_schedule.txt (This file contains schedule for running database_config.sh to satisfy pre-requisites for RMAN for any new oracle instance added to the compute node)

Cron job schedules
1) Cron.sh (This script will schedule all the necessary RMAN jobs. Need too run as oracle user id to schedule backup)
2) cron_db_config.sh (This script will schedule database_config.sh that will satisfy pre-requisite for any new databses needing RMAN backup. Need to run as "root" user)

Sequence of flow from deployment onwards:-
Scripts are deployed from RPM using root or oracle user id---><scripts are placed in the home directory>-------->All *.sh and *.py files shoukd have "rwx" permission for owner and "rx" for others>----->post RPM executes <home directory of scripts>/cron.sh--->cronjob is created as oracle user id.

