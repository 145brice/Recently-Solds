from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time

options = Options()
driver = webdriver.Edge(options=options)

try:
    # Test Williamson property search - look for sales link
    driver.get('https://inigo.williamson-tn.org/')
    time.sleep(5)
    
    print('Title:', driver.title)
    
    links = driver.find_elements(By.TAG_NAME, 'a')
    print(f'\nFound {len(links)} links, sales-related ones:')
    for link in links:
        text = link.text.lower()
        href = link.get_attribute('href') or ''
        if 'sale' in text or 'search' in text or 'sale' in href:
            print(f'  {link.text[:50]} -> {href}')
        
finally:
    driver.quit()
