from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import csv

print("=" * 60)
print("Starting Chrome...")
print("=" * 60)

options = Options()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

# Try to start Chrome with explicit service
try:
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    print("✓ Chrome started successfully")
except Exception as e:
    print(f"✗ Error starting Chrome: {e}")
    print("\nTrying alternative method...")
    driver = webdriver.Chrome(options=options)

# Nashville sold homes - last 60 days
# Use the /filter/ URL format that works
url = "https://www.redfin.com/city/13415/TN/Nashville/filter/property-type=house+condo+townhouse+other,include=sold-2mo"

print(f"\nLoading page: {url}")
print("(This may take 10-15 seconds...)")

# First load the city page
driver.set_page_load_timeout(30)
driver.get("https://www.redfin.com/city/13415/TN/Nashville")
time.sleep(3)

print("Setting sold filter...")

try:
    driver.set_page_load_timeout(30)
    driver.get(url)
    print("✓ Page loaded!")
    time.sleep(5)

    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")

    # Simple scrape - just first page for now
    data = []
    seen_addresses = set()

    print("\nScrolling to load results...")
    for i in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    print("Searching for property listings...")
    selectors = [
        "div[data-rf-test-id='home-card']",
        "div[class*='HomeCard']",
        "div[class*='SearchResult']",
    ]

    rows = []
    for selector in selectors:
        rows = driver.find_elements(By.CSS_SELECTOR, selector)
        if len(rows) > 0:
            print(f"✓ Found {len(rows)} listings")
            break

    if len(rows) == 0:
        print("✗ No listings found")
        driver.quit()
        exit(1)

    print("Extracting data...")
    for idx, row in enumerate(rows, 1):
        try:
            # Debug: print first row HTML
            if idx == 1:
                print(f"\nDEBUG - First row HTML:\n{row.get_attribute('outerHTML')[:500]}...\n")

            # Address
            address = None
            for addr_sel in ["div[data-rf-test-name='formattedAddress']", "[class*='address']", ".bp-Homecard__Address"]:
                try:
                    address = row.find_element(By.CSS_SELECTOR, addr_sel).text.strip()
                    if address:
                        print(f"  DEBUG: Found address with selector: {addr_sel}")
                        break
                except Exception as e:
                    continue

            if not address:
                if idx <= 3:
                    print(f"  DEBUG: Could not find address in row {idx}")
                continue

            if address in seen_addresses:
                continue

            seen_addresses.add(address)

            # Price
            price = "N/A"
            try:
                price_elem = row.find_element(By.CSS_SELECTOR, "span[data-rf-test-name='price']")
                price = price_elem.text.replace("\n", "").replace("Last sold price", "").strip()
            except:
                pass

            # Sold date
            sold_date = "N/A"
            try:
                date_elem = row.find_element(By.CSS_SELECTOR, "span[data-rf-test-name='sold-date']")
                sold_date = date_elem.text.strip()
            except:
                pass

            data.append([address, price, sold_date])
            print(f"  {len(data)}. {address} - {price}")

        except Exception as e:
            continue

    # Save
    if data:
        with open("nashville_recent_comps.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Address", "Price", "Sold Date"])
            writer.writerows(data)

        print(f"\n{'='*60}")
        print(f"✓ Saved {len(data)} properties to nashville_recent_comps.csv")
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
