# Nashville Metro Property Leads - Back End

Automated scraping pipeline that collects recent property sales data from 7 Nashville-area county assessor portals and feeds it to a front-end dashboard.

## Architecture

```
Property-Managers---Back-End-Recents/
├── server.py                  # HTTP server (port 8082) - serves dashboard + pipeline API
├── run_daily.py               # CLI launcher - runs the full pipeline from terminal
├── production/
│   ├── scrapers/              # One scraper per data source
│   │   ├── davidson_scraper.py        # padctn.org Excel download (requests only)
│   │   ├── williamson_scraper.py      # williamson-tn.org (Selenium)
│   │   ├── tn_state_portal_scraper.py # assessment.cot.tn.gov (Selenium + parallel requests)
│   │   ├── wilson_sumner_scraper.py   # Legacy - replaced by tn_state_portal_scraper
│   │   └── rutherford_scraper.py      # rutherfordcountytn.gov (Selenium)
│   ├── runners/
│   │   └── all_counties_daily.py      # Master orchestrator - runs all enabled scrapers
│   └── utilities/
│       ├── normalize_columns.py       # Maps any scraper output to 6-column frontend schema
│       └── common_names.py            # Top 100 US surnames for name-based search counties
├── archive/                   # Non-production code organized by category
│   ├── cron-stubs/            # Old cron job wrappers
│   ├── out-of-scope/          # Non-Nashville county scrapers
│   ├── templates/             # Incomplete/prototype scrapers
│   ├── debug/                 # Debug and inspection scripts
│   ├── redfin/                # Redfin data download scripts
│   └── tests/                 # Test files
└── output/                    # Generated CSV archives
```

## Data Flow

```
County Assessor Websites
        |
        v
   Scrapers (Selenium / requests)
        |
        v
   Raw DataFrames (varying column names per county)
        |
        v
   normalize_columns.py  -->  Unified 6-column schema
        |
        v
   all_counties_daily.py  -->  Price filter ($150K-$1.5M default)
        |
        v
   nashville_cash_leads_clean.csv  -->  Front-end dashboard
```

## County Status

| County | Method | Source | Status | Speed |
|--------|--------|--------|--------|-------|
| **Davidson** | Excel download | padctn.org | Working | ~60 sec, ~2,500 records |
| **Williamson** | Selenium date search | williamson-tn.org | Working | ~5 min, ~500 records |
| **Wilson** | Selenium + parallel requests | assessment.cot.tn.gov | Ready (needs testing) | ~3 min est. |
| **Sumner** | Selenium + parallel requests | assessment.cot.tn.gov | Ready (needs testing) | ~3 min est. |
| **Robertson** | Selenium + parallel requests | assessment.cot.tn.gov | Ready (needs testing) | ~2 min est. |
| **Cheatham** | Selenium + parallel requests | assessment.cot.tn.gov | Ready (needs testing) | ~1 min est. |
| **Rutherford** | Selenium name search | rutherfordcountytn.gov | Slow | ~15 min, name-based only |

**Default enabled counties:** Davidson, Williamson

Wilson, Sumner, Robertson, and Cheatham all use a new unified scraper (`tn_state_portal_scraper.py`) that searches the TN State Property Assessment portal by date range. These are built and wired up but haven't been fully end-to-end tested yet. Enable them in the admin panel or via the `ENABLED_COUNTIES` environment variable.

## Output Schema

The front-end expects exactly 6 columns in the CSV:

| Column | Example | Notes |
|--------|---------|-------|
| Owner Name | `SMITH JOHN` | From scraper if available, `N/A` if not |
| County | `Davidson` | Set by the runner for each county |
| Address | `123 MAIN ST, NASHVILLE, TN` | Combined address + city + state |
| Price | `$350,000` | Formatted with $ and commas |
| Sold Date | `03/15/2026` | Formatted as MM/DD/YYYY |
| Agent Phone | `N/A` | Not available from county records |

## Setup

### Requirements

```bash
pip install pandas requests beautifulsoup4 openpyxl selenium webdriver-manager
```

- Python 3.10+
- Google Chrome (for Selenium-based scrapers)
- ChromeDriver is auto-managed by `webdriver-manager`

### Running

**Option 1: Web server with admin panel**
```bash
python server.py
# Dashboard:  http://localhost:8082/
# Admin:      http://localhost:8082/admin.html
```

The admin panel has:
- County toggle switches (enable/disable each county)
- Lookback period sliders (how many days back to search)
- Price range sliders
- Run Pipeline button with live log output
- Status indicator (idle/running/success/error)

**Option 2: Command line**
```bash
python run_daily.py
```

**Option 3: Specific counties only**
```bash
# Linux/Mac
ENABLED_COUNTIES=Davidson,Williamson python run_daily.py

# Windows PowerShell
$env:ENABLED_COUNTIES="Davidson,Williamson"; python run_daily.py
```

## Configuration

