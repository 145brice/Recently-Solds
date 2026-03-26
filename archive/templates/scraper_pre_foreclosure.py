from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import csv
import time

# Set up Chrome in headless mode
options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Davidson County Register of Deeds search URL
url = "https://www.davidsoncounty-tn.gov/Departments/Register-of-Deeds/Pages/Search-Records.aspx"

driver.get(url)

print(f"Page title: {driver.title}")

# Wait for page to load
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ddlDocType")))
    print("Page loaded successfully")
except Exception as e:
    print(f"Failed to load page: {e}")
    driver.quit()
    exit()

# Select document type for pre-foreclosure (e.g., "Notice of Default" or "Lis Pendens")
try:
    doc_type_select = Select(driver.find_element(By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_ddlDocType"))
    doc_type_select.select_by_visible_text("Notice of Default")  # Or "Lis Pendens" if available
    print("Document type selected")
except Exception as e:
    print(f"Failed to select document type: {e}")
    driver.quit()
    exit()

# Set date range for recent (last 30 days)
from datetime import datetime, timedelta
today = datetime.now()
thirty_days_ago = today - timedelta(days=30)

# Fill from date
from_date = driver.find_element(By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_txtFromDate")
from_date.clear()
from_date.send_keys(thirty_days_ago.strftime("%m/%d/%Y"))

# Fill to date
to_date = driver.find_element(By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_txtToDate")
to_date.clear()
to_date.send_keys(today.strftime("%m/%d/%Y"))

# Click search
search_button = driver.find_element(By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_btnSearch")
search_button.click()

# Wait for results
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_gvResults")))

data = []

# Scrape results table
table = driver.find_element(By.ID, "ctl00_ctl00_ContentPlaceHolder1_ContentPlaceHolder1_gvResults")
rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header

for row in rows:
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) >= 5:  # Adjust based on columns
        doc_number = cells[0].text.strip()
        date = cells[1].text.strip()
        grantor = cells[2].text.strip()
        grantee = cells[3].text.strip()
        description = cells[4].text.strip()
        data.append({
            'doc_number': doc_number,
            'date': date,
            'grantor': grantor,
            'grantee': grantee,
            'description': description
        })

driver.quit()

# Save to CSV
with open('pre_foreclosures_davidson.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['doc_number', 'date', 'grantor', 'grantee', 'description'])
    writer.writeheader()
    writer.writerows(data)

print(f"Scraped {len(data)} pre-foreclosure notices - check pre_foreclosures_davidson.csv")