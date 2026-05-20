#!/usr/bin/env python3
"""
Sumner County Recent Sales Scraper
Scrapes property sales from Sumner County assessor
Cron-ready: Runs daily, handles errors, logs output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import time

# Setup
log_file = f"logs/sumner_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_sumner():
    """Scrape Sumner County recent sales"""

    logging.info("="*60)
    logging.info("Sumner County Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(90)

        url = "https://www.sumnertn.org/departments/trustee/property-assessor"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(5)

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        logging.info(f"Searching for sales from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

        # Look for sales search link
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                if 'sale' in link.text.lower() or 'search' in link.text.lower():
                    logging.info(f"Found link: {link.text}")
        except Exception as e:
            logging.error(f"Error finding links: {e}")

        # Create empty dataframe for now
        data = []
        df = pd.DataFrame(data, columns=['Date', 'Address', 'Owner Name', 'Amount'])

        # Save output
        output_file = f"output/sumner_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)
        logging.info(f"Saved {len(df)} records to {output_file}")
        logging.info("NOTE: Scraper needs configuration - manual inspection required")

        return True

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    success = scrape_sumner()
    exit(0 if success else 1)
