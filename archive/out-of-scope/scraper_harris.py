from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import csv
from datetime import datetime, timedelta

# Setup Chrome options
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--disable-extensions")
options.add_argument("--disable-plugins")
options.add_argument("--disable-images")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)

url = "https://www.hctax.net/property-search/property-search"

print("Scraping recent property records from Harris County, TX")
print(f"URL: {url}")

driver.get(url)
time.sleep(5)

# Wait for search form
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "propertySearch")))
except:
    print("Search form not found")
    print(driver.page_source[:2000])
    driver.quit()
    exit()

# Note: Harris County property search may require specific form filling
# This is a template; inspect the page for correct selectors

# Example: Enter address or parcel
# search_input = driver.find_element(By.ID, "searchInput")
# search_input.send_keys("123 Main St")

# Submit search
# submit_btn = driver.find_element(By.ID, "searchButton")
# submit_btn.click()

time.sleep(5)

# Scrape results - placeholder
data = []
# Add scraping logic here based on page structure

driver.quit()

# Save to CSV
filename = "harris_deeds.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Type", "Grantor", "Grantee", "Description", "Amount"])
    writer.writerows(data)

print(f"Saved {len(data)} records to {filename}")