"""
Williamson County Production Scraper
=====================================

Production scraper for Williamson County (Franklin, Brentwood).
High-end market with ~$775k median sale price.

WHAT IT DOES:
- Searches by subdivision and date range
- Gets recent property sales
- Filters for your target price range
- Exports to CSV/Excel

USAGE:
    python williamson_scraper_full.py

NOTE: Williamson County works best with subdivision-specific searches.
      Edit SUBDIVISIONS list below to target your areas.
"""

from williamson_scraper import WilliamsonCountyScraper
import pandas as pd
from datetime import datetime, timedelta

# ============================================
# CONFIGURATION
# ============================================

DAYS_BACK = 30  # Look back 30 days

# Target subdivisions (add/remove as needed)
SUBDIVISIONS = [
    "Westhaven",
    "Cool Springs",
    "Downtown Franklin",
    "Brentwood",
    "Arrington",
    # Add more subdivisions here
]

# Price filter
MIN_PRICE = 400000  # High-end market
MAX_PRICE = 2000000

HEADLESS = True

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    print("\n" + "="*70)
    print(" WILLIAMSON COUNTY PRODUCTION SCRAPER")
    print("="*70)
    print(f" Date Range: Last {DAYS_BACK} days")
    print(f" Subdivisions: {len(SUBDIVISIONS)}")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("="*70 + "\n")
    
    all_properties = []
    
    try:
        with WilliamsonCountyScraper(headless=HEADLESS) as scraper:
            
            # Calculate dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=DAYS_BACK)
            
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            # Search each subdivision
            for idx, subdivision in enumerate(SUBDIVISIONS, 1):
                print(f"[{idx}/{len(SUBDIVISIONS)}] Searching: {subdivision}")
                
                properties = scraper.search_by_subdivision_and_date(
                    subdivision=subdivision,
                    start_date=start_str,
                    end_date=end_str
                )
                
                if properties:
                    for prop in properties:
                        prop['subdivision'] = subdivision
                        all_properties.append(prop)
                    print(f"  ✓ Found {len(properties)} properties")
                else:
                    print(f"  - No properties found")
                
                # Be polite
                import time
                time.sleep(2)
        
        if not all_properties:
            print("\n⚠ No properties found in any subdivision")
            print("Try adding more subdivisions or increasing DAYS_BACK")
            return 0
        
        # Convert to DataFrame
        df = pd.DataFrame(all_properties)
        df['county'] = 'Williamson'
        df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
        
        print(f"\n✓ Total properties found: {len(df)}")
        
        # Filter by price if available
        if 'sale_price_clean' in df.columns:
            filtered = df[
                (df['sale_price_clean'] >= MIN_PRICE) &
                (df['sale_price_clean'] <= MAX_PRICE)
            ]
            print(f"✓ Properties in target range: {len(filtered)}")
        else:
            filtered = df
        
        if filtered.empty:
            print("⚠ No properties in target price range")
            return 0
        
        # Summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"Total Properties: {len(filtered)}")
        
        if 'sale_price_clean' in filtered.columns:
            print(f"\nPrice Statistics:")
            print(f"  Min: ${filtered['sale_price_clean'].min():,.0f}")
            print(f"  Max: ${filtered['sale_price_clean'].max():,.0f}")
            print(f"  Avg: ${filtered['sale_price_clean'].mean():,.0f}")
        
        # Save files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = f"williamson_sales_{timestamp}.csv"
        filtered.to_csv(csv_file, index=False)
        print(f"\n✓ Saved CSV: {csv_file}")
        
        excel_file = f"williamson_sales_{timestamp}.xlsx"
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
