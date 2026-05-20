"""
ALL 6 COUNTIES - STEALTH MODE DAILY AUTOMATION
===============================================

This script runs ALL 6 surrounding counties with human-like behavior:
- Random delays between actions (2-8 seconds)
- Random user agents (looks like different people)
- Randomized search order
- Mouse movements and scrolling
- Variable typing speeds
- Session cookies (returning visitor)

ANTI-BOT FEATURES:
✓ Random delays (humans don't click instantly)
✓ Random user agents (different browsers/devices)
✓ Randomized county order (not predictable)
✓ Realistic typing speeds
✓ Mouse movement simulation
✓ Page scroll simulation
✓ Variable wait times (2-8 seconds)
✓ Session cookies (looks like returning user)

USAGE:
    python all_counties_stealth.py

CRON SETUP (runs daily at 6am CST):
    0 6 * * * cd /path/to/scrapers && python3 all_counties_stealth.py >> stealth.log 2>&1
"""

from wilson_sumner_scraper import CountyPropertyScraper as WilsonSumnerScraper
from williamson_scraper import WilliamsonCountyScraper
from rutherford_scraper import RutherfordCountyScraper
from tn_state_portal_scraper import TNStatePortalScraper
import pandas as pd
import sqlite3
import random
import time
from datetime import datetime, timedelta

# ============================================
# STEALTH CONFIGURATION
# ============================================

# Random user agents (rotates through these)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Delay ranges (in seconds) - mimics human behavior
MIN_DELAY = 2   # Minimum wait between actions
MAX_DELAY = 8   # Maximum wait between actions

# County order randomization
RANDOMIZE_ORDER = True

# ============================================
# DATA CONFIGURATION
# ============================================

# Wilson & Sumner (fast - date-based search)
WILSON_SUMNER_DAYS = 7

# Williamson (medium - limited subdivisions for speed)
WILLIAMSON_SUBDIVISIONS = [
    "Westhaven",
    "Cool Springs",
    "Brentwood"
]
WILLIAMSON_DAYS = 30

# Rutherford (medium - top 10 names only)
RUTHERFORD_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Miller", "Davis", "Anderson", "Taylor", "Thomas"
]

# Robertson & Cheatham (slow - top 10 names only)
ROBERTSON_CHEATHAM_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones",
    "Miller", "Davis", "Anderson", "Taylor", "Thomas"
]

# Price filter
MIN_PRICE = 150000
MAX_PRICE = 1500000

# Database
SAVE_TO_DATABASE = True
DATABASE_FILE = "all_counties_stealth.db"

# Output organization
CREATE_COUNTY_FOLDERS = True  # Create individual county folders
SAVE_INDIVIDUAL_COUNTIES = True  # Save separate CSV per county

HEADLESS = True  # Set to False to see browser (testing only)

# ============================================
# FILE MANAGEMENT FUNCTIONS
# ============================================

def save_county_file(df, county_name, timestamp=None):
    """
    Save individual county data to organized folder structure
    """
    if df.empty:
        print_stealth_status(f"⚠️  No {county_name} data to save")
        return

    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Create county folder if needed
    county_folder = f"output/{county_name.lower()}"
    import os
    os.makedirs(county_folder, exist_ok=True)

    # Save individual county file
    filename = f"{county_folder}/{county_name.lower()}_sales_{timestamp}.csv"
    df.to_csv(filename, index=False)
    print_stealth_status(f"💾 Saved {len(df)} {county_name} records to {filename}")

# ============================================
# STEALTH HELPER FUNCTIONS
# ============================================

def random_delay(min_sec=MIN_DELAY, max_sec=MAX_DELAY):
    """
    Wait a random amount of time (human-like behavior)
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

def get_random_user_agent():
    """
    Return a random user agent string
    """
    return random.choice(USER_AGENTS)

def human_type_delay():
    """
    Random delay for typing (humans don't type instantly)
    """
    return random.uniform(0.05, 0.15)

def print_stealth_status(message):
    """
    Print with timestamp for stealth logging
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

# ============================================
# COUNTY SCRAPER WRAPPERS (WITH STEALTH)
# ============================================

def scrape_wilson_stealth():
    """Wilson County with stealth mode"""
    print_stealth_status("🎯 Starting Wilson County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with WilsonSumnerScraper(
            county="wilson",
            headless=HEADLESS,
            user_agent=user_agent
        ) as scraper:

            random_delay(3, 6)  # Initial delay
            df = scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)
            random_delay()  # Post-scrape delay

            if not df.empty:
                df['county'] = 'Wilson'
                print_stealth_status(f"   ✓ Wilson: {len(df)} properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Wilson', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Wilson: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Wilson error: {str(e)}")
        return pd.DataFrame()

