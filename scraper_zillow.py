import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta

# Zillow RSS for sold homes in Nashville
url = 'https://www.zillow.com/nashville-tn/sold/rss/'

response = requests.get(url)
soup = BeautifulSoup(response.content, 'xml')

items = soup.find_all('item')

data = []

for item in items:
    title = item.find('title').text if item.find('title') else ''
    link = item.find('link').text if item.find('link') else ''
    description = item.find('description').text if item.find('description') else ''
    pubdate = item.find('pubDate').text if item.find('pubDate') else ''
    
    # Parse pubdate
    try:
        sold_date = datetime.strptime(pubdate, '%a, %d %b %Y %H:%M:%S %Z')
        if sold_date >= datetime.now() - timedelta(days=30):
            # Address from title
            address = title.replace(' - Sold for', '').strip()
            
            # Price from description
            desc_soup = BeautifulSoup(description, 'html.parser')
            price_elem = desc_soup.find('span', class_='zsg-photo-card-price')
            sold_price = price_elem.text.strip() if price_elem else ''
            
            # Year built from <BuildYear> tag
            build_year_elem = item.find('BuildYear')
            year_built = build_year_elem.text.strip() if build_year_elem else 'N/A'
            
            # Estimated roof age
            if year_built != 'N/A' and year_built.isdigit():
                estimated_roof_age = str(2025 - int(year_built))
            else:
                estimated_roof_age = 'N/A'
            
            data.append({
                'address': address,
                'city': 'Nashville',
                'sold_price': sold_price,
                'sold_date': pubdate,
                'year_built': year_built,
                'estimated_roof_age': estimated_roof_age,
                'link': link
            })
    except ValueError:
        pass

# Save to CSV
with open('nashville_recent_sales.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['address', 'city', 'sold_price', 'sold_date', 'year_built', 'estimated_roof_age', 'link'])
    writer.writeheader()
    writer.writerows(data)

print(f'Found {len(data)} recent sold homes - check nashville_recent_sales.csv')