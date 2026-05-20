from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    driver.get('https://inigo.williamson-tn.org/property_search/')
    time.sleep(3)
    
    # Fill in search form
    driver.find_element(By.ID, 'sales_date_start').send_keys('12/26/2025')
    driver.find_element(By.ID, 'sales_date_end').send_keys('01/02/2026')
    
    # Click search
    search_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'].button")
    search_btn.click()
    
    time.sleep(10)  # Wait for content
    
    # Check table structure
    table = driver.find_element(By.ID, 'results_table')
    rows = table.find_elements(By.TAG_NAME, 'tr')
    print(f'Table has {len(rows)} rows')
    
    for i, row in enumerate(rows):
        print(f'\nRow {i}:')
        cols = row.find_elements(By.TAG_NAME, 'td')
        print(f'  Has {len(cols)} td cells')
        
        # Print raw HTML of row
        html = row.get_attribute('innerHTML')
        print(f'  HTML: {html[:300]}...')
        
        if cols:
            for j, col in enumerate(cols):
                print(f'  Cell {j}: "{col.text}"')
                
finally:
    driver.quit()
