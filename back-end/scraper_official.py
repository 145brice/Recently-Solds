import requests
from bs4 import BeautifulSoup
import pdfplumber
from datetime import datetime, timedelta
import csv
import os

# URL for recent property sales
url = "https://www.padctn.org/department/finance/property-tax/recent-property-sales/"

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# Find the latest quarterly report link (assuming it's a PDF)
links = soup.find_all('a', href=True)
report_link = None
for link in links:
    if 'property' in link.text.lower() and ('sales' in link.text.lower() or 'report' in link.text.lower()) and link['href'].endswith('.pdf'):
        report_link = link['href']
        if not report_link.startswith('http'):
            report_link = 'https://www.padctn.org' + report_link
        break

if not report_link:
    print("No recent sales report found.")
    exit()

# Download the report
report_response = requests.get(report_link)
report_filename = 'quarterly_sales.pdf'
with open(report_filename, 'wb') as f:
    f.write(report_response.content)

# Parse the PDF
data = []
with pdfplumber.open(report_filename) as pdf:
    for page in pdf.pages:
        table = page.extract_table()
        if table:
            headers = table[0]  # First row as headers
            for row in table[1:]:
                row_dict = dict(zip(headers, row))
                # Extract fields
                address = row_dict.get('Address', '')
                price = row_dict.get('Sale Price', '')
                city = 'Nashville'
                year_built = row_dict.get('Year Built', 'N/A')
                estimated_roof_age = str(2025 - int(year_built)) if year_built and year_built != 'N/A' and str(year_built).isdigit() else 'N/A'
                sold_date = row_dict.get('Sale Date', '')
                data.append({
                    'address': address,
                    'city': city,
                    'sold_price': price,
                    'sold_date': sold_date,
                    'year_built': year_built,
                    'estimated_roof_age': estimated_roof_age,
                    'link': ''
                })

# Save to CSV
with open('nashville_recent_sales.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['address', 'city', 'sold_price', 'sold_date', 'year_built', 'estimated_roof_age', 'link'])
    writer.writeheader()
    writer.writerows(data)

os.remove(report_filename)

print(f"Scraped {len(data)} sold homes from quarterly report - check nashville_recent_sales.csv")