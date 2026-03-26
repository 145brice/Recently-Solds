"""
Robertson County Production Scraper
====================================

Production scraper for Robertson County (Springfield area).
Uses Tennessee State Portal.

WHAT IT DOES:
- Searches by owner name (bulk search)
- Gets recent property sales
- Filters for your target price range
- Exports to CSV/Excel

USAGE:
    python robertson_scraper_full.py
"""

from tn_state_portal_scraper import TNStatePortalScraper
import pandas as pd
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

COUNTY = "Robertson"  # Robertson County

# Common last names to search
COMMON_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Miller", "Davis", "Anderson", "Taylor", "Thomas",
    "Moore", "Martin", "Jackson", "Thompson", "White",
    # Add more names as needed
]

# Price filter
MIN_PRICE = 150000
MAX_PRICE = 600000

HEADLESS = True

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    print("\n" + "="*70)
    print(f" {COUNTY.upper()} COUNTY PRODUCTION SCRAPER")
    print("="*70)
    print(f" Searching {len(COMMON_NAMES)} common names")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("="*70 + "\n")
    
    all_properties = []
    
    try:
        with TNStatePortalScraper(county=COUNTY, headless=HEADLESS) as scraper:
            
            for idx, name in enumerate(COMMON_NAMES, 1):
                print(f"[{idx}/{len(COMMON_NAMES)}] Searching: {name}")
                
                properties = scraper.search_by_owner(owner_name=name)
                
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
        
        if not all_properties:
            print("\n⚠ No properties found")
            return 0
        
        # Convert to DataFrame
        df = pd.DataFrame(all_properties)
        df['county'] = COUNTY
        df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n✓ Total properties found: {len(df)}")
        
        # Filter by price if available
        price_col = None
        for col in ['assessed_value', 'total_assessed', 'last_sale_price']:
            if col in df.columns:
                price_col = col
                break
        
        if price_col:
            # Clean price
            df[f'{price_col}_clean'] = df[price_col].astype(str).str.replace('$', '').str.replace(',', '')
            df[f'{price_col}_clean'] = pd.to_numeric(df[f'{price_col}_clean'], errors='coerce')
            
            filtered = df[
                (df[f'{price_col}_clean'] >= MIN_PRICE) &
                (df[f'{price_col}_clean'] <= MAX_PRICE)
            ]
            print(f"✓ Properties in target range: {len(filtered)}")
        else:
            filtered = df
            print("⚠ No price data for filtering")
        
        if filtered.empty:
            print("⚠ No properties in target range")
            return 0
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total Properties: {len(filtered)}")
        
        if price_col:
            print(f"\nPrice Statistics ({price_col}):")
            print(f"  Min: ${filtered[f'{price_col}_clean'].min():,.0f}")
            print(f"  Max: ${filtered[f'{price_col}_clean'].max():,.0f}")
            print(f"  Avg: ${filtered[f'{price_col}_clean'].mean():,.0f}")
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = f"{COUNTY.lower()}_sales_{timestamp}.csv"
        filtered.to_csv(csv_file, index=False)
        print(f"\n✓ Saved CSV: {csv_file}")
        
        excel_file = f"{COUNTY.lower()}_sales_{timestamp}.xlsx"
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
