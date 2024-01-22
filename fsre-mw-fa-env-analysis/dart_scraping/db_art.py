#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import os
import unittest
import sys
import traceback
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables,commonutils

db_art_url = "https://dashboards.odin.oraclecloud.com/DART/EODR_20231010074921988360_DARTAutomatedAnalysis/dbart_07.html"

@globalvariables.timer
def get_dart_html_data(URL: str)-> dict:
    """ make the request call to shared URL to get the html data for scraping
        Args:
            URL (str): dbart URL
        Returns:
            db_art_dict (dict): db art dictionary data 
        Raises:
            Exception: url format is not correct
        """
    try:
        # dart_json_file="{0}/pod_db_art.json".format(globalvariables.dart_data)
        # URL = globalvariables.odin_dashboard
        if URL:
            response=commonutils.get_request_data(URL)
            db_art_dict=get_pod_db_dart_data(response.text)
            return db_art_dict
        else:
            return None
    except Exception as e:
        traceback.print_exc()
        message = "{2}Error in getting perf data for dashboard -> {0}{1}".format(URL,e,globalvariables.RED)
        print(message)

def get_pod_db_dart_data(html_data:str)-> dict:
    """ scrap the DB art data for given html data
        Args:
            html_data (str): html data to scrap
        Returns:
            db_art_json (dict): db art dictionary data 
        Raises:
            Exception: tag not present
        """
    try:
        # with open(globalvariables.db_art_config_file,'r') as config:
        #     config_json=json.loads(config.read())
        # print(config_json)
        db_art_json={}
        soup = BeautifulSoup(html_data, 'html.parser')
        tables=soup.find_all('table')
        for table in tables:
            if table.parent.has_attr('id') and table.parent['id'] == "hang":# hanganalysis tables parsing
                hang_dict=hang_analyis(html_data)
                db_art_json.update({"hang_analysis":hang_dict})
            else:
                table_name=table.find('b').text
                if "Top SQL ID" in table_name:
                    table_name="top_sql_id"
                if "Top event is" in table_name:
                    table_name="top_event"
                sql_id=""
                if table.parent.name == "div":
                    sql_id=table.parent["id"]
                # if (table_name in config_json and config_json[table_name]) or (sql_id in config_json):#selective table data validation as per config file -> db_art_config_file="../config/db_art/db_art_table.json"
                table_json_data=get_table_data(table,table_name)
                if sql_id:
                    if sql_id in db_art_json:
                        db_art_json[sql_id].append(table_json_data)
                    else:
                        db_art_json.update({sql_id:[table_json_data]})
                else:
                    db_art_json.update(table_json_data)
        
        return db_art_json
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping db art data func - get_pod_db_dart_data  {1}".format(globalvariables.RED,e)
        print(message)

def get_table_data(table: str,table_name: str)-> dict:
    """ parse the html table data 
        Args:
            table (str): table format html data for parsing 
            table_name (str):table name for given table data
        Returns:
            table_json_data (dict): parsed json data from html table 
        Raises:
            Exception: tag not present
        """
    try:
        # print(table_name)
        keys=[key.text.strip().lower().replace(" ","_") for key in table.find_all(['th'])]
        # keys=["top_sql_id" if "top_sql_id_is" in key:  for key in keys]
        values=[td.text.strip().lower().replace(" ","_") for td in table.find_all(['td'])]
        if table_name:
            table_name=table_name.strip().lower().replace(" ","_")
        table_json_data={}
        table_json_data.update({table_name:[]})
        while values:
            row_json={}
            for ind in range(0,len(keys)):
                row_json.update({keys[ind]:values[ind]})

            del values[0:len(keys)]
            table_json_data[table_name].append(row_json)
        # print(table_json_data)
        return table_json_data
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping db table data func - get_table_data  {1}".format(globalvariables.RED,e)
        print(message)

def hang_analyis(html_Data: str)-> dict:
    """ parse the hang analysis data from db art page 
        Args:
            html_Data (str): html data for hanganalysis table from db art page
        Returns:
            hang_analysis_json (dict): parsed json data from html hanganalysis details 
        Raises:
            Exception: tag not present
        """
    try:
        hang_analysis_json={}
        soup = BeautifulSoup(html_Data, 'html.parser')
        hang_analysis=soup.find('div',{'id' :'hang'})
        hang_analysis_json.update({"message" : [line for line in hang_analysis.text.split('\n') if "***" in line ]})
        tables=hang_analysis.find_all('table')
        for table in tables:
            table_json_data={}
            rows=table.find_all(['tr'])
            t_head=table.find('tr').find_all('th')
            if isinstance(globalvariables.table_name_json[len(t_head)],list):
                if t_head[4] == "num_waiters":
                    table_name = globalvariables.table_name_json[len(t_head)][0]
                else:
                    table_name = globalvariables.table_name_json[len(t_head)][1]
            else:
                table_name = globalvariables.table_name_json[len(t_head)]
            
            table_json_data=get_table_data(table,table_name)
            if table_json_data[table_name]:
                hang_analysis_json.update(table_json_data)
        
        return hang_analysis_json
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in parsing hang_analysis data func - hang_analyis {1}".format(globalvariables.RED,e)
        print(message)


class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_pod_dart_url(self):
        actual = get_dart_html_data(db_art_url)
        expected = 7
        self.assertEqual(actual, expected)

# data=get_dart_html_data(db_art_url)
# print(data["hang_analysis"]["blocking_sessions"])