import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Cities
cities = ['Nashville', 'Franklin', 'Brentwood', 'Murfreesboro', 'Smyrna', 'Mount-Juliet', 'Hendersonville', 'Gallatin']

# Base URL
base_url = "https://www.redfin.com/TN/{city}/sold-1mo"

# City IDs
city_ids = {'Nashville': '13493', 'Franklin': '6184', 'Brentwood': '1944', 'Murfreesboro': '13315', 'Smyrna': '18263', 'Mount-Juliet': '13320', 'Hendersonville': '8276', 'Gallatin': '6480'}

data = []

# Set up Selenium
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

for city in cities:
    url = base_url.format(city_id=city_ids.get(city, ''), city=city.replace(' ', '-'))
    try:
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        print(f"Page title: {driver.title}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        homes = soup.find_all('div', class_='HomeCardContainer')
        print(f"Found {len(homes)} homes for {city}")
        if homes:
            print(homes[0].prettify()[:1000])  # Debug first 1000 chars
            break
            address = home.find('span', class_='street-address')
            address = address.text.strip() if address else ''
            
            price = home.find('span', class_='homecardV2Price')
            price = price.text.strip() if price else ''
            
            stats = home.find('div', class_='stats')
            if stats:
                stats_text = stats.text.strip()
                # Assuming format like "3 Beds, 2 Baths, 1,500 Sq Ft"
                parts = stats_text.split(',')
                beds = parts[0].strip() if len(parts) > 0 else ''
                baths = parts[1].strip() if len(parts) > 1 else ''
                sqft = parts[2].strip() if len(parts) > 2 else ''
            else:
                beds = baths = sqft = ''
            
            # Sold date might be in another element, e.g., 'Sold: Oct 15, 2023'
            sold_date_elem = home.find('span', class_='sold-date')  # Adjust if needed
            sold_date = sold_date_elem.text.strip() if sold_date_elem else ''
            
            # Parse sold_date to datetime and check if within 30 days
            if sold_date:
                try:
                    # Assuming format 'Sold: MMM DD, YYYY'
                    sold_date_parsed = datetime.strptime(sold_date.replace('Sold: ', ''), '%b %d, %Y')
                    if sold_date_parsed >= datetime.now() - timedelta(days=30):
                        data.append({
                            'City': city,
                            'Address': address,
                            'Price': price,
                            'Beds': beds,
                            'Baths': baths,
                            'SqFt': sqft,
                            'Sold Date': sold_date
                        })
                except ValueError:
                    # If parsing fails, still add if date is present
                    data.append({
                        'City': city,
                        'Address': address,
                        'Price': price,
                        'Beds': beds,
                        'Baths': baths,
                        'SqFt': sqft,
                        'Sold Date': sold_date
                    })
            else:
                data.append({
                    'City': city,
                    'Address': address,
                    'Price': price,
                    'Beds': beds,
                    'Baths': baths,
                    'SqFt': sqft,
                    'Sold Date': sold_date
                })
        
        time.sleep(1)  # Delay to be respectful
        
    except requests.RequestException as e:
        print(f"Error scraping {city}: {e}")

df = pd.DataFrame(data)
df.to_csv('sold_homes.csv', index=False)
print("Scraping complete. Data saved to sold_homes.csv")