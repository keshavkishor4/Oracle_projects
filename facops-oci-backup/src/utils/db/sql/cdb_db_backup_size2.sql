REM Get DB Backup Size
REM RUN Instructions
REM @cdb_db_backup_size2.sql <DISK/TAPE>
set colsep ,     
set pagesize 0   
set trimspool on 
set headsep off 
set linesize 600 
set numw 30 
set verify off

REM TAG is passed during runtime , eg COMPRESSED_FULL_TO_OSS
 SELECT 
    ROUND(SUM(OUTPUT_GB),2) OUTPUT_GB
    FROM
    (
        SELECT DISTINCT 
            ROUND((rbjd.OUTPUT_BYTES)/1024/1024/1024,2) OUTPUT_GB
        FROM v$rman_backup_job_details rbjd,
          v$backup_set_details bsd,
          V$BACKUP_PIECE_DETAILS bpd
        WHERE bsd.session_recid      = rbjd.session_recid
         AND bsd.session_recid       = bpd.session_recid
         AND bsd.session_key         = rbjd.session_key
         AND bsd.session_key         = bpd.session_key
         AND bsd.session_stamp       = rbjd.session_stamp
         AND bsd.session_stamp       = bpd.session_stamp
         AND bsd.COMPLETION_TIME = (
             select max(COMPLETION_TIME) from v$BACKUP_PIECE_DETAILS WHERE
                TAG='&1'
             )
         AND bpd.TAG='&1'
    )
    WHERE ROWNUM <2;
exit;