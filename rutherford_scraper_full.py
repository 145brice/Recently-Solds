"""
Rutherford County Production Scraper
=====================================

Production scraper for Rutherford County (Murfreesboro area).
Fast-growing county with lots of new development.

WHAT IT DOES:
- Searches by owner name (bulk search)
- Gets recent property sales
- Filters for your target price range
- Exports to CSV/Excel

USAGE:
    python rutherford_scraper_full.py

NOTE: Rutherford County works best with owner name searches.
      You can also search by specific addresses.
"""

from rutherford_scraper import RutherfordCountyScraper
import pandas as pd
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

# Common last names to search (cast wide net)
COMMON_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
    "Martinez", "Anderson", "Taylor", "Thomas", "Moore",
    # Add more names or specific names you're targeting
]

# Or use specific addresses
SEARCH_BY = "owner"  # "owner" or "address"
ADDRESSES = [
    # "123 Main St, Murfreesboro",
    # Add specific addresses here if using address search
]

# Price filter
MIN_PRICE = 200000
MAX_PRICE = 800000

HEADLESS = True

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    print("\n" + "="*70)
    print(" RUTHERFORD COUNTY PRODUCTION SCRAPER")
    print("="*70)
    print(f" Search Method: {SEARCH_BY}")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("="*70 + "\n")
    
    all_properties = []
    
    try:
        with RutherfordCountyScraper(headless=HEADLESS) as scraper:
            
            if SEARCH_BY == "owner":
                # Search by owner names
                print(f"Searching {len(COMMON_NAMES)} common last names...")
                
                for idx, name in enumerate(COMMON_NAMES, 1):
                    print(f"[{idx}/{len(COMMON_NAMES)}] Searching: {name}")
                    
                    properties = scraper.search_by_owner(last_name=name)
                    
                    if properties:
                        for prop in properties:
                            prop['search_name'] = name
                            all_properties.append(prop)
                        print(f"  ✓ Found {len(properties)} properties")
                    else:
                        print(f"  - No properties found")
                    
                    # Be polite
                    import time
                    time.sleep(2)
            
            elif SEARCH_BY == "address":
                # Search by addresses
                print(f"Searching {len(ADDRESSES)} addresses...")
                
                for idx, address in enumerate(ADDRESSES, 1):
                    print(f"[{idx}/{len(ADDRESSES)}] Searching: {address}")
                    
                    property_data = scraper.search_by_address(address=address)
                    
                    if property_data:
                        property_data['search_address'] = address
                        all_properties.append(property_data)
                        print(f"  ✓ Found property")
                    else:
                        print(f"  - Not found")
                    
                    import time
                    time.sleep(2)
        
        if not all_properties:
            print("\n⚠ No properties found")
            print("Try different search terms or increase the name list")
            return 0
        
        # Convert to DataFrame
        df = pd.DataFrame(all_properties)
        df['county'] = 'Rutherford'
        df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n✓ Total properties found: {len(df)}")
        
        # Filter by price if available
        price_col = None
        for col in ['sale_price_clean', 'total_assessed_value']:
            if col in df.columns:
                price_col = col
                break
        
        if price_col:
            # Clean price column
            df[price_col] = df[price_col].astype(str).str.replace('$', '').str.replace(',', '')
            df[price_col] = pd.to_numeric(df[price_col], errors='coerce')
            
            filtered = df[
                (df[price_col] >= MIN_PRICE) &
                (df[price_col] <= MAX_PRICE)
            ]
            print(f"✓ Properties in target range: {len(filtered)}")
        else:
            filtered = df
        
        if filtered.empty:
            print("⚠ No properties in target range")
            return 0
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total Properties: {len(filtered)}")
        
        if price_col and price_col in filtered.columns:
            print(f"\nPrice Statistics ({price_col}):")
            print(f"  Min: ${filtered[price_col].min():,.0f}")
            print(f"  Max: ${filtered[price_col].max():,.0f}")
            print(f"  Avg: ${filtered[price_col].mean():,.0f}")
        
        # Display sample
        print(f"\nSample (first 5):")
        display_cols = ['owner', 'address', 'sale_price', 'sale_date']
        available = [c for c in display_cols if c in filtered.columns]
        if available:
            print(filtered[available].head().to_string(index=False))
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = f"rutherford_sales_{timestamp}.csv"
        filtered.to_csv(csv_file, index=False)
        print(f"\n✓ Saved CSV: {csv_file}")
        
        excel_file = f"rutherford_sales_{timestamp}.xlsx"
        filtered.to_excel(excel_file, index=False, engine='openpyxl')
        print(f"✓ Saved Excel: {excel_file}")
        
        print(f"\n{'='*70}")
        print("✓ COMPLETE!")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
