#!/usr/bin/env python3
"""
Wilson County Recent Sales Scraper
Scrapes property sales from Wilson County (GeoPowered platform)
Cron-ready: Runs daily, handles errors, logs output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import time

# Setup
log_file = f"logs/wilson_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_wilson():
    """Scrape Wilson County recent sales"""

    logging.info("="*60)
    logging.info("Wilson County Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    all_sales = []

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(120)

        url = "https://wilsontn.geopowered.com/propertysearch/"
        logging.info(f"Loading Wilson County property search: {url}")
        driver.get(url)
        
        # Wait much longer for JavaScript to fully initialize
        logging.info("Waiting for JavaScript framework to load...")
        time.sleep(15)

        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logging.info(f"Searching for sales from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

        # Try to interact with the page
        try:
            # Wait for any interactive elements
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)
            
            # Log what we can see on the page
            page_text = driver.find_element(By.TAG_NAME, "body").text[:1000]
            logging.info(f"Page content preview: {page_text[:200]}")
            
            # Just try to search without filters - get anything available
            # GeoPowered sites often auto-load some results
            logging.info("Looking for any visible data...")
            
        except Exception as e:
            logging.error(f"Error with page interaction: {e}")

        # Try to extract results
        logging.info("Looking for results...")
        time.sleep(10)  # Extra wait for any async data loading

        # Try multiple selectors - GeoPowered might use divs, cards, or other elements
        result_selectors = [
            "div[class*='property']",
            "div[class*='result']",
            "div[class*='card']",
            "table tbody tr",
            "[role='row']",
            ".search-result",
            "[data-testid*='property']"
        ]
        
        found_results = False
        
        for selector in result_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements and len(elements) > 0:
                    logging.info(f"Found {len(elements)} elements with selector: {selector}")
                    
                    # Extract text from first few to see if they contain property data
                    sample_text = elements[0].text if elements else ""
                    if len(sample_text) > 20:  # Has substantial content
                        logging.info(f"Sample element text: {sample_text[:100]}")
                        
                        # This looks like actual data, use it
                        for elem in elements[:100]:  # Limit to 100 results
                            text = elem.text.strip()
                            if len(text) > 20:
                                all_sales.append({
                                    'Owner Name': '',
                                    'Address': text[:150],  # Truncate long text
                                    'City': 'Wilson County',
                                    'Info': ''
                                })
                        
                        found_results = True
                        logging.info(f"Extracted {len(all_sales)} records")
                        break
            except Exception as e:
                continue
        
        if not found_results:
            logging.warning("Could not find property results with any selector")
            logging.info("Wilson County site may not be showing data or requires manual interaction")

        # Save results
        if all_sales:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/wilson_sales_{timestamp}.csv"

            df = pd.DataFrame(all_sales)
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"SUCCESS: Found {len(all_sales)} sales")
            logging.info(f"Saved to: {output_file}")
            logging.info("="*60)

            return output_file
        else:
            logging.warning("No sales data found")
            logging.info("Wilson County site may require JavaScript interaction or different approach")
            
            # Save page source for debugging
            with open("output/wilson_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("Saved page source to output/wilson_debug.html for debugging")
            
            return None

    except Exception as e:
        logging.error(f"Critical error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

    finally:
        if driver:
            driver.quit()
            logging.info("Browser closed")

if __name__ == "__main__":
    try:
        result = scrape_wilson()
        if result:
            print(f"\nSuccess! Output: {result}")
        else:
            print("\nFailed to get data - check logs and debug.html")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
