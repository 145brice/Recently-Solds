from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

options = Options()
# Set download directory to current folder
download_dir = os.path.abspath(".")
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)
options.add_argument("--no-sandbox")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")

driver = webdriver.Chrome(options=options)

print("=" * 60)
print("Downloading Redfin Data - Nashville")
print("=" * 60)

try:
    # Go directly to Nashville data page
    url = "https://www.redfin.com/news/data-center/metro-market-tracker/nashville-tn"
    print(f"\nOpening: {url}")
    driver.get(url)
    time.sleep(5)

    print("\nPage loaded. Looking for download options...")

    # Scroll down to find download section
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
    time.sleep(2)

    # Try multiple methods to find download button
    download_button = None

    # Method 1: Look for CSV download link
    try:
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            href = link.get_attribute("href") or ""
            text = link.text.lower()
            if ".csv" in href or "download" in text or "export" in text:
                download_button = link
                print(f"  Found download link: {text or href}")
                break
    except Exception as e:
        print(f"  Method 1 failed: {e}")

    # Method 2: Look for buttons with download text
    if not download_button:
        try:
            buttons = driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                if "download" in btn.text.lower() or "csv" in btn.text.lower():
                    download_button = btn
                    print(f"  Found download button: {btn.text}")
                    break
        except Exception as e:
            print(f"  Method 2 failed: {e}")

    # Method 3: Try specific Redfin download selectors
    if not download_button:
        selectors = [
            "a[href*='.csv']",
            "button[class*='download']",
            "a[class*='download']",
            "[data-rf-test-name='download']",
        ]
        for selector in selectors:
            try:
                download_button = driver.find_element(By.CSS_SELECTOR, selector)
                print(f"  Found download element with selector: {selector}")
                break
            except:
                continue

    if download_button:
        # Scroll to button and click
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", download_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", download_button)
        print("\n✓ Download button clicked!")
        print("  Waiting for file to download...")
        time.sleep(15)

        # Check if file downloaded
        csv_files = [f for f in os.listdir(download_dir) if f.endswith('.csv')]
        if csv_files:
            # Get most recent CSV
            latest_file = max([os.path.join(download_dir, f) for f in csv_files], key=os.path.getctime)
            new_name = os.path.join(download_dir, "redfin_download.csv")
            if os.path.exists(new_name):
                os.remove(new_name)
            os.rename(latest_file, new_name)
            print(f"\n✓ Downloaded and saved as: redfin_download.csv")
            print(f"  File size: {os.path.getsize(new_name)} bytes")
        else:
            print("\n⚠ No CSV file found in download directory")
            print("  The file may be in your Downloads folder")
    else:
        print("\n⚠ Could not find download button")
        print("  Leaving browser open for manual download...")
        print("  Browser will stay open for 60 seconds")
        time.sleep(60)

except Exception as e:
    print(f"\nError: {e}")
    print("\nManual fallback:")
    print("1. Browser will stay open")
    print("2. Navigate to data.redfin.com")
    print("3. Select Nashville")
    print("4. Click 'Download Report'")
    print("5. Save as 'redfin_download.csv'")
    time.sleep(60)

finally:
    driver.quit()
    print("\n" + "=" * 60)
    print("Next step: Run process_redfin_data.py to analyze the leads")
    print("=" * 60)
