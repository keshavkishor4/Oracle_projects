import unittest,sys,os
from datetime import datetime,timedelta
BASE_DIR = os.path.abspath(__file__ +"/../../")
sys.path.append(BASE_DIR)
from common import globalvariables
from octo_metric import octo_db

class Test_get_pod_perf_metric(unittest.TestCase):
    def test_get_octo_exa_cpu(self):
        for exa in globalvariables.exa_test_sample:
            now=datetime.now()
            start_delta=timedelta(hours=8)
            end_delta=timedelta(hours=2)
            start_time=now-start_delta
            start_time=datetime.strftime(start_time,"%Y-%m-%dT%H:%M:%S")
            end_time=now-end_delta
            end_time=datetime.strftime(end_time,"%Y-%m-%dT%H:%M:%S")
            cpu_spike_details = octo_db.getexadata_cpu_details(exa,start_time,end_time)
            print(cpu_spike_details)
            self.assertIsNotNone(cpu_spike_details,"Test value is None")

    def test_getexadata_load_details(self):
        for exa in globalvariables.exa_test_sample:
            now=datetime.now()
            start_delta=timedelta(hours=8)
            end_delta=timedelta(hours=2)
            start_time=now-start_delta
            start_time=datetime.strftime(start_time,"%Y-%m-%dT%H:%M:%S")
            end_time=now-end_delta
            end_time=datetime.strftime(end_time,"%Y-%m-%dT%H:%M:%S")
            exa_load_details = octo_db.getexadata_load_details(exa,start_time,end_time)
            print(exa_load_details)
            self.assertIsNotNone(exa_load_details,"Test value is None")
    
    def test_getexadata_swap_details(self):
        for exa in globalvariables.exa_test_sample:
            now=datetime.now()
            start_delta=timedelta(hours=8)
            end_delta=timedelta(hours=2)
            start_time=now-start_delta
            start_time=datetime.strftime(start_time,"%Y-%m-%dT%H:%M:%S")
            end_time=now-end_delta
            end_time=datetime.strftime(end_time,"%Y-%m-%dT%H:%M:%S")
            exa_swap_details = octo_db.getexadata_swap_details(exa,start_time,end_time)
            print(exa_swap_details)
            self.assertIsNotNone(exa_swap_details,"Test value is None")

    def test_get_db_perf_metric(self):
        for exa in globalvariables.exa_test_sample:
            now=datetime.now()
            start_delta=timedelta(hours=8)
            end_delta=timedelta(hours=2)
            start_time=now-start_delta
            start_time=datetime.strftime(start_time,"%Y-%m-%dT%H:%M:%S")
            end_time=now-end_delta
            end_time=datetime.strftime(end_time,"%Y-%m-%dT%H:%M:%S")
            exa_db_perf_details = octo_db.get_db_perf_metric(exa,start_time,end_time)
            print(exa_db_perf_details)
            self.assertIsNotNone(exa_db_perf_details,"Test value is None")
    
if __name__ == '__main__': 
    unittest.main()