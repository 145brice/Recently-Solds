from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import csv
import time

# Set up Chrome in headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Davidson County property search URL
url = "https://propertysearch.padctn.org/"

driver.get(url)

# Wait for page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "saleDateFrom")))

# Calculate dates: last 30 days
today = datetime.now()
thirty_days_ago = today - timedelta(days=30)

# Fill sale date from
sale_from = driver.find_element(By.ID, "saleDateFrom")
sale_from.clear()
sale_from.send_keys(thirty_days_ago.strftime("%m/%d/%Y"))

# Fill sale date to
sale_to = driver.find_element(By.ID, "saleDateTo")
sale_to.clear()
sale_to.send_keys(today.strftime("%m/%d/%Y"))

# Click search
search_button = driver.find_element(By.ID, "searchButton")  # Adjust ID if needed
search_button.click()

# Wait for results
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "property-result")))

# Scrape results
results = driver.find_elements(By.CLASS_NAME, "property-result")

data = []

for result in results:
    try:
        address = result.find_element(By.CLASS_NAME, "address").text
        sold_date = result.find_element(By.CLASS_NAME, "sale-date").text
        price = result.find_element(By.CLASS_NAME, "sale-price").text
        # Add other fields if available
        data.append({
            'address': address,
            'sold_date': sold_date,
            'price': price,
            'city': 'Nashville',  # Assuming Davidson County
            'year_built': 'N/A',  # May need to click into detail
            'estimated_roof_age': 'N/A'
        })
    except:
        continue

driver.quit()

# Save to CSV
with open('davidson_county_sales.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['address', 'city', 'sold_date', 'price', 'year_built', 'estimated_roof_age'])
    writer.writeheader()
    writer.writerows(data)

print(f"Scraped {len(data)} sold homes from Davidson County - check davidson_county_sales.csv")