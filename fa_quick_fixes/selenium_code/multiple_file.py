from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
try:
    # Set the download directory
    download_dir = os.path.join(os.getcwd(), 'csv_downloads')
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    # Set Firefox preferences for automatically downloading files to the download directory
    options.set_preference("browser.download.folderList", 2)
    options.set_preference("browser.download.manager.showWhenStarting", False)
    options.set_preference("browser.download.dir", download_dir)
    options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/csv")
    driver = webdriver.Firefox(options=options)
    my_username = "sso_cred"
    my_password = "sso_password"
    urls = ["https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FNagarajan%20Ramachandran%2FSpectra%20Pods&Action=Download&format=CSV",
            "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FOCI-Payroll%20SKU%20Customers-Prompted&Action=Download&format=CSV",
            "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FBGCustomersbySKU-OCI&Action=Download&format=CSV",
            "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FOCI-DataMasking-Customers&Action=Download&format=CSV",
            "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FPOD%20constraint-Exalogic-OCI&Action=Download&format=CSV"]
    #url = "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FBGCustomersbySKU-OCI&Action=Download&format=CSV"
    # Set Firefox preferences for automatically downloading files to the download directory
    for url in urls:
        try:
            print(url)
            driver.implicitly_wait(10)
            driver.get(url)
            time.sleep(2)
        #username = driver.find_element(by=By.NAME, value="ssousername")
            username = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, 'ssousername'))
            )
            username.send_keys(my_username)
            #password = driver.find_element(by=By.NAME, value="password")
            password = WebDriverWait(driver, 5).until(
                EC.visibility_of_element_located((By.NAME, 'password'))
            )
            password.send_keys(my_password)
            #login_button = driver.find_elementby=By.XPATH, value=('//input[@value=" Sign in]')
            login_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "signin_button"))
            )
            login_button.click()
            time.sleep(5)
        except Exception as e:
            print(e)
    #time.sleep(20)
        #time.sleep(30)
    driver.close()
except Exception as e:
    print("Not able to fetch user details")
    print(e)
    driver.close()

