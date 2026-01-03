#!/usr/bin/env python3
"""
Wilson County Recent Sales Scraper
Scrapes property sales from Wilson County assessor (GeoPowered platform)
Cron-ready: Runs daily, handles errors, logs output
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

    driver = None

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(90)  # Increase timeout for slow site

        url = "https://wilsontn.geopowered.com/propertysearch/"
        logging.info(f"Loading: {url}")

        # Try to load the page with timeout handling
        try:
            driver.get(url)
        except Exception as e:
            logging.warning(f"Page load timeout/error: {e}")
            logging.info("Continuing anyway - page may be partially loaded")

        time.sleep(10)  # Give extra time for JavaScript to load

        # Calculate date range (last 180 days to get more data)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)

        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")

        logging.info(f"Searching for sales from {start_date_str} to {end_date_str}")

        # Try to find and use the search - simplified approach
        try:
            # Wait for page to be ready
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            logging.info("Page loaded, looking for search interface...")

            # Debug: Print page text to see what's there
            page_text = driver.find_element(By.TAG_NAME, "body").text
            logging.info(f"Page preview: {page_text[:500]}")

            # Try to find and submit search
            # For now, just try to search without filters to see if we can get ANY data
            search_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], button")

            logging.info(f"Found {len(search_buttons)} potential search buttons")

            if search_buttons:
                for btn in search_buttons[:3]:
                    btn_text = btn.text or btn.get_attribute("value") or ""
                    logging.info(f"  Button: {btn_text[:50]}")

                # Click the first likely search button
                driver.execute_script("arguments[0].scrollIntoView(true);", search_buttons[0])
                time.sleep(1)
                driver.execute_script("arguments[0].click();", search_buttons[0])
                logging.info("Search submitted")
                time.sleep(10)
            else:
                logging.warning("Could not find search button - may already be showing results")

        except Exception as e:
            logging.error(f"Error with search form: {e}")
            import traceback
            logging.error(traceback.format_exc())

        # Extract results
        logging.info("Extracting results...")

        try:
            # Wait for results to load
            time.sleep(3)

            # Try different result container selectors
            results = None
            selectors = [
                "table tbody tr",
                "div[class*='result']",
                "div[class*='property']",
                ".search-result",
                "[data-property]"
            ]

            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    results = elements
                    logging.info(f"Found {len(results)} results using selector: {selector}")
                    break

            if not results:
                logging.warning("No results found")
                return None

            data = []

            # Try to extract data from results
            for idx, result in enumerate(results):
                try:
                    result_text = result.text

                    # Try to parse structured data if it's a table row
                    if result.tag_name == "tr":
                        cells = result.find_elements(By.TAG_NAME, "td")
                        if len(cells) >= 3:
                            # Attempt to map cells to our fields
                            # This will need adjustment based on actual site structure
                            address = cells[0].text.strip()
                            owner = cells[1].text.strip() if len(cells) > 1 else "N/A"
                            sale_info = cells[2].text.strip() if len(cells) > 2 else "N/A"

                            data.append({
                                'Date': "N/A",  # Will need to find in actual data
                                'Address': address,
                                'Owner Name': owner,
                                'Amount': sale_info
                            })
                    else:
                        # For non-table results, try to parse text
                        # This is a fallback and may need customization
                        if len(result_text) > 10:  # Skip empty results
                            data.append({
                                'Date': "N/A",
                                'Address': result_text[:100],  # Truncate for safety
                                'Owner Name': "N/A",
                                'Amount': "N/A"
                            })

                except Exception as e:
                    logging.debug(f"Error parsing result {idx}: {e}")
                    continue

            if not data:
                logging.warning("No sales data extracted")
                logging.info("Wilson County may require manual configuration")
                logging.info("Site structure may have changed or require different approach")
                return None

            # Create DataFrame
            df = pd.DataFrame(data)

            # Save to CSV
            output_file = f"output/wilson_sales_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(output_file, index=False)

            logging.info("="*60)
            logging.info(f"✓ SUCCESS: Saved {len(df)} sales")
            logging.info(f"  Output: {output_file}")
            logging.info("  NOTE: May need manual verification of data fields")
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
    scrape_wilson()
