#!/usr/bin/env python3
"""
Shelby County (Memphis) Recent Sales Scraper
Scrapes property sales from Shelby County Assessor and Register of Deeds
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
log_file = f"logs/shelby_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
os.makedirs("output", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)

def scrape_shelby():
    """Scrape Shelby County recent sales"""

    logging.info("="*60)
    logging.info("Shelby County (Memphis) Recent Sales Scraper")
    logging.info("="*60)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)

        # Use Shelby County Register of Deeds - public portal with warranty deeds
        url = "https://register.shelby.tn.us/"
        logging.info(f"Loading: {url}")
        driver.get(url)
        time.sleep(5)

        # Look for deed search or document search
        page_text = driver.find_element(By.TAG_NAME, "body").text
        logging.info(f"Page preview: {page_text[:800]}")

        # Look for "PROPERTY SEARCH" link on main page
        search_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "PROPERTY SEARCH")
        if not search_links:
            search_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Search")
        if not search_links:
            search_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Records")

        logging.info(f"Found {len(search_links)} search/records links")

        if search_links:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", search_links[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_links[0])
                logging.info("Clicked search link")
                time.sleep(10)  # Wait longer for JavaScript to load

                # Check current URL
                current_url = driver.current_url
                logging.info(f"Current URL after click: {current_url}")

                # Check for iframes
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                logging.info(f"Found {len(iframes)} iframes")

                if iframes:
                    # Switch to the first iframe
                    driver.switch_to.frame(iframes[0])
                    logging.info("Switched to iframe")
                    time.sleep(3)

                # Debug: See what's on the search page
                page_text = driver.find_element(By.TAG_NAME, "body").text
                logging.info(f"Search page preview: {page_text[:1000]}")

                # Debug: List all inputs and buttons
                all_inputs = driver.find_elements(By.TAG_NAME, "input")
                logging.info(f"Found {len(all_inputs)} input elements total")

                # Count input types
                input_types = {}
                for inp in all_inputs:
                    inp_type = inp.get_attribute("type") or "text"
                    input_types[inp_type] = input_types.get(inp_type, 0) + 1

                logging.info(f"Input type counts: {input_types}")

                # Look specifically for submit/image/button type inputs
                for i, inp in enumerate(all_inputs):
                    inp_type = inp.get_attribute("type") or "text"
                    if inp_type in ["submit", "image", "button"]:
                        inp_name = inp.get_attribute("name") or ""
                        inp_id = inp.get_attribute("id") or ""
                        inp_val = inp.get_attribute("value") or ""
                        logging.info(f"  Found {inp_type} at index {i}: name={inp_name}, id={inp_id}, val={inp_val}")

            except Exception as e:
                logging.warning(f"Could not click search link: {e}")

        # Look for document type dropdown or warranty deed filter
        # Search for warranty deeds from last 90 days (wider range to ensure we get some results)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)

        # Try to find and fill date fields
        date_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='date'], input[type='text'][name*='date'], input[id*='date']")
        logging.info(f"Found {len(date_inputs)} date inputs")

        # TEMPORARILY SKIP DATE FILTERING TO TEST IF WE GET ANY RESULTS
        # if len(date_inputs) >= 2:
        #     try:
        #         date_inputs[0].clear()
        #         date_inputs[0].send_keys(start_date.strftime("%m/%d/%Y"))
        #         date_inputs[1].clear()
        #         date_inputs[1].send_keys(end_date.strftime("%m/%d/%Y"))
        #         logging.info(f"Filled dates: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
        #     except Exception as e:
        #         logging.warning(f"Could not fill dates: {e}")

        # SIMPLER APPROACH: Fill in recent dates and click "Select All Instruments"
        # Then filter for warranty deeds in post-processing

        # Re-enable date filling with last 30 days
        if len(date_inputs) >= 2:
            try:
                date_inputs[0].clear()
                date_inputs[0].send_keys(start_date.strftime("%m/%d/%Y"))
                date_inputs[1].clear()
                date_inputs[1].send_keys(end_date.strftime("%m/%d/%Y"))
                logging.info(f"Filled dates: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
            except Exception as e:
                logging.warning(f"Could not fill dates: {e}")

        # Click "Select All Instruments" button to get all document types
        try:
            select_all_btn = driver.find_element(By.ID, "selectAllButton")
            driver.execute_script("arguments[0].click();", select_all_btn)
            logging.info("Clicked 'Select All Instruments' button")
            time.sleep(1)
        except Exception as e:
            logging.warning(f"Could not click Select All button: {e}")

        # Submit search - look for submit button or image button
        # First try standard submit buttons
        search_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit'], input[type='image']")

        if not search_buttons:
            # Try looking for any button element with submit text
            search_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Search') or contains(text(), 'Submit')]")

        if not search_buttons:
            # Try looking for images that might be submit buttons
            search_buttons = driver.find_elements(By.XPATH, "//img[contains(@alt, 'Search') or contains(@alt, 'Submit') or contains(@src, 'search') or contains(@src, 'submit')]")

        if not search_buttons:
            # Try looking for links that might submit
            search_buttons = driver.find_elements(By.XPATH, "//a[contains(text(), 'Search') or contains(text(), 'Submit')]")

        logging.info(f"Found {len(search_buttons)} search buttons/elements")

        # Try submitting the form directly with JavaScript
        try:
            # Find the form element
            forms = driver.find_elements(By.TAG_NAME, "form")
            logging.info(f"Found {len(forms)} form elements")

            if forms:
                # Submit the first form
                driver.execute_script("arguments[0].submit();", forms[0])
                logging.info("Submitted form via JavaScript")
                time.sleep(10)  # Wait for results to load
            elif search_buttons:
                # Fallback to clicking button
                for i, btn in enumerate(search_buttons[:3]):
                    btn_tag = btn.tag_name
                    btn_text = btn.text[:30] if btn.text else ""
                    logging.info(f"  Button {i}: tag={btn_tag}, text='{btn_text}'")

                driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_buttons[0])
                logging.info("Clicked search button")
                time.sleep(10)
            else:
                logging.warning("No form or submit button found")
        except Exception as e:
            logging.warning(f"Could not submit search: {e}")
            import traceback
            logging.debug(traceback.format_exc())

        # Extract results
        logging.info("Looking for results...")

        # Try to find tables or result divs
        tables = driver.find_elements(By.TAG_NAME, "table")
        logging.info(f"Found {len(tables)} tables")

        # Check all tables and find the one with the most rows (likely the results)
        rows = []
        best_table_idx = -1
        max_rows = 0

        for i, table in enumerate(tables):
            table_rows = table.find_elements(By.TAG_NAME, "tr")
            logging.info(f"  Table {i}: {len(table_rows)} rows")

            # Log first row of tables with multiple rows to see content
            if len(table_rows) > 1:
                first_row_text = table_rows[0].text.strip()[:100]
                second_row_text = table_rows[1].text.strip()[:100] if len(table_rows) > 1 else ""
                logging.info(f"    First row: {first_row_text}")
                logging.info(f"    Second row: {second_row_text}")

            # Find table with most rows (likely the results table)
            if len(table_rows) > max_rows:
                max_rows = len(table_rows)
                rows = table_rows
                best_table_idx = i

        if best_table_idx >= 0:
            logging.info(f"Using table {best_table_idx} with {max_rows} rows as results table")

        if len(rows) == 0:
            # Try the Register of Deeds site instead
            logging.info("No results on Assessor site, trying Register of Deeds...")

            url2 = "https://search.register.shelby.tn.us/search/index.php"
            driver.get(url2)
            time.sleep(3)

            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Register page preview: {page_text[:800]}")

            # Look for date fields to search recent sales
            date_fields = driver.find_elements(By.CSS_SELECTOR, "input[id*='date'], input[name*='date']")
            logging.info(f"Found {len(date_fields)} date fields")

            if len(date_fields) >= 2:
                # Fill in date range for last 60 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=60)

                try:
                    date_fields[0].clear()
                    date_fields[0].send_keys(start_date.strftime("%m/%d/%Y"))
                    date_fields[1].clear()
                    date_fields[1].send_keys(end_date.strftime("%m/%d/%Y"))
                    logging.info(f"Filled dates: {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}")
                except Exception as e:
                    logging.warning(f"Could not fill date fields: {e}")

            # Submit search
            search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            if search_buttons:
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", search_buttons[0])
                    logging.info("Submitted search on Register site")
                    time.sleep(5)
                except Exception as e:
                    logging.warning(f"Could not submit search: {e}")

            # Look for results again
            tables = driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Found {len(tables)} tables on Register site")

            for i, table in enumerate(tables):
                table_rows = table.find_elements(By.TAG_NAME, "tr")
                logging.info(f"  Table {i}: {len(table_rows)} rows")
                if len(table_rows) > 1:
                    rows = table_rows
                    break

        if len(rows) == 0:
            logging.warning("No sales data found on either site")
            return None

        # Extract data from rows
        data = []

        for idx, row in enumerate(rows):
            try:
                # Skip header
                row_text = row.text.strip()
                if not row_text or ('address' in row_text.lower() and 'owner' in row_text.lower()):
                    continue

                cells = row.find_elements(By.TAG_NAME, "td")

                if idx < 3:
                    logging.info(f"Row {idx}: {len(cells)} cells - {[c.text[:30] for c in cells]}")

                if len(cells) < 2:
                    continue

                # Extract: Date, Address, Buyer/Grantee (Owner), Amount
                # For warranty deeds: look for grantee/buyer name
                row_data = [cell.text.strip() for cell in cells]

                # Intelligently map columns
                date = "N/A"
                address = "N/A"
                buyer = "N/A"  # Grantee/Buyer name
                seller = "N/A"  # Grantor/Seller name (optional)
                amount = "N/A"
                doc_type = "N/A"

                for i, cell_text in enumerate(row_data):
                    # Date has /
                    if '/' in cell_text and len(cell_text) < 15:
                        date = cell_text
                    # Amount has $ or is large number
                    elif '$' in cell_text or (cell_text.replace(',', '').replace('.', '').isdigit() and len(cell_text) > 4):
                        amount = cell_text
                    # Document type
                    elif 'deed' in cell_text.lower() or 'wd' == cell_text.lower():
                        doc_type = cell_text
                    # Address has numbers
                    elif any(char.isdigit() for char in cell_text) and len(cell_text) > 5:
                        if address == "N/A":
                            address = cell_text
                    # Buyer/Seller names - typically text without numbers
                    elif cell_text and len(cell_text) > 3:
                        # First name field is usually seller/grantor
                        if seller == "N/A" and not any(char.isdigit() for char in cell_text):
                            seller = cell_text
                        # Second name field is usually buyer/grantee
                        elif buyer == "N/A" and not any(char.isdigit() for char in cell_text):
                            buyer = cell_text

                if address != "N/A" or buyer != "N/A":
                    data.append({
                        'Date': date,
                        'Address': address,
                        'Buyer/Grantee': buyer,
                        'Seller/Grantor': seller,
                        'Amount': amount,
                        'Doc Type': doc_type
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
        output_file = f"output/shelby_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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
    scrape_shelby()
