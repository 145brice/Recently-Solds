"""
ALL COUNTIES - DAILY AUTOMATION
================================

Master automation script for 7 Nashville-area counties:
1. Davidson County (Nashville) - NEW
2. Wilson County (Mt. Juliet area)
3. Sumner County (Hendersonville, Gallatin)
4. Williamson County (Franklin, Brentwood)
5. Rutherford County (Murfreesboro)
6. Robertson County (Springfield)
7. Cheatham County (Ashland City)

WHAT IT DOES:
- Runs all 7 county scrapers
- Normalizes output to a unified schema
- Exports combined CSV directly to the front-end dashboard
- Saves archive copies and optional SQLite database

USAGE:
    python all_counties_daily.py

Or use the launcher:
    python ../../run_daily.py
"""

import sys
import os

# Fix import paths — scrapers and utilities live in sibling folders
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_this_dir, '..', 'scrapers'))
sys.path.insert(0, os.path.join(_this_dir, '..', 'utilities'))

# Lazy imports for scrapers — only loaded when the county is enabled.
# This avoids requiring selenium if only running Davidson (which uses requests).
from normalize_columns import normalize_to_frontend_schema
from common_names import TOP_100_SURNAMES

import pandas as pd
from datetime import datetime, timedelta
import sqlite3

# ============================================
# CONFIGURATION
# ============================================
# All values can be overridden via environment variables (set by the control panel).

# Davidson (Excel download from padctn.org)
DAVIDSON_DAYS = int(os.environ.get('DAVIDSON_DAYS', 7))

# Wilson & Sumner (date-based search)
WILSON_SUMNER_DAYS = int(os.environ.get('WILSON_SUMNER_DAYS', 7))

# Williamson (date-based search)
WILLIAMSON_DAYS = int(os.environ.get('WILLIAMSON_DAYS', 7))

# Rutherford, Robertson, Cheatham (name-based search)
# Using top 100 surnames for better coverage (~25-30% of population)
NAME_SEARCH_LIST = TOP_100_SURNAMES

# Price filter (across all counties)
MIN_PRICE = int(os.environ.get('MIN_PRICE', 150000))
MAX_PRICE = int(os.environ.get('MAX_PRICE', 1500000))

# Which counties to run (comma-separated, or "all")
_enabled = os.environ.get('ENABLED_COUNTIES', 'Davidson,Williamson')
ENABLED_COUNTIES = (
    {'Davidson', 'Wilson', 'Sumner', 'Williamson', 'Rutherford', 'Robertson', 'Cheatham'}
    if _enabled == 'all'
    else set(c.strip() for c in _enabled.split(',') if c.strip())
)

# Database
SAVE_TO_DATABASE = True
DATABASE_FILE = os.path.join(_this_dir, '..', '..', 'all_counties_leads.db')

# Output paths
OUTPUT_DIR = os.path.join(_this_dir, '..', '..', 'output')
FRONTEND_DIR = os.path.join(_this_dir, '..', '..', '..', 'Property-Managers--Front-End')
FRONTEND_CSV = os.path.join(FRONTEND_DIR, 'nashville_cash_leads_clean.csv')

# Save individual county CSVs
SAVE_INDIVIDUAL_COUNTIES = True

HEADLESS = True

# ============================================
# HELPER FUNCTIONS
# ============================================

def save_county_file(df, county_name, timestamp):
    """Save individual county CSV to output folder."""
    if df.empty:
        return
    county_folder = os.path.join(OUTPUT_DIR, county_name.lower())
    os.makedirs(county_folder, exist_ok=True)
    county_csv = os.path.join(county_folder, f"{county_name.lower()}_sales_{timestamp}.csv")
    df.to_csv(county_csv, index=False)
    print(f"  Saved: {county_csv}")


def scrape_county(name, number, total, scrape_fn):
    """
    Wrapper that runs a scrape function, catches errors, and returns
    a normalized DataFrame (or empty DataFrame on failure).
    """
    print(f"\n{'='*70}")
    print(f"{number}/{total} - {name.upper()} COUNTY")
    print("=" * 70)

    if name not in ENABLED_COUNTIES:
        print(f"[SKIP] {name}: Disabled")
        return pd.DataFrame()

    try:
        raw_df = scrape_fn()
        if raw_df is not None and not raw_df.empty:
            normalized = normalize_to_frontend_schema(raw_df, name)
            print(f"[OK] {name}: {len(normalized)} properties")
            return normalized
        else:
            print(f"[WARN] {name}: No properties found")
            return pd.DataFrame()
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
        return pd.DataFrame()


