"""
Tennessee State Portal Property Scraper
======================================

Scraper for Tennessee State Portal used by Robertson and Cheatham counties.
Centralized property search system for multiple counties.

Supports owner name searches and property ID searches.
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


class TNStatePortalScraper:
    """
    Scraper for Tennessee State Portal property records
    Used by Robertson and Cheatham counties
    """

    def __init__(self, county="robertson", headless=True):
        """
        Initialize the scraper

        Args:
            county (str): County to search ('robertson' or 'cheatham')
            headless (bool): Run browser in headless mode
        """
        self.county = county.lower()

        # County-specific URLs
        self.county_urls = {
            'robertson': "https://robertson-tn.gov/property-search/",
            'cheatham': "https://cheathamcounty-tn.gov/property-search/"
        }

        if self.county not in self.county_urls:
            raise ValueError(f"Unsupported county: {county}. Must be 'robertson' or 'cheatham'")

        self.base_url = self.county_urls[self.county]

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

        print(f"✓ Initialized TN State Portal scraper for {county.title()} County")

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

    def search_by_owner(self, last_name, first_name=""):
        """
        Search for properties by owner name

        Args:
            last_name (str): Owner's last name
            first_name (str): Owner's first name (optional)

        Returns:
            list: List of property dictionaries
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Find and fill owner name fields
            try:
                last_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "owner_last_name"))
                )
                last_field.clear()
                last_field.send_keys(last_name)

                if first_name:
                    first_field = self.driver.find_element(By.ID, "owner_first_name")
                    first_field.clear()
                    first_field.send_keys(first_name)

                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ Could not find owner name fields: {str(e)}")
                return []

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "search_button"))
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

    def search_by_property_id(self, property_id):
        """
        Search for property by property ID

        Args:
            property_id (str): Property ID or parcel number

        Returns:
            dict: Property information or empty dict if not found
        """
        try:
            # Navigate to search page
            self.navigate_to_search()

            # Find and fill property ID field
            try:
                id_field = self.wait.until(
                    EC.presence_of_element_located((By.ID, "property_id"))
                )
                id_field.clear()
                id_field.send_keys(property_id)
                time.sleep(1)
            except Exception as e:
                print(f"  ⚠ Could not find property ID field: {str(e)}")
                return {}

            # Click search button
            try:
                search_btn = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "search_button"))
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
            print(f"  ❌ Property ID search error: {str(e)}")
            return {}

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
                    EC.element_to_be_clickable((By.ID, "search_button"))
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
                EC.presence_of_element_located((By.CLASS_NAME, "property-results"))
            )

            # Find all result rows
            rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header

            print(f"  Found {len(rows)} properties")

            for idx, row in enumerate(rows, 1):
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")

                    property_data = {
                        'property_id': cols[0].text if len(cols) > 0 else '',
                        'owner_name': cols[1].text if len(cols) > 1 else '',
                        'address': cols[2].text if len(cols) > 2 else '',
                        'city': cols[3].text if len(cols) > 3 else '',
                        'zip_code': cols[4].text if len(cols) > 4 else '',
                        'sale_date': cols[5].text if len(cols) > 5 else '',
                        'sale_price': cols[6].text if len(cols) > 6 else '',
                        'property_type': cols[7].text if len(cols) > 7 else '',
                        'land_use': cols[8].text if len(cols) > 8 else '',
                        'total_value': cols[9].text if len(cols) > 9 else '',
                        'year_built': cols[10].text if len(cols) > 10 else '',
                        'square_feet': cols[11].text if len(cols) > 11 else '',
                    }

                    # Clean up data
                    if property_data.get('sale_price'):
                        property_data['sale_price_clean'] = property_data['sale_price'].replace('$', '').replace(',', '')
                        try:
                            property_data['sale_price_clean'] = float(property_data['sale_price_clean'])
                        except:
                            property_data['sale_price_clean'] = None

                    if property_data.get('total_value'):
                        property_data['total_value_clean'] = property_data['total_value'].replace('$', '').replace(',', '')
                        try:
                            property_data['total_value_clean'] = float(property_data['total_value_clean'])
                        except:
                            property_data['total_value_clean'] = None

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

    def get_property_details(self, property_id):
        """
        Get detailed information for a specific property

        Args:
            property_id (str): Property ID

        Returns:
            dict: Detailed property information
        """
        try:
            # Navigate to detail page
            detail_url = f"{self.base_url}details/{property_id}"
            self.driver.get(detail_url)
            time.sleep(2)

            details = {}

            # Extract additional details
            try:
                # Building information
                building_section = self.driver.find_element(By.ID, "building_details")
                details['bedrooms'] = building_section.find_element(By.CLASS_NAME, "bedrooms").text
                details['bathrooms'] = building_section.find_element(By.CLASS_NAME, "bathrooms").text
                details['garage'] = building_section.find_element(By.CLASS_NAME, "garage").text
            except:
                pass

            # Land information
            try:
                land_section = self.driver.find_element(By.ID, "land_details")
                details['lot_size'] = land_section.find_element(By.CLASS_NAME, "lot-size").text
                details['zoning'] = land_section.find_element(By.CLASS_NAME, "zoning").text
                details['subdivision'] = land_section.find_element(By.CLASS_NAME, "subdivision").text
            except:
                pass

            # Tax information
            try:
                tax_section = self.driver.find_element(By.ID, "tax_details")
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
    print(" TN STATE PORTAL SCRAPER - TEST")
    print("="*60 + "\n")

    try:
        with TNStatePortalScraper(county="robertson", headless=False) as scraper:
            # Test owner search
            properties = scraper.search_by_owner(last_name="Smith")

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