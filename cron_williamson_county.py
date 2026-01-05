#!/usr/bin/env python3
"""
Williamson County Recent Sales Scraper
Scrapes property sales from Williamson County assessor
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

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(90)  # Increased timeout

        # Try the sales search directly
        url = "https://inigo.williamson-tn.org/sales_search/"
        logging.info(f"Loading sales search: {url}")
        driver.get(url)
        time.sleep(5)

        # Calculate date range (last 30 days for recent sales - more focused)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        logging.info(f"Searching for sales from {start_date_str} to {end_date_str}")

        # Fill in the date range fields
        try:
            # Find date inputs by looking for common patterns
            date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='date'], input[name*='date'], input[id*='date']")
            
            filled_start = False
            filled_end = False
            
            for field in date_inputs:
                field_name = (field.get_attribute('name') or field.get_attribute('id') or '').lower()
                placeholder = (field.get_attribute('placeholder') or '').lower()
                
                if not filled_start and ('from' in field_name or 'start' in field_name or 'from' in placeholder):
                    field.clear()
                    field.send_keys(start_date_str)
                    logging.info(f"Filled start date in: {field_name or placeholder}")
                    filled_start = True
                elif not filled_end and ('to' in field_name or 'end' in field_name or 'to' in placeholder):
                    field.clear()
                    field.send_keys(end_date_str)
                    logging.info(f"Filled end date in: {field_name or placeholder}")
                    filled_end = True
            
            if not filled_start or not filled_end:
                logging.warning(f"Could not fill date fields - filled_start:{filled_start}, filled_end:{filled_end}")

            time.sleep(2)

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

            # Try to load all results by scrolling or clicking "show more"
            try:
                # Look for pagination or "show all" button
                show_all_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Show All') or contains(text(), 'View All')]")
                if show_all_buttons:
                    driver.execute_script("arguments[0].click();", show_all_buttons[0])
                    logging.info("Clicked 'Show All' button")
                    time.sleep(3)
                else:
                    # Try scrolling to load lazy-loaded content
                    last_height = driver.execute_script("return document.body.scrollHeight")
                    for _ in range(10):  # Scroll up to 10 times
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(1)
                        new_height = driver.execute_script("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                    logging.info("Scrolled to bottom to load all results")
            except Exception as e:
                logging.info(f"No pagination needed or scroll failed: {e}")

            # Try multiple ways to find results
            rows = []
            all_data = []
            
            # Check for pagination and collect all pages
            page_num = 1
            max_pages = 50  # Safety limit
            
            while page_num <= max_pages:
                logging.info(f"Processing page {page_num}...")
                time.sleep(2)
                
                # Method 1: Look for table rows
                page_rows = []
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "table"))
                    )
                    page_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    logging.info(f"  Found {len(page_rows)} rows on page {page_num}")
                except Exception as e:
                    logging.info(f"  No tbody rows - {e}")

                    page_rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    logging.info(f"  Found {len(page_rows)} rows on page {page_num}")
                except Exception as e:
                    logging.info(f"  No tbody rows - {e}")

                if len(page_rows) == 0:
                    try:
                        page_rows = driver.find_elements(By.CSS_SELECTOR, "table tr")
                        logging.info(f"  Found {len(page_rows)} table rows on page {page_num}")
                    except:
                        pass
                
                if len(page_rows) == 0:
                    logging.info("  No rows found on this page")
                    break
                
                # Process rows on this page
                for idx, row in enumerate(page_rows):
                    try:
                        row_text = row.text.strip()
                        if not row_text or 'owner' in row_text.lower() and 'address' in row_text.lower():
                            continue

                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) < 3:
                            continue

                        owner = cells[0].text.strip() if len(cells) > 0 else "N/A"
                        address = cells[1].text.strip() if len(cells) > 1 else "N/A"
                        city = cells[2].text.strip() if len(cells) > 2 else ""

                        sale_date = "N/A"
                        price = "N/A"

                        for i in range(3, len(cells)):
                            cell_text = cells[i].text.strip()
                            if '$' in cell_text or (cell_text.replace(',', '').replace('.', '').isdigit() and len(cell_text) > 4):
                                price = cell_text
                            elif '/' in cell_text and len(cell_text) < 12:
                                sale_date = cell_text

                        full_address = f"{address}, {city}" if city else address

                        if address and address != "N/A":
                            all_data.append({
                                'Date': sale_date,
                                'Address': full_address,
                                'Owner Name': owner,
                                'Amount': price
                            })

                    except Exception as e:
                        continue
                
                # Look for "Next" button or pagination
                try:
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')] | //button[contains(text(), 'Next')] | //a[contains(@class, 'next')]")
                    if next_buttons and next_buttons[0].is_enabled():
                        driver.execute_script("arguments[0].scrollIntoView(true);", next_buttons[0])
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", next_buttons[0])
                        logging.info(f"  Clicked Next button for page {page_num + 1}")
                        page_num += 1
                        time.sleep(3)
                    else:
                        logging.info("  No more pages")
                        break
                except Exception as e:
                    logging.info(f"  No Next button found - {e}")
                    break

            logging.info(f"Total rows collected from all pages: {len(all_data)}")

            # Use the collected data instead of processing rows again
            data = all_data

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
