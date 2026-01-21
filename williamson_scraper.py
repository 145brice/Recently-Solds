"""
Williamson County Property Scraper
===================================

Scraper for Williamson County (Franklin, Brentwood area).
High-end market with ~$775k median sale price.

Uses subdivision-based searches for best results.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import random
from datetime import datetime


class WilliamsonCountyScraper:
    """
    Scraper for Williamson County property records
    """

    def __init__(self, headless=True, human_like=True):
        """
        Initialize the scraper

        Args:
            headless (bool): Run browser in headless mode
            human_like (bool): Add human-like delays and behaviors
        """
        self.base_url = "https://inigo.williamson-tn.org/property_search/"
        self.human_like = human_like

        # Setup Chrome options with realistic user agent
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        # More realistic user agent
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Initialize driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)

        # Execute CDP commands to mask automation (optional, may timeout)
        try:
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    })
                """
            })
        except:
            pass  # CDP command optional, continue if it fails

        print("✓ Initialized Williamson County scraper")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def human_delay(self, min_seconds=1, max_seconds=3):
        """
        Add a human-like random delay

        Args:
            min_seconds (float): Minimum delay in seconds
            max_seconds (float): Maximum delay in seconds
        """
        if self.human_like:
            delay = random.uniform(min_seconds, max_seconds)
            time.sleep(delay)
        else:
            time.sleep(min_seconds)

    def navigate_to_search(self):
        """Navigate to the property search page"""
        print(f"Loading {self.base_url}...")
        self.driver.get(self.base_url)
        self.human_delay(2, 4)  # Human-like page load wait

        # Wait for page to fully load
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✓ Page loaded successfully")
        except TimeoutException:
            print("⚠ Page load timeout - attempting to continue")

    def search_by_subdivision_and_date(self, subdivision, start_date, end_date):
        """
        Search for properties by subdivision and date range

        Args:
            subdivision (str): Subdivision name
            start_date (str): Start date 'YYYY-MM-DD' (will be converted to MM/DD/YYYY)
            end_date (str): End date 'YYYY-MM-DD' (will be converted to MM/DD/YYYY)

        Returns:
            list: List of property dictionaries
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Find and fill subdivision field
            try:
                subdiv_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "subdivision"))
                )
                subdiv_field.clear()
                self.human_delay(0.3, 0.7)  # Pause before typing
                subdiv_field.send_keys(subdivision)
                self.human_delay(0.5, 1.2)  # Pause after typing
            except Exception as e:
                print(f"  ⚠ Could not find subdivision field: {str(e)}")
                return []

            # Find and fill date fields
            # Convert YYYY-MM-DD to MM/DD/YYYY format
            try:
                start_field = self.driver.find_element(By.ID, "sales_date_start")
                start_field.clear()
                self.human_delay(0.3, 0.6)
                start_converted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%m/%d/%Y')
                start_field.send_keys(start_converted)
                self.human_delay(0.4, 0.8)

                end_field = self.driver.find_element(By.ID, "sales_date_end")
                end_field.clear()
                self.human_delay(0.3, 0.6)
                end_converted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
                end_field.send_keys(end_converted)
                self.human_delay(0.5, 1.0)
            except Exception as e:
                print(f"  ⚠ Could not find date fields: {str(e)}")
                return []

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'].button"))
                )
                search_btn.click()
                self.human_delay(3, 5)  # Wait for results to load
            except Exception as e:
                print(f"  ⚠ Could not find search button: {str(e)}")
                return []

            # Extract results
            return self.extract_search_results()

        except Exception as e:
            print(f"  ❌ Search error: {str(e)}")
            return []

    def search_by_date_only(self, start_date, end_date):
        """
        Search for properties by date range only (no subdivision filter)

        Args:
            start_date (str): Start date 'YYYY-MM-DD' (will be converted to MM/DD/YYYY)
            end_date (str): End date 'YYYY-MM-DD' (will be converted to MM/DD/YYYY)

        Returns:
            list: List of property dictionaries
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Fill date fields only (skip subdivision)
            # Convert YYYY-MM-DD to MM/DD/YYYY format
            try:
                start_field = self.driver.find_element(By.ID, "sales_date_start")
                start_field.clear()
                self.human_delay(0.3, 0.6)
                start_converted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%m/%d/%Y')
                start_field.send_keys(start_converted)
                self.human_delay(0.4, 0.8)

                end_field = self.driver.find_element(By.ID, "sales_date_end")
                end_field.clear()
                self.human_delay(0.3, 0.6)
                end_converted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%m/%d/%Y')
                end_field.send_keys(end_converted)
                self.human_delay(0.5, 1.0)
            except Exception as e:
                print(f"  ⚠ Could not find date fields: {str(e)}")
                return []

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'].button"))
                )
                search_btn.click()
                self.human_delay(3, 5)  # Wait for results to load
            except Exception as e:
                print(f"  ⚠ Could not find search button: {str(e)}")
                return []

            # Extract results
            return self.extract_search_results()

        except Exception as e:
            print(f"  ❌ Search error: {str(e)}")
            return []

    def extract_search_results(self):
        """Extract property data from search results with pagination support"""
        all_properties = []
        page_num = 1

        try:
            # Wait for results table
            self.human_delay(4, 6)
            results_table = self.wait.until(
                EC.presence_of_element_located((By.ID, "results_table"))
            )

            # Wait for actual data rows to load (not just empty table)
            # Poll for data rows for up to 30 seconds
            max_wait = 30
            wait_time = 0
            rows = []

            while wait_time < max_wait and len(rows) <= 1:  # 1 or fewer rows means no data (just header)
                self.human_delay(1.5, 2.5)
                wait_time += 2
                try:
                    rows = results_table.find_elements(By.TAG_NAME, "tr")
                    print(f"  Waiting for data... found {len(rows)} rows after {wait_time}s")
                except:
                    continue

            if len(rows) <= 1:
                print("  ⚠ No data rows found in table after waiting")
                return []

            # Check for total count in DataTables info
            try:
                info_element = self.driver.find_element(By.CLASS_NAME, "dataTables_info")
                info_text = info_element.text
                print(f"  {info_text}")

                # Extract total from "Showing X to Y of Z entries"
                if "of" in info_text and "entries" in info_text:
                    total_str = info_text.split("of")[1].split("entries")[0].strip()
                    total_count = int(total_str.replace(',', ''))
                    print(f"  Total properties in search: {total_count}")
            except:
                pass

            # Process all pages
            while True:
                print(f"  Processing page {page_num}...")

                # Get current page data
                results_table = self.driver.find_element(By.ID, "results_table")
                rows = results_table.find_elements(By.TAG_NAME, "tr")
                data_rows = rows[1:]  # Skip header

                # Extract data from current page
                for idx, row in enumerate(data_rows, 1):
                    try:
                        cols = row.find_elements(By.TAG_NAME, "td")

                        # Check if this is a "no data" message row
                        if len(cols) > 0 and "no data available" in cols[0].text.lower():
                            print(f"  ⚠ No data available in table")
                            return []

                        property_data = {
                            'owner_name': cols[0].text if len(cols) > 0 else '',
                            'address': cols[1].text if len(cols) > 1 else '',
                            'city': cols[2].text if len(cols) > 2 else '',
                            'parcel_id': cols[3].text if len(cols) > 3 else '',
                            'lot_number': cols[4].text if len(cols) > 4 else '',
                            'sale_date': cols[5].text if len(cols) > 5 else '',
                            'sale_price': cols[6].text if len(cols) > 6 else '',
                            'property_type': '',
                            'bedrooms': '',
                            'bathrooms': '',
                            'square_feet': '',
                            'year_built': '',
                        }

                        # Clean up price
                        if property_data.get('sale_price'):
                            property_data['sale_price_clean'] = property_data['sale_price'].replace('$', '').replace(',', '')
                            try:
                                property_data['sale_price_clean'] = float(property_data['sale_price_clean'])
                            except:
                                property_data['sale_price_clean'] = None

                        all_properties.append(property_data)

                    except Exception as e:
                        print(f"    Error extracting row {idx}: {str(e)}")
                        continue

                print(f"    Page {page_num}: extracted {len(data_rows)} properties (total so far: {len(all_properties)})")

                # Try to click "Next" button
                try:
                    # Find Next button - DataTables uses "next" class
                    next_button = self.driver.find_element(By.ID, "results_table_next")

                    # Check if Next button is disabled (last page)
                    if "disabled" in next_button.get_attribute("class"):
                        print(f"  ✓ Reached last page")
                        break

                    # Click Next with human-like delay
                    next_link = next_button.find_element(By.TAG_NAME, "a")
                    self.human_delay(1.5, 3.5)  # Pause before clicking (like reading the page)
                    next_link.click()
                    self.human_delay(2, 4)  # Wait for page to load with variation
                    page_num += 1

                except Exception as e:
                    print(f"  No more pages or error with pagination: {str(e)}")
                    break

            print(f"  ✓ Extracted {len(all_properties)} total properties from {page_num} pages")
            return all_properties

        except Exception as e:
            print(f"  ⚠ Error extracting results: {str(e)}")
            return all_properties if all_properties else []

    def get_property_details(self, property_url):
        """
        Get detailed information for a specific property

        Args:
            property_url (str): URL to property detail page

        Returns:
            dict: Detailed property information
        """
        try:
            self.driver.get(property_url)
            time.sleep(2)

            details = {}

            # Extract additional details
            try:
                # Property characteristics
                char_section = self.driver.find_element(By.ID, "property_characteristics")
                details['lot_size'] = char_section.find_element(By.CLASS_NAME, "lot-size").text
                details['zoning'] = char_section.find_element(By.CLASS_NAME, "zoning").text
            except:
                pass

            # Tax information
            try:
                tax_section = self.driver.find_element(By.ID, "tax_info")
                details['tax_year'] = tax_section.find_element(By.CLASS_NAME, "tax-year").text
                details['tax_amount'] = tax_section.find_element(By.CLASS_NAME, "tax-amount").text
            except:
                pass

            return details

        except Exception as e:
            print(f"  Error getting property details: {str(e)}")
            return {}


def main():
    """
    Example usage
    """
    print("\n" + "="*60)
    print(" WILLIAMSON COUNTY SCRAPER - TEST")
    print("="*60 + "\n")

    try:
        with WilliamsonCountyScraper(headless=False) as scraper:
            # Test search
            properties = scraper.search_by_subdivision_and_date(
                subdivision="Westhaven",
                start_date="2024-01-01",
                end_date="2024-12-31"
            )

            if properties:
                print(f"\nFound {len(properties)} properties")
                print("\nFirst 3 properties:")
                for prop in properties[:3]:
                    print(f"  {prop.get('owner_name', 'N/A')} - {prop.get('address', 'N/A')} - ${prop.get('sale_price', 'N/A')}")
            else:
                print("No properties found")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
