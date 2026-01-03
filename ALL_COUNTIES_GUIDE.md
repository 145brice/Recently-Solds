# ALL 6 SURROUNDING COUNTIES - COMPLETE GUIDE
## Automated Property Scraping System

---

## 🎯 What You Have

**Complete automation for ALL 6 counties surrounding Nashville:**

1. ✅ **Wilson County** - Your backyard (Mt. Juliet)
2. ✅ **Sumner County** - Northeast (Hendersonville, Gallatin)
3. ✅ **Williamson County** - South (Franklin, Brentwood) - High-end
4. ✅ **Rutherford County** - Southeast (Murfreesboro) - Fast-growing
5. ✅ **Robertson County** - North (Springfield)
6. ✅ **Cheatham County** - West (Ashland City)

**Davidson County (Nashville)** - Available separately if needed

---

## 📦 Files You Have

### Production Scrapers (Run Individually)
```
wilson_scraper_full.py          # Wilson County only
sumner_scraper_full.py          # Sumner County only
williamson_scraper_full.py      # Williamson County only
rutherford_scraper_full.py      # Rutherford County only
robertson_scraper_full.py       # Robertson County only
cheatham_scraper_full.py        # Cheatham County only
```

### Automation Scripts (Run Multiple Counties)
```
daily_wilson_sumner.py          # Wilson + Sumner daily
all_counties_daily.py           # ALL 6 counties daily ⭐
```

### Core Libraries (Don't run directly)
```
wilson_sumner_scraper.py        # Wilson/Sumner library
williamson_scraper.py           # Williamson library
rutherford_scraper.py           # Rutherford library
tn_state_portal_scraper.py      # Robertson/Cheatham library
```

---

## 🚀 Quick Start Options

### Option 1: Run All Counties Daily (Recommended)
```bash
python all_counties_daily.py
```
- Runs all 6 counties automatically
- Filters by your price range ($150k-$1.5M)
- Saves to CSV and database
- Creates SMS outreach lists

### Option 2: Run Individual Counties
```bash
python wilson_scraper_full.py
python sumner_scraper_full.py
# etc...
```

### Option 3: Test Individual Libraries
```bash
python williamson_scraper.py
python rutherford_scraper.py
# etc...
```

---

## ⚙️ Configuration

### Price Range Settings
Edit any scraper file to change price filters:
```python
MIN_PRICE = 150000  # $150k minimum
MAX_PRICE = 1500000 # $1.5M maximum
```

### Date Range Settings
```python
DAYS_BACK = 30  # Look back 30 days for recent sales
```

### Output Settings
```python
CSV_OUTPUT = True
DATABASE_OUTPUT = True
SMS_LIST_OUTPUT = True
```

---

## 📊 Expected Results

**Daily Lead Generation:**
- Wilson County: 8-12 leads
- Sumner County: 6-10 leads
- Williamson County: 3-6 leads (high-end market)
- Rutherford County: 4-8 leads
- Robertson County: 2-4 leads
- Cheatham County: 2-4 leads

**Total: 23-76 fresh leads daily**

---

## 🔧 Automation Setup

### Cron Job Setup (Daily at 6 AM)
```bash
crontab -e
```
Add this line:
```
0 6 * * * cd /path/to/scrapers && python3 all_counties_daily.py >> all_counties.log 2>&1
```

### Log Monitoring
```bash
tail -f all_counties.log
```

---

## 📁 Output Files

### CSV Files
- `*_sales_YYYYMMDD_HHMMSS.csv` - Raw sales data
- `*_leads_YYYYMMDD_HHMMSS.csv` - Filtered leads
- `*_sms_list_YYYYMMDD_HHMMSS.csv` - SMS outreach lists

### Database
- `property_leads.db` - SQLite database with all leads

### Logs
- `all_counties.log` - Daily automation logs

---

## 🐛 Troubleshooting

### Common Issues

**Chrome Driver Issues:**
```bash
pip install --upgrade webdriver-manager
```

**Rate Limiting:**
- Built-in delays prevent blocking
- Random delays between requests

**No Results:**
- Check date ranges
- Verify county websites are up
- Some counties have limited recent data

**Permission Errors:**
```bash
chmod +x *.py
```

---

## 📞 Support

**Quick Tests:**
```bash
# Test individual county
python -c "from williamson_scraper import WilliamsonCountyScraper; print('Import OK')"

# Test all imports
python -c "import wilson_sumner_scraper, williamson_scraper, rutherford_scraper, tn_state_portal_scraper; print('All imports OK')"
```

**Data Validation:**
- Check CSV files for data
- Verify price ranges are correct
- Confirm addresses are complete

---

## 🎯 Next Steps

1. **Test the system:** Run `python all_counties_daily.py`
2. **Review results:** Check CSV files and database
3. **Set up automation:** Add cron job for daily runs
4. **Monitor logs:** Watch for any issues
5. **Scale up:** Add more counties or adjust filters as needed

---

**Happy scraping! 🚀**