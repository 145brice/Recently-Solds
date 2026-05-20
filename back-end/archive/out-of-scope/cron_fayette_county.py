#!/usr/bin/env python3
"""
Fayette County TN Recent Sales Scraper
Scrapes property sales from Tennessee state assessment database
Cron-ready: Runs daily, handles errors, logs output
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
log_file = f"logs/fayette_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_fayette():
    """Scrape Fayette County recent sales"""

    logging.info("="*60)
    logging.info("Fayette County Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        # Try Tennessee state assessment database
        url = "https://assessment.cot.tn.gov/"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(3)

        # Debug: See what's on the page
        page_text = driver.find_element(By.TAG_NAME, "body").text
        logging.info(f"Page preview: {page_text[:800]}")

        # Look for Fayette County selection
        try:
            # Try to find county dropdown or link
            fayette_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Fayette")
            if fayette_links:
                driver.execute_script("arguments[0].scrollIntoView(true);", fayette_links[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", fayette_links[0])
                logging.info("Clicked Fayette County link")
                time.sleep(3)
        except Exception as e:
            logging.warning(f"Could not find Fayette County link: {e}")

        # Look for recent sales or property search
        page_text = driver.find_element(By.TAG_NAME, "body").text
        logging.info(f"After county selection: {page_text[:800]}")

        # Try to find sales search or recent sales link
        sales_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Sales")
        if not sales_links:
            sales_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Recent")

        if sales_links:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", sales_links[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", sales_links[0])
                logging.info("Clicked sales link")
                time.sleep(3)
            except Exception as e:
                logging.warning(f"Could not click sales link: {e}")

        # Look for search form with date fields
        date_fields = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text'][name*='date'], input[id*='date']")
        logging.info(f"Found {len(date_fields)} date-related fields")

        if len(date_fields) >= 2:
            # Fill in date range for last 180 days
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)

            try:
                date_fields[0].clear()
                date_fields[0].send_keys(start_date.strftime("%m/%d/%Y"))
                date_fields[1].clear()
                date_fields[1].send_keys(end_date.strftime("%m/%d/%Y"))
                logging.info(f"Filled dates: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
            except Exception as e:
                logging.warning(f"Could not fill date fields: {e}")

        # Submit search
        search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button:contains('Search')")
        if search_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_buttons[0])
                logging.info("Submitted search")
                time.sleep(5)
            except Exception as e:
                logging.warning(f"Could not submit search: {e}")

        # Look for results
        page_text = driver.find_element(By.TAG_NAME, "body").text
        logging.info(f"Results page: {page_text[:1000]}")

        tables = driver.find_elements(By.TAG_NAME, "table")
        logging.info(f"Found {len(tables)} tables")

        rows = []
        for i, table in enumerate(tables):
            table_rows = table.find_elements(By.TAG_NAME, "tr")
            logging.info(f"  Table {i}: {len(table_rows)} rows")
            if len(table_rows) > 1:
                rows = table_rows
                break

        if len(rows) == 0:
            logging.warning("No data found - Fayette County may not have recent sales export on state database")
            logging.info("Recommendation: Contact Fayette County Assessor directly for sales data")
            return None

        # Extract data
        data = []

        for idx, row in enumerate(rows):
            try:
                row_text = row.text.strip()
                if not row_text or ('address' in row_text.lower() and 'owner' in row_text.lower()):
                    continue

                cells = row.find_elements(By.TAG_NAME, "td")

                if idx < 3:
                    logging.info(f"Row {idx}: {len(cells)} cells - {[c.text[:30] for c in cells]}")

                if len(cells) < 2:
                    continue

                row_data = [cell.text.strip() for cell in cells]

                # Extract fields
                date = "N/A"
                address = "N/A"
                owner = "N/A"
                amount = "N/A"

                for cell_text in row_data:
                    if '/' in cell_text and len(cell_text) < 15:
                        date = cell_text
                    elif '$' in cell_text:
                        amount = cell_text
                    elif any(char.isdigit() for char in cell_text) and len(cell_text) > 5:
                        if address == "N/A":
                            address = cell_text
                    elif cell_text and len(cell_text) > 3:
                        if owner == "N/A":
                            owner = cell_text

                if address != "N/A" or amount != "N/A":
                    data.append({
                        'Date': date,
                        'Address': address,
                        'Owner Name': owner,
                        'Amount': amount
                    })

            except Exception as e:
                logging.debug(f"Error parsing row {idx}: {e}")
                continue

        if not data:
            logging.warning("No sales data extracted")
            return None

        df = pd.DataFrame(data)
        output_file = f"output/fayette_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(output_file, index=False)

        logging.info("="*60)
        logging.info(f"✓ SUCCESS: Saved {len(df)} sales")
        logging.info(f"  Output: {output_file}")
        logging.info("="*60)

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
    scrape_fayette()
