from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta

# Davidson County - Actual property assessor site
url = "https://www.padctn.org/"  # Property Assessor Davidson County TN
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")

print(f"Accessing Davidson County Property Assessor...")

# Setup Edge
options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Edge(options=options)

try:
    print(f"Loading {url}...")
    driver.get(url)
    time.sleep(3)
    
    print(f"Page title: {driver.title}")
    print(f"Current URL: {driver.current_url}")
    
    # Look for sales search link
    print("\nLooking for sales/search options...")
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links[:20]:
        text = link.text.strip()
        href = link.get_attribute('href')
        if text and ('sale' in text.lower() or 'search' in text.lower() or 'record' in text.lower()):
            print(f"  Found: {text} -> {href}")
    
finally:
    driver.quit()
    print("\nDone.")