# ============================================
# MAIN SCRIPT
# ============================================

def main():
    start_time = datetime.now()

    print("\n" + "=" * 70)
    print(" NASHVILLE METRO - ALL COUNTIES DAILY AUTOMATION")
    print("=" * 70)
    print(f" Run Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Counties: {', '.join(sorted(ENABLED_COUNTIES))}")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("=" * 70)

    all_properties = []
    county_stats = {}
    total_counties = 7

    # ------------------------------------------
    # 1. DAVIDSON COUNTY (Excel download)
    # ------------------------------------------
    def scrape_davidson():
        from davidson_scraper import DavidsonCountyScraper
        with DavidsonCountyScraper(headless=HEADLESS) as scraper:
            return scraper.scrape_recent_sales(days_back=DAVIDSON_DAYS)

    df = scrape_county("Davidson", 1, total_counties, scrape_davidson)
    county_stats['Davidson'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Davidson', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 2. WILSON COUNTY (TN State Portal - date-based)
    # ------------------------------------------
    def scrape_wilson():
        from tn_state_portal_scraper import TNStatePortalScraper
        with TNStatePortalScraper(county="wilson", headless=HEADLESS) as scraper:
            return scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)

    df = scrape_county("Wilson", 2, total_counties, scrape_wilson)
    county_stats['Wilson'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Wilson', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 3. SUMNER COUNTY (TN State Portal - date-based)
    # ------------------------------------------
    def scrape_sumner():
        from tn_state_portal_scraper import TNStatePortalScraper
        with TNStatePortalScraper(county="sumner", headless=HEADLESS) as scraper:
            return scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)

    df = scrape_county("Sumner", 3, total_counties, scrape_sumner)
    county_stats['Sumner'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Sumner', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 4. WILLIAMSON COUNTY (date-based)
    # ------------------------------------------
    def scrape_williamson():
        from williamson_scraper import WilliamsonCountyScraper
        with WilliamsonCountyScraper(headless=HEADLESS) as scraper:
            # Portal data lags behind real time (often months behind).
            # Search a wide window (180 days back) to capture whatever's
            # available, then filter down to the most recent N days of actual data.
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)
            results = scraper.search_by_date_only(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            if not results:
                return pd.DataFrame()
            df = pd.DataFrame(results)
            # Filter to most recent WILLIAMSON_DAYS of available data
            if 'sale_date' in df.columns:
                df['sale_date_parsed'] = pd.to_datetime(df['sale_date'], errors='coerce')
                valid = df['sale_date_parsed'].dropna()
                if not valid.empty:
                    most_recent = valid.max()
                    cutoff = most_recent - timedelta(days=WILLIAMSON_DAYS)
                    before = len(df)
                    df = df[df['sale_date_parsed'] >= cutoff]
                    print(f"  Date range: {cutoff.strftime('%Y-%m-%d')} to {most_recent.strftime('%Y-%m-%d')}")
                    print(f"  Filtered to last {WILLIAMSON_DAYS} days of data: {before} -> {len(df)} records")
                df = df.drop(columns=['sale_date_parsed'], errors='ignore')
            return df

    df = scrape_county("Williamson", 4, total_counties, scrape_williamson)
    county_stats['Williamson'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Williamson', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 5. RUTHERFORD COUNTY (name-based)
    # ------------------------------------------
    def scrape_rutherford():
        from rutherford_scraper import RutherfordCountyScraper
        with RutherfordCountyScraper(headless=HEADLESS) as scraper:
            all_props = []
            for name in NAME_SEARCH_LIST:
                print(f"  Searching: {name}")
                props = scraper.search_by_owner(last_name=name)
                if props:
                    all_props.extend(props)
            return pd.DataFrame(all_props) if all_props else pd.DataFrame()

    df = scrape_county("Rutherford", 5, total_counties, scrape_rutherford)
    county_stats['Rutherford'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Rutherford', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 6. ROBERTSON COUNTY (TN State Portal - date-based)
    # ------------------------------------------
    def scrape_robertson():
        from tn_state_portal_scraper import TNStatePortalScraper
        with TNStatePortalScraper(county="robertson", headless=HEADLESS) as scraper:
            return scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)

    df = scrape_county("Robertson", 6, total_counties, scrape_robertson)
    county_stats['Robertson'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Robertson', start_time.strftime("%Y%m%d_%H%M%S"))

    # ------------------------------------------
    # 7. CHEATHAM COUNTY (TN State Portal - date-based)
    # ------------------------------------------
    def scrape_cheatham():
        from tn_state_portal_scraper import TNStatePortalScraper
        with TNStatePortalScraper(county="cheatham", headless=HEADLESS) as scraper:
            return scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)

    df = scrape_county("Cheatham", 7, total_counties, scrape_cheatham)
    county_stats['Cheatham'] = len(df)
    if not df.empty:
        all_properties.append(df)
        if SAVE_INDIVIDUAL_COUNTIES:
            save_county_file(df, 'Cheatham', start_time.strftime("%Y%m%d_%H%M%S"))

    # ========================================
    # COMBINE & FILTER
    # ========================================
    if not all_properties:
        print("\n[WARN] No properties found in any county")
        return 1

    print(f"\n{'='*70}")
    print("COMBINING RESULTS")
    print("=" * 70)

    combined = pd.concat(all_properties, ignore_index=True)
    print(f"Total properties: {len(combined)}")

    # Filter by price — Price column is now a formatted string like "$250,000"
    def parse_price_for_filter(val):
        try:
            return float(str(val).replace('$', '').replace(',', '').strip())
        except (ValueError, TypeError):
            return 0.0

    combined['_price_num'] = combined['Price'].apply(parse_price_for_filter)
    filtered = combined[
        (combined['_price_num'] >= MIN_PRICE) &
        (combined['_price_num'] <= MAX_PRICE)
    ].drop(columns=['_price_num'])
    # Also drop the helper column from combined for archive
    combined = combined.drop(columns=['_price_num'])

    print(f"In target range (${MIN_PRICE:,}-${MAX_PRICE:,}): {len(filtered)}")

    # ========================================
    # SAVE FILES
    # ========================================
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print("=" * 70)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = start_time.strftime("%Y%m%d")

    # 1. Archive copy (back-end)
    archive_csv = os.path.join(OUTPUT_DIR, f"all_counties_{timestamp}.csv")
    filtered.to_csv(archive_csv, index=False)
    print(f"[OK] Archive CSV: {archive_csv}")

    # 2. Front-end CSV (directly to dashboard directory)
    if os.path.isdir(FRONTEND_DIR):
        filtered.to_csv(FRONTEND_CSV, index=False)
        print(f"[OK] Front-end CSV: {FRONTEND_CSV}")
    else:
        print(f"[WARN] Front-end directory not found: {FRONTEND_DIR}")
        print(f"  Saving to output/ instead")
        filtered.to_csv(os.path.join(OUTPUT_DIR, "nashville_cash_leads_clean.csv"), index=False)

    # 3. Database
    if SAVE_TO_DATABASE:
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            filtered.to_sql('all_county_sales', conn, if_exists='append', index=False)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM all_county_sales")
            total = cursor.fetchone()[0]
            print(f"[OK] Database: {DATABASE_FILE} (Total: {total} records)")
            conn.close()
        except Exception as e:
            print(f"[WARN] Database error: {e}")

    # ========================================
    # SUMMARY
    # ========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60

    print(f"\n{'='*70}")
    print("[OK] ALL COUNTIES SCRAPE COMPLETE")
    print("=" * 70)
    print(f"Duration: {duration:.1f} minutes")
    print(f"Total Properties: {len(filtered)}")
    print(f"Counties Scraped: {len([c for c in county_stats.values() if c > 0])}/{total_counties}")
    print(f"\nBy County:")
    for county, count in sorted(county_stats.items()):
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"  {status} {county}: {count}")
    print("=" * 70 + "\n")

    return 0


if __name__ == "__main__":
    exit(main())
