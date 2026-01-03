#!/usr/bin/env python3
"""
Rutherford County Recent Sales Scraper
Scrapes property sales from Rutherford County assessor
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
log_file = f"logs/rutherford_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_rutherford():
    """Scrape Rutherford County recent sales"""

    logging.info("="*60)
    logging.info("Rutherford County Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        url = "https://secured.rutherfordcountytn.gov/propertydata/RealPropertySearch2.aspx"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(3)

        # Calculate date range (last 180 days to get more data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        logging.info(f"Searching for sales from {start_date_str} to {end_date_str}")

        # Look for the property sales search
        try:
            # Debug: See what's on the page
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Page preview: {page_text[:800]}")

            # Click on Advanced Search to get a better interface
            try:
                adv_search_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Advanced Search")
                driver.execute_script("arguments[0].scrollIntoView(true);", adv_search_link)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", adv_search_link)
                time.sleep(3)
                logging.info("Clicked on Advanced Search")
            except Exception as e:
                logging.warning(f"Could not click Advanced Search: {e}")

            # Now try to find Real Property Sales search
            try:
                # Look for link/button to sales search
                sales_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Search for Real Property Sales")
                driver.execute_script("arguments[0].scrollIntoView(true);", sales_link)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", sales_link)
                time.sleep(3)
                logging.info("Clicked on Real Property Sales link")

                # After clicking sales link, page should show sales search form
                page_text = driver.find_element(By.TAG_NAME, "body").text
                logging.info(f"Sales page preview: {page_text[:600]}")

            except Exception as e:
                logging.warning(f"Could not find Sales link: {e}")

            # Submit search
            search_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")

            logging.info(f"Found {len(search_buttons)} search buttons")

            if search_buttons:
                for i, btn in enumerate(search_buttons[:3]):
                    btn_text = btn.get_attribute("value") or btn.text or ""
                    logging.info(f"  Button {i}: {btn_text}")

                # Click the first search button
                driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_buttons[0])
                logging.info("Search submitted")

                # Wait for results to load
                logging.info("Waiting for results...")
                time.sleep(8)

        except Exception as e:
            logging.error(f"Error with search form: {e}")
            import traceback
            logging.error(traceback.format_exc())

        # Extract results
        logging.info("Extracting results...")

        try:
            # Wait for results
            time.sleep(3)

            # Debug: Print page text after search
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Results page preview: {page_text[:1000]}")

            # Find results table
            tables = driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Found {len(tables)} tables on page")

            results_table = None
            for i, table in enumerate(tables):
                # Look for a table with multiple rows (results)
                rows = table.find_elements(By.TAG_NAME, "tr")
                logging.info(f"  Table {i}: {len(rows)} rows")
                if len(rows) > 1:  # At least header + one row
                    results_table = table
                    logging.info(f"  Using table {i} as results table")
                    break

            if not results_table:
                logging.warning("No results table found")
                return None

            # Try both tbody and regular tr selectors
            rows = results_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            if len(rows) == 0:
                rows = results_table.find_elements(By.TAG_NAME, "tr")

            logging.info(f"Found {len(rows)} total rows to process")

            data = []

            for idx, row in enumerate(rows):
                try:
                    # Skip header row
                    row_text = row.text.strip()
                    if not row_text or ('owner' in row_text.lower() and 'address' in row_text.lower()):
                        continue

                    cells = row.find_elements(By.TAG_NAME, "td")

                    # Debug first few rows
                    if idx < 3:
                        logging.info(f"Row {idx}: {len(cells)} cells - {[c.text[:30] for c in cells]}")

                    if len(cells) < 2:
                        continue

                    # Try to extract data
                    # The exact column order may vary - this is a best guess
                    # Common fields: Owner, Address, Sale Date, Sale Price

                    # Attempt to map columns intelligently
                    row_data = [cell.text.strip() for cell in cells]

                    # Try to identify which column is which
                    owner = "N/A"
                    address = "N/A"
                    sale_date = "N/A"
                    price = "N/A"

                    for i, cell_text in enumerate(row_data):
                        # Look for price (contains $ or looks like a number)
                        if '$' in cell_text or (cell_text.replace(',', '').replace('.', '').isdigit() and len(cell_text) > 3):
                            price = cell_text

                        # Look for date (contains / or -)
                        elif '/' in cell_text or '-' in cell_text:
                            if len(cell_text) < 15:  # Dates are typically short
                                sale_date = cell_text

                        # Address typically has numbers
                        elif any(char.isdigit() for char in cell_text) and len(cell_text) > 5:
                            if address == "N/A":
                                address = cell_text

                        # Owner name is typically text without numbers
                        elif cell_text and not any(char.isdigit() for char in cell_text) and len(cell_text) > 3:
                            if owner == "N/A":
                                owner = cell_text

                    # If we still don't have data, use positional extraction
                    if address == "N/A" and len(row_data) > 0:
                        address = row_data[0]
                    if owner == "N/A" and len(row_data) > 1:
                        owner = row_data[1]
                    if sale_date == "N/A" and len(row_data) > 2:
                        sale_date = row_data[2]
                    if price == "N/A" and len(row_data) > 3:
                        price = row_data[3]

                    data.append({
                        'Date': sale_date,
                        'Address': address,
                        'Owner Name': owner,
                        'Amount': price
                    })

                except Exception as e:
                    logging.debug(f"Error parsing row: {e}")
                    continue

            if not data:
                logging.warning("No sales data extracted")
                return None

            # Create DataFrame
            df = pd.DataFrame(data)

            # Save to CSV
            output_file = f"output/rutherford_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"✓ SUCCESS: Saved {len(df)} sales")
            logging.info(f"  Output: {output_file}")
            logging.info("  NOTE: Column mapping may need verification")
            logging.info("="*60)

            return output_file

        except Exception as e:
            logging.error(f"Error extracting results: {e}")
            import traceback
            logging.error(traceback.format_exc())
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
    scrape_rutherford()
