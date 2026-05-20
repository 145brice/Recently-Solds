"""
Tennessee State Portal Property Scraper
========================================

Scrapes recent property sales from the TN State Property Assessment portal
(assessment.cot.tn.gov/TPAD). Supports date-range search for counties that
are hosted on this portal.

Supported counties:
  - Wilson (095)
  - Sumner (083)
  - Cheatham (011)
  - Robertson (074)

Strategy:
  1. Selenium submits the Advanced Search form (date range + county)
  2. Paginate through DataTable to collect all result rows (owner, address, sale date)
  3. Fetch detail pages in parallel using requests + BeautifulSoup for sale price
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

COUNTY_CODES = {
    'wilson': '095',
    'sumner': '083',
    'cheatham': '011',
    'robertson': '074',
}

PORTAL_URL = 'https://assessment.cot.tn.gov/TPAD'


class TNStatePortalScraper:
    """
    Scraper for the TN State Property Assessment portal.
    Uses date-range search to find recent sales across multiple counties.
    """

    def __init__(self, county="wilson", headless=True):
        self.county = county.lower()
        if self.county not in COUNTY_CODES:
            raise ValueError(f"County must be one of: {list(COUNTY_CODES.keys())}")

        self.county_code = COUNTY_CODES[self.county]

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 15)

        # Requests session for parallel detail page fetching
        self.session = requests.Session()
        self.session.headers['User-Agent'] = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        print(f"[OK] Initialized {self.county.title()} County scraper (TN State Portal)")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        self.session.close()

    def scrape_recent_sales(self, days_back=30, max_results=None):
        """
        Search for recent property sales by date range.

        Args:
            days_back: How many days back to search
            max_results: Optional limit on number of results

        Returns:
            pandas DataFrame with columns: owner_name, address, sale_date,
            sale_price, sale_price_clean
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        print(f"Searching {self.county.title()} County: {start_str} to {end_str}")

        # Step 1: Submit advanced search form via Selenium
        rows = self._submit_search(start_str, end_str)
        if not rows:
            print(f"[WARN] No results found for {self.county.title()} County")
            return pd.DataFrame()

        if max_results and len(rows) > max_results:
            rows = rows[:max_results]

        print(f"  Found {len(rows)} records in list view")

        # Step 2: Fetch detail pages in parallel for sale prices
        print(f"  Fetching sale prices from detail pages...")
        self._fetch_sale_prices(rows)

        # Count how many got prices
        priced = sum(1 for r in rows if r.get('sale_price'))
        print(f"  Got sale prices for {priced}/{len(rows)} records")

        # Build DataFrame
        df = pd.DataFrame(rows)
        if 'sale_price' in df.columns:
            df['sale_price_clean'] = df['sale_price'].apply(self._parse_price)

        print(f"[OK] {self.county.title()} County: {len(df)} records ready")
        return df

    def search_by_owner(self, last_name=""):
        """Legacy API compatibility - redirect to date-based search."""
        return self.scrape_recent_sales(days_back=30)

    def _submit_search(self, start_date, end_date):
        """Submit the advanced search form and extract all result rows."""
        self.driver.get(PORTAL_URL)
        time.sleep(4)

        # Select county in basic form
        try:
            basic_county = self.driver.find_element(
                By.CSS_SELECTOR, '#basicSearchForm select[name=Jur]'
            )
            Select(basic_county).select_by_value(self.county_code)
            time.sleep(1)
        except Exception as e:
            print(f"  [WARN] Could not select county in basic form: {e}")

        # Click Advanced Search to reveal the advanced form
        try:
            adv_btns = self.driver.find_elements(
                By.XPATH, "//button[contains(text(),'Advanced Search')]"
            )
            for btn in adv_btns:
                if btn.is_displayed():
                    self.driver.execute_script('arguments[0].click()', btn)
                    break
            time.sleep(2)
        except Exception as e:
            print(f"  [ERROR] Could not click Advanced Search: {e}")
            return []

        # Set county in advanced form, dates, and sort order via JS
        self.driver.execute_script(f'''
            var form = document.getElementById('advancedSearchForm');
            var countySel = form.querySelector('select[name=Jur]');
            if (countySel) countySel.value = '{self.county_code}';
            form.querySelector('#saleDateRangeStartSelect').value = '{start_date}';
            form.querySelector('#saleDateRangeEndSelect').value = '{end_date}';
            form.querySelector('#saleDateRadio').checked = true;
        ''')
        time.sleep(0.5)

        # Submit the advanced form
        self.driver.execute_script(
            'document.getElementById("advancedSearchForm").submit()'
        )
        time.sleep(8)

        # Check for results
        info = self.driver.execute_script(
            'var el = document.querySelector(".dataTables_info"); '
            'return el ? el.textContent : "";'
        )
        if not info or 'of 0' in info:
            return []

        print(f"  {info}")

        # Set page size to 100 and collect all pages
        return self._collect_all_rows()

    def _collect_all_rows(self):
        """Paginate through the DataTable and collect all result rows."""
        # Set page size to 100
        self.driver.execute_script('''
            var sel = document.querySelector('.dataTables_length select');
            if (sel) {
                sel.value = '100';
                sel.dispatchEvent(new Event('change', {bubbles: true}));
            }
        ''')
        time.sleep(3)

        all_rows = []
        page = 1

        while True:
            # Extract rows from current page
            data = self.driver.execute_script('''
                var tbody = document.querySelector('table tbody');
                if (!tbody) return [];
                var rows = tbody.querySelectorAll('tr');
                var result = [];
                for (var r of rows) {
                    var cells = r.querySelectorAll('td');
                    if (cells.length < 12) continue;

                    // Find detail URL
                    var link = cells[0].querySelector('a');
                    var detailUrl = link ? link.href : null;

                    result.push({
                        owner_name: cells[1].textContent.trim(),
                        address: cells[2].textContent.trim(),
                        sale_date: cells[11].textContent.trim(),
                        detail_url: detailUrl
                    });
                }
                return result;
            ''')

            if not data:
                break

            all_rows.extend(data)

            if page % 2 == 0:
                print(f"    Page {page}: {len(all_rows)} total rows collected")

            # Check for next page button
            has_next = self.driver.execute_script('''
                var nextBtn = document.querySelector('.dataTables_paginate .next:not(.disabled)');
                if (nextBtn) { nextBtn.click(); return true; }
                return false;
            ''')

            if not has_next:
                break

            page += 1
            time.sleep(2)

        return all_rows

    def _fetch_sale_prices(self, rows, max_workers=6):
        """Fetch sale prices from detail pages using parallel requests."""
        detail_rows = [r for r in rows if r.get('detail_url')]
        if not detail_rows:
            return

        def fetch_price(row):
            url = row['detail_url']
            try:
                resp = self.session.get(url, timeout=15)
                if resp.status_code != 200:
                    return
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Find the sale information table
                for table in soup.find_all('table'):
                    headers = [th.get_text(strip=True) for th in table.find_all('th')]
                    if 'Sale Date' in headers and 'Price' in headers:
                        # Get first data row (most recent sale)
                        data_rows = table.find_all('tr')[1:]
                        for tr in data_rows:
                            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                            if len(cells) >= 2 and cells[1] and cells[1] != '$0':
                                row['sale_price'] = cells[1]
                                return
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_price, r): r for r in detail_rows}
            done = 0
            for future in as_completed(futures):
                done += 1
                if done % 50 == 0:
                    print(f"    Fetched {done}/{len(detail_rows)} detail pages")
                future.result()  # Propagate exceptions

    @staticmethod
    def _parse_price(value):
        """Convert a price string like '$669,900' to float."""
        if pd.isna(value) or not value or value == 'N/A':
            return 0.0
        try:
            return float(str(value).replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return 0.0


if __name__ == "__main__":
    county = "wilson"
    with TNStatePortalScraper(county=county, headless=True) as scraper:
        df = scraper.scrape_recent_sales(days_back=30)
        if not df.empty:
            print(f"\nColumns: {list(df.columns)}")
            print(f"Records: {len(df)}")
            print(df[['owner_name', 'address', 'sale_date', 'sale_price']].head(10))
            df.to_csv(f"{county}_test_output.csv", index=False)
            print(f"Saved to {county}_test_output.csv")
