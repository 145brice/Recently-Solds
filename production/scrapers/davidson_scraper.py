"""
Davidson County (Nashville) Property Scraper
=============================================

Scrapes recent property sales from the Nashville Property Assessor (padctn.org).
Downloads monthly Excel files from the Recent Sales page — no Selenium needed.

This is the largest county in the Nashville metro area.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import logging

logger = logging.getLogger(__name__)


class DavidsonCountyScraper:
    """
    Scraper for Davidson County (Nashville) property records.
    Downloads Excel files from padctn.org/resources/recent-sales/.
    """

    def __init__(self, headless=True):
        """
        Initialize the scraper.

        Args:
            headless: Accepted for API consistency with other scrapers but unused
                      (this scraper uses requests, not Selenium).
        """
        self.base_url = "https://www.padctn.org"
        self.recent_sales_url = f"{self.base_url}/resources/recent-sales/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        print("[OK] Initialized Davidson County scraper")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def scrape_recent_sales(self, days_back=60, max_results=None):
        """
        Download and parse recent sales data from padctn.org.

        Args:
            days_back: How many days back to include (default 60 to cover 2 months)
            max_results: Optional limit on number of results

        Returns:
            pandas DataFrame with columns: owner_name, address, sale_date,
            sale_price, sale_price_clean
        """
        print(f"Fetching recent sales page: {self.recent_sales_url}")

        try:
            response = self.session.get(self.recent_sales_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch recent sales page: {e}")
            return pd.DataFrame()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all Excel file links
        excel_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '.xlsx' in href.lower() or '.xls' in href.lower():
                url = href if href.startswith('http') else self.base_url + href
                parent_text = link.parent.get_text().strip() if link.parent else ""
                filename = href.split('/')[-1] if '/' in href else href
                excel_links.append({
                    'url': url,
                    'text': f"{parent_text} {filename}".strip(),
                    'filename': filename
                })

        print(f"Found {len(excel_links)} Excel files on page")

        if not excel_links:
            print("[ERROR] No Excel files found on recent sales page")
            return pd.DataFrame()

        # padctn.org organizes files by district/zone and year (e.g. "1_rural_2025.xlsx")
        # Strategy: find the most recent year with files, download all of them
        import re
        now = datetime.now()
        year_to_try = now.year

        # Find files for the most recent year available
        year_files = []
        for attempt_year in [year_to_try, year_to_try - 1, year_to_try - 2]:
            year_str = str(attempt_year)
            year_files = [l for l in excel_links if year_str in l['filename']]
            if year_files:
                print(f"Found {len(year_files)} files for {attempt_year}")
                break

        if not year_files:
            print("[ERROR] No files found for recent years")
            return pd.DataFrame()

        # Download all files for that year
        all_data = []
        temp_files = []
        errors = 0

        for i, file_link in enumerate(year_files):
            try:
                if i % 10 == 0:
                    print(f"  Downloading {i+1}/{len(year_files)}: {file_link['filename']}")
                file_response = self.session.get(file_link['url'], timeout=60)
                file_response.raise_for_status()

                temp_filename = f"temp_davidson_{i}.xlsx"
                with open(temp_filename, 'wb') as f:
                    f.write(file_response.content)

                df = pd.read_excel(temp_filename, engine='openpyxl')
                if not df.empty:
                    all_data.append(df)
                temp_files.append(temp_filename)

                time.sleep(0.3)  # Be nice to the server

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"    [WARN] Error on {file_link['filename']}: {e}")
                continue

        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except OSError:
                pass

        if not all_data:
            print("[ERROR] No data downloaded")
            return pd.DataFrame()

        # Combine all downloaded data
        combined = pd.concat(all_data, ignore_index=True)
        print(f"[OK] Combined {len(combined)} total records")

        # Normalize column names
        combined = self._normalize_columns(combined)

        # Filter by date range — use most recent date in data as reference
        # (padctn.org publishes data with a lag, so "now" may be months ahead)
        if 'sale_date' in combined.columns:
            try:
                combined['sale_date'] = pd.to_datetime(combined['sale_date'], errors='coerce')
                valid_dates = combined['sale_date'].dropna()
                if not valid_dates.empty:
                    most_recent = valid_dates.max()
                    cutoff = most_recent - timedelta(days=days_back)
                    before_filter = len(combined)
                    combined = combined[combined['sale_date'] >= cutoff]
                    print(f"  Date range: {cutoff.strftime('%Y-%m-%d')} to {most_recent.strftime('%Y-%m-%d')}")
                    print(f"  Filtered to last {days_back} days: {before_filter} -> {len(combined)} records")
            except Exception as e:
                print(f"  Could not filter by date: {e}")

        # Create clean price column
        if 'sale_price' in combined.columns:
            combined['sale_price_clean'] = combined['sale_price'].apply(self._parse_price)

        if max_results and len(combined) > max_results:
            combined = combined.head(max_results)

        print(f"[OK] Davidson County: {len(combined)} records ready")
        return combined

    def _normalize_columns(self, df):
        """Map padctn.org Excel column names to standard scraper column names."""
        # Known padctn.org columns:
        # Zone, Parcel ID, Land Use, Property Address, Suite/Condo,
        # Property City, Sale Date, Sale Price, Legal Reference,
        # Sold As Vacant, Multiple Parcels Involved in Sale
        col_map = {}
        city_col = None

        for col in df.columns:
            cl = col.lower().strip()
            if 'owner' in cl or 'grantor' in cl or 'grantee' in cl or 'buyer' in cl:
                col_map[col] = 'owner_name'
            elif cl == 'property address' or (cl == 'address' and 'address' not in col_map.values()):
                col_map[col] = 'address'
            elif 'city' in cl:
                city_col = col
            elif cl == 'sale date':
                col_map[col] = 'sale_date'
            elif cl == 'sale price':
                col_map[col] = 'sale_price'

        if col_map:
            df = df.rename(columns=col_map)

        # Combine address + city into full address
        if 'address' in df.columns and city_col:
            df['address'] = (
                df['address'].fillna('').astype(str).str.strip() + ', ' +
                df[city_col].fillna('Nashville').astype(str).str.strip() + ', TN'
            )

        return df

    @staticmethod
    def _parse_price(value):
        """Convert a price value to float."""
        if pd.isna(value):
            return 0.0
        try:
            return float(str(value).replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return 0.0


if __name__ == "__main__":
    with DavidsonCountyScraper() as scraper:
        df = scraper.scrape_recent_sales(days_back=30)
        if not df.empty:
            print(f"\nColumns: {list(df.columns)}")
            print(f"Records: {len(df)}")
            print(df.head())
            df.to_csv("davidson_test_output.csv", index=False)
            print("Saved to davidson_test_output.csv")
