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
import gc

bi_art_url = "https://dashboards.odin.oraclecloud.com/DART/EINO_20230922172450432513_FullPodSlowness/bi_art.html"

def get_dart_html_data(URL: str)-> dict:
    """ make the request call to shared URL to get the html data for scraping
        Args:
            URL (str): bi art URL
        Returns:
            bi_art_dict (dict): bi art dictionary data 
        Raises:
            Exception: url format is not correct
        """
    try:
        # dart_json_file="{0}/pod_bi_art.json".format(globalvariables.dart_data)
        # URL = globalvariables.odin_dashboard
        if URL:
            response=commonutils.get_request_data(URL)
            bi_art_dict=get_bi_perf_data(response.text)
            return bi_art_dict
        else:
            return None
    except Exception as e:
        traceback.print_exc()
        message = "{0} Error in getting bi dashboard data  -> {1}{2}".format(globalvariables.RED,URL,e)
        print(message)

def get_bi_perf_data(html_data: str)-> dict:
    """ scrap the bi art data for given html data
        Args:
            html_data (str): html data to scrap
        Returns:
            bi_art_json (dict): bi art dictionary data 
        Raises:
            Exception: tag not present
        """
    try:
        bi_art_json={}
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
                    bi_art_json.update(table_json)
                else:
                    message="could not get data for table {0}".format(table_name)
                    print(message)
        
        return bi_art_json
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping bi art data {1}".format(globalvariables.RED,e)
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
        keys=[key.text.strip().lower().replace(" ","_") for key in table.find_all(['th'])]
        values=[td.text.strip().lower().replace(" ","_") for td in table.find_all(['td'])]
        if table_name:
            table_name=table_name.strip().lower().replace(" ","_")
        table_json_data={}
        table_json_data.update({table_name:[]})
        while values:
            row_json={}
            for ind in range(0,len(keys)):
                if ind < len(values):
                    row_json.update({keys[ind]:values[ind]})
                else:
                    row_json.update({keys[ind]:"NAN"})

            del values[0:len(keys)]
            table_json_data[table_name].append(row_json)
        return table_json_data
    except Exception as e:
        traceback.print_exc()
        message = "{0}Error in scraping bi art table data {1} \n {2}".format(globalvariables.RED,e,table_name)
        print(message)

class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_pod_dart_url(self):
        actual = get_dart_html_data(bi_art_url)
        expected = 6
        self.assertEqual(actual, expected)

# get_dart_html_data(bi_art_url)