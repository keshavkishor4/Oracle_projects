#! /usr/bin/python

#############################################################################

import time
from tkinter.messagebox import RETRY
#import datetime

#start_time = datetime.datetime.now()

import requests
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
from requests.adapters import HTTPAdapter, Retry

start = time.time()

from multiprocessing.dummy import Pool
pool = Pool(8) # Number of concurrent threads

#input file
URLS = open("url.txt","r")

#output file
file = open('output.csv', 'w')

#############################################################################

GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
ENDC = '\033[0m'

def main():
    with open('url.txt') as f:

        url = f.read().splitlines()
        print( "\nTesting URLs.", time.ctime())

        all_text = pool.map(checkUrls,url)
        print("closing p")
        pool.close()
        pool.join()
            #checkUrls()
        print("Press CTRL+C to exit")
        #I don't need this sleep any longer.
        #time.sleep(100000) #Sleep 10 seconds

def checkUrls(url):
    count = 0
    status = "N/A"
    try:
        status = checkUrl(url)
    except requests.exceptions.ConnectionError:
        status = "DOWN"
    except requests.exceptions.HTTPError:
        status = "HttpError"
    except requests.exceptions.ProxyError:
        status = "ProxyError"
    except requests.exceptions.Timeout:
        status = "TimeoutError"
    except requests.exceptions.ConnectTimeout:
        status = "connectTimeout"
    except requests.exceptions.ReadTimeout:
        status = "ReadTimeout"
    except requests.exceptions.TooManyRedirects:
        status = "TooManyRedirects"
    except requests.exceptions.MissingSchema:
        status = "MissingSchema"
    except requests.exceptions.InvalidURL:
        status = "InvalidURL"
    except requests.exceptions.InvalidHeader:
        status = "InvalidHeader"
    except requests.exceptions.URLRequired:
        status = "URLmissing"
    except requests.exceptions.InvalidProxyURL:
        status = "InvalidProxy"
    except requests.exceptions.RetryError:
        status = "RetryError"
    except requests.exceptions.InvalidSchema:
        status = "InvalidSchema"

    printStatus(url, status, count)

    count+=1
    time_elapsed = time.time() - start


def checkUrl(url):
    retry_strategy = Retry(total=2, backoff_factor=1,
                               status_forcelist=[ 503, 504, 500, 429])
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.session()
    http.mount('https://', adapter)
    http.mount('http://', adapter)
    r = http.get(url,verify=False, timeout=30)
    #print r.status_code
    return str(r.status_code)


def printStatus(url, status, count):
    color = GREEN

    count= count+1
    if status != "200":
        color=RED

    #print(color+status+ENDC+' '+ url)
    print(str(count)+'\t' + color+status+ENDC+' '+ url)
    file.write(str(count)+'\t' + color+status+ENDC+' '+ url +'\n')

    #print('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))

end = time.time()
print(end - start)

# Main app
#
if __name__ == '__main__':
    main()
