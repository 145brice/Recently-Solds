"""
ALL SURROUNDING COUNTIES - DAILY AUTOMATION
============================================

Master automation script for ALL 6 counties surrounding Nashville:
1. Wilson County (Mt. Juliet area)
2. Sumner County (Hendersonville, Gallatin)
3. Williamson County (Franklin, Brentwood) 
4. Rutherford County (Murfreesboro)
5. Robertson County (Springfield)
6. Cheatham County (Ashland City)

Excludes Davidson County (Nashville) - run that separately if needed.

WHAT IT DOES:
- Runs all 6 county scrapers
- Combines into single master database
- Exports combined CSV/Excel
- Creates SMS leads list
- Saves to database

USAGE:
    python all_counties_daily.py

CRON SETUP (runs daily at 6am):
    0 6 * * * cd /path/to/scrapers && python3 all_counties_daily.py >> all_counties.log 2>&1
"""

from wilson_sumner_scraper import CountyPropertyScraper as WilsonSumnerScraper
from williamson_scraper import WilliamsonCountyScraper
from rutherford_scraper import RutherfordCountyScraper
from tn_state_portal_scraper import TNStatePortalScraper
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os

# ============================================
# CONFIGURATION
# ============================================

# Wilson & Sumner (date-based search)
WILSON_SUMNER_DAYS = 7  # Last 7 days

# Williamson (subdivision search - limited list for speed)
WILLIAMSON_SUBDIVISIONS = ["Westhaven", "Cool Springs", "Brentwood"]
WILLIAMSON_DAYS = 30

# Rutherford (name search - top 10 names for speed)
RUTHERFORD_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                     "Miller", "Davis", "Anderson", "Taylor", "Thomas"]

# Robertson & Cheatham (name search - top 10 for speed)
ROBERTSON_CHEATHAM_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                             "Miller", "Davis", "Anderson", "Taylor", "Thomas"]

# Price filter (across all counties)
MIN_PRICE = 150000
MAX_PRICE = 1500000

# Database
SAVE_TO_DATABASE = True
DATABASE_FILE = "all_counties_leads.db"

# Output organization
CREATE_COUNTY_FOLDERS = True  # Create individual county folders
SAVE_INDIVIDUAL_COUNTIES = True  # Save separate CSV per county

HEADLESS = True

# ============================================
# HELPER FUNCTIONS
# ============================================

