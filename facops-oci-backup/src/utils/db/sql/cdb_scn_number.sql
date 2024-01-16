REM Get current SCN number
set colsep ,     
set pagesize 0   
set trimspool on 
set headsep off 
set linesize 600 
set numw 30 
set verify off

SELECT CURRENT_SCN from v$database;
exit;