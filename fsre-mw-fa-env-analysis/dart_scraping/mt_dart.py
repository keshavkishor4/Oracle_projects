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

mt_art_url = "https://dashboards.odin.oraclecloud.com/DART/EEHO_20230921200805723841_FullPodSlowness/MTArt.html"

def get_dart_html_data(URL: str)-> dict:
    """ make the request call to shared URL to get the html data for scraping
        Args:
            URL (str): mt art URL
        Returns:
            mt_art_dict (dict): mt art dictionary data 
        Raises:
            Exception: url format is not correct
        """
    try:
        # dart_json_file="{0}/pod_mt_art.json".format(globalvariables.dart_data)
        # URL = globalvariables.odin_dashboard
        if URL:
            response=commonutils.get_request_data(URL)
            mt_art_dict=get_mt_perf_data(response.text)
            return mt_art_dict
        else:
            return None
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in getting mt dashboard data for dashboard -> {1}{2}".format(globalvariables.RED,URL,e)
        print(message)

def get_mt_perf_data(html_data: str)-> dict:
    """ scrap the mt art data for given html data
        Args:
            html_data (str): html data to scrap
        Returns:
            mt_art_json (dict): mt art dictionary data 
        Raises:
            Exception: tag not present
        """
    try:
        mt_art_json={}
        table_list=["metric_wls","metric_datasource"]
        soup=BeautifulSoup(html_data,'html.parser')
        for table_name in table_list:
            if soup.find('div',id=table_name):
                table=soup.find('div',id=table_name).find('table')
                table_json=get_table_data(table,table_name)
                mt_art_json.update(table_json)
            else:
                message="error - could not found mt table data"
                print(message)
        return mt_art_json
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping mt art data {1}".format(globalvariables.RED,e)
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
        keys=[key.text.strip().lower().replace(" ","_") for key in table.find('tr',class_="trh").find_all('td')]
        all_rows=table.find_all('tr')
        if table_name:
            table_name=table_name.strip().lower().replace(" ","_")
        table_json_data={}
        table_json_data.update({table_name:[]})
        for row in all_rows:
            row_data={}
            if row.has_attr("class"):
                if row["class"][0] != "trh":
                    row_td=[td.text.strip().lower().replace(" ","_") for td in row.find_all('td')]
                    for i in range(len(keys)):
                        row_data.update({keys[i]:row_td[i]})
                    table_json_data[table_name].append(row_data)
            else:
                row_td=[td.text.strip().lower().replace(" ","_") for td in row.find_all('td')]
                for i in range(len(keys)):
                    row_data.update({keys[i]:row_td[i]})
                table_json_data[table_name].append(row_data)
        return table_json_data
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping mt art table data {1}".format(globalvariables.RED,e)
        print(message)

class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_pod_dart_url(self):
        actual = get_dart_html_data(mt_art_url)
        expected = 2
        self.assertEqual(actual, expected)
        
# print(get_dart_html_data(mt_art_url))
