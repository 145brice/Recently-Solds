from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

print("=" * 60)
print("Scraping Nashville Sold Homes (Comps)")
print("=" * 60)

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)
driver.set_page_load_timeout(30)

try:
    # Load Nashville page
    print("\nLoading Nashville page...")
    driver.get("https://www.redfin.com/city/13415/TN/Nashville")
    time.sleep(5)

    # Click on "Sold" tab
    print("Clicking 'Sold' filter...")
    try:
        # Try to find and click the Sold button
        sold_selectors = [
            "button[data-rf-test-name='status-sold']",
            "button[value='sold']",
            "//button[contains(text(), 'Sold')]",
            "//a[contains(text(), 'Sold')]"
        ]

        sold_button = None
        for selector in sold_selectors:
            try:
                if selector.startswith("//"):
                    sold_button = driver.find_element(By.XPATH, selector)
                else:
                    sold_button = driver.find_element(By.CSS_SELECTOR, selector)
                if sold_button:
                    print(f"  Found Sold button with: {selector}")
                    break
            except:
                continue

        if sold_button:
            driver.execute_script("arguments[0].click();", sold_button)
            print("  ✓ Clicked Sold filter")
            time.sleep(5)
        else:
            print("  ⚠ Could not find Sold button, trying URL directly...")
            driver.get("https://www.redfin.com/city/13415/TN/Nashville/filter/include=sold-2mo")
            time.sleep(5)

    except Exception as e:
        print(f"  Error clicking Sold: {e}")
        print("  Trying URL directly...")
        driver.get("https://www.redfin.com/city/13415/TN/Nashville/filter/include=sold-2mo")
        time.sleep(5)

    print(f"\nCurrent URL: {driver.current_url}")
    print(f"Page title: {driver.title}")

    # Scroll to load listings
    print("\nScrolling to load results...")
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # Find listings
    print("Searching for property listings...")
    rows = driver.find_elements(By.CSS_SELECTOR, "div[class*='HomeCard']")
    print(f"✓ Found {len(rows)} potential listings")

    if len(rows) == 0:
        print("✗ No listings found")
        driver.quit()
        exit(1)

    # Extract data
    data = []
    seen_addresses = set()

    print("Extracting data...")
    for idx, row in enumerate(rows, 1):
        try:
            # Get full text content to see what's there
            if idx == 1:
                print(f"\nDEBUG - First card text:\n{row.text[:300]}\n")

            # Try to find address
            address = None
            try:
                # Try the most common selector
                addr_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__Address--block")
                address = addr_elem.text.strip()
            except:
                try:
                    addr_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__Address")
                    address = addr_elem.text.strip()
                except:
                    pass

            if not address or address in seen_addresses:
                continue

            seen_addresses.add(address)

            # Get price
            price = "N/A"
            try:
                price_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__Price")
                price = price_elem.text.strip()
            except:
                pass

            # Get sold date
            sold_date = "N/A"
            try:
                date_elem = row.find_element(By.CSS_SELECTOR, ".bp-Homecard__ClosedDate")
                sold_date = date_elem.text.strip()
            except:
                try:
                    # Alternative selector
                    date_elem = row.find_element(By.CSS_SELECTOR, "[class*='sold']")
                    sold_date = date_elem.text.strip()
                except:
                    pass

            data.append([address, price, sold_date])
            print(f"  {len(data)}. {address} | {price} | {sold_date}")

        except Exception as e:
            continue

    # Save
    if data:
        with open("nashville_sold_comps.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Price", "Sold Date"])
            writer.writerows(data)

        print(f"\n{'='*60}")
        print(f"✓ Saved {len(data)} properties to nashville_sold_comps.csv")
        print(f"{'='*60}")
    else:
        print("\n✗ No data extracted")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    driver.quit()
    print("\n✓ Browser closed")
