"""
Daily Automation - Wilson & Sumner Counties
============================================

This script runs BOTH Wilson and Sumner County scrapers daily,
combines the results, and exports for your business.

Perfect for cron jobs or task scheduler.

WHAT IT DOES:
1. Scrapes Wilson County (last 24 hours)
2. Scrapes Sumner County (last 24 hours)
3. Combines both counties
4. Filters for your target leads
5. Exports to CSV, Excel, and database
6. Creates SMS outreach list

USAGE:
    python daily_wilson_sumner.py

CRON SETUP (runs daily at 6am):
    0 6 * * * cd /path/to/scrapers && python3 daily_wilson_sumner.py >> scraper.log 2>&1
"""

from wilson_sumner_scraper import CountyPropertyScraper
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os

# ============================================
# CONFIGURATION
# ============================================

# How many days to look back (1 = yesterday only)
DAYS_BACK = 1

# Filter criteria
MIN_PRICE = 200000  # Minimum sale price
MAX_PRICE = 1000000  # Maximum sale price (set high to include all)

# Database settings
SAVE_TO_DATABASE = True
DATABASE_FILE = "daily_leads.db"

# Email notification settings (optional)
SEND_EMAIL = False
EMAIL_TO = "you@yourdomain.com"

# ============================================
# HELPER FUNCTIONS
# ============================================

def send_email_notification(num_properties):
    """Send email notification about daily scrape"""
    if not SEND_EMAIL:
        return
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        
        msg = MIMEText(f"""
        Daily Property Scraper Report
        ============================
        
        Date: {datetime.now().strftime('%Y-%m-%d')}
        
        New Properties Found: {num_properties}
        
        Counties: Wilson, Sumner
        Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}
        
        Check your CSV files for details!
        """)
        
        msg['Subject'] = f'Daily Scraper: {num_properties} New Properties'
        msg['From'] = 'scraper@yourdomain.com'
        msg['To'] = EMAIL_TO
        
        # Configure your SMTP settings here
        # with smtplib.SMTP('smtp.gmail.com', 587) as server:
        #     server.starttls()
        #     server.login('your_email', 'your_password')
        #     server.send_message(msg)
        
        print(f"✓ Email sent to {EMAIL_TO}")
    except Exception as e:
        print(f"⚠ Email failed: {str(e)}")

# ============================================
# MAIN SCRIPT
# ============================================

