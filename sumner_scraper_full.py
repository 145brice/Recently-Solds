"""
Sumner County Production Scraper
=================================

This is your main production scraper for Sumner County.
Run this daily to get fresh property sales data.

Uses the SAME code as Wilson County (same platform).

WHAT IT DOES:
- Scrapes last 7 days of property sales (configurable)
- Exports to CSV and Excel
- Saves to database (optional)
- Filters for high-value properties

USAGE:
    python sumner_scraper_full.py
"""

from wilson_sumner_scraper import CountyPropertyScraper
import pandas as pd
from datetime import datetime
import os

# ============================================
# CONFIGURATION - CUSTOMIZE THESE
# ============================================

DAYS_BACK = 7  # Look back 7 days (daily scraper)
MIN_PRICE = 250000  # Minimum sale price to include
HEADLESS = True  # Run without showing browser

# Database settings (set to True to enable)
SAVE_TO_DATABASE = False
DATABASE_FILE = "sumner_leads.db"

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    print("\n" + "="*70)
    print(" SUMNER COUNTY PROPERTY SCRAPER - PRODUCTION")
    print("="*70)
    print(f" Date Range: Last {DAYS_BACK} days")
    print(f" Min Price: ${MIN_PRICE:,}")
    print(f" Headless: {HEADLESS}")
    print("="*70 + "\n")
    
    try:
        # Initialize scraper (note: county="sumner")
        with CountyPropertyScraper(county="sumner", headless=HEADLESS) as scraper:
            
            # Scrape data
            print(f"Scraping Sumner County...")
            df = scraper.scrape_recent_sales(days_back=DAYS_BACK, max_results=500)
            
            if df.empty:
                print("\n⚠ No properties found")
                print("Try increasing DAYS_BACK or check the website")
                return
            
            print(f"✓ Found {len(df)} total properties")
            
            # Filter for high-value properties
            if 'sale_price_clean' in df.columns:
                high_value = df[df['sale_price_clean'] >= MIN_PRICE]
                print(f"✓ {len(high_value)} properties over ${MIN_PRICE:,}")
            else:
                high_value = df
            
            # Add metadata
            high_value['county'] = 'Sumner'
            high_value['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
            
            # Display summary
            print(f"\n{'='*70}")
            print("SUMMARY")
            print(f"{'='*70}")
            print(f"Total Properties: {len(high_value)}")
            
            if 'sale_price_clean' in high_value.columns:
                print(f"\nPrice Range:")
                print(f"  Min: ${high_value['sale_price_clean'].min():,.0f}")
                print(f"  Max: ${high_value['sale_price_clean'].max():,.0f}")
                print(f"  Avg: ${high_value['sale_price_clean'].mean():,.0f}")
            
            # Show sample
            print(f"\nSample (first 5 properties):")
            display_cols = ['owner_name', 'address', 'sale_date', 'sale_price']
            available_cols = [col for col in display_cols if col in high_value.columns]
            print(high_value[available_cols].head().to_string(index=False))
            
            # Save to files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"sumner_sales_{timestamp}.csv"
            excel_filename = f"sumner_sales_{timestamp}.xlsx"
            
            high_value.to_csv(csv_filename, index=False)
            print(f"\n✓ Saved CSV: {csv_filename}")
            
            high_value.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f"✓ Saved Excel: {excel_filename}")
            
            # Optional: Save to database
            if SAVE_TO_DATABASE:
                import sqlite3
                conn = sqlite3.connect(DATABASE_FILE)
                high_value.to_sql('sumner_sales', conn, if_exists='append', index=False)
                print(f"✓ Saved to database: {DATABASE_FILE}")
                conn.close()
            
            # Create leads export for SMS/CRM
            if len(high_value) > 0:
                leads_export = high_value[['owner_name', 'address', 'sale_price', 'sale_date']].copy()
                leads_filename = f"sumner_leads_{timestamp}.csv"
                leads_export.to_csv(leads_filename, index=False)
                print(f"✓ Created leads file: {leads_filename}")
            
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