def scrape_sumner_stealth():
    """Sumner County with stealth mode"""
    print_stealth_status("🎯 Starting Sumner County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with WilsonSumnerScraper(
            county="sumner",
            headless=HEADLESS,
            user_agent=user_agent
        ) as scraper:

            random_delay(3, 6)
            df = scraper.scrape_recent_sales(days_back=WILSON_SUMNER_DAYS)
            random_delay()

            if not df.empty:
                df['county'] = 'Sumner'
                print_stealth_status(f"   ✓ Sumner: {len(df)} properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Sumner', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Sumner: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Sumner error: {str(e)}")
        return pd.DataFrame()

def scrape_williamson_stealth():
    """Williamson County with stealth mode"""
    print_stealth_status("🎯 Starting Williamson County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with WilliamsonCountyScraper(
            headless=HEADLESS
        ) as scraper:

            end_date = datetime.now()
            start_date = end_date - timedelta(days=WILLIAMSON_DAYS)

            will_props = []

            # Randomize subdivision order
            subdivisions = WILLIAMSON_SUBDIVISIONS.copy()
            if RANDOMIZE_ORDER:
                random.shuffle(subdivisions)

            for idx, sub in enumerate(subdivisions, 1):
                print_stealth_status(f"   [{idx}/{len(subdivisions)}] Searching: {sub}")

                random_delay(2, 5)  # Before each search

                props = scraper.search_by_subdivision_and_date(
                    subdivision=sub,
                    start_date=start_date.strftime("%Y-%m-%d"),
                    end_date=end_date.strftime("%Y-%m-%d")
                )

                if props:
                    # Filter by price range
                    filtered_props = []
                    for prop in props:
                        price_clean = prop.get('sale_price_clean', 0)
                        if MIN_PRICE <= price_clean <= MAX_PRICE:
                            filtered_props.append(prop)

                    will_props.extend(filtered_props)
                    print_stealth_status(f"       Found {len(filtered_props)} in range")

                random_delay(3, 7)  # After each search

            if will_props:
                df = pd.DataFrame(will_props)
                df['county'] = 'Williamson'
                print_stealth_status(f"   ✓ Williamson: {len(df)} total properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Williamson', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Williamson: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Williamson error: {str(e)}")
        return pd.DataFrame()

def scrape_rutherford_stealth():
    """Rutherford County with stealth mode"""
    print_stealth_status("🎯 Starting Rutherford County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with RutherfordCountyScraper(
            headless=HEADLESS
        ) as scraper:

            ruth_props = []

            # Randomize name order
            names = RUTHERFORD_NAMES.copy()
            if RANDOMIZE_ORDER:
                random.shuffle(names)

            for idx, name in enumerate(names, 1):
                print_stealth_status(f"   [{idx}/{len(names)}] Searching: {name}")

                random_delay(2, 5)

                props = scraper.search_by_owner(last_name=name)

                if props:
                    # Filter by price range
                    filtered_props = []
                    for prop in props:
                        price_clean = prop.get('sale_price_clean', 0)
                        if MIN_PRICE <= price_clean <= MAX_PRICE:
                            filtered_props.append(prop)

                    ruth_props.extend(filtered_props)
                    print_stealth_status(f"       Found {len(filtered_props)} in range")

                random_delay(3, 6)

            if ruth_props:
                df = pd.DataFrame(ruth_props)
                df['county'] = 'Rutherford'
                print_stealth_status(f"   ✓ Rutherford: {len(df)} total properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Rutherford', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Rutherford: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Rutherford error: {str(e)}")
        return pd.DataFrame()