All settings can be overridden via environment variables (set automatically by the admin panel):

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLED_COUNTIES` | `Davidson,Williamson` | Comma-separated list, or `all` for all 7 |
| `DAVIDSON_DAYS` | `60` | How far back to pull Davidson data |
| `WILSON_SUMNER_DAYS` | `7` | Lookback for Wilson, Sumner, Robertson, Cheatham |
| `WILLIAMSON_DAYS` | `30` | Lookback for Williamson |
| `MIN_PRICE` | `150000` | Minimum sale price filter |
| `MAX_PRICE` | `1500000` | Maximum sale price filter |

## Server API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves front-end dashboard (index.html) |
| `/admin.html` | GET | Admin control panel |
| `/api/status` | GET | Returns JSON: `{running, last_run, last_result, log}` |
| `/api/run` | POST | Starts pipeline. Body: JSON config object |

### POST /api/run example body

```json
{
  "enabled_counties": "Davidson,Williamson",
  "davidson_days": 60,
  "williamson_days": 30,
  "min_price": 150000,
  "max_price": 1500000
}
```

## Scraper Details

### Davidson County - padctn.org
- Downloads Excel (.xlsx) files from the Recent Sales page using `requests` (no Selenium)
- Files are organized by district/zone and year (e.g., `1_rural_2025.xlsx`)
- Downloads all files for the most recent year available, combines with `pd.concat`
- Date filter uses the most recent sale date in the data as reference point (not `datetime.now()`) because padctn.org publishes data with a lag
- No owner name data in the Excel files - Owner Name will show as `N/A`
- Fastest scraper: ~60 seconds for ~2,500 records

### Williamson County - williamson-tn.org
- Selenium-based date range search on the county's own property assessor portal
- Returns owner name, address, sale price, sale date
- Handles pagination automatically (clicks through all result pages)
- Date format must be MM/DD/YYYY (the portal rejects YYYY-MM-DD)

### Wilson / Sumner / Robertson / Cheatham - assessment.cot.tn.gov
- All four use a unified scraper (`tn_state_portal_scraper.py`) targeting the TN State Property Assessment Data portal (TPAD)
- County codes: Wilson=095, Sumner=083, Robertson=074, Cheatham=011
- Selenium opens the portal, selects the county, clicks "Advanced Search", fills in date range, and submits the form
- Paginates through the DataTable results to collect owner name, address, and sale date
- Sale prices are NOT in the list view - they're on individual detail pages
- Detail pages are fetched in parallel using `requests` + `ThreadPoolExecutor` (6 threads) at ~1 sec per page, much faster than Selenium's ~4 sec per page
- Typical result: 300-400 records per county for a 30-day window

### Rutherford County - rutherfordcountytn.gov
- Name-based search only (the portal does not support date range queries)
- Uses the top 100 US surnames from `common_names.py` for broader coverage (~25-30% of population)
- Each name search takes ~8 seconds, so 100 names = ~15 minutes
- Consider reducing to 25 names for faster runs

## Front-End Integration

The pipeline writes its output CSV directly to the sibling front-end directory:
```
../Property-Managers--Front-End/nashville_cash_leads_clean.csv
```

The front-end dashboard reads this CSV on page load and organizes leads into per-county tabs (Davidson, Williamson, etc.). Each tab shows:
- Sortable table (owner, address, price, sold date)
- Stats bar (total leads, avg price, price range, date range)
- Search filter and price range filter
- CSV export (per-county or all)

An archive copy is also saved to `output/all_counties_YYYYMMDD.csv`.

## Troubleshooting

**Pipeline shows "running" but no log output:**
Python buffers stdout in subprocess pipes. The server uses `python -u` (unbuffered) to fix this. If you still see no output, the scraper may be downloading large Excel files (Davidson) or waiting for Selenium page loads.

**Pipeline takes too long:**
Disable slow counties. Davidson + Williamson together take ~6 minutes. Adding Wilson/Sumner/Robertson/Cheatham adds ~10 more minutes. Rutherford alone takes ~15 minutes.

**ChromeDriver version mismatch:**
```bash
pip install --upgrade webdriver-manager
```
Then delete any cached chromedriver in `~/.wdm/` and re-run.

**Port 8082 already in use:**
```bash
# Find the process
netstat -ano | findstr :8082
# Kill it (Windows)
taskkill /F /PID <pid_number>
```

**No data for a county:**
Check the county's portal is accessible in a browser. The TN State Portal (`assessment.cot.tn.gov`) occasionally has maintenance windows between 12:30-2:00 AM CST.

**CSV has empty County column:**
This happens if the normalizer receives an empty `county_name` parameter. Check that `scrape_county()` in `all_counties_daily.py` passes the correct county name string.

## Legal

All data is sourced from public county property assessment records. Built-in delays between requests respect server rate limits. Use the data ethically and in compliance with local regulations.

---

**Last Updated:** 2026-03-26
