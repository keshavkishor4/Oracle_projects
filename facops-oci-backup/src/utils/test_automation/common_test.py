#!/usr/bin/env python
from __future__ import absolute_import, division, print_function

import os
import sys
BASE_DIR = os.path.abspath(__file__ + "/../../../")
sys.path.append(BASE_DIR + "/lib/python")
from common import commonutils,apscom
def get_ols_host_conn(dbname):
    try:
        second_node_conn=False
        running_db_odd_hosts, running_db_even_hosts = commonutils.get_dbname_db_nodes(dbname)
        min_odd_node_name = min(running_db_odd_hosts, key=lambda odd_node: odd_node['running_db_node_num'])
        if running_db_even_hosts:
            min_even_node_name = min(running_db_even_hosts,
                                     key=lambda even_node: even_node['running_db_node_num'])
        else:
            min_even_node_name = min(running_db_odd_hosts,
                                     key=lambda odd_node: odd_node['running_db_node_num'])
        ols_host = min_even_node_name["running_db_node_name"]
        second_node_conn=commonutils.verify_ols_connect(ols_host)
        return second_node_conn
    except Exception as e:
        #traceback.print_exc()
        message = "Failed to execute get_ols_host_conn!\n{0},{1})".format(sys.exc_info()[1:2], e)
        apscom.warn(message)
        return message