#!/usr/bin/env python3
"""
Davidson County (Nashville) Recent Sales Scraper
Downloads last 30 days of property sales from Nashville Property Assessor
Cron-ready: Runs daily, handles errors, logs output
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
log_file = f"logs/davidson_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def lookup_owner_name(address, driver=None):
    """Look up owner name for an address using property assessor search"""

    close_driver = False
    if driver is None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)
        close_driver = True

    try:
        search_url = "https://www.padctn.org/real-property-search/"
        driver.get(search_url)
        time.sleep(2)

        # Find and fill address search box
        search_box = driver.find_element(By.ID, "searchByOwner")
        search_box.clear()
        search_box.send_keys(address)

        # Click search
        search_button = driver.find_element(By.ID, "searchButton")
        search_button.click()
        time.sleep(3)

        # Try to find owner name in results
        owner_name = "N/A"
        try:
            # Look for owner name field
            owner_elem = driver.find_element(By.XPATH, "//td[contains(text(), 'Owner:')]/following-sibling::td")
            owner_name = owner_elem.text.strip()
        except:
            pass

        return owner_name

    except Exception as e:
        logging.debug(f"Error looking up owner for {address}: {e}")
        return "N/A"

    finally:
        if close_driver and driver:
            driver.quit()

def download_recent_sales():
    """Download recent sales Excel files from Davidson County"""

    logging.info("="*60)
    logging.info("Davidson County Recent Sales Scraper")
    logging.info("="*60)

    base_url = "https://www.padctn.org"
    recent_sales_url = f"{base_url}/resources/recent-sales/"

    # Get current and previous month
    current_month = datetime.now()
    prev_month = current_month - timedelta(days=30)

    months_to_check = [
        (current_month.year, current_month.month, current_month.strftime("%B")),
        (prev_month.year, prev_month.month, prev_month.strftime("%B"))
    ]

    all_data = []

    try:
        # Fetch the recent sales page
        logging.info(f"Fetching: {recent_sales_url}")
        response = requests.get(recent_sales_url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all Excel file links
        excel_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.xlsx' in href.lower() or '.xls' in href.lower():
                # Get context from parent element or URL
                parent_text = ""
                if link.parent:
                    parent_text = link.parent.get_text().strip()

                # Extract useful info from URL
                url_parts = href.split('/')
                filename = url_parts[-1] if url_parts else ""

                context = f"{parent_text} {filename}".strip()

                excel_links.append({
                    'url': href if href.startswith('http') else base_url + href,
                    'text': context,
                    'filename': filename
                })

        logging.info(f"Found {len(excel_links)} Excel files")

        # Debug: Show first 10 file names
        logging.info("\nSample file names:")
        for link in excel_links[:10]:
            logging.info(f"  - {link['text']}")

        # Download files for current and previous month
        downloaded_files = []

        for year, month_num, month_name in months_to_check:
            logging.info(f"\nLooking for {month_name} {year} files...")

            # Find files matching this month - try multiple patterns
            month_files = []
            for link in excel_links:
                link_text = link['text'].lower()
                # Match on year and month name OR month number
                if (str(year) in link_text and
                    (month_name.lower() in link_text or
                     f"{month_num:02d}" in link_text or
                     month_name[:3].lower() in link_text)):
                    month_files.append(link)

            if not month_files:
                logging.warning(f"No files found for {month_name} {year}")
                continue

            logging.info(f"Found {len(month_files)} files for {month_name} {year}")

            # Download each file
            for file_link in month_files[:5]:  # Limit to first 5 files per month
                try:
                    logging.info(f"  Downloading: {file_link['text']}")
                    file_response = requests.get(file_link['url'], timeout=60)
                    file_response.raise_for_status()

                    # Save temporary file
                    temp_filename = f"temp_{month_name}_{year}_{len(downloaded_files)}.xlsx"
                    with open(temp_filename, 'wb') as f:
                        f.write(file_response.content)

                    # Read Excel file
                    df = pd.read_excel(temp_filename, engine='openpyxl')

                    # Add source info
                    df['Source_Month'] = month_name
                    df['Source_Year'] = year
                    df['Downloaded'] = datetime.now().strftime('%Y-%m-%d')

                    all_data.append(df)
                    downloaded_files.append(temp_filename)

                    logging.info(f"    ✓ Read {len(df)} records")
                    time.sleep(1)  # Be nice to the server

                except Exception as e:
                    logging.error(f"    ✗ Error downloading {file_link['text']}: {e}")
                    continue

        # Clean up temp files
        for temp_file in downloaded_files:
            try:
                os.remove(temp_file)
            except:
                pass

        if not all_data:
            logging.error("No data downloaded")
            return None

        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)

        # Filter to last 60 days if Sale Date column exists
        date_columns = [col for col in combined_df.columns if 'sale' in col.lower() and 'date' in col.lower()]
        if date_columns:
            logging.info(f"\nFiltering by date column: {date_columns[0]}")
            try:
                combined_df[date_columns[0]] = pd.to_datetime(combined_df[date_columns[0]], errors='coerce')
                cutoff_date = datetime.now() - timedelta(days=60)
                combined_df = combined_df[combined_df[date_columns[0]] >= cutoff_date]
                logging.info(f"  Kept {len(combined_df)} records from last 60 days")
            except Exception as e:
                logging.warning(f"Could not filter by date: {e}")

        # Standardize column names for consistency across all scrapers
        column_mapping = {
            'Sale Date': 'Date',
            'Property Address': 'Address',
            'Sale Price': 'Amount'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in combined_df.columns:
                combined_df = combined_df.rename(columns={old_col: new_col})

        # Look up owner names for each address
        if 'Owner Name' not in combined_df.columns and 'Address' in combined_df.columns:
            logging.info("\nLooking up owner names (this may take a while)...")

            # Initialize Selenium driver once for all lookups
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            try:
                driver = webdriver.Chrome(options=options)

                owner_names = []
                for idx, address in enumerate(combined_df['Address'], 1):
                    if idx % 10 == 0:
                        logging.info(f"  Looked up {idx}/{len(combined_df)} addresses...")

                    owner = lookup_owner_name(address, driver)
                    owner_names.append(owner)
                    time.sleep(0.5)  # Be respectful to the server

                combined_df['Owner Name'] = owner_names
                logging.info(f"  ✓ Completed {len(owner_names)} owner lookups")

            except Exception as e:
                logging.error(f"Error during owner lookups: {e}")
                combined_df['Owner Name'] = 'N/A - Lookup failed'

            finally:
                try:
                    driver.quit()
                except:
                    pass

        # Select and reorder key columns first
        key_columns = ['Date', 'Address', 'Owner Name', 'Amount']
        available_key_cols = [col for col in key_columns if col in combined_df.columns]
        other_cols = [col for col in combined_df.columns if col not in available_key_cols]
        combined_df = combined_df[available_key_cols + other_cols]

        # Save output
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"{output_dir}/davidson_sales_{timestamp}.csv"

        combined_df.to_csv(output_file, index=False)

        logging.info(f"\n{'='*60}")
        logging.info(f"✓ SUCCESS: Saved {len(combined_df)} records")
        logging.info(f"  File: {output_file}")
        logging.info(f"{'='*60}")

        return output_file

    except Exception as e:
        logging.error(f"\n✗ FATAL ERROR: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    download_recent_sales()
