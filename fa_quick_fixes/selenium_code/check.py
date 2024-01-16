import requests
import csv
from bs4 import BeautifulSoup as bs

url = "https://fleetmanager.oraclecloud.com/analytics/saw.dll?PortalGo&Action=prompt&path=%2Fshared%2FReport%20Requests%2FSaaS%20Ops%2FGhanshyam%20Gupta%2FOCI-DataMasking-Customers"
response = requests.get(url)
soup = bs(response.content, "html.parser")
filename = "test.csv"

# Find the table element
table = soup.find('table', {'class': 'PTChildPivotTable'})

# Extract the column headers from the first row of the table
headers = [th.get_text() for th in table.find('tr').find_all('td')]

# Extract the table data from the remaining rows
data = []
for tr in table.find_all('tr')[1:]:
    row = [td.get_text() for td in tr.find_all('td')]
    data.append(row)

# Write the table data to a CSV file
with open('output.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(data)