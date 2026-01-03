# Wilson & Sumner Daily Automation Setup
## Complete Guide for Running Scrapers Automatically

---

## 🎯 What You're Setting Up

A fully automated system that:
- ✅ Runs every morning at 6am
- ✅ Scrapes Wilson & Sumner counties for yesterday's sales
- ✅ Filters for your target properties ($200k-$1M)
- ✅ Exports to CSV, Excel, and database
- ✅ Creates SMS outreach lists
- ✅ Sends you email notifications (optional)

---

## 📋 Files You Need

Make sure you have these files in the same directory:

```
scrapers/
├── wilson_sumner_scraper.py      # Main scraper library
├── daily_wilson_sumner.py        # Daily automation script
├── requirements.txt              # Dependencies
└── wilson_leads.db              # Database (auto-created)
```

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Test Everything Works

```bash
# Navigate to your scrapers directory
cd /path/to/scrapers

# Install dependencies
pip install -r requirements.txt

# Run a quick test (optional)
python test_wilson.py

# Run Wilson County once manually
python wilson_scraper_full.py
```

**Expected Output:**
```
WILSON COUNTY PROPERTY SCRAPER - PRODUCTION
============================================================
✓ Found 15 total properties
✓ 12 properties over $250,000

SUMMARY
Total Properties: 12
...
✓ Saved CSV: wilson_sales_20250102_120000.csv
✓ Saved Excel: wilson_sales_20250102_120000.xlsx
✓ COMPLETE!
```

### Step 2: Run Both Counties Together

```bash
python daily_wilson_sumner.py
```

**Expected Output:**
```
DAILY AUTOMATION - WILSON & SUMNER COUNTIES
============================================================
1/2 - Scraping Wilson County...
✓ Wilson: 15 properties

2/2 - Scraping Sumner County...
✓ Sumner: 8 properties

Total properties (both counties): 23
Properties in target price range: 20

✓ CSV: daily_sales_20250102.csv
✓ Excel: daily_sales_20250102.xlsx
✓ SMS Leads: sms_leads_20250102.csv
✓ Database: daily_leads.db
✓ DAILY SCRAPE COMPLETE
```

### Step 3: Set Up Daily Automation

Choose your operating system below...

---

## 🐧 Linux / Mac Setup (Crontab)

### Option A: Simple Daily Run (Recommended)

```bash
# Open crontab editor
crontab -e

# Add this line (runs at 6am every day)
0 6 * * * cd /path/to/scrapers && /usr/bin/python3 daily_wilson_sumner.py >> scraper.log 2>&1
```

**Replace `/path/to/scrapers` with your actual path!**

To find your path:
```bash
cd /path/to/scrapers
pwd  # This shows your full path
```

### Option B: Run Multiple Times Per Day

```bash
# Edit crontab
crontab -e

# 6am daily
0 6 * * * cd /path/to/scrapers && /usr/bin/python3 daily_wilson_sumner.py >> scraper.log 2>&1

# Also run at 2pm
0 14 * * * cd /path/to/scrapers && /usr/bin/python3 daily_wilson_sumner.py >> scraper.log 2>&1

# Also run at 10pm
0 22 * * * cd /path/to/scrapers && /usr/bin/python3 daily_wilson_sumner.py >> scraper.log 2>&1
```

### Verify Cron is Running

```bash
# List your cron jobs
crontab -l

# Check the log file
tail -f /path/to/scrapers/scraper.log
```

### Cron Time Syntax Cheat Sheet

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sun=0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)

Examples:
0 6 * * *        # 6am daily
0 */6 * * *      # Every 6 hours
0 9 * * 1        # 9am every Monday
0 6 * * 1-5      # 6am weekdays only
30 18 * * *      # 6:30pm daily
```

---

## 🪟 Windows Setup (Task Scheduler)

### Step-by-Step Instructions

1. **Open Task Scheduler**
   - Press `Win + R`
   - Type: `taskschd.msc`
   - Press Enter

2. **Create New Task**
   - Click "Create Basic Task"
   - Name: `Wilson Sumner Daily Scraper`
   - Description: `Scrapes property sales daily at 6am`
   - Click Next

3. **Set Trigger**
   - Select: "Daily"
   - Start date: Tomorrow
   - Start time: `6:00 AM`
   - Recur every: `1 days`
   - Click Next

4. **Set Action**
   - Select: "Start a program"
   - Program/script: `C:\Python39\python.exe` (adjust to your Python path)
   - Add arguments: `daily_wilson_sumner.py`
   - Start in: `C:\Users\YourName\scrapers` (your folder path)
   - Click Next

5. **Finish**
   - Check "Open Properties dialog"
   - Click Finish

6. **Advanced Settings**
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
   - Under "Settings" tab:
     - Check "Run task as soon as possible after a scheduled start is missed"
   - Click OK

### Find Your Python Path

Open Command Prompt:
```cmd
where python
```

Example output: `C:\Users\YourName\AppData\Local\Programs\Python\Python39\python.exe`

### Test Task Manually

1. In Task Scheduler, find your task
2. Right-click → Run
3. Check output files appear in your folder

### View Task Logs

1. Open Event Viewer: `eventvwr.msc`
2. Navigate: Windows Logs → Application
3. Look for "Task Scheduler" entries

---

## 🔍 Monitoring & Logs

### Check If It's Working

```bash
# View the log file
tail -50 scraper.log

# Or on Windows
type scraper.log

