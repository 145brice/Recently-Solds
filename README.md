# Nashville Area Multi-County Property Scraper

Complete toolkit for scraping recently sold homes data from 6 counties surrounding Nashville, Tennessee.

## 🎯 What This Does

- ✅ Scrapes recent property sales from 6 counties around Nashville
- ✅ Extracts new owner names and addresses
- ✅ Gets sale prices and dates
- ✅ Exports to CSV/Excel for easy analysis
- ✅ Automated daily runs for fresh leads
- ✅ Combined master database of all counties

## 📍 Counties Covered

| County | Status | Records (30 days) | Avg Price |
|--------|--------|-------------------|-----------|
| **Williamson** (Brentwood, Franklin) | ✅ **WORKING** | ~342 | $1,176,076 |
| **Wilson** (Mt. Juliet) | ⚠️ Disabled | - | - |
| **Sumner** (Hendersonville, Gallatin) | ⚠️ Disabled | - | - |
| **Rutherford** (Murfreesboro) | ⚠️ Disabled | - | - |
| **Robertson** (Springfield) | ⚠️ Disabled | - | - |
| **Cheatham** (Ashland City) | ⚠️ Disabled | - | - |

### Status Notes
- **Williamson County**: ✅ Fully functional (Fixed: 2026-01-20)
  - Fixed date format issue (MM/DD/YYYY required)
  - Added pagination support (now captures all 342 properties vs. only 10)
- **Wilson & Sumner**: Platform changed, needs redevelopment
- **Rutherford**: Search interface not interactable
- **Robertson & Cheatham**: URLs not resolving

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

### 2. Run All Counties (Automated)

```bash
# Run all working county scrapers
python all_counties_daily.py
```

### 3. Run Individual County

```bash
# Williamson County only
python williamson_scraper.py

# Wilson/Sumner (currently disabled)
python wilson_sumner_scraper.py

# Rutherford (currently disabled)
python rutherford_scraper.py
```

### 4. Output Files

Files are saved to the `output/` folder:
- `output/williamson_YYYYMMDD_HHMMSS.csv`
- `output/williamson/williamson_sales_YYYYMMDD.csv`
- Combined files: `all_counties_YYYYMMDD.csv` and `.xlsx`

## 📊 Data Fields Extracted

| Field | Description |
|-------|-------------|
| `owner_name` | Current owner's name |
| `address` | Property address |
| `city` | City |
| `parcel_id` | Unique property identifier |
| `lot_number` | Lot number |
| `sale_date` | Date of sale |
| `sale_price` | Sale price |
| `sale_price_clean` | Numeric sale price for filtering |
| `county` | County name |
| `scrape_date` | Date data was scraped |
| `scrape_timestamp` | Full timestamp of scrape |

## 🔧 Recent Fixes & Updates

### Williamson County (2026-01-20)

**Fixed Two Critical Issues:**

1. **Date Format Bug**: The website requires dates in `MM/DD/YYYY` format, but scraper was sending `YYYY-MM-DD`
   - **Impact**: Search was returning 0 results
   - **Fix**: Added automatic date conversion in both `search_by_date_only()` and `search_by_subdivision_and_date()`

2. **Pagination Missing**: Scraper only captured first page (10 properties out of 342)
   - **Impact**: Missing 97% of available data
   - **Fix**: Implemented pagination loop to click through all pages
   - **Result**: Now captures all 342 properties across 35 pages

**Results After Fix:**
- Properties found: **342** (was 1)
- Properties with valid prices: **220**
- Price range: $232,200 - $14,031,707
- Average price: $1,176,076
- Median price: $851,585

## 🔧 Configuration Options

### Change Search Date Range

Edit `all_counties_daily.py`:

```python
# Last 60 days instead of 30 for Williamson
WILLIAMSON_DAYS = 60
```

### Run Without Browser Window

```python
# In all_counties_daily.py
HEADLESS = True  # Change to False to see browser
```

### Price Filtering

```python
# In all_counties_daily.py
MIN_PRICE = 150000
MAX_PRICE = 1500000
```

## 📝 Example Usage

### Williamson County - Custom Date Range

