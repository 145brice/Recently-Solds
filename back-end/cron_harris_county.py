#!/usr/bin/env python3
"""
Harris County (Houston, TX) Warranty Deed Scraper
Scrapes property records from Harris County Clerk's public search
Public portal: https://www.cclerk.hctx.net/applications/websearch/RP.aspx
Records from 1836 to present - free watermarked copies available
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
log_file = f"logs/harris_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_harris():
    """Scrape Harris County warranty deeds - last 30 days"""

    logging.info("="*60)
    logging.info("Harris County (Houston, TX) Warranty Deed Scraper")
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

        url = "https://www.cclerk.hctx.net/applications/websearch/RP.aspx"
        logging.info(f"Loading: {url}")
        driver.get(url)

        time.sleep(3)

        # Try to find search form
        logging.info("Looking for search form...")

        # Look for document type dropdown
        try:
            doc_type = Select(driver.find_element(By.ID, "cphContent_ddlDocType"))
            doc_type.select_by_visible_text("DEED")
            logging.info("Selected document type: DEED")
        except Exception as e:
            logging.warning(f"Could not find doc type dropdown: {e}")

        # Set date range - last 30 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        try:
            date_from = driver.find_element(By.ID, "cphContent_txtDateFrom")
            date_from.clear()
            date_from.send_keys(start_date.strftime("%m/%d/%Y"))
            logging.info(f"Set start date: {start_date.strftime('%m/%d/%Y')}")
        except Exception as e:
            logging.warning(f"Could not set start date: {e}")

        try:
            date_to = driver.find_element(By.ID, "cphContent_txtDateTo")
            date_to.clear()
            date_to.send_keys(end_date.strftime("%m/%d/%Y"))
            logging.info(f"Set end date: {end_date.strftime('%m/%d/%Y')}")
        except Exception as e:
            logging.warning(f"Could not set end date: {e}")

        # Click search button
        try:
            search_btn = driver.find_element(By.ID, "cphContent_btnSearch")
            search_btn.click()
            logging.info("Clicked search button")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Could not click search: {e}")
            return []

        # Extract results
        logging.info("Looking for results...")

        try:
            # Look for results table
            tables = driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Found {len(tables)} tables")

            # Try to find results in grid view
            rows = driver.find_elements(By.CSS_SELECTOR, "tr[class*='Grid']")
            logging.info(f"Found {len(rows)} result rows")

            for row in rows[:10]:  # Test first 10
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 4:
                        record = {
                            'date': cells[0].text.strip(),
                            'doc_type': cells[1].text.strip(),
                            'parties': cells[2].text.strip(),
                            'doc_number': cells[3].text.strip(),
                            'county': 'Harris',
                            'state': 'TX',
                            'scraped_date': datetime.now().strftime('%Y-%m-%d')
                        }
                        all_records.append(record)
                except Exception as e:
                    logging.warning(f"Error parsing row: {e}")
                    continue

            logging.info(f"Extracted {len(all_records)} records")

        except Exception as e:
            logging.error(f"Error extracting results: {e}")

        # Save to CSV
        if all_records:
            df = pd.DataFrame(all_records)
            output_file = f"output/harris_deeds_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False)
            logging.info(f"✓ Saved {len(all_records)} records to {output_file}")
        else:
            logging.warning("No records extracted")

    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

    finally:
        if driver:
            driver.quit()

    return all_records

if __name__ == "__main__":
    records = scrape_harris()
    print(f"\nCompleted: {len(records)} records scraped")
