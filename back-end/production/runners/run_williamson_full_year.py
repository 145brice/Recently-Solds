"""
Run Williamson County scraper for full year (365 days)
With human-like delays to avoid detection
"""

from williamson_scraper import WilliamsonCountyScraper
from datetime import datetime, timedelta
import pandas as pd
import os

def main():
    print("\n" + "="*70)
    print(" WILLIAMSON COUNTY - FULL YEAR SCRAPE")
    print("="*70)
    print(" Using human-like delays and behaviors")
    print(" This will take longer but appears more natural")
    print("="*70 + "\n")

    start_time = datetime.now()

    # Create output folder
    os.makedirs('output', exist_ok=True)
    os.makedirs('output/williamson', exist_ok=True)

    try:
        # Initialize with human_like=True for natural behavior
        with WilliamsonCountyScraper(headless=True, human_like=True) as scraper:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

            # Run the search
            props = scraper.search_by_date_only(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )

            if props:
                # Create DataFrame
                df = pd.DataFrame(props)
                df['county'] = 'Williamson'
                df['scrape_date'] = datetime.now().strftime('%Y-%m-%d')
                df['scrape_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Generate filenames
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Save main CSV
                csv_file = f'output/williamson_full_year_{timestamp}.csv'
                df.to_csv(csv_file, index=False)
                print(f"\n✓ Main CSV: {csv_file}")

                # Save to dated folder
                dated_file = f'output/williamson/williamson_full_year_{datetime.now().strftime("%Y%m%d")}.csv'
                df.to_csv(dated_file, index=False)
                print(f"✓ Dated folder: {dated_file}")

                # Save Excel version
                excel_file = f'output/williamson_full_year_{timestamp}.xlsx'
                df.to_excel(excel_file, index=False, engine='openpyxl')
                print(f"✓ Excel file: {excel_file}")

                # Print statistics
                print(f"\n" + "="*70)
                print(" RESULTS SUMMARY")
                print("="*70)
                print(f"Total properties: {len(props)}")

                if 'sale_price_clean' in df.columns:
                    valid_prices = df[df['sale_price_clean'] > 0]['sale_price_clean']
                    print(f"Properties with valid prices: {len(valid_prices)}")

                    if len(valid_prices) > 0:
                        print(f"\nPrice Statistics:")
                        print(f"  Min:    ${valid_prices.min():>15,.2f}")
                        print(f"  Max:    ${valid_prices.max():>15,.2f}")
                        print(f"  Avg:    ${valid_prices.mean():>15,.2f}")
                        print(f"  Median: ${valid_prices.median():>15,.2f}")

                # City breakdown
                if 'city' in df.columns:
                    print(f"\nProperties by City:")
                    city_counts = df['city'].value_counts().head(10)
                    for city, count in city_counts.items():
                        print(f"  {city:20s} {count:>5d}")

                # Monthly breakdown
                if 'sale_date' in df.columns:
                    # Try to parse the dates
                    try:
                        df['sale_month'] = pd.to_datetime(df['sale_date'], format='%m/%d/%Y').dt.strftime('%Y-%m')
                        print(f"\nProperties by Month:")
                        month_counts = df['sale_month'].value_counts().sort_index()
                        for month, count in month_counts.items():
                            print(f"  {month}: {count:>4d}")
                    except:
                        pass

                # Time taken
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                minutes = duration / 60

                print(f"\n" + "="*70)
                print(f"✓ SCRAPE COMPLETE")
                print("="*70)
                print(f"Started:  {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Duration: {minutes:.1f} minutes ({duration:.0f} seconds)")
                print(f"Properties: {len(props)}")
                print(f"Avg time per property: {duration/len(props):.2f} seconds")
                print("="*70 + "\n")

            else:
                print("\n⚠ No properties found")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
