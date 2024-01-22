import requests,os,sys
from requests.adapters import HTTPAdapter, Retry
BASE_DIR = os.path.abspath(__file__ +"/..")
sys.path.append(BASE_DIR)
from common import globalvariables

@globalvariables.timer
def get_request_data(url):
    try:
        retry_strategy = Retry(total=5,
                    backoff_factor=1)
        http = requests.session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        http.mount('https://', adapter)
        http.mount('http://', adapter)
        
        response=http.get(url)
        return response
    except Exception as e:
        message="error in request module for func get_request_data status code => {1} - {0}".format(e,response.status_code)
        print(message)


def main():
    get_request_data("test.com")

if __name__ == "__main__":
    main()