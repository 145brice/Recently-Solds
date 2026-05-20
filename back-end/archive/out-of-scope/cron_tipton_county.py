#!/usr/bin/env python3
"""
Tipton County TN Recent Sales Scraper
Scrapes property sales from Tipton County GeoPowered site
Cron-ready: Runs daily, handles errors, logs output
NOTE: Uses GeoPowered platform which may have timeout issues
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
log_file = f"logs/tipton_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_tipton():
    """Scrape Tipton County recent sales"""

    logging.info("="*60)
    logging.info("Tipton County Recent Sales Scraper")
    logging.info("="*60)
    logging.info("NOTE: Uses GeoPowered platform - may be slow")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(90)  # Increased for GeoPowered

        url = "https://tiptontn.geopowered.com/PropertySearch/"
        logging.info(f"Loading: {url}")

        # Try to load with timeout handling
        try:
            driver.get(url)
        except Exception as e:
            logging.warning(f"Page load timeout/error: {e}")
            logging.info("Continuing anyway - page may be partially loaded")

        time.sleep(10)  # Extra time for JavaScript

        # Debug
        try:
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Page preview: {page_text[:500]}")
        except:
            logging.warning("Could not get page text")

        # Look for search interface
        search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button")
        logging.info(f"Found {len(search_buttons)} potential search buttons")

        if search_buttons:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_buttons[0])
                logging.info("Clicked search button")
                time.sleep(10)
            except Exception as e:
                logging.warning(f"Could not click search: {e}")

        # Look for results
        time.sleep(5)

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
            # Try looking for divs
            result_divs = driver.find_elements(By.CSS_SELECTOR, "div[class*='result'], div[class*='property']")
            logging.info(f"Found {len(result_divs)} result divs")

        if len(rows) == 0:
            logging.warning("No data found - GeoPowered site may be too slow or empty")
            logging.info("Recommendation: Try non-headless browser or contact Tipton County for data export")
            return None

        # Extract data
        data = []

        for idx, row in enumerate(rows):
            try:
                row_text = row.text.strip()
                if not row_text:
                    continue

                cells = row.find_elements(By.TAG_NAME, "td")

                if idx < 3:
                    logging.info(f"Row {idx}: {len(cells)} cells - {[c.text[:30] for c in cells]}")

                if len(cells) < 2:
                    continue

                row_data = [cell.text.strip() for cell in cells]

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
        output_file = f"output/tipton_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
    scrape_tipton()
