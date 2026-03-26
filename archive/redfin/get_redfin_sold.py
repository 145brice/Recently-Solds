from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

print("=" * 60)
print("Redfin Sold Homes Scraper - Nashville")
print("=" * 60)

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)

try:
    # Start with the main Nashville page and manually navigate to sold
    print("\n1. Loading Nashville page...")
    driver.get("https://www.redfin.com/city/13415/TN/Nashville")
    time.sleep(5)

    # Try to click the Sold filter
    print("2. Looking for 'Sold' status filter...")

    # Method 1: Try to find and click a Sold button/link
    sold_clicked = False
    try:
        # Look for any element with "sold" in the text that's clickable
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Sold') or contains(text(), 'SOLD')]")
        for elem in elements:
            if elem.is_displayed() and elem.tag_name in ['button', 'a', 'div']:
                try:
                    print(f"  Trying to click: {elem.text[:50]}")
                    driver.execute_script("arguments[0].click();", elem)
                    sold_clicked = True
                    time.sleep(3)
                    print(f"  ✓ Clicked element")
                    break
                except:
                    continue
    except Exception as e:
        print(f"  Method 1 failed: {e}")

    # Method 2: If clicking failed, try URL with /status=9009 (Redfin's sold status code)
    if not sold_clicked:
        print("  Trying direct URL with sold filter...")
        driver.get("https://www.redfin.com/city/13415/TN/Nashville?status=9009")
        time.sleep(5)

    current_url = driver.current_url
    print(f"\n3. Current URL: {current_url}")

    # Check if we're on a sold page
    page_source = driver.page_source.lower()
    if 'sold' not in page_source and 'recently sold' not in page_source:
        print("  ⚠ Warning: Page may not be showing sold homes")
        print("  Trying alternative: adding filter to URL manually...")
        driver.get("https://www.redfin.com/city/13415/TN/Nashville/filter/include=sold-1mo")
        time.sleep(5)

    # Scroll and extract
    print("\n4. Scrolling to load results...")
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    print("5. Searching for property cards...")
    rows = driver.find_elements(By.CSS_SELECTOR, "div[class*='HomeCard']")
    print(f"  Found {len(rows)} property cards")

    if len(rows) == 0:
        print("\n✗ No properties found. Exiting.")
        driver.quit()
        exit(1)

    # Extract data
    data = []
    seen = set()

    print("\n6. Extracting data...")
    for idx, row in enumerate(rows, 1):
        try:
            # Get address
            address = None
            try:
                addr_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__Address")
                address = addr_elem.text.strip()
            except:
                continue

            if not address or address in seen:
                continue
            seen.add(address)

            # Get price
            price = "N/A"
            try:
                price_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__Price")
                price = price_elem.text.strip()
            except:
                pass

            # Get sold date - look for text containing "SOLD"
            sold_date = "N/A"
            row_text = row.text
            if "SOLD" in row_text.upper():
                lines = row_text.split("\n")
                for line in lines:
                    if "SOLD" in line.upper():
                        sold_date = line.strip()
                        break

            # Only add if it looks like a sold property
            if "SOLD" in sold_date.upper() or "SOLD" in row_text.upper():
                data.append([address, price, sold_date])
                print(f"  {len(data)}. {address} | {price} | {sold_date}")
            elif len(data) < 5:  # For first few, show what we're skipping
                print(f"  SKIP: {address} (no sold date found)")

        except Exception as e:
            continue

    # Save
    if data:
        with open("nashville_sold_comps.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Price", "Sold Date"])
            writer.writerows(data)

        print(f"\n{'='*60}")
        print(f"✓ SUCCESS: Saved {len(data)} sold properties")
        print(f"  File: nashville_sold_comps.csv")
        print(f"{'='*60}")
    else:
        print("\n✗ No sold properties found")
        print("  The page may be showing active listings instead of sold")
        print("\nRecommendation: Use county records for sold property data")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n✓ Browser closed")
