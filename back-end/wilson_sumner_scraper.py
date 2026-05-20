"""
Wilson & Sumner County Property Scraper
========================================

This scraper extracts recent sold homes data from Wilson and Sumner County, TN
property search websites. Both counties use the same geopowered.com platform.

SETUP INSTRUCTIONS:
==================
1. Install required packages:
   pip install selenium pandas webdriver-manager

2. Install Chrome browser if not already installed

3. Run the scraper:
   python wilson_sumner_scraper.py

FEATURES:
=========
- Search for recently sold properties
- Extract new owner information
- Get sale prices and dates
- Export to CSV/Excel
- Works for both Wilson and Sumner counties

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
from datetime import datetime, timedelta
import os


class CountyPropertyScraper:
    """
    Scraper for Wilson and Sumner County property records
    """
    
    def __init__(self, county="wilson", headless=True, user_agent=None):
        """
        Initialize the scraper
        
        Args:
            county (str): 'wilson' or 'sumner'
            headless (bool): Run browser in headless mode
            user_agent (str): Optional custom user agent string
        """
        self.county = county.lower()
        self.urls = {
            "wilson": "https://wilsontn.geopowered.com/propertysearch/",
            "sumner": "https://sumnertn.geopowered.com/propertysearch/"
        }
        
        if self.county not in self.urls:
            raise ValueError("County must be 'wilson' or 'sumner'")
        
        self.base_url = self.urls[self.county]
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        
        # Add custom user agent if provided
        if user_agent:
            chrome_options.add_argument(f'user-agent={user_agent}')
        
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
        
        print(f"✓ Initialized {self.county.title()} County scraper")
    
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
    
    def perform_advanced_search(self, sale_date_from=None, sale_date_to=None):
        """
        Perform advanced search with sale date filters
        
        Args:
            sale_date_from (str): Start date 'MM/DD/YYYY'
            sale_date_to (str): End date 'MM/DD/YYYY'
        """
        try:
            # Look for Advanced Search link/button
            advanced_link = self.wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Advanced Search"))
            )
            advanced_link.click()
            time.sleep(2)
            
            # Fill in sale date fields if provided
            if sale_date_from:
                sale_from_field = self.driver.find_element(By.NAME, "sale_date_from")
                sale_from_field.clear()
                sale_from_field.send_keys(sale_date_from)
            
            if sale_date_to:
                sale_to_field = self.driver.find_element(By.NAME, "sale_date_to")
                sale_to_field.clear()
                sale_to_field.send_keys(sale_date_to)
            
            # Click search button
            search_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
            search_btn.click()
            
            time.sleep(3)
            print("✓ Advanced search submitted")
            
        except Exception as e:
            print(f"⚠ Advanced search error: {str(e)}")
            print("  Attempting alternative search method...")
    
    def extract_search_results(self):
        """Extract property data from search results page"""
        properties = []
        
        try:
            # Wait for results table
            results_table = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
            )
            
            # Find all result rows
            rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header
            
            print(f"Found {len(rows)} properties")
            
            for idx, row in enumerate(rows, 1):
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    
                    property_data = {
                        'parcel_id': cols[0].text if len(cols) > 0 else '',
                        'owner_name': cols[1].text if len(cols) > 1 else '',
                        'address': cols[2].text if len(cols) > 2 else '',
                        'sale_date': cols[3].text if len(cols) > 3 else '',
                        'sale_price': cols[4].text if len(cols) > 4 else '',
                    }
                    
                    # Click to get more details
                    detail_link = row.find_element(By.TAG_NAME, "a")
                    detail_url = detail_link.get_attribute('href')
                    property_data['detail_url'] = detail_url
                    
                    properties.append(property_data)
                    
                    if idx % 10 == 0:
                        print(f"  Processed {idx}/{len(rows)} properties...")
                    
                except Exception as e:
                    print(f"  Error extracting row {idx}: {str(e)}")
                    continue
            
            print(f"✓ Extracted {len(properties)} properties")
            return properties
            
        except Exception as e:
            print(f"⚠ Error extracting results: {str(e)}")
            return []
    
    def get_property_details(self, detail_url):
        """
        Navigate to property detail page and extract full information
        
        Args:
            detail_url (str): URL to property detail page
        
        Returns:
            dict: Detailed property information
        """
        try:
            self.driver.get(detail_url)
            time.sleep(2)
            
            details = {}
            
            # Extract owner information
            try:
                owner_section = self.driver.find_element(By.ID, "owner_info")
                details['owner_name'] = owner_section.find_element(By.CLASS_NAME, "owner-name").text
                details['owner_address'] = owner_section.find_element(By.CLASS_NAME, "owner-address").text
            except:
                pass
            
            # Extract sale history
            try:
                sale_history = self.driver.find_element(By.ID, "sale_history")
                rows = sale_history.find_elements(By.TAG_NAME, "tr")
                
                if len(rows) > 1:  # Skip header
                    latest_sale = rows[1].find_elements(By.TAG_NAME, "td")
                    details['sale_date'] = latest_sale[0].text if len(latest_sale) > 0 else ''
                    details['sale_price'] = latest_sale[1].text if len(latest_sale) > 1 else ''
                    details['sale_type'] = latest_sale[2].text if len(latest_sale) > 2 else ''
            except:
                pass
            
            # Extract property characteristics
            try:
                prop_info = self.driver.find_element(By.ID, "property_info")
                details['property_type'] = prop_info.find_element(By.CLASS_NAME, "property-type").text
                details['bedrooms'] = prop_info.find_element(By.CLASS_NAME, "bedrooms").text
                details['bathrooms'] = prop_info.find_element(By.CLASS_NAME, "bathrooms").text
                details['square_feet'] = prop_info.find_element(By.CLASS_NAME, "sqft").text
                details['year_built'] = prop_info.find_element(By.CLASS_NAME, "year-built").text
            except:
                pass
            
            return details
            
        except Exception as e:
            print(f"  Error getting property details: {str(e)}")
            return {}
    
    def scrape_recent_sales(self, days_back=30, max_results=100):
        """
        Main method to scrape recent property sales
        
        Args:
            days_back (int): How many days back to search
            max_results (int): Maximum number of results to retrieve
        
        Returns:
            pandas.DataFrame: Property sales data
        """
        print(f"\n{'='*60}")
        print(f"Scraping {self.county.title()} County - Last {days_back} days")
        print(f"{'='*60}\n")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        sale_date_from = start_date.strftime("%m/%d/%Y")
        sale_date_to = end_date.strftime("%m/%d/%Y")
        
        print(f"Date range: {sale_date_from} to {sale_date_to}\n")
        
        # Navigate and search
        self.navigate_to_search()
        self.perform_advanced_search(sale_date_from, sale_date_to)
        
        # Extract results
        properties = self.extract_search_results()
        
        if not properties:
            print("⚠ No properties found")
            return pd.DataFrame()
        
        # Optionally get detailed info for each property
        # Uncomment if you want full details (slower)
        # for prop in properties[:max_results]:
        #     if 'detail_url' in prop:
        #         details = self.get_property_details(prop['detail_url'])
        #         prop.update(details)
        
        # Convert to DataFrame
        df = pd.DataFrame(properties)
        
        # Clean up data
        if 'sale_price' in df.columns:
            df['sale_price_clean'] = df['sale_price'].str.replace('$', '').str.replace(',', '')
            df['sale_price_clean'] = pd.to_numeric(df['sale_price_clean'], errors='coerce')
        
        if 'sale_date' in df.columns:
            df['sale_date_parsed'] = pd.to_datetime(df['sale_date'], errors='coerce')
        
        return df
    
    def save_to_file(self, df, filename=None):
        """
        Save results to CSV and Excel files
        
        Args:
            df (pandas.DataFrame): Data to save
            filename (str): Base filename (without extension)
        """
        if df.empty:
            print("No data to save")
            return
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.county}_county_sales_{timestamp}"
        
        # Save to CSV
        csv_file = f"{filename}.csv"
        df.to_csv(csv_file, index=False)
        print(f"✓ Saved to {csv_file}")
        
        # Save to Excel
        excel_file = f"{filename}.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"✓ Saved to {excel_file}")


def main():
    """
    Example usage
    """
    print("\n" + "="*60)
    print(" WILSON & SUMNER COUNTY PROPERTY SCRAPER")
    print("="*60 + "\n")
    
    # Choose county
    county = "wilson"  # Change to "sumner" for Sumner County
    
    # Initialize scraper
    try:
        with CountyPropertyScraper(county=county, headless=False) as scraper:
            
            # Scrape recent sales (last 30 days)
            df = scraper.scrape_recent_sales(days_back=30, max_results=100)
            
            # Display results
            if not df.empty:
                print(f"\n{'='*60}")
                print("RESULTS SUMMARY")
                print(f"{'='*60}\n")
                print(f"Total properties found: {len(df)}")
                print(f"\nFirst 5 properties:")
                print(df[['owner_name', 'address', 'sale_date', 'sale_price']].head())
                
                # Save results
                scraper.save_to_file(df)
            else:
                print("\nNo data retrieved")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
