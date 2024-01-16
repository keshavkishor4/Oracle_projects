#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    NAME
      ApsSqldb.py

    DESCRIPTION
      Common functions for oci backup.

    NOTES

    MODIFIED        (MM/DD/YY)

    Saritha Gireddy       07/29/20 - initial version (code refactoring)
"""
#### imports start here ##############################
import os
import sqlite3
import sys

BASE_DIR = os.path.abspath(__file__ + "/../../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import apscom,globalvariables

#### imports end here ##############################
class ApsSqldb(object):

    def __init__(self, db_path):
        self.sql_db = db_path

        self.conn = None
        self.cursor = None
        self.open(db_path)

    def open(self, name):
        self.conn = sqlite3.connect(name);
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.commit()
            self.cursor.close()
            #self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def get(self, table, columns, limit=None):
        query = "SELECT {0} from {1};".format(columns, table)
        self.cursor.execute(query)
        # fetch data
        rows = self.cursor.fetchall()
        return rows[len(rows) - limit if limit else 0:]

    def getLast(self, table, columns):
        return self.get(table, columns, limit=1)[0]

    def write(self, table, columns, data):
        query = "INSERT INTO {0} ({1}) VALUES ({2});".format(table, columns, data)
        self.cursor.execute(query)

    def query(self, sql):
        self.cursor.execute(sql)

    def querymany(self, sql, iter):
        self.cursor.executemany(sql, iter)

    def get_existing_tables(self):
        try:
            table_list = []
            self.query("select tbl_name FROM sqlite_master")
            existing_tables = self.cursor.fetchall()

            for item in existing_tables:
                table_list.append(item[0])

            return table_list

        except Exception:
            message = "Failed to get existing tables from database!"
            apscom.warn(message)
            raise

    def delete_from_table_older_than(self, table_name, thresh_seconds):
        """Delete records older than seconds from db.
        Args:
            table_name: name of table to operate
            thresh_seconds: Records older than thresh_seconds will be removed.
        Returns:
        Raises:
        """
        try:
            existing_tables = self.get_existing_tables()
            if table_name in existing_tables:
                sql = 'DELETE FROM ' + table_name + ' WHERE \
                    ((STRFTIME("%s", CURRENT_TIMESTAMP) - STRFTIME("%s", date_time)) > ' + thresh_seconds + ')'
                self.query(sql)

            return globalvariables.BACKUP_SUCCESS

        except Exception:
            message = "Failed to delete obsolete items from table {0}!".format(table_name)
            apscom.warn(message)

    CREATE_BACKUP_HISTORY_TABLE = """CREATE TABLE IF NOT EXISTS backup_history_table (
        backup_id INTEGER PRIMARY KEY,
        btimestamp TEXT,
        etimestamp TEXT,
        backup_type TEXT,
        piece_name TEXT,
        retention_days INTEGER,
        status TEXT,
        pod_name TEXT,
        hostname TEXT,
        client_type TEXT,
        log_file TEXT,
        date_time DATETIME DEFAULT CURRENT_TIMESTAMP)"""

    CREATE_BACKUP_HISTORY_TABLE_V2 = """CREATE TABLE IF NOT EXISTS backup_history_table_v2 (
        backup_id INTEGER PRIMARY KEY,
        backup_tool TEXT,
        btimestamp TEXT,
        etimestamp TEXT,
        backup_type TEXT,
        piece_name TEXT,
        retention_days INTEGER,
        status TEXT,
        pod_name TEXT,
        hostname TEXT,
        client_type TEXT,
        client_name TEXT,
        log_file TEXT,
        tag TEXT,
        date_time DATETIME DEFAULT CURRENT_TIMESTAMP)"""

    CREATE_TABLE = {
        "backup_history_table": CREATE_BACKUP_HISTORY_TABLE,
        "backup_history_table_v2": CREATE_BACKUP_HISTORY_TABLE_V2
    }

    def init_table(self,database, table_name):
        """Initialize a sqlite3 db.
        Args:
            database: database.
            table_name: table to create.
        Returns:
            None
        Raises:
        """
        try:
            # Check existing tables in current sqlite3 db.
            existing_tables = database.get_existing_tables()

            if table_name not in existing_tables:
                database.query(self.CREATE_TABLE[table_name])

        except Exception:
            message = "Failed to create database table {0}!\n{1}".format(table_name, sys.exc_info()[1:2])
            apscom.warn(message)
            raise

    def insert_table(self,database, table_name, value_list):
        try:
            if table_name == "backup_history_table":
                database.write(table_name,
                               "btimestamp, etimestamp, backup_type, piece_name, retention_days, status, pod_name, hostname, client_type, log_file",
                               ','.join('"' + item + '"' for item in value_list))
            elif table_name == "backup_history_table_v2":
                database.write(table_name,
                               "backup_tool, btimestamp, etimestamp, backup_type, piece_name, retention_days, status, pod_name, hostname, client_type, client_name, log_file, tag",
                               ','.join('"' + item + '"' for item in value_list))

        except Exception:
            message = "Failed to insert data to database table {0}!\n{1}".format(table_name, sys.exc_info()[1:2])
            apscom.warn(message)
            raise
