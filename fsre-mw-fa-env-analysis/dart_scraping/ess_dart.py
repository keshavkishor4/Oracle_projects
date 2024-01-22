#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import os
import json
import unittest
import sys
import traceback
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables,commonutils
import re


# ess_art_url = "https://dashboards.odin.oraclecloud.com/DART/ECGY_20230922052455917583_FullPodSlowness/ess_art.html"
ess_art_url="https://dashboards.odin.oraclecloud.com/DART/HDIU_20231110073519492691_ESSArt/20360419/ess_art.html"

def get_dart_html_data(URL: str)-> dict:
    """ make the request call to shared URL to get the html data for scraping
        Args:
            URL (str): ess art URL
        Returns:
            ess_art_dict (dict): ess art dictionary data 
        Raises:
            Exception: url format is not correct
        """
    try:
        # dart_json_file="{0}/pod_ess_art.json".format(globalvariables.dart_data)
        # URL = globalvariables.odin_dashboard
        if URL:
            response=commonutils.get_request_data(URL)
            ess_art_dict=get_ess_perf_data(response.text)
            return ess_art_dict
        else:
            return None
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in getting ess dashboard data  -> {1}{2}".format(globalvariables.RED,URL,e)
        print(message)

def get_ess_perf_data(html_data: str)-> dict:
    """ scrap the ess art data for given html data
        Args:
            html_data (str): html data to scrap
        Returns:
            ess_art_json (dict): ess art dictionary data 
        Raises:
            Exception: tag not present
        """
    try:
        ess_art_json={}
        soup=BeautifulSoup(html_data,'html.parser')
        all_tag=soup.find_all()
        for ind in range(0,len(all_tag)):
            table_name=""
            if all_tag[ind].name == 'table':
                if all_tag[ind-1].name == 'br':
                    table_name=all_tag[ind-2].text
                else:
                    table_name=all_tag[ind-1].text
                
                # print(table_name)
                table=all_tag[ind]
                table_json=get_table_data(table,table_name)
                if table_json:
                    ess_art_json.update(table_json)
                else:
                    message="could not get data for table {0}".format(globalvariables.RED,table_name)
                    print(message)
        return ess_art_json
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in scraping ess art data {1}".format(e)
        print(message)

# [<th>Instance ParentID<th>Name</th><th>Definition</th><th>Job Type</th><th>Type</th><th>Elapsed Minutes </th><th>Running Thread Count</th><th>Total Child Threads</th></th>, <th>Name</th>, <th>Definition</th>, <th>Job Type</th>, <th>Type</th>, <th>Elapsed Minutes </th>, <th>Running Thread Count</th>, <th>Total Child Threads</th>]

def table_key_check(key: str,table_name: str)->str:
    """ verify the table heading to identify the key for table "Details of Top 100 Parent jobs in Running State for more than 1 Hour, Excluding BI:" 
        Args:
            key (str): accept table heading and json jey 
            table_name (str):table name for given table data
        Returns:
            key name (str): return the possible key name for final json 
        Raises:
            Exception: tag not present
        """
    try:
        res=len(re.findall('(?=(<th>))', str(key)))
        if res > 1:
            if table_name == "Details of Top 100 Parent jobs in Running State for more than 1 Hour, Excluding BI:":
                return "Instance ParentID"
            else:
                return "test_name"
        else:
            return key.text
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in identifyng table key  func => table_key_check {1}".format(globalvariables.RED,e)
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
        if not table_name:
            table_name="test"
        keys=[table_key_check(key,table_name).strip().lower().replace(" ","_") for key in table.find_all(['th'])]
        values=[td.text.strip().lower().replace(" ","_") for td in table.find_all(['td'])]
        if table_name:
            table_name=table_name.strip().lower().replace(" ","_")
        table_json_data={}
        table_json_data.update({table_name:[]})
        while values:
            row_json={}
            for ind in range(0,len(keys)):
                # print(keys[ind])
                row_json.update({keys[ind]:values[ind]})

            del values[0:len(keys)]
            table_json_data[table_name].append(row_json)
        return table_json_data
    except Exception as e:
        traceback.print_exc()
        for key in table.find_all(['th']):
            print(key.text.strip().lower().replace(" ","_"))
            # print(key.text)
        print(f'tablename -> {table_name}')
        print(table)
        message = "{0}Error in scraping ess art table data function => get_table_data {1}".format(globalvariables.RED,e)
        print(message)

class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_pod_dart_url(self):
        actual = get_dart_html_data(ess_art_url)
        expected = 10
        self.assertEqual(actual, expected)

# get_dart_html_data(ess_art_url)