```python
from williamson_scraper import WilliamsonCountyScraper
from datetime import datetime, timedelta

with WilliamsonCountyScraper(headless=True) as scraper:
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # Search by date only
    properties = scraper.search_by_date_only(
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

    print(f"Found {len(properties)} properties")
```

### Filter Results After Scraping

```python
import pandas as pd

# Load the CSV
df = pd.read_csv('output/williamson_20260120_132943.csv')

# Filter by price range
target_range = df[
    (df['sale_price_clean'] >= 400000) &
    (df['sale_price_clean'] <= 800000)
]

# Filter by city
brentwood_only = df[df['city'] == 'Brentwood']

# Filter by date
recent = df[df['sale_date'] >= '12/20/2025']
```

## 🛠 Troubleshooting

### Chrome Driver Issues

```bash
pip install webdriver-manager --upgrade
```

### Page Load Timeout

If you see timeout errors, increase the wait time:

```python
# In the scraper file
self.wait = WebDriverWait(self.driver, 30)  # Increase from 20 to 30
```

### No Results Found

Check that:
1. Date range is valid (not in the future)
2. Website hasn't changed structure
3. Network connection is stable

### Pagination Not Working

The Williamson County scraper looks for the "Next" button with ID `results_table_next`. If this changes, update the pagination logic in `extract_search_results()`.

## 💡 Daily Automation

### Setup Cron Job (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 6am
0 6 * * * cd /path/to/Property-Managers---Back-End-Recents && /usr/bin/python3 all_counties_daily.py >> logs/daily.log 2>&1
```

### Setup Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `all_counties_daily.py`
7. Start in: `[path to project folder]`

## 📊 Database Integration

### Save to SQLite

The automation script automatically saves to SQLite:

```python
# In all_counties_daily.py
SAVE_TO_DATABASE = True
DATABASE_FILE = "all_counties_leads.db"
```

### Query the Database

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('all_counties_leads.db')

# Get all Williamson County sales
df = pd.read_sql_query(
    "SELECT * FROM all_county_sales WHERE county = 'Williamson'",
    conn
)

# Get high-value properties
df = pd.read_sql_query(
    "SELECT * FROM all_county_sales WHERE sale_price_clean > 1000000",
    conn
)
```

## 🔐 Legal & Ethical Use

- ✅ Public records are legally accessible
- ✅ Built-in delays to avoid overwhelming servers
- ✅ Respects website rate limits
- ✅ Use data ethically for legitimate business purposes
- ⚠️ Check local regulations for data usage
- ⚠️ Do not use for harassment or spam

## 📞 Support & Maintenance

### Common Issues

1. **"No data available in table"**: Date format or search parameters incorrect
2. **Timeout errors**: Website slow, increase timeout or run with `headless=True`
3. **Missing pagination**: Website structure changed, update selectors
4. **Element not found**: Website redesign, scraper needs updating

### Debugging

Run with visible browser to see what's happening:

```python
scraper = WilliamsonCountyScraper(headless=False)
```

## 🎓 Next Steps

1. **Re-enable other counties**: Update scrapers for Wilson, Sumner, Rutherford, Robertson, and Cheatham
2. **Add more data fields**: Extract property details (bedrooms, bathrooms, sqft)
3. **Build dashboard**: Visualize trends and statistics
4. **Integrate with CRM**: Auto-import leads to your system
5. **Add email alerts**: Get notified of high-value properties

## 📂 Project Structure

```
Property-Managers---Back-End-Recents/
├── all_counties_daily.py          # Master automation script
├── williamson_scraper.py           # Williamson County (WORKING)
├── wilson_sumner_scraper.py        # Wilson/Sumner (needs update)
├── rutherford_scraper.py           # Rutherford (needs update)
├── tn_state_portal_scraper.py      # Robertson/Cheatham (needs update)
├── output/                         # CSV/Excel output files
│   ├── williamson/                 # Williamson County folder
│   └── [other county folders]
├── all_counties_leads.db           # SQLite database
└── README.md                       # This file
```

## 📄 License

Public data scraping for legitimate business use. Use responsibly.

---

**Last Updated**: 2026-01-20
**Version**: 2.0 - Williamson County Fix (Date Format + Pagination)