def save_county_file(df, county_name, timestamp):
    """
    Save individual county CSV file organized by county/date

    Args:
        df (DataFrame): County data
        county_name (str): County name
        timestamp (str): Date timestamp YYYYMMDD
    """
    if df.empty:
        return

    # Create county folder
    if CREATE_COUNTY_FOLDERS:
        county_folder = f"output/{county_name.lower()}"
        os.makedirs(county_folder, exist_ok=True)

        # Save individual county CSV
        county_csv = f"{county_folder}/{county_name.lower()}_sales_{timestamp}.csv"
        df.to_csv(county_csv, index=False)
        print(f"  ✓ Individual CSV: {county_csv}")

        # Also save in root output folder for easy access
        root_csv = f"output/{county_name.lower()}_{timestamp}.csv"
        df.to_csv(root_csv, index=False)
        print(f"  ✓ Root CSV: {root_csv}")

    else:
        # Save in current directory
        county_csv = f"{county_name.lower()}_sales_{timestamp}.csv"
        df.to_csv(county_csv, index=False)
        print(f"  ✓ CSV: {county_csv}")

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print(" ALL SURROUNDING COUNTIES - DAILY AUTOMATION")
    print("="*70)
    print(f" Run Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Counties: Wilson, Sumner, Williamson, Rutherford, Robertson, Cheatham")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("="*70 + "\n")
    
    all_properties = []
    county_stats = {}
    
    # ========================================
    # 1. WILSON COUNTY
    # ========================================
    print("="*70)
    print("1/6 - WILSON COUNTY")
    print("="*70)
    try:
        with WilsonSumnerScraper(county="wilson", headless=HEADLESS) as scraper:
            df = scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)
            if not df.empty:
                df['county'] = 'Wilson'
                df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(df)
                county_stats['Wilson'] = len(df)
                print(f"✓ Wilson: {len(df)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(df, 'Wilson', timestamp)
            else:
                print("⚠ Wilson: No properties found")
                county_stats['Wilson'] = 0
    except Exception as e:
        print(f"❌ Wilson error: {str(e)}")
        county_stats['Wilson'] = 0
    
    # ========================================
    # 2. SUMNER COUNTY
    # ========================================
    print("="*70)
    print("2/6 - SUMNER COUNTY")
    print("="*70)
    try:
        with WilsonSumnerScraper(county="sumner", headless=HEADLESS) as scraper:
            df = scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)
            if not df.empty:
                df['county'] = 'Sumner'
                df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(df)
                county_stats['Sumner'] = len(df)
                print(f"✓ Sumner: {len(df)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(df, 'Sumner', timestamp)
            else:
                print("⚠ Sumner: No properties found")
                county_stats['Sumner'] = 0
    except Exception as e:
        print(f"❌ Sumner error: {str(e)}")
        county_stats['Sumner'] = 0
    
    # ========================================
    # 3. WILLIAMSON COUNTY
    # ========================================
    print("="*70)
    print("3/6 - WILLIAMSON COUNTY")
    print("="*70)
    try:
        with WilliamsonCountyScraper(headless=HEADLESS) as scraper:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=WILLIAMSON_DAYS)
            
            will_props = []
            print(f"  Searching: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            will_props = scraper.search_by_date_only(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            if will_props:
                will_df = pd.DataFrame(will_props)
                will_df['county'] = 'Williamson'
                will_df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                will_df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(will_df)
                county_stats['Williamson'] = len(will_props)
                print(f"✓ Williamson: {len(will_props)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(will_df, 'Williamson', timestamp)
            else:
                print("⚠ Williamson: No properties found")
                county_stats['Williamson'] = 0
    except Exception as e:
        print(f"❌ Williamson error: {str(e)}")
        county_stats['Williamson'] = 0

    # ========================================
    # 4. RUTHERFORD COUNTY
    # ========================================
    print("="*70)
    print("4/6 - RUTHERFORD COUNTY")
    print("="*70)
    try:
        with RutherfordCountyScraper(headless=HEADLESS) as scraper:
            ruth_props = []
            for name in RUTHERFORD_NAMES:
                print(f"  Searching: {name}")
                properties = scraper.search_by_owner(last_name=name)
                if properties:
                    for prop in properties:
                        prop['search_name'] = name
                        ruth_props.append(prop)

            if ruth_props:
                ruth_df = pd.DataFrame(ruth_props)
                ruth_df['county'] = 'Rutherford'
                ruth_df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                ruth_df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(ruth_df)
                county_stats['Rutherford'] = len(ruth_props)
                print(f"✓ Rutherford: {len(ruth_props)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(ruth_df, 'Rutherford', timestamp)
            else:
                print("⚠ Rutherford: No properties found")
                county_stats['Rutherford'] = 0
    except Exception as e:
        print(f"❌ Rutherford error: {str(e)}")
        county_stats['Rutherford'] = 0
    
    # ========================================
    # 5. ROBERTSON COUNTY
    # ========================================
    print("="*70)
    print("5/6 - ROBERTSON COUNTY")
    print("="*70)
    try:
        with TNStatePortalScraper(county="Robertson", headless=HEADLESS) as scraper:
            rob_props = []
            for name in ROBERTSON_CHEATHAM_NAMES:
                print(f"  Searching: {name}")
                properties = scraper.search_by_owner(owner_name=name)
                if properties:
                    for prop in properties:
                        prop['search_name'] = name
                        rob_props.append(prop)
            
            if rob_props:
                rob_df = pd.DataFrame(rob_props)
                rob_df['county'] = 'Robertson'
                rob_df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                rob_df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(rob_df)
                county_stats['Robertson'] = len(rob_props)
                print(f"✓ Robertson: {len(rob_props)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(rob_df, 'Robertson', timestamp)
            else:
                print("⚠ Robertson: No properties found")
                county_stats['Robertson'] = 0
    except Exception as e:
        print(f"❌ Robertson error: {str(e)}")
        county_stats['Robertson'] = 0

    # ========================================
    # 6. CHEATHAM COUNTY
    # ========================================
    print("="*70)
    print("6/6 - CHEATHAM COUNTY")
    print("="*70)
    try:
        with TNStatePortalScraper(county="Cheatham", headless=HEADLESS) as scraper:
            cheat_props = []
            for name in ROBERTSON_CHEATHAM_NAMES:
                print(f"  Searching: {name}")
                properties = scraper.search_by_owner(owner_name=name)
                if properties:
                    for prop in properties:
                        prop['search_name'] = name
                        cheat_props.append(prop)

            if cheat_props:
                cheat_df = pd.DataFrame(cheat_props)
                cheat_df['county'] = 'Cheatham'
                cheat_df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                cheat_df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                all_properties.append(cheat_df)
                county_stats['Cheatham'] = len(cheat_props)
                print(f"✓ Cheatham: {len(cheat_props)} properties")

                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_county_file(cheat_df, 'Cheatham', timestamp)
            else:
                print("⚠ Cheatham: No properties found")
                county_stats['Cheatham'] = 0
    except Exception as e:
        print(f"❌ Cheatham error: {str(e)}")
        county_stats['Cheatham'] = 0
    
    # ========================================
    # COMBINE & PROCESS
    # ========================================
    if not all_properties:
        print("\n⚠ No properties found in any county")
        return 0
    
    print("="*70)
    print("COMBINING RESULTS")
    print("="*70)
    
    combined = pd.concat(all_properties, ignore_index=True)
    combined['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
    combined['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Total properties: {len(combined)}")
    
    # Filter by price
    price_cols = [col for col in combined.columns if 'price' in col.lower() and 'clean' in col.lower()]
    if price_cols:
        price_col = price_cols[0]
        filtered = combined[
            (combined[price_col] >= MIN_PRICE) &
            (combined[price_col] <= MAX_PRICE)
        ]
        print(f"In target range: {len(filtered)}")
    else:
        filtered = combined
        print("⚠ No price filtering available")
    
    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print("DAILY SUMMARY - ALL COUNTIES")
    print(f"{'='*70}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total Properties: {len(filtered)}")
    print(f"\nBy County:")
    for county, count in sorted(county_stats.items()):
        print(f"  {county}: {count}")
    
    if price_cols and price_col in filtered.columns:
        print(f"\nPrice Statistics:")
        print(f"  Min: ${filtered[price_col].min():,.0f}")
        print(f"  Max: ${filtered[price_col].max():,.0f}")
        print(f"  Avg: ${filtered[price_col].mean():,.0f}")
    
    # ========================================
    # SAVE FILES
    # ========================================
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print(f"{'='*70}")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    csv_file = f"all_counties_{timestamp}.csv"
    filtered.to_csv(csv_file, index=False)
    print(f"✓ CSV: {csv_file}")
    
    excel_file = f"all_counties_{timestamp}.xlsx"
    filtered.to_excel(excel_file, index=False, engine='openpyxl')
    print(f"✓ Excel: {excel_file}")
    
    # SMS leads
    leads_cols = ['county', 'owner_name', 'owner', 'address', 'sale_price']
    available = [c for c in leads_cols if c in filtered.columns]
    if available:
        leads = filtered[available].copy()
        leads_file = f"sms_leads_all_{timestamp}.csv"
        leads.to_csv(leads_file, index=False)
        print(f"✓ SMS Leads: {leads_file}")
    
    # Database
    if SAVE_TO_DATABASE:
        conn = sqlite3.connect(DATABASE_FILE)
        filtered.to_sql('all_county_sales', conn, if_exists='append', index=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM all_county_sales")
        total = cursor.fetchone()[0]
        print(f"✓ Database: {DATABASE_FILE} (Total: {total} records)")
        conn.close()
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print(f"\n{'='*70}")
    print("✓ ALL COUNTIES SCRAPE COMPLETE")
    print(f"{'='*70}")
    print(f"Duration: {duration:.1f} minutes")
    print(f"Total Properties: {len(filtered)}")
    print(f"Counties Scraped: {len([c for c in county_stats.values() if c > 0])}/6")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
