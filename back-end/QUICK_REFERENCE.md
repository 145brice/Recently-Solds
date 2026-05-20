# QUICK REFERENCE GUIDE
# Wilson & Sumner County Property Scrapers

## URLs for All Counties Around Nashville

### Wilson County (East - Mt. Juliet area)
Main Site: https://wilsontn.geopowered.com/propertysearch/
Platform: GeoPowered.com
Register of Deeds: https://www.wilsondeeds.com/

### Sumner County (Northeast - Hendersonville, Gallatin)  
Main Site: https://sumnertn.geopowered.com/propertysearch/
Platform: GeoPowered.com (same as Wilson)
Register of Deeds: https://www.deeds.sumnercounty.org/

### Davidson County (Nashville)
Property Search: https://portal.padctn.org/OFS/WP/Home
Recent Sales (XLSX): https://www.padctn.org/resources/recent-sales/
Register of Deeds: www.davidsonportal.com (PAID)

### Williamson County (South - Franklin, Brentwood)
Property Search: https://inigo.williamson-tn.org/property_search/
Platform: Custom (inigo)
Higher-end market: ~$775k median

### Rutherford County (Southeast - Murfreesboro)
Property Search: https://secured.rutherfordcountytn.gov/propertydata/
Main Site: https://rcpatn.com/
Fast-growing with Nissan plant

### Robertson County (North - Springfield)
State Portal: https://tnmap.tn.gov/assessment/
Select: Robertson County from dropdown

### Cheatham County (West - Ashland City)
State Portal: https://tnmap.tn.gov/assessment/
Select: Cheatham County from dropdown

## Installation Command

```bash
pip install -r requirements.txt
```

## Run Commands

```bash
# Wilson County
python wilson_sumner_scraper.py

# For Sumner, edit the file and change:
county = "sumner"
```

## Common Scraping Patterns

### Pattern 1: Same Platform (Easiest)
Wilson + Sumner = Same scraper, just change URL
✅ Use wilson_sumner_scraper.py

### Pattern 2: State Portal
Robertson + Cheatham = Tennessee state system
🔨 Need new scraper for TN state portal

### Pattern 3: Unique Platforms
Williamson = inigo platform
Rutherford = custom platform
Davidson = Catalis WebPro platform
🔨 Each needs separate scraper

## Daily Automation Setup

### Linux/Mac (Crontab)
```bash
# Edit crontab
crontab -e

# Add this line (runs at 6am daily)
0 6 * * * cd /path/to/scraper && python3 wilson_sumner_scraper.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 6:00 AM
4. Action: Start a program
5. Program: python.exe
6. Arguments: C:\path\to\wilson_sumner_scraper.py

## Data Processing Tips

### Load and Filter Data
```python
import pandas as pd

# Load scraped data
df = pd.read_csv('wilson_county_sales_20250102_120000.csv')

# Filter last 7 days
recent = df[df['sale_date_parsed'] > '2024-12-25']

# Filter by price
high_value = df[df['sale_price_clean'] > 400000]

# Filter by location (if address contains city)
mt_juliet = df[df['address'].str.contains('Mt Juliet|Mount Juliet', case=False)]

# Get unique owners
new_buyers = df['owner_name'].unique()
```

### Export to Your Format
```python
# To JSON
df.to_json('sales.json', orient='records')

# To Database
import sqlite3
conn = sqlite3.connect('property_leads.db')
df.to_sql('wilson_sales', conn, if_exists='append')

# To Google Sheets (requires gspread)
import gspread
gc = gspread.service_account()
sh = gc.open("Property Leads")
worksheet = sh.sheet1
worksheet.update([df.columns.values.tolist()] + df.values.tolist())
```

## Combining Multiple Counties

```python
# Scrape all at once
results = []

for county in ['wilson', 'sumner']:
    with CountyPropertyScraper(county=county) as scraper:
        df = scraper.scrape_recent_sales(days_back=30)
        df['county'] = county.title()
        results.append(df)

# Combine into single DataFrame
all_sales = pd.concat(results, ignore_index=True)
all_sales.to_csv('multi_county_sales.csv', index=False)
```

## Freshness of Data

| County | Data Source | Update Frequency |
|--------|-------------|------------------|
| Wilson | Property Assessor | Weekly |
| Sumner | Property Assessor | Weekly |
| Davidson | Recent Sales XLSX | Quarterly |
| Williamson | Property Assessor | Real-time |
| Rutherford | Property Assessor | Weekly |
| Robertson | State Portal | Monthly |
| Cheatham | State Portal | Monthly |

**For MOST RECENT data (within days of sale):**
- Register of Deeds portals (usually paid)
- Wilson: https://www.wilsondeeds.com/
- Sumner: https://www.deeds.sumnercounty.org/
- Davidson: www.davidsonportal.com (paid)

## Priority Order for Your Business

Based on your Mount Juliet location:

1. **Wilson County** ⭐ (Your backyard)
2. **Sumner County** ⭐ (Same scraper)
3. **Davidson County** (Nashville - biggest market)
4. **Williamson County** (High-end market)
5. **Rutherford County** (Fast-growing)
6. **Robertson County** (Smaller market)
7. **Cheatham County** (Smallest market)

## Next Steps

1. ✅ Get Wilson/Sumner scraper working
2. Build Davidson County scraper (different platform)
3. Build Williamson County scraper
4. Build Rutherford County scraper
5. Automate daily runs
6. Integrate with your CRM/database
7. Build dashboard for visualization

## Contact Info for County Offices

### Wilson County Assessor
Phone: 615-444-8661
Address: Wilson County, TN

### Sumner County Assessor  
Phone: (See county website)
Gallatin, TN

### For Data Issues
Contact the respective county's Register of Deeds office
