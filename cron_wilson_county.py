#!/usr/bin/env python3
"""
Wilson County Recent Sales Scraper
Scrapes property sales from Wilson County (GeoPowered platform)
Cron-ready: Runs daily, handles errors, logs output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import pandas as pd
import logging
from datetime import datetime, timedelta
import os
import time

# Setup
log_file = f"logs/wilson_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_wilson():
    """Scrape Wilson County recent sales"""

    logging.info("="*60)
    logging.info("Wilson County Recent Sales Scraper")
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

        url = "https://wilsontn.geopowered.com/propertysearch/"
        logging.info(f"Loading Wilson County property search: {url}")
        driver.get(url)
        time.sleep(10)  # Give extra time for JavaScript framework to load

        # Calculate date range (last 7 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        logging.info(f"Searching for sales from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

        # Wait for page to fully load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)
            
            # Try to find search fields/buttons
            # GeoPowered uses JavaScript framework, so we need to wait and interact carefully
            
            # Look for any search/filter controls
            try:
                # Try clicking on search tab or sales search if available
                search_tabs = driver.find_elements(By.XPATH, "//*[contains(text(), 'Search')] | //*[contains(text(), 'Sales')]")
                if search_tabs:
                    driver.execute_script("arguments[0].click();", search_tabs[0])
                    logging.info("Clicked search/sales tab")
                    time.sleep(3)
            except Exception as e:
                logging.warning(f"No search tab found: {e}")
            
            # Look for date fields
            try:
                date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text']")
                logging.info(f"Found {len(date_inputs)} input fields")
                
                # Try to fill any date-related fields
                for field in date_inputs:
                    field_name = (field.get_attribute('name') or field.get_attribute('id') or '').lower()
                    placeholder = (field.get_attribute('placeholder') or '').lower()
                    
                    if 'date' in field_name or 'date' in placeholder:
                        try:
                            if 'from' in field_name or 'start' in field_name or 'from' in placeholder:
                                field.clear()
                                field.send_keys(start_date.strftime('%m/%d/%Y'))
                                logging.info(f"Filled start date field")
                            elif 'to' in field_name or 'end' in field_name or 'to' in placeholder:
                                field.clear()
                                field.send_keys(end_date.strftime('%m/%d/%Y'))
                                logging.info(f"Filled end date field")
                        except:
                            pass
                            
                time.sleep(2)
            except Exception as e:
                logging.warning(f"Could not fill date fields: {e}")
            
            # Try to submit search
            try:
                search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button")
                for btn in search_buttons:
                    btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                    if 'search' in btn_text or 'submit' in btn_text or 'find' in btn_text:
                        driver.execute_script("arguments[0].click();", btn)
                        logging.info("Submitted search")
                        time.sleep(5)
                        break
            except Exception as e:
                logging.warning(f"Could not submit search: {e}")
            
        except Exception as e:
            logging.error(f"Error interacting with search form: {e}")

        # Try to extract results
        logging.info("Looking for results...")
        time.sleep(5)

        # Collect data from pages
        page_num = 1
        max_pages = 100

        while page_num <= max_pages:
            logging.info(f"Processing page {page_num}")
            
            try:
                # Try multiple selectors for results
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr, .property-result, .search-result, [data-property]")
                logging.info(f"Found {len(rows)} potential result elements")
                
                if len(rows) == 0:
                    # No results found, log page source snippet for debugging
                    page_text = driver.find_element(By.TAG_NAME, "body").text[:500]
                    logging.warning(f"No results found. Page preview: {page_text}")
                    break
                
                for row in rows:
                    try:
                        text = row.text.strip()
                        if len(text) < 10:  # Skip empty/small elements
                            continue
                            
                        # Try to extract from table structure
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        if len(cells) >= 2:
                            # Table structure - extract cells
                            row_data = [cell.text.strip() for cell in cells]
                            sale_data = {
                                'Owner Name': row_data[0] if len(row_data) > 0 else '',
                                'Address': row_data[1] if len(row_data) > 1 else '',
                                'City': row_data[2] if len(row_data) > 2 else '',
                                'Info': row_data[3] if len(row_data) > 3 else ''
                            }
                        else:
                            # Non-table structure - use text parsing
                            sale_data = {
                                'Owner Name': '',
                                'Address': text[:100],
                                'City': '',
                                'Info': ''
                            }
                        
                        if sale_data['Address'] or sale_data['Owner Name']:
                            all_sales.append(sale_data)
                            
                    except Exception as e:
                        continue

                logging.info(f"Collected {len(all_sales)} sales so far")

                # Try to go to next page
                try:
                    next_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Next')] | //button[contains(text(), 'Next')] | //*[contains(@class, 'next')]")
                    if next_buttons:
                        next_btn = next_buttons[0]
                        if 'disabled' not in next_btn.get_attribute('class'):
                            driver.execute_script("arguments[0].click();", next_btn)
                            logging.info(f"Clicked Next to page {page_num + 1}")
                            time.sleep(3)
                            page_num += 1
                        else:
                            logging.info("Next button disabled")
                            break
                    else:
                        logging.info("No Next button found")
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
            output_file = f"output/wilson_sales_{timestamp}.csv"

            df = pd.DataFrame(all_sales)
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"SUCCESS: Found {len(all_sales)} sales")
            logging.info(f"Saved to: {output_file}")
            logging.info("="*60)

            return output_file
        else:
            logging.warning("No sales data found")
            logging.info("Wilson County site may require JavaScript interaction or different approach")
            
            # Save page source for debugging
            with open("output/wilson_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("Saved page source to output/wilson_debug.html for debugging")
            
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
        result = scrape_wilson()
        if result:
            print(f"\nSuccess! Output: {result}")
        else:
            print("\nFailed to get data - check logs and debug.html")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