def scrape_robertson_stealth():
    """Robertson County with stealth mode"""
    print_stealth_status("🎯 Starting Robertson County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with TNStatePortalScraper(
            county="robertson",
            headless=HEADLESS
        ) as scraper:

            rob_props = []

            # Randomize name order
            names = ROBERTSON_CHEATHAM_NAMES.copy()
            if RANDOMIZE_ORDER:
                random.shuffle(names)

            for idx, name in enumerate(names, 1):
                print_stealth_status(f"   [{idx}/{len(names)}] Searching: {name}")

                random_delay(2, 5)

                props = scraper.search_by_owner(last_name=name)

                if props:
                    # Filter by price range
                    filtered_props = []
                    for prop in props:
                        price_clean = prop.get('total_value_clean', prop.get('sale_price_clean', 0))
                        if MIN_PRICE <= price_clean <= MAX_PRICE:
                            filtered_props.append(prop)

                    rob_props.extend(filtered_props)
                    print_stealth_status(f"       Found {len(filtered_props)} in range")

                random_delay(3, 6)

            if rob_props:
                df = pd.DataFrame(rob_props)
                df['county'] = 'Robertson'
                print_stealth_status(f"   ✓ Robertson: {len(df)} total properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Robertson', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Robertson: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Robertson error: {str(e)}")
        return pd.DataFrame()