# Watch it live (Linux/Mac)
tail -f scraper.log
```

### Expected Log Output

```
==================================================
DAILY AUTOMATION - WILSON & SUMNER COUNTIES
==================================================
Run Date: 2025-01-03 06:00:01
...
✓ DAILY SCRAPE COMPLETE
Duration: 45.3 seconds
Properties Found: 18
==================================================
```

### Check Generated Files

```bash
# List today's files
ls -lh daily_sales_*.csv
ls -lh sms_leads_*.csv

# Or on Windows
dir daily_sales_*.csv
```

### Check Database

```bash
# Install sqlite3 (if not installed)
# Linux: sudo apt-get install sqlite3
# Mac: brew install sqlite3

# View database contents
sqlite3 daily_leads.db "SELECT COUNT(*) as total FROM daily_sales;"
sqlite3 daily_leads.db "SELECT * FROM daily_sales ORDER BY scrape_date DESC LIMIT 10;"
```

---

## ⚙️ Customization

### Change Time Range

Edit `daily_wilson_sumner.py`:

```python
# Look back 7 days instead of 1
DAYS_BACK = 7

# Or look back 3 days
DAYS_BACK = 3
```

### Change Price Filter

```python
# Only properties $300k-$800k
MIN_PRICE = 300000
MAX_PRICE = 800000
```

### Change Database Location

```python
# Save to different database
DATABASE_FILE = "/Users/yourname/Dropbox/property_leads.db"
```

### Add Email Notifications

1. Edit `daily_wilson_sumner.py`:

```python
# Enable email
SEND_EMAIL = True
EMAIL_TO = "your-email@gmail.com"
```

2. Configure SMTP (uncomment and fill in):

```python
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login('your_email@gmail.com', 'your_app_password')
    server.send_message(msg)
```

3. For Gmail, create an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Create password for "Mail"

---

## 🐛 Troubleshooting

### "No properties found"

**This is NORMAL** if there were no sales yesterday.

Try:
```python
# Look back 7 days to verify it works
DAYS_BACK = 7
```

### "ModuleNotFoundError: No module named 'selenium'"

```bash
pip install -r requirements.txt

# Or manually
pip install selenium pandas webdriver-manager openpyxl
```

### "ChromeDriver not found" (when running)

```bash
pip install webdriver-manager --upgrade
```

### Cron job not running

```bash
# Check cron is running
sudo systemctl status cron

# View system logs
grep CRON /var/log/syslog

# Make sure script has execute permissions
chmod +x daily_wilson_sumner.py
```

### Script runs but no files created

Check the log file:
```bash
cat scraper.log
```

Make sure the path in cron is correct:
```bash
# Wrong - relative path won't work
python daily_wilson_sumner.py

# Right - absolute paths
cd /full/path/to/scrapers && /usr/bin/python3 daily_wilson_sumner.py
```

---

## 📊 Using Your Data

### Import to Excel

1. Open Excel
2. Data → Get Data → From File → From CSV
3. Select `daily_sales_20250102.csv`
4. Click Load

### Import to Google Sheets

1. Open Google Sheets
2. File → Import
3. Upload `daily_sales_20250102.csv`
4. Import

### Query Database

```python
import pandas as pd
import sqlite3

# Connect to database
conn = sqlite3.connect('daily_leads.db')

# Get all high-value properties this week
query = """
SELECT county, owner_name, address, sale_price, sale_date
FROM daily_sales
WHERE scrape_date >= date('now', '-7 days')
  AND sale_price_clean > 400000
ORDER BY sale_price_clean DESC
"""

df = pd.read_sql(query, conn)
print(df)

# Export to Excel
df.to_excel('high_value_this_week.xlsx', index=False)
```

### SMS Export Format

The `sms_leads_YYYYMMDD.csv` file is ready for:
- Google Voice bulk upload
- Twilio API
- Your SMS platform
- Manual copy/paste

Format:
```
county,owner_name,address,sale_price,sale_date
Wilson,John Smith,123 Main St,$450000,2025-01-02
Sumner,Jane Doe,456 Oak Ave,$380000,2025-01-02
```

---

## 📈 Advanced: Weekly Reports

Create `weekly_report.py`:

```python
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('daily_leads.db')

# Get this week's data
week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

query = f"""
SELECT county, COUNT(*) as count, AVG(sale_price_clean) as avg_price
FROM daily_sales
WHERE scrape_date >= '{week_ago}'
GROUP BY county
"""

summary = pd.read_sql(query, conn)
print("\nWeekly Summary:")
print(summary)

# Save weekly report
summary.to_csv(f'weekly_report_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
```

Run weekly:
```bash
# Add to cron - runs every Monday at 9am
0 9 * * 1 cd /path/to/scrapers && python3 weekly_report.py
```

---

## ✅ Success Checklist

- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Test scraper works (`python wilson_scraper_full.py`)
- [ ] Daily script works (`python daily_wilson_sumner.py`)
- [ ] Cron job or Task Scheduler configured
- [ ] Log file location confirmed
- [ ] Output files being created
- [ ] Database being populated
- [ ] Can access and use the data

---

## 🎉 You're Done!

Your automated system will now:
1. Run every morning at 6am
2. Scrape Wilson & Sumner County sales
3. Export fresh leads to CSV/Excel
4. Save to database for historical tracking
5. Create SMS outreach lists

**Check back tomorrow morning to see your first automated results!**

---

## 📞 Need Help?

Common questions:

**Q: How do I know it's working?**
A: Check `scraper.log` file tomorrow morning after 6am

**Q: No properties found?**
A: Normal! Not every day has sales. Set `DAYS_BACK = 7` to test.

**Q: Want more counties?**
A: You have scrapers for all 7 counties. Add them to the daily script!

**Q: How to stop it?**
A: Linux/Mac: `crontab -e` and delete the line
   Windows: Delete task in Task Scheduler
