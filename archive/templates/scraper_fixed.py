import requests
from bs4 import BeautifulSoup
import time, csv

session = requests.Session()
r = session.get('https://propertysearch.padctn.org/parcel-search/results?soldDateFrom=11/04/2025&soldDateTo=12/04/2025')
soup = BeautifulSoup(r.text, 'html.parser')

# Find the Load More or First Page button
btn = soup.find('button', string='Load Results') or soup.find('a', href='#load')
if btn:
    btn['href'] = '#load'
    session.post('https://propertysearch.padctn.org/parcel-search/load-more', data={'page':1})  # fakes click

# Wait, grab
time.sleep(2)
r = session.get('https://propertysearch.padctn.org/parcel-search/results?soldDateFrom=11/04/2025&soldDateTo=12/04/2025')
soup = BeautifulSoup(r.text, 'html.parser')

rows = soup.find_all('tr', class_='parcel-result')

with open('nashville_sales_fixed.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Address', 'Sold Date', 'Price', 'Year Built', 'Roof Age'])
    for row in rows:
        cells = row.find_all('td')
        if len(cells) >= 5:
            addr = cells[0].text.strip()
            date = cells[1].text.strip()
            price = cells[2].text.strip().replace('$', '').replace(',', '')
            year = cells[3].text.strip()
            roof_age = 'N/A' if not year.isdigit() else str(2025 - int(year))
            writer.writerow([addr, date, price, year, roof_age])

print(f'Found {len(rows)} rows - check nashville_sales_fixed.csv')