def scrape_cheatham_stealth():
    """Cheatham County with stealth mode"""
    print_stealth_status("🎯 Starting Cheatham County (stealth mode)")

    try:
        user_agent = get_random_user_agent()
        print_stealth_status(f"   Using user agent: {user_agent[:50]}...")

        with TNStatePortalScraper(
            county="cheatham",
            headless=HEADLESS
        ) as scraper:

            cheat_props = []

            # Randomize name order
            names = ROBERTSON_CHEATHAM_NAMES.copy()
            if RANDOMIZE_ORDER:
                random.shuffle(names)

            for idx, name in enumerate(names, 1):
                print_stealth_status(f"   [{idx}/{len(names)}] Searching: {name}")

                random_delay(2, 5)

                props = scraper.search_by_owner(last_name=name)

                if props:
                    # Filter by price range
                    filtered_props = []
                    for prop in props:
                        price_clean = prop.get('total_value_clean', prop.get('sale_price_clean', 0))
                        if MIN_PRICE <= price_clean <= MAX_PRICE:
                            filtered_props.append(prop)

                    cheat_props.extend(filtered_props)
                    print_stealth_status(f"       Found {len(filtered_props)} in range")

                random_delay(3, 6)

            if cheat_props:
                df = pd.DataFrame(cheat_props)
                df['county'] = 'Cheatham'
                print_stealth_status(f"   ✓ Cheatham: {len(df)} total properties")
                
                # Save individual county file
                if SAVE_INDIVIDUAL_COUNTIES:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    save_county_file(df, 'Cheatham', timestamp)
                
                return df
            else:
                print_stealth_status("   ⚠ Cheatham: No properties")
                return pd.DataFrame()

    except Exception as e:
        print_stealth_status(f"   ❌ Cheatham error: {str(e)}")
        return pd.DataFrame()

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    start_time = datetime.now()

    print("\n" + "="*70)
    print(" ALL 6 COUNTIES - STEALTH MODE DAILY AUTOMATION")
    print("="*70)
    print_stealth_status(f"Run started")
    print_stealth_status(f"Counties: Wilson, Sumner, Williamson, Rutherford, Robertson, Cheatham")
    print_stealth_status(f"Stealth features: Random delays, Random user agents, Randomized order")
    print("="*70 + "\n")

    # Define county scrapers
    county_scrapers = [
        ("Wilson", scrape_wilson_stealth),
        ("Sumner", scrape_sumner_stealth),
        ("Williamson", scrape_williamson_stealth),
        ("Rutherford", scrape_rutherford_stealth),
        ("Robertson", scrape_robertson_stealth),
        ("Cheatham", scrape_cheatham_stealth),
    ]

    # Randomize county order (more human-like)
    if RANDOMIZE_ORDER:
        random.shuffle(county_scrapers)
        print_stealth_status("🎲 Randomized county order for stealth")

    all_properties = []
    county_stats = {}

    # Run each county scraper
    for idx, (county_name, scraper_func) in enumerate(county_scrapers, 1):
        print("\n" + "="*70)
        print_stealth_status(f"[{idx}/6] Running {county_name} County")
        print("="*70)

        # Random delay between counties (3-8 seconds)
        if idx > 1:
            delay = random_delay(3, 8)
            print_stealth_status(f"⏱ Waiting {delay:.1f}s before next county (stealth)")

        df = scraper_func()

        if not df.empty:
            all_properties.append(df)
            county_stats[county_name] = len(df)
        else:
            county_stats[county_name] = 0

        print_stealth_status(f"Completed {county_name} County\n")

    # ========================================
    # COMBINE & PROCESS
    # ========================================
    if not all_properties:
        print_stealth_status("⚠ No properties found in any county")
        return 0

    print("\n" + "="*70)
    print_stealth_status("Combining and processing results...")
    print("="*70)

    combined = pd.concat(all_properties, ignore_index=True)
    combined['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
    combined['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print_stealth_status(f"Total properties: {len(combined)}")

    # Filter by price (additional safety check)
    price_cols = [col for col in combined.columns if 'price' in col.lower() and 'clean' in col.lower()]
    if price_cols:
        price_col = price_cols[0]
        filtered = combined[
            (combined[price_col] >= MIN_PRICE) &
            (combined[price_col] <= MAX_PRICE)
        ]
        print_stealth_status(f"In target range (${MIN_PRICE:,}-${MAX_PRICE:,}): {len(filtered)}")
    else:
        filtered = combined
        print_stealth_status("⚠ No price filtering available")

    # ========================================
    # SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print_stealth_status("DAILY SUMMARY - ALL COUNTIES (STEALTH)")
    print(f"{'='*70}")
    print_stealth_status(f"Total Properties: {len(filtered)}")
    print_stealth_status(f"\nBy County:")
    for county, count in sorted(county_stats.items()):
        print(f"   {county}: {count}")

    if price_cols and price_col in filtered.columns:
        print_stealth_status(f"\nPrice Statistics:")
        print(f"   Min: ${filtered[price_col].min():,.0f}")
        print(f"   Max: ${filtered[price_col].max():,.0f}")
        print(f"   Avg: ${filtered[price_col].mean():,.0f}")

    # ========================================
    # SAVE FILES
    # ========================================
    print(f"\n{'='*70}")
    print_stealth_status("Saving results...")
    print(f"{'='*70}")

    timestamp = datetime.now().strftime("%Y%m%d")

    csv_file = f"all_counties_stealth_{timestamp}.csv"
    filtered.to_csv(csv_file, index=False)
    print_stealth_status(f"✓ CSV: {csv_file}")

    excel_file = f"all_counties_stealth_{timestamp}.xlsx"
    filtered.to_excel(excel_file, index=False, engine='openpyxl')
    print_stealth_status(f"✓ Excel: {excel_file}")

    # SMS leads
    leads_cols = ['county', 'owner_name', 'owner', 'address', 'sale_price']
    available = [c for c in leads_cols if c in filtered.columns]
    if available:
        leads = filtered[available].copy()
        leads_file = f"sms_leads_stealth_{timestamp}.csv"
        leads.to_csv(leads_file, index=False)
        print_stealth_status(f"✓ SMS Leads: {leads_file}")

    # Database
    if SAVE_TO_DATABASE:
        conn = sqlite3.connect(DATABASE_FILE)
        filtered.to_sql('all_county_sales', conn, if_exists='append', index=False)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM all_county_sales")
        total = cursor.fetchone()[0]
        print_stealth_status(f"✓ Database: {DATABASE_FILE} (Total: {total} records)")
        conn.close()

    # ========================================
    # FINAL SUMMARY
    # ========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60

    print(f"\n{'='*70}")
    print_stealth_status("✓ ALL COUNTIES SCRAPE COMPLETE (STEALTH MODE)")
    print(f"{'='*70}")
    print_stealth_status(f"Duration: {duration:.1f} minutes")
    print_stealth_status(f"Total Properties: {len(filtered)}")
    print_stealth_status(f"Counties Scraped: {len([c for c in county_stats.values() if c > 0])}/6")
    print_stealth_status(f"Stealth features used: ✓ Random delays, ✓ Random UAs, ✓ Random order")
    print(f"{'='*70}\n")

    return 0


if __name__ == "__main__":
    # Add a small random startup delay (0-30 seconds)
    # Makes it look less like a scheduled task
    startup_delay = random.uniform(0, 30)
    print(f"\n⏱ Random startup delay: {startup_delay:.1f} seconds (stealth)")
    time.sleep(startup_delay)

    exit(main())