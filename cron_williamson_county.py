#!/usr/bin/env python3
"""
Williamson County Recent Sales Scraper
Scrapes property sales from Williamson County assessor
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
log_file = f"logs/williamson_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_williamson():
    """Scrape Williamson County recent sales"""

    logging.info("="*60)
    logging.info("Williamson County Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        url = "https://inigo.williamson-tn.org/property_search/"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(3)

        # Calculate date range (last 180 days to ensure we get data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        logging.info(f"Searching for sales from {start_date_str} to {end_date_str}")

        # Fill in the date range fields
        try:
            # DON'T fill date fields - search all records to see if there's any data
            logging.info("Searching ALL records (no date filter) to test data availability")

            # Submit the search
            search_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
            # Scroll to button first
            driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(1)
            # Use JavaScript click to avoid interception
            driver.execute_script("arguments[0].click();", search_button)
            logging.info("Search submitted")
            time.sleep(2)

            # Wait for "Please Wait" message to disappear
            logging.info("Waiting for results to load...")
            max_wait = 30
            for i in range(max_wait):
                page_text = driver.find_element(By.TAG_NAME, "body").text
                if "Please Wait" not in page_text and "processing your request" not in page_text.lower():
                    logging.info(f"Results loaded after {i+1} seconds")
                    break
                time.sleep(1)
            else:
                logging.warning(f"Still waiting after {max_wait} seconds")

            time.sleep(3)  # Extra buffer

        except Exception as e:
            logging.error(f"Error filling search form: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return None

        # Extract results from table
        logging.info("Extracting results...")

        try:
            # Wait for results to load
            time.sleep(5)

            # Try multiple ways to find results
            rows = []

            # Method 1: Look for table rows
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                logging.info(f"Method 1: Found {len(rows)} table rows")
            except:
                logging.info("Method 1: No table tbody rows found")

            # Method 2: Try different table selectors
            if len(rows) == 0:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
                logging.info(f"Method 2: Found {len(rows)} total table rows")
                # Debug what's in these rows
                for i, row in enumerate(rows[:3]):
                    logging.info(f"  Row {i} text: {row.text[:200]}")

            # Method 3: Look for div-based results
            if len(rows) == 0:
                rows = driver.find_elements(By.CSS_SELECTOR, "div[class*='result'], div[class*='property']")
                logging.info(f"Method 3: Found {len(rows)} div results")

            # Debug: Print page source snippet to see what's there
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Page text preview: {page_text[:1000]}")

            data = []

            for idx, row in enumerate(rows):
                try:
                    # Skip header rows
                    row_text = row.text.strip()
                    if not row_text or 'owner' in row_text.lower() and 'address' in row_text.lower():
                        continue

                    cells = row.find_elements(By.TAG_NAME, "td")

                    # Debug first few rows
                    if idx < 3:
                        logging.info(f"Row {idx} has {len(cells)} cells: {[c.text[:30] for c in cells]}")

                    if len(cells) < 3:
                        continue

                    # Extract data based on expected columns:
                    # Owner(s), Property address, City, Parcel description, Lot number, Sale date, Price
                    # Adjust indices based on actual structure
                    owner = cells[0].text.strip() if len(cells) > 0 else "N/A"
                    address = cells[1].text.strip() if len(cells) > 1 else "N/A"
                    city = cells[2].text.strip() if len(cells) > 2 else ""

                    # Look for sale date and price in remaining cells
                    sale_date = "N/A"
                    price = "N/A"

                    for i in range(3, len(cells)):
                        cell_text = cells[i].text.strip()
                        # Price usually has $ or is a large number
                        if '$' in cell_text or (cell_text.replace(',', '').replace('.', '').isdigit() and len(cell_text) > 4):
                            price = cell_text
                        # Date usually has /
                        elif '/' in cell_text and len(cell_text) < 12:
                            sale_date = cell_text

                    # Combine address and city
                    full_address = f"{address}, {city}" if city else address

                    if address and address != "N/A":
                        data.append({
                            'Date': sale_date,
                            'Address': full_address,
                            'Owner Name': owner,
                            'Amount': price
                        })

                except Exception as e:
                    logging.debug(f"Error parsing row {idx}: {e}")
                    continue

            if not data:
                logging.warning("No sales data extracted")
                return None

            # Create DataFrame
            df = pd.DataFrame(data)

            # Save to CSV
            output_file = f"output/williamson_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"✓ SUCCESS: Saved {len(df)} sales")
            logging.info(f"  Output: {output_file}")
            logging.info("="*60)

            return output_file

        except Exception as e:
            logging.error(f"Error extracting results: {e}")
            return None

    except Exception as e:
        logging.error(f"Error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    scrape_williamson()
