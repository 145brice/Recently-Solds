# Wilson & Sumner County Property Scraper

Complete toolkit for scraping recently sold homes data from Wilson and Sumner County, Tennessee property records.

## 🎯 What This Does

- ✅ Scrapes recent property sales from both counties
- ✅ Extracts new owner names and addresses
- ✅ Gets sale prices and dates
- ✅ Exports to CSV/Excel for easy analysis
- ✅ Works with the same code for Wilson AND Sumner counties

## 📋 Prerequisites

```bash
# Python 3.8 or higher
python --version

# Chrome browser (latest version)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install selenium pandas webdriver-manager openpyxl
```

### 2. Run the Scraper

```bash
# For Wilson County
python wilson_sumner_scraper.py

# For Sumner County (edit the script and change county="sumner")
```

### 3. Output Files

The scraper creates two files:
- `wilson_county_sales_YYYYMMDD_HHMMSS.csv`
- `wilson_county_sales_YYYYMMDD_HHMMSS.xlsx`

## 📊 Data Fields Extracted

| Field | Description |
|-------|-------------|
| `parcel_id` | Unique property identifier |
| `owner_name` | Current owner's name |
| `owner_address` | Owner's mailing address |
| `address` | Property address |
| `sale_date` | Date of sale |
| `sale_price` | Sale price |
| `property_type` | Residential, Commercial, etc. |
| `bedrooms` | Number of bedrooms |
| `bathrooms` | Number of bathrooms |
| `square_feet` | Property square footage |
| `year_built` | Year property was built |

## 🔧 Configuration Options

### Change Search Date Range

```python
# Last 60 days instead of 30
df = scraper.scrape_recent_sales(days_back=60, max_results=100)
```

### Switch Counties

```python
# In main() function, change:
county = "wilson"  # to
county = "sumner"
```

### Run Without Browser Window

```python
# Change headless=False to headless=True
with CountyPropertyScraper(county=county, headless=True) as scraper:
```

## 📝 Example Usage

```python
from wilson_sumner_scraper import CountyPropertyScraper
import pandas as pd

# Wilson County - Last 90 days
with CountyPropertyScraper(county="wilson", headless=True) as scraper:
    df = scraper.scrape_recent_sales(days_back=90)
    scraper.save_to_file(df, filename="wilson_q4_2024")

# Sumner County - Last 30 days
with CountyPropertyScraper(county="sumner", headless=True) as scraper:
    df = scraper.scrape_recent_sales(days_back=30)
    scraper.save_to_file(df, filename="sumner_december")
```

## 🛠 Troubleshooting

### Chrome Driver Issues

If you get ChromeDriver errors:

```bash
# Manually install specific version
pip install webdriver-manager --upgrade
```

### Page Load Timeout

Increase wait time in the code:

```python
self.wait = WebDriverWait(self.driver, 30)  # Increase from 20 to 30
```

### Network Restrictions

If running on a server with network restrictions, you may need to:
1. Run locally on your computer
2. Use a proxy
3. Download ChromeDriver manually

### Element Not Found

The website structure might have changed. To debug:

```python
# Add this to see the page
scraper = CountyPropertyScraper(county="wilson", headless=False)
# Browser will stay open so you can inspect
```

## 🔍 Advanced Features

### Get Detailed Property Info

Uncomment this section in `scrape_recent_sales()`:

```python
# Optionally get detailed info for each property
for prop in properties[:max_results]:
    if 'detail_url' in prop:
        details = scraper.get_property_details(prop['detail_url'])
        prop.update(details)
```

⚠️ **Warning**: This makes the scraper significantly slower (1-2 seconds per property)

### Filter Results

```python
# After scraping
df = scraper.scrape_recent_sales(days_back=30)

# Filter by price range
expensive_homes = df[df['sale_price_clean'] > 500000]

# Filter by date
recent = df[df['sale_date_parsed'] > '2024-12-01']

# Filter by owner name (find specific buyer)
specific_buyer = df[df['owner_name'].str.contains('Smith', case=False)]
```

## 📦 Other Counties

The same approach works for these surrounding counties:

### Williamson County
```python
# URL: https://inigo.williamson-tn.org/property_search/
# Different platform - requires separate scraper
```

### Rutherford County
```python
# URL: https://secured.rutherfordcountytn.gov/propertydata/
# Different platform - requires separate scraper
```

### Robertson & Cheatham Counties
```python
# URL: https://tnmap.tn.gov/assessment/
# State portal - requires separate scraper
```

## 💡 Tips for Your Lead Generation Business

### 1. Run Daily for Fresh Leads
```bash
# Add to cron job (runs daily at 6am)
0 6 * * * /usr/bin/python3 /path/to/wilson_sumner_scraper.py
```

### 2. Combine with Your Existing Systems
```python
# Export to your database
import sqlite3

conn = sqlite3.connect('leads.db')
df.to_sql('wilson_sales', conn, if_exists='append', index=False)
```

### 3. Filter for Your Target Market
```python
# Example: Find properties sold in last 7 days over $300k
recent_df = df[
    (df['sale_date_parsed'] > datetime.now() - timedelta(days=7)) &
    (df['sale_price_clean'] > 300000)
]
```

### 4. Cross-Reference with Your Permit Data
```python
# Match with your building permit scraper
permits_df = pd.read_csv('nashville_permits.csv')
merged = df.merge(permits_df, left_on='address', right_on='permit_address')
```

## 🔐 Legal & Ethical Use

- ✅ Public records are legally accessible
- ✅ Don't overwhelm the server (use delays)
- ✅ Respect robots.txt
- ✅ Use data ethically for legitimate business purposes
- ⚠️ Check local regulations for data usage

## 📞 Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Verify the website hasn't changed structure
3. Ensure Chrome and ChromeDriver are up to date

## 🎓 Next Steps

Once you have Wilson/Sumner working, you can:
1. Build scrapers for the other counties (Williamson, Rutherford, etc.)
2. Automate daily runs
3. Integrate with your CRM
4. Build a dashboard to visualize the data

## 📄 License

Use for your business purposes. Public data scraping for legitimate business use.

---

**Need scrapers for the other counties?** Let me know and I'll help you build them!
