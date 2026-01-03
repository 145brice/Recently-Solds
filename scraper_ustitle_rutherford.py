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
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)

url = "https://www.ustitlesearch.net/search"

print("Scraping recent deeds from Rutherford County via US Title Search")
print(f"URL: {url}")

driver.get(url)
time.sleep(5)

# Wait for search form
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "county")))
except:
    print("Search form not found")
    driver.quit()
    exit()

# Select county: Rutherford County, TN
county_select = Select(driver.find_element(By.ID, "county"))
county_select.select_by_visible_text("Rutherford County, TN")

# Select document type: Deed
doc_select = Select(driver.find_element(By.ID, "documentType"))
doc_select.select_by_visible_text("Deed")

# Set date range: last 30 days
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

start_input = driver.find_element(By.ID, "fromDate")
start_input.clear()
start_input.send_keys(start_date.strftime("%m/%d/%Y"))

end_input = driver.find_element(By.ID, "toDate")
end_input.clear()
end_input.send_keys(end_date.strftime("%m/%d/%Y"))

# Submit search
submit_btn = driver.find_element(By.ID, "searchButton")
submit_btn.click()

time.sleep(5)

# Scrape results
data = []
try:
    table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "resultsTable")))
    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 5:
            date = cols[0].text
            doc_type = cols[1].text
            grantor = cols[2].text
            grantee = cols[3].text
            description = cols[4].text
            amount = cols[5].text if len(cols) > 5 else "N/A"
            data.append([date, doc_type, grantor, grantee, description, amount])

except Exception as e:
    print(f"Error scraping results: {e}")

driver.quit()

# Save to CSV
filename = "rutherford_deeds.csv"
with open(filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Date", "Type", "Grantor", "Grantee", "Description", "Amount"])
    writer.writerows(data)

print(f"Saved {len(data)} deeds to {filename}")