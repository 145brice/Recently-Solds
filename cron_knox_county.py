#!/usr/bin/env python3
"""
Knox County (Knoxville) Warranty Deed Scraper
Scrapes warranty deeds from Knox County Register of Deeds
Public portal: https://rod.knoxcounty.org/
Cron-ready: Runs daily, handles errors, logs output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import time

# Setup
log_file = f"logs/knox_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_knox():
    """Scrape Knox County warranty deeds - last 30 days"""

    logging.info("="*60)
    logging.info("Knox County (Knoxville) Warranty Deed Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        url = "https://rod.knoxcounty.org/"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(3)

        # Look for search link
        search_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Search")
        logging.info(f"Found {len(search_links)} search links")

        if search_links:
            driver.execute_script("arguments[0].click();", search_links[0])
            logging.info("Clicked search link")
            time.sleep(3)

        # Set date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Fill date fields
        date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text'][name*='date'], input[id*='date']")
        logging.info(f"Found {len(date_inputs)} date inputs")

        if len(date_inputs) >= 2:
            try:
                date_inputs[0].send_keys(start_date.strftime("%m/%d/%Y"))
                date_inputs[1].send_keys(end_date.strftime("%m/%d/%Y"))
                logging.info(f"Set dates: {start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}")
            except Exception as e:
                logging.warning(f"Could not fill dates: {e}")

        # Select warranty deed document type
        doc_selects = driver.find_elements(By.CSS_SELECTOR, "select")
        for sel in doc_selects:
            try:
                select_obj = Select(sel)
                for opt in ["Warranty Deed", "WD", "DEED"]:
                    try:
                        select_obj.select_by_visible_text(opt)
                        logging.info(f"Selected: {opt}")
                        break
                    except:
                        continue
            except:
                continue

        # Submit
        submit_btns = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        if submit_btns:
            driver.execute_script("arguments[0].click();", submit_btns[0])
            logging.info("Submitted search")
            time.sleep(5)

        # Extract results
        tables = driver.find_elements(By.TAG_NAME, "table")
        logging.info(f"Found {len(tables)} tables")

        data = []
        for table in tables:
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) > 1:
                for idx, row in enumerate(rows[1:]):  # Skip header
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        row_data = [c.text.strip() for c in cells]
                        data.append({
                            'Date': row_data[0] if len(row_data) > 0 else "N/A",
                            'Doc Type': row_data[1] if len(row_data) > 1 else "N/A",
                            'Buyer/Grantee': row_data[2] if len(row_data) > 2 else "N/A",
                            'Seller/Grantor': row_data[3] if len(row_data) > 3 else "N/A",
                            'Address': row_data[4] if len(row_data) > 4 else "N/A",
                            'Amount': row_data[5] if len(row_data) > 5 else "N/A"
                        })
                break

        if not data:
            logging.warning("No data extracted")
            return None

        df = pd.DataFrame(data)
        output_file = f"output/knox_deeds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)

        logging.info(f"✓ SUCCESS: Saved {len(df)} deeds to {output_file}")
        return output_file

    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    scrape_knox()
