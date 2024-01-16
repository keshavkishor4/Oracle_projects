### Oracle_Home configuration files.
#
# Doc Spec
dbcfg.spec
# DB id
dbid
#
# Directories
DB_HOME/admin/DB_UNIQ_NAME/xdb_wallet
/u02/app/oracle/admin/DB_UNIQ_NAME/xdb_wallet
/var/opt/oracle/dbaas_acfs/DB_UNIQ_NAME/db_wallet
# Note: tde_wallet must be backed up in a different location than DATA bkup.
/var/opt/oracle/dbaas_acfs/DB_UNIQ_NAME/wallet_root/tde
/u02/app/oracle/admin/DB_UNIQ_NAME/cat_wallet
#/u01/app/oraInventory
#
# Single files
/var/opt/oracle/dbaas_acfs/DB_UNIQ_NAME/opc/opcDB_UNIQ_NAME.ora
DB_HOME/dbs/opcDB_UNIQ_NAME.ora
DB_HOME/dbs/orapwDB_SID
DB_HOME/network/admin/listener.ora
DB_HOME/network/admin/sqlnet.ora
DB_HOME/network/admin/DB_UNIQ_NAME/sqlnet.ora
DB_HOME/network/admin/tnsnames.ora
DB_HOME/network/admin/DB_UNIQ_NAME/tnsnames.ora
DB_HOME/rdbms/lib/env_rdbms.mk
DB_HOME/rdbms/lib/ins_rdbms.mk
#
# Creg
/var/opt/oracle/creg/DB_UNIQ_NAME.ini
#
