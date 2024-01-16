REM RUN Instructions
REM @cdb_db_backup_size1.sql <DISK/TAPE>
set colsep ,     
set pagesize 0   
set trimspool on 
set headsep off 
set linesize 600 
set numw 30 
set verify off

SELECT
  OUTPUT_GB
FROM
  (SELECT 
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT 
      ROUND((rbjd.OUTPUT_BYTES)/1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND rbjd.INPUT_TYPE         ='DB FULL'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.OUTPUT_DEVICE_TYPE = '&1'
    AND rbjd.START_TIME         > sysdate - 8)
 WHERE rownum < 2
  UNION ALL
  SELECT 
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT 
      ROUND((rbjd.OUTPUT_BYTES) /1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND bsd.incremental_level  IN ( 0)
    AND rbjd.OUTPUT_DEVICE_TYPE = '&1'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.START_TIME         >  sysdate - 8)
 WHERE rownum < 2
  UNION ALL
  SELECT 
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT 
      ROUND((rbjd.OUTPUT_BYTES)/1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND bsd.incremental_level  IN ( 1)
    AND rbjd.OUTPUT_DEVICE_TYPE = '&1'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.START_TIME         > sysdate - 8)
 WHERE rownum < 2
  ) a
;
exit;