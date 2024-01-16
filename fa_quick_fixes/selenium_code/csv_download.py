from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
try:
    options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')
    driver = webdriver.Firefox()
    my_username = "sso_creds"
    my_password = "Sso_password"
    url = "https://fleetmanager.oraclecloud.com/analytics/saw.dll?Go&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FBGCustomersbySKU-OCI&Action=Download&format=CSV"
    driver.get(url)
    #username = driver.find_element(by=By.NAME, value="ssousername")
    username = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, 'ssousername'))
    )
    username.send_keys(my_username)
    #password = driver.find_element(by=By.NAME, value="password")
    password = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.NAME, 'password'))
    )
    password.send_keys(my_password)
    #login_button = driver.find_elementby=By.XPATH, value=('//input[@value=" Sign in]')
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "signin_button"))
    )
    login_button.click()
    time.sleep(30)
    driver.close()
except Exception as e:
    print("Not able to fetch user details")
    print(e)
    driver.close()

