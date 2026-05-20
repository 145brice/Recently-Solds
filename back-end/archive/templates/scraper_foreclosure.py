from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

# Set up Chrome in headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Foreclosure.com search URL for Nashville, TN
base_url = "https://www.foreclosure.com/listing/search/TN/Nashville/"

driver.get(base_url)

print(f"Page title: {driver.title}")

# Wait for page to load
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

# Debug: print buttons
buttons = driver.find_elements(By.TAG_NAME, "button")
print("Buttons found:")
for b in buttons:
    print(f"- {b.text}")

# Scroll to load more listings
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
time.sleep(2)

data = []

# Find listings - try different selectors
selectors = [".property-card", ".listing", ".result", ".item", "article", ".card", ".foreclosure"]
listings = []
for sel in selectors:
    listings = driver.find_elements(By.CSS_SELECTOR, sel)
    print(f"Found {len(listings)} with {sel}")
    if listings:
        print(f"First listing text: {listings[0].text[:200]}")
        break
for listing in listings:
    try:
        text = listing.text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines and lines[0].startswith('$'):
            # Has price
            price = lines[0]
            address = lines[1] if len(lines) > 1 else ''
            city = lines[2] if len(lines) > 2 else ''
            status = lines[3] if len(lines) > 3 else ''
        else:
            # No price
            price = ''
            address = lines[0] if lines else ''
            city = lines[1] if len(lines) > 1 else ''
            status = lines[2] if len(lines) > 2 else ''
        link = listing.find_element(By.TAG_NAME, "a").get_attribute("href") if listing.find_elements(By.TAG_NAME, "a") else ''
        data.append({
            'address': address,
            'city': city,
            'price': price,
            'status': status,
            'link': link
        })
    except:
        continue

driver.quit()

# Save to CSV
with open('nashville_foreclosures.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['address', 'city', 'price', 'status', 'link'])
    writer.writeheader()
    writer.writerows(data)

print(f"Scraped {len(data)} foreclosure listings - check nashville_foreclosures.csv")