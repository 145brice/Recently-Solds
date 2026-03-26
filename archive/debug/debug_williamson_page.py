"""Check what data is actually available on Williamson County search results"""
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Edge(options=options)
driver.set_page_load_timeout(90)

try:
    # Load search page
    driver.get("https://inigo.williamson-tn.org/property_search/")
    time.sleep(5)
    
    # Fill in dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    date_from = driver.find_element(By.NAME, "sales_date_start")
    date_from.clear()
    date_from.send_keys(start_date.strftime('%m/%d/%Y'))
    
    date_to = driver.find_element(By.NAME, "sales_date_end")
    date_to.clear()
    date_to.send_keys(end_date.strftime('%m/%d/%Y'))
    
    time.sleep(2)
    
    # Submit
    search_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
    driver.execute_script("arguments[0].click();", search_button)
    time.sleep(5)
    
    # Check table structure
    print("="*60)
    print("TABLE STRUCTURE")
    print("="*60)
    
    # Get header row
    header_row = driver.find_element(By.CSS_SELECTOR, "table tr:first-child")
    headers = header_row.find_elements(By.TAG_NAME, "th")
    if not headers:
        headers = header_row.find_elements(By.TAG_NAME, "td")
    
    print(f"\nFound {len(headers)} columns:")
    for i, header in enumerate(headers):
        print(f"  Column {i}: {header.text.strip()}")
    
    # Get first data row
    print("\n" + "="*60)
    print("FIRST DATA ROW")
    print("="*60)
    
    rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
    if len(rows) > 1:
        first_data_row = rows[1]
        cells = first_data_row.find_elements(By.TAG_NAME, "td")
        print(f"\nFound {len(cells)} cells in first data row:")
        for i, cell in enumerate(cells):
            print(f"  Cell {i}: {cell.text.strip()[:100]}")
    
    # Check for property type filter
    print("\n" + "="*60)
    print("AVAILABLE FILTERS")
    print("="*60)
    
    inputs = driver.find_elements(By.CSS_SELECTOR, "input, select")
    print(f"\nFound {len(inputs)} input/select elements:")
    for inp in inputs[:20]:  # First 20
        inp_type = inp.get_attribute('type') or 'select'
        inp_name = inp.get_attribute('name') or inp.get_attribute('id') or 'unnamed'
        print(f"  {inp_type}: {inp_name}")
    
finally:
    driver.quit()
