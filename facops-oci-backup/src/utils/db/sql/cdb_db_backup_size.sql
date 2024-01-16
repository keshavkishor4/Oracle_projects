set colsep ,     
set pagesize 0   
set trimspool on 
set headsep off 
set linesize 600 
set numw 30 

SELECT
  START_TIME,
  END_TIME,
  INCREMENTAL_TYPE,
  BACKUPTIME_MINS,
  INPUT_GB,
  OUTPUT_GB
FROM
  (SELECT MIN(START_TIME) START_TIME,
    MAX(END_TIME) END_TIME,
    INCREMENTAL_TYPE,
    ROUND(SUM(BACKUPTIME_MINS),2) BACKUPTIME_MINS,
    ROUND(SUM(INPUT_GB),2) INPUT_GB,
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT rbjd.START_TIME,
      rbjd.END_TIME,
      ROUND(rbjd.elapsed_seconds/60,2) BACKUPTIME_MINS,
      'DB_FULL' "INCREMENTAL_TYPE",
      ROUND((rbjd.INPUT_BYTES) /1024/1024/1024,2) INPUT_GB,
      ROUND((rbjd.OUTPUT_BYTES)/1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND rbjd.INPUT_TYPE         ='DB FULL'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.OUTPUT_DEVICE_TYPE = 'DISK'
    AND rbjd.START_TIME         > sysdate - 8
   order by ROUND((rbjd.elapsed_seconds)/60,2) desc)
 WHERE rownum < 2
 GROUP BY INCREMENTAL_TYPE
  UNION ALL
  SELECT MIN(START_TIME) START_TIME,
    MAX(END_TIME) END_TIME,
    INCREMENTAL_TYPE,
    ROUND(SUM(BACKUPTIME_MINS),2) BACKUPTIME_MINS,
    ROUND(SUM(INPUT_GB),2) INPUT_GB,
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT rbjd.START_TIME,
      rbjd.END_TIME,
      'DB_INCR_L0' "INCREMENTAL_TYPE",
      ROUND(rbjd.elapsed_seconds/60,2) BACKUPTIME_MINS,
      ROUND((rbjd.INPUT_BYTES)  /1024/1024/1024,2) INPUT_GB,
      ROUND((rbjd.OUTPUT_BYTES) /1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND bsd.incremental_level  IN ( 0)
    AND rbjd.OUTPUT_DEVICE_TYPE = 'DISK'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.START_TIME         >  sysdate - 8
    order by ROUND((rbjd.elapsed_seconds)/60,2) desc)
 WHERE rownum < 2
 GROUP BY INCREMENTAL_TYPE
  UNION ALL
  SELECT MIN(START_TIME) START_TIME,
    MAX(END_TIME) END_TIME,
    INCREMENTAL_TYPE,
    ROUND(SUM(BACKUPTIME_MINS),2) BACKUPTIME_MINS,
    ROUND(SUM(INPUT_GB),2) INPUT_GB,
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
  FROM
    (SELECT DISTINCT rbjd.START_TIME,
      rbjd.END_TIME,
      'DB_INCR_L1' "INCREMENTAL_TYPE",
      ROUND((rbjd.elapsed_seconds)/60,2) BACKUPTIME_MINS,
      ROUND((rbjd.INPUT_BYTES)/1024/1024/1024,2) INPUT_GB,
      ROUND((rbjd.OUTPUT_BYTES)/1024/1024/1024,2) OUTPUT_GB
    FROM v$rman_backup_job_details rbjd,
      v$backup_set_details bsd
    WHERE bsd.session_recid     = rbjd.session_recid
    AND bsd.session_key         = rbjd.session_key
    AND bsd.session_stamp       = rbjd.session_stamp
    AND bsd.incremental_level  IN ( 1)
    AND rbjd.OUTPUT_DEVICE_TYPE = 'DISK'
    AND rbjd.status             = 'COMPLETED'
    AND rbjd.START_TIME         > sysdate - 8
    order by ROUND((rbjd.elapsed_seconds)/60,2) desc)
 WHERE rownum < 2
group by INCREMENTAL_TYPE
  ) a
;
exit;