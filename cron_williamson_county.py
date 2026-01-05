#!/usr/bin/env python3
"""
Williamson County Recent Sales Scraper
Scrapes property sales from Williamson County property search
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    all_sales = []

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(90)

        # Use the property search page which has sales date filters
        url = "https://inigo.williamson-tn.org/property_search/"
        logging.info(f"Loading property search page: {url}")
        driver.get(url)
        time.sleep(5)

        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        logging.info(f"Searching for sales from {start_date_str} to {end_date_str}")

        # Fill in the sales_date_start and sales_date_end fields
        try:
            date_from = driver.find_element(By.NAME, "sales_date_start")
            date_from.clear()
            date_from.send_keys(start_date_str)
            
            date_to = driver.find_element(By.NAME, "sales_date_end")
            date_to.clear()
            date_to.send_keys(end_date_str)
            
            logging.info(f"Filled date fields successfully")
            time.sleep(2)
        except Exception as e:
            logging.error(f"Could not find/fill date fields: {e}")
            # Continue anyway - search without dates

        # Submit the search
        try:
            search_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
            driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", search_button)
            logging.info("Search submitted")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Could not submit search: {e}")
            return None

        # Wait for results
        logging.info("Waiting for results to load...")
        time.sleep(5)

        # Collect data from all pages
        page_num = 1
        max_pages = 100  # Safety limit

        while page_num <= max_pages:
            logging.info(f"Processing page {page_num}")
            
            # Get current page data
            try:
                # Look for table rows
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
                logging.info(f"Found {len(rows)} rows on page {page_num}")
                
                for row in rows[1:]:  # Skip header
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 1:
                            # Get text from each cell separately
                            row_data = [cell.text.strip() for cell in cells]
                            
                            # The table structure is: Owner Name, Address, City/Tax Info, Map Number
                            # We need to extract what we can
                            if len(row_data) >= 2:
                                sale_data = {
                                    'Owner Name': row_data[0] if len(row_data) > 0 else '',
                                    'Address': row_data[1] if len(row_data) > 1 else '',
                                    'City': row_data[2] if len(row_data) > 2 else '',
                                    'Map Number': row_data[3] if len(row_data) > 3 else ''
                                }
                                
                                # Only add if we have actual data
                                if sale_data['Owner Name'] and sale_data['Address']:
                                    all_sales.append(sale_data)
                    except Exception as e:
                        continue

                logging.info(f"Collected {len(all_sales)} sales so far")

                # Try to click Next button
                try:
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')] | //button[contains(text(), 'Next')]")
                    if next_buttons:
                        # Check if next button is disabled
                        next_btn = next_buttons[0]
                        if 'disabled' not in next_btn.get_attribute('class'):
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            time.sleep(1)
                            driver.execute_script("arguments[0].click();", next_btn)
                            logging.info(f"Clicked Next to page {page_num + 1}")
                            time.sleep(3)
                            page_num += 1
                        else:
                            logging.info("Next button is disabled - reached last page")
                            break
                    else:
                        logging.info("No Next button found - only one page of results")
                        break
                except Exception as e:
                    logging.info(f"No more pages: {e}")
                    break

            except Exception as e:
                logging.error(f"Error processing page {page_num}: {e}")
                break

        # Save results
        if all_sales:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"output/williamson_sales_{timestamp}.csv"

            df = pd.DataFrame(all_sales)
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"SUCCESS: Found {len(all_sales)} sales")
            logging.info(f"Saved to: {output_file}")
            logging.info("="*60)

            return output_file
        else:
            logging.warning("No sales data found")
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
        result = scrape_williamson()
        if result:
            print(f"\nSuccess! Output: {result}")
        else:
            print("\nFailed to get data")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
