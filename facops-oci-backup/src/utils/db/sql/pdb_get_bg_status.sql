set feed off
set head off
SET VERIFY OFF
alter session set container=&1;
REM -- > sample get in JSON Format
REM --> select JSON_OBJECT('PDB_NAME' is name) from v$pdbs where name like '%_F';
select VALUE from fusion.ask_topology_information where name in ('BREAKGLASS_ENABLED');
exit; 