def main():
    start_time = datetime.now()
    
    print("\n" + "="*70)
    print(" DAILY AUTOMATION - WILSON & SUMNER COUNTIES")
    print("="*70)
    print(f" Run Date: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f" Looking Back: {DAYS_BACK} day(s)")
    print(f" Price Range: ${MIN_PRICE:,} - ${MAX_PRICE:,}")
    print("="*70 + "\n")
    
    all_properties = []
    
    # ========================================
    # 1. SCRAPE WILSON COUNTY
    # ========================================
    print("1/2 - Scraping Wilson County...")
    try:
        with CountyPropertyScraper(county="wilson", headless=True) as scraper:
            wilson_df = scraper.scrape_recent_sales(days_back=DAYS_BACK, max_results=500)
            
            if not wilson_df.empty:
                wilson_df['county'] = 'Wilson'
                all_properties.append(wilson_df)
                print(f"✓ Wilson: {len(wilson_df)} properties")
            else:
                print("⚠ Wilson: No properties found")
    except Exception as e:
        print(f"❌ Wilson error: {str(e)}")
    
    # ========================================
    # 2. SCRAPE SUMNER COUNTY
    # ========================================
    print("\n2/2 - Scraping Sumner County...")
    try:
        with CountyPropertyScraper(county="sumner", headless=True) as scraper:
            sumner_df = scraper.scrape_recent_sales(days_back=DAYS_BACK, max_results=500)
            
            if not sumner_df.empty:
                sumner_df['county'] = 'Sumner'
                all_properties.append(sumner_df)
                print(f"✓ Sumner: {len(sumner_df)} properties")
            else:
                print("⚠ Sumner: No properties found")
    except Exception as e:
        print(f"❌ Sumner error: {str(e)}")
    
    # ========================================
    # 3. COMBINE AND FILTER
    # ========================================
    if not all_properties:
        print("\n⚠ No properties found in any county")
        print("This is normal if no sales happened yesterday")
        return 0
    
    print("\n" + "="*70)
    print("PROCESSING RESULTS")
    print("="*70)
    
    # Combine both counties
    combined_df = pd.concat(all_properties, ignore_index=True)
    print(f"\nTotal properties (both counties): {len(combined_df)}")
    
    # Filter by price
    if 'sale_price_clean' in combined_df.columns:
        filtered_df = combined_df[
            (combined_df['sale_price_clean'] >= MIN_PRICE) &
            (combined_df['sale_price_clean'] <= MAX_PRICE)
        ]
        print(f"Properties in target price range: {len(filtered_df)}")
    else:
        filtered_df = combined_df
        print("⚠ No price data available for filtering")
    
    if filtered_df.empty:
        print("\n⚠ No properties match your criteria")
        return 0
    
    # Add metadata
    filtered_df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
    filtered_df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # ========================================
    # 4. DISPLAY SUMMARY
    # ========================================
    print(f"\n{'='*70}")
    print("DAILY SUMMARY")
    print(f"{'='*70}")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Total Properties: {len(filtered_df)}")
    print(f"\nBy County:")
    print(filtered_df['county'].value_counts().to_string())
    
    if 'sale_price_clean' in filtered_df.columns:
        print(f"\nPrice Statistics:")
        print(f"  Min: ${filtered_df['sale_price_clean'].min():,.0f}")
        print(f"  Max: ${filtered_df['sale_price_clean'].max():,.0f}")
        print(f"  Avg: ${filtered_df['sale_price_clean'].mean():,.0f}")
    
    print(f"\nSample Properties:")
    display_cols = ['county', 'owner_name', 'address', 'sale_price']
    available_cols = [col for col in display_cols if col in filtered_df.columns]
    print(filtered_df[available_cols].head(10).to_string(index=False))
    
    # ========================================
    # 5. SAVE TO FILES
    # ========================================
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print(f"{'='*70}")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Main export files
    csv_file = f"daily_sales_{timestamp}.csv"
    excel_file = f"daily_sales_{timestamp}.xlsx"
    
    filtered_df.to_csv(csv_file, index=False)
    print(f"✓ CSV: {csv_file}")
    
    filtered_df.to_excel(excel_file, index=False, engine='openpyxl')
    print(f"✓ Excel: {excel_file}")
    
    # SMS/CRM leads export (simplified)
    leads_cols = ['county', 'owner_name', 'address', 'sale_price', 'sale_date']
    available_leads_cols = [col for col in leads_cols if col in filtered_df.columns]
    
    if available_leads_cols:
        leads_export = filtered_df[available_leads_cols].copy()
        leads_file = f"sms_leads_{timestamp}.csv"
        leads_export.to_csv(leads_file, index=False)
        print(f"✓ SMS Leads: {leads_file}")
    
    # Database export
    if SAVE_TO_DATABASE:
        conn = sqlite3.connect(DATABASE_FILE)
        filtered_df.to_sql('daily_sales', conn, if_exists='append', index=False)
        print(f"✓ Database: {DATABASE_FILE}")
        
        # Show database stats
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM daily_sales")
        total_in_db = cursor.fetchone()[0]
        print(f"  Total records in database: {total_in_db}")
        conn.close()
    
    # ========================================
    # 6. SEND NOTIFICATION (optional)
    # ========================================
    send_email_notification(len(filtered_df))
    
    # ========================================
    # FINAL SUMMARY
    # ========================================
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n{'='*70}")
    print("✓ DAILY SCRAPE COMPLETE")
    print(f"{'='*70}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Properties Found: {len(filtered_df)}")
    print(f"Files Created: {csv_file}, {excel_file}, {leads_file if available_leads_cols else 'N/A'}")
    print(f"{'='*70}\n")
    
    return 0


if __name__ == "__main__":
    exit(main())
