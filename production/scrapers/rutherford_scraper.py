"""
Rutherford County Property Scraper
==================================

Scraper for Rutherford County (Murfreesboro area).
Fast-growing county with lots of new development.

Supports both owner name searches and address searches.
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
from datetime import datetime


class RutherfordCountyScraper:
    """
    Scraper for Rutherford County property records
    """

    def __init__(self, headless=True):
        """
        Initialize the scraper

        Args:
            headless (bool): Run browser in headless mode
        """
        self.base_url = "https://secured.rutherfordcountytn.gov/propertydata/"

        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
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

        print("✓ Initialized Rutherford County scraper")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def navigate_to_search(self):
        """Navigate to the property search page"""
        print(f"Loading {self.base_url}...")
        self.driver.get(self.base_url)
        time.sleep(3)

        # Wait for page to fully load
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("✓ Page loaded successfully")
        except TimeoutException:
            print("⚠ Page load timeout - attempting to continue")

    def search_by_owner(self, last_name):
        """
        Search for properties by owner last name

        Args:
            last_name (str): Owner's last name

        Returns:
            list: List of property dictionaries
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Find and fill owner name field
            try:
                owner_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "owner_name"))
                )
                owner_field.clear()
                owner_field.send_keys(last_name)
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ Could not find owner field: {str(e)}")
                return []

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "search_btn"))
                )
                search_btn.click()
                time.sleep(3)
            except Exception as e:
                print(f"  ⚠ Could not find search button: {str(e)}")
                return []

            # Extract results
            return self.extract_search_results()

        except Exception as e:
            print(f"  ❌ Owner search error: {str(e)}")
            return []

    def search_by_address(self, address):
        """
        Search for property by address

        Args:
            address (str): Property address

        Returns:
            dict: Property information or empty dict if not found
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Find and fill address field
            try:
                address_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "property_address"))
                )
                address_field.clear()
                address_field.send_keys(address)
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ Could not find address field: {str(e)}")
                return {}

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "search_btn"))
                )
                search_btn.click()
                time.sleep(3)
            except Exception as e:
                print(f"  ⚠ Could not find search button: {str(e)}")
                return {}

            # Extract single result
            results = self.extract_search_results()
            return results[0] if results else {}

        except Exception as e:
            print(f"  ❌ Address search error: {str(e)}")
            return {}

    def extract_search_results(self):
        """Extract property data from search results"""
        properties = []

        try:
            # Wait for results table
            results_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "results-table"))
            )

            # Find all result rows
            rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header

            print(f"  Found {len(rows)} properties")

            for idx, row in enumerate(rows, 1):
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")

                    property_data = {
                        'parcel_id': cols[0].text if len(cols) > 0 else '',
                        'owner': cols[1].text if len(cols) > 1 else '',
                        'address': cols[2].text if len(cols) > 2 else '',
                        'sale_date': cols[3].text if len(cols) > 3 else '',
                        'sale_price': cols[4].text if len(cols) > 4 else '',
                        'property_type': cols[5].text if len(cols) > 5 else '',
                        'land_use': cols[6].text if len(cols) > 6 else '',
                        'total_assessed_value': cols[7].text if len(cols) > 7 else '',
                        'year_built': cols[8].text if len(cols) > 8 else '',
                        'square_feet': cols[9].text if len(cols) > 9 else '',
                    }

                    # Clean up data
                    if property_data.get('sale_price'):
                        property_data['sale_price_clean'] = property_data['sale_price'].replace('$', '').replace(',', '')
                        try:
                            property_data['sale_price_clean'] = float(property_data['sale_price_clean'])
                        except:
                            property_data['sale_price_clean'] = None

                    if property_data.get('total_assessed_value'):
                        property_data['total_assessed_clean'] = property_data['total_assessed_value'].replace('$', '').replace(',', '')
                        try:
                            property_data['total_assessed_clean'] = float(property_data['total_assessed_clean'])
                        except:
                            property_data['total_assessed_clean'] = None

                    properties.append(property_data)

                    if idx % 10 == 0:
                        print(f"    Processed {idx}/{len(rows)} properties...")

                except Exception as e:
                    print(f"    Error extracting row {idx}: {str(e)}")
                    continue

            print(f"  ✓ Extracted {len(properties)} properties")
            return properties

        except Exception as e:
            print(f"  ⚠ Error extracting results: {str(e)}")
            return []

    def get_property_details(self, parcel_id):
        """
        Get detailed information for a specific property

        Args:
            parcel_id (str): Property parcel ID

        Returns:
            dict: Detailed property information
        """
        try:
            # Navigate to detail page
            detail_url = f"{self.base_url}details/{parcel_id}"
            self.driver.get(detail_url)
            time.sleep(2)

            details = {}

            # Extract additional details
            try:
                # Building information
                building_section = self.driver.find_element(By.ID, "building_info")
                details['bedrooms'] = building_section.find_element(By.CLASS_NAME, "bedrooms").text
                details['bathrooms'] = building_section.find_element(By.CLASS_NAME, "bathrooms").text
                details['stories'] = building_section.find_element(By.CLASS_NAME, "stories").text
            except:
                pass

            # Land information
            try:
                land_section = self.driver.find_element(By.ID, "land_info")
                details['lot_size'] = land_section.find_element(By.CLASS_NAME, "lot-size").text
                details['zoning'] = land_section.find_element(By.CLASS_NAME, "zoning").text
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
    print(" RUTHERFORD COUNTY SCRAPER - TEST")
    print("="*60 + "\n")

    try:
        with RutherfordCountyScraper(headless=False) as scraper:
            # Test owner search
            properties = scraper.search_by_owner(last_name="Smith")

            if properties:
                print(f"\nFound {len(properties)} properties")
                print("\nFirst 3 properties:")
                for prop in properties[:3]:
                    print(f"  {prop.get('owner', 'N/A')} - {prop.get('address', 'N/A')} - ${prop.get('sale_price', 'N/A')}")
            else:
                print("No properties found")

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
