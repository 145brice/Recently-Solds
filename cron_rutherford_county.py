#!/usr/bin/env python3
"""
Rutherford County Recent Sales Scraper
Uses the new WebPro 5 system at secured.rutherfordcountytn.gov
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    all_sales = []

    try:
        driver = webdriver.Edge(options=options)
        driver.set_page_load_timeout(90)

        # Load the new WebPro 5 property search page
        url = "https://secured.rutherfordcountytn.gov/OFS/WP/Home"
        logging.info(f"Loading WebPro 5 page: {url}")
        driver.get(url)
        time.sleep(5)

        # Calculate date range (last 30 days for more results)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        logging.info(f"Searching for sales from {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")

        # Click Advanced Search
        try:
            adv_search = driver.find_element(By.LINK_TEXT, "Advanced Search")
            adv_search.click()
            logging.info("Clicked Advanced Search")
            time.sleep(3)
        except Exception as e:
            logging.warning(f"Could not click Advanced Search: {e}")

        # Fill in sale date fields
        try:
            date_start = driver.find_element(By.ID, "SaleDateStart")
            date_start.clear()
            date_start.send_keys(start_date.strftime('%m/%d/%Y'))
            
            date_end = driver.find_element(By.ID, "SaleDateEnd")
            date_end.clear()
            date_end.send_keys(end_date.strftime('%m/%d/%Y'))
            
            logging.info(f"Filled sale date fields")
            time.sleep(2)
        except Exception as e:
            logging.error(f"Could not fill date fields: {e}")

        # Submit the search
        try:
            search_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Search']")
            driver.execute_script("arguments[0].scrollIntoView(true);", search_btn)
            time.sleep(1)
            driver.execute_script("arguments[0].click();", search_btn)
            logging.info("Submitted search")
            
            # Wait for AJAX results to load
            time.sleep(15)  # Longer wait for AJAX
            
            # Wait for results grid to populate
            try:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.ID, "gridSearchResults2"))
                )
                logging.info("Results grid loaded")
                time.sleep(5)  # Extra wait for content
            except:
                logging.warning("Results grid did not load in time")
                
        except Exception as e:
            logging.warning(f"Could not submit search: {e}")

        # Wait for results to load
        logging.info("Waiting for results...")
        time.sleep(5)

        # Look for results in the grid
        try:
            # The results load into #gridSearchResults2
            results_grid = driver.find_element(By.ID, "gridSearchResults2")
            
            # Look for table rows within the results grid
            rows = results_grid.find_elements(By.CSS_SELECTOR, "table tbody tr")
            logging.info(f"Found {len(rows)} result rows in grid")
            
            if len(rows) > 0:
                # Get table headers to understand column structure
                headers = driver.find_elements(By.CSS_SELECTOR, "#gridSearchResults2 table thead th")
                header_names = [h.text.strip() for h in headers]
                logging.info(f"Table columns: {header_names}")
                
                # Extract data from each row
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        cell_data = [cell.text.strip() for cell in cells]
                        
                        # Map based on typical structure: Parcel, Owner, Address, Sale Date, Sale Price, etc.
                        sale_data = {
                            'Parcel': cell_data[0] if len(cell_data) > 0 else '',
                            'Owner Name': cell_data[1] if len(cell_data) > 1 else '',
                            'Address': cell_data[2] if len(cell_data) > 2 else '',
                            'Sale Date': cell_data[3] if len(cell_data) > 3 else '',
                            'Sale Price': cell_data[4] if len(cell_data) > 4 else ''
                        }
                        
                        if sale_data['Address'] or sale_data['Owner Name']:
                            all_sales.append(sale_data)
                
                logging.info(f"Extracted {len(all_sales)} sales from grid")
            
        except Exception as e:
            logging.error(f"Error extracting from results grid: {e}")

        # Collect data from pages
        page_num = 1
        max_pages = 100

        while page_num <= max_pages:
            logging.info(f"Processing page {page_num}")
            
            try:
                # Look for results - could be in table or div structure
                rows = driver.find_elements(By.CSS_SELECTOR, "table tr, .property-row, .result-row")
                logging.info(f"Found {len(rows)} potential result elements")
                
                for row in rows:
                    try:
                        text = row.text.strip()
                        if text and len(text) > 10:  # Has substantial content
                            # Try to extract structured data
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 3:
                                sale_data = {
                                    'Date': cells[0].text.strip() if len(cells) > 0 else '',
                                    'Address': cells[1].text.strip() if len(cells) > 1 else '',
                                    'Owner Name': cells[2].text.strip() if len(cells) > 2 else '',
                                    'Amount': cells[3].text.strip() if len(cells) > 3 else ''
                                }
                                
                                if sale_data['Address']:
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
                            logging.info("Next button is disabled")
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
            output_file = f"output/rutherford_sales_{timestamp}.csv"

            df = pd.DataFrame(all_sales)
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"SUCCESS: Found {len(all_sales)} sales")
            logging.info(f"Saved to: {output_file}")
            logging.info("="*60)

            return output_file
        else:
            logging.warning("No sales data found")
            logging.info("Saving page source for debugging...")
            with open("output/rutherford_debug.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("Saved to output/rutherford_debug.html")
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
        result = scrape_rutherford()
        if result:
            print(f"\nSuccess! Output: {result}")
        else:
            print("\nFailed to get data - check logs and debug.html")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
