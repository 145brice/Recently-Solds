#!/usr/bin/env python3
"""
Maricopa County (Phoenix, AZ) Recorder Document Search
Scrapes property records from Maricopa County Recorder
Public portal: https://recorder.maricopa.gov/recording/document-search.html
Over 50 million documents - searchable by name, legal description, or address
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import time

# Setup
log_file = f"logs/maricopa_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_maricopa():
    """Scrape Maricopa County property records - last 30 days"""

    logging.info("="*60)
    logging.info("Maricopa County (Phoenix, AZ) Document Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    all_records = []

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)

        url = "https://recorder.maricopa.gov/recdocdata/searchentry.aspx"
        logging.info(f"Loading: {url}")
        driver.get(url)

        time.sleep(3)

        # Check what's on the page
        page_text = driver.page_source[:500]
        logging.info(f"Page loaded, checking structure...")

        # Look for search options
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logging.info(f"Found {len(buttons)} buttons")

        inputs = driver.find_elements(By.TAG_NAME, "input")
        logging.info(f"Found {len(inputs)} input fields")

        links = driver.find_elements(By.TAG_NAME, "a")
        logging.info(f"Found {len(links)} links")

        # Try to find date search
        try:
            # Look for date inputs
            date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[id*='date'], input[id*='Date']")
            logging.info(f"Found {len(date_inputs)} date input fields")

            for inp in date_inputs[:3]:
                logging.info(f"  Date input ID: {inp.get_attribute('id')}, Name: {inp.get_attribute('name')}")

        except Exception as e:
            logging.warning(f"Error finding date inputs: {e}")

        # Try to find warranty deed filter
        try:
            selects = driver.find_elements(By.TAG_NAME, "select")
            logging.info(f"Found {len(selects)} dropdown menus")

            for select in selects[:3]:
                logging.info(f"  Dropdown ID: {select.get_attribute('id')}, Name: {select.get_attribute('name')}")

        except Exception as e:
            logging.warning(f"Error finding dropdowns: {e}")

        logging.info("Portal structure identified - needs custom implementation")

    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

    finally:
        if driver:
            driver.quit()

    return all_records

if __name__ == "__main__":
    records = scrape_maricopa()
    print(f"\nCompleted: {len(records)} records scraped")
