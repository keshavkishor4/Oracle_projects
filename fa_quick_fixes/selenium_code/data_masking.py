from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from bs4 import BeautifulSoup
import csv
try:
    #options = webdriver.FirefoxOptions()
    #options.add_argument('--headless')
    driver = webdriver.Firefox()
    my_username = "sso_cred"
    my_password = "sso_password"
    url = "https://fleetmanager.oraclecloud.com/analytics/saw.dll?PortalGo&Action=prompt&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FOCI-DataMasking-Customers"
    table_url = "https://fleetmanager.oraclecloud.com/analytics/saw.dll?PortalGo&Action=prompt&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FOCI-DataMasking-Customers"
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
    # Navigate to the page containing the table
    driver.get(url)

    # Parse the HTML content of the table page using Beautiful Soup
    table_soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Find the table on the table page
    table = table_soup.find('table')

    # Create a CSV file and write the table data to it
    with open('table_data.csv', mode='w', newline='') as file:
        writer = csv.writer(file)
        for row in table.find_all('tr'):
            row_data = []
            for cell in row.find_all('td'):
                row_data.append(cell.get_text())
            writer.writerow(row_data)
    # Close the browser
    #driver.close()
except Exception as e:
    print("Not able to fetch user details")
    print(e)
    driver.close()
