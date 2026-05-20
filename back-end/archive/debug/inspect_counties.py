"""
Inspect each county website to find the correct sales search URLs
"""
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import time

def inspect_site(name, url):
    print(f"\n{'='*60}")
    print(f"INSPECTING: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(60)
    
    try:
        driver.get(url)
        time.sleep(3)
        
        print(f"Title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Find all links
        links = driver.find_elements(By.TAG_NAME, 'a')
        print(f"\nFound {len(links)} links")
        
        # Look for sales/search related links
        keywords = ['sale', 'search', 'property', 'recent', 'record', 'deed', 'transfer']
        relevant_links = []
        for link in links:
            text = link.text.lower()
            href = link.get_attribute('href') or ''
            for keyword in keywords:
                if keyword in text or keyword in href.lower():
                    relevant_links.append(f"{link.text[:50]} -> {href}")
                    break
        
        print("\nRelevant links:")
        for link in list(set(relevant_links))[:15]:  # Unique and limit to 15
            print(f"  - {link}")
        
        # Find search forms
        forms = driver.find_elements(By.TAG_NAME, 'form')
        print(f"\nFound {len(forms)} forms")
        
        # Find input fields
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"Found {len(inputs)} input fields")
        input_types = {}
        for inp in inputs:
            inp_type = inp.get_attribute('type') or 'text'
            inp_name = inp.get_attribute('name') or inp.get_attribute('id') or 'unnamed'
            if inp_type not in input_types:
                input_types[inp_type] = []
            input_types[inp_type].append(inp_name[:30])
        
        print("Input field types:")
        for itype, names in input_types.items():
            print(f"  {itype}: {len(names)} fields")
            if itype in ['text', 'date', 'search']:
                print(f"    Examples: {', '.join(names[:5])}")
        
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        driver.quit()

# Test each county
counties = [
    ("Williamson", "https://inigo.williamson-tn.org/assessor"),
    ("Rutherford", "https://secured.rutherfordcountytn.gov/propertydata/RealPropertySearch2.aspx"),
    ("Wilson", "https://wilsontn.geopowered.com/propertysearch/"),
    ("Davidson", "https://www.padctn.org/resources/recent-sales/"),
]

for name, url in counties:
    try:
        inspect_site(name, url)
        time.sleep(2)
    except Exception as e:
        print(f"Failed {name}: {e}")
        continue
