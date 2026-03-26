from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

options = Options()
# options.add_argument("--headless")  # Keep visible for manual URL setup
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)

# Nashville sold homes - last 60 days for comps
url = "https://www.redfin.com/city/13415/TN/Nashville/filter/include=sold-2mo"

print("=" * 60, flush=True)
print(f"Scraping Nashville Recently Sold Homes (Last 60 Days - Comps)", flush=True)
print(f"URL: {url}", flush=True)
print("=" * 60, flush=True)

driver.get(url)
time.sleep(8)

print(f"Current URL: {driver.current_url}")
print(f"Page title: {driver.title}")

# Handle pagination - Redfin shows results across multiple pages
data = []
seen_addresses = set()
page_num = 1
MAX_PAGES = None  # Set to None to scrape all pages
MAX_PROPERTIES_PER_PAGE = None  # Set to None for all properties

while True:
    if MAX_PAGES and page_num > MAX_PAGES:
        print(f"\n  Reached max pages limit ({MAX_PAGES})")
        break
    print(f"\n{'='*60}")
    print(f"Processing Page {page_num}")
    print(f"{'='*60}")

    # Scroll to load all results on this page
    print("Scrolling to load page results...")
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Try multiple selectors to find property listings
    print("\nSearching for property listings...")
    selectors = [
        "div[data-rf-test-id='home-card']",
        "div[class*='HomeCard']",
        "div[class*='SearchResult']",
        ".HomeViews",
        "[class*='homeSummary']",
    ]

    rows = []
    for selector in selectors:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        if len(rows) > 0:
            print(f"  Found {len(rows)} listings on page {page_num}")
            break

    if len(rows) == 0:
        print("\n✗ No listings found on this page")
        break

    # Extract data from this page
    print("Extracting data from this page...")
    page_data_count = 0

    for idx, row in enumerate(rows, 1):
        # Check if we've hit the per-page limit
        if MAX_PROPERTIES_PER_PAGE and page_data_count >= MAX_PROPERTIES_PER_PAGE:
            print(f"    Reached max properties per page ({MAX_PROPERTIES_PER_PAGE})")
            break
        try:
            # Try multiple selectors for address
            address = None
            for addr_sel in ["div[data-rf-test-name='formattedAddress']", ".bp-Homecard__Address", "[class*='address']", ".homeAddressV2"]:
                try:
                    address = row.find_element(By.CSS_SELECTOR, addr_sel).text.strip()
                    break
                except:
                    continue

            # Skip duplicates
            if address and address in seen_addresses:
                continue

            # Try multiple selectors for price
            price = None
            for price_sel in ["span[data-rf-test-name='price']", ".bp-Homecard__Price", "[class*='price']", ".homecardV2Price"]:
                try:
                    price = row.find_element(By.CSS_SELECTOR, price_sel).text
                    # Clean up price
                    price = price.replace("\n", "").replace("Last sold price", "").strip()
                    break
                except:
                    continue

            # Try multiple selectors for sold date
            sold_date = None
            for date_sel in ["span[data-rf-test-name='sold-date']", ".bp-Homecard__SoldDate", "[class*='sold']", ".sold-date"]:
                try:
                    sold_date = row.find_element(By.CSS_SELECTOR, date_sel).text.strip()
                    break
                except:
                    continue

            # If we got basic info, add to results
            if address:
                seen_addresses.add(address)
                data.append([address, price or "N/A", sold_date or "N/A"])
                page_data_count += 1
                print(f"    {page_data_count}. {address} - {price}")

        except Exception as e:
            continue

    print(f"  Extracted {page_data_count} unique properties from page {page_num}")
    print(f"  Total so far: {len(data)} properties")

    # Try to find and click the "Next" button
    try:
        # Scroll to bottom where pagination controls are
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Try to find Next button with multiple approaches
        next_button = None

        # Look for the specific next page link
        try:
            # Look for page-(page_num+1) specifically
            next_page_num = page_num + 1
            next_page_url_part = f"/page-{next_page_num}"

            # Try to find link with exact page number
            page_links = driver.find_elements(By.TAG_NAME, "a")
            for link in page_links:
                href = link.get_attribute("href")
                if href and next_page_url_part in href and "/Nashville/" in href:
                    # Make sure it's the exact page, not just contains the number
                    if f"/page-{next_page_num}" in href or href.endswith(f"/page-{next_page_num}"):
                        next_button = link
                        print(f"  Found next page link for page {next_page_num}: {href}")
                        break

            if not next_button:
                print(f"  No link found for page {next_page_num}")

        except Exception as e:
            print(f"  Error finding next page: {e}")

        if next_button and next_button.is_displayed():
            print(f"\n  ✓ Found next page button. Clicking to go to page {page_num + 1}...")

            # Use JavaScript click to avoid "element click intercepted" error
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)
                print(f"  Clicked! Loading page {page_num + 1}...")
                time.sleep(5)  # Wait for page to load
                page_num += 1
            except Exception as click_error:
                print(f"  Error clicking: {click_error}")
                break
        else:
            print(f"\n  ✗ No more pages found. Finished at page {page_num}.")
            break

    except Exception as e:
        print(f"\n  Error finding Next button: {e}")
        print(f"  Finished at page {page_num}.")
        break

# Save
with open("nashville_recent_comps.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Address", "Price", "Sold Date"])
    writer.writerows(data)

print(f"\n{'='*60}")
print(f"✓ Done! Saved {len(data)} unique properties to nashville_recent_comps.csv")
print(f"{'='*60}")
driver.quit()