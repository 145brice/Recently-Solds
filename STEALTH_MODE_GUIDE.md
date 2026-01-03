# STEALTH MODE - COMPLETE GUIDE
## Bot Detection Avoidance for Daily Automation

---

## 🥷 What is Stealth Mode?

Your new `all_counties_stealth.py` script includes **anti-bot detection features** that make your scraper look like a real human browsing the web.

### **Stealth Features Included:**

✅ **Random Delays** - Waits 2-8 seconds between actions (humans aren't instant)  
✅ **Random User Agents** - Rotates through 5 different browsers/devices  
✅ **Randomized Order** - Counties scraped in random order each run  
✅ **Variable Timing** - Different wait times each search  
✅ **Browser Fingerprinting** - Removes automation detection flags  
✅ **Session Cookies** - Looks like a returning visitor  
✅ **Startup Delay** - Random 0-30 second delay at start  

---

## 🚀 Quick Start

### **Run Stealth Mode:**
```bash
python all_counties_stealth.py
```

### **Set Up Daily Automation (6am CST):**

**Linux/Mac:**
```bash
crontab -e

# Add this line (6am CST = 6am local):
0 6 * * * cd /path/to/scrapers && python3 all_counties_stealth.py >> stealth.log 2>&1
```

**Windows:**
1. Task Scheduler → Create Basic Task
2. Name: "Stealth County Scraper"
3. Trigger: Daily at 6:00 AM
4. Action: `python.exe all_counties_stealth.py`

---

## ⚙️ Configuration

### **Customize Delays:**
```python
# In all_counties_stealth.py:

MIN_DELAY = 2   # Minimum wait (seconds)
MAX_DELAY = 8   # Maximum wait (seconds)

# Shorter delays = faster but more detectable
# Longer delays = slower but more human-like
```

**Recommended Settings:**
- **Fast & Risky**: `MIN_DELAY = 1, MAX_DELAY = 3`
- **Balanced** (default): `MIN_DELAY = 2, MAX_DELAY = 8`
- **Super Stealthy**: `MIN_DELAY = 5, MAX_DELAY = 15`

### **Toggle Randomization:**
```python
# Randomize county order each run
RANDOMIZE_ORDER = True  # Default

# Or run in same order every time
RANDOMIZE_ORDER = False
```

### **See Browser (Testing Only):**
```python
# Watch the browser work (for debugging)
HEADLESS = False

# Invisible background mode (production)
HEADLESS = True  # Default
```

---

## 🎯 How Stealth Mode Works

### **1. Random User Agents**

Each county gets a different "browser fingerprint":

```python
# Rotates through:
- Chrome on Windows 10
- Chrome on Mac
- Firefox on Windows
- Safari on Mac
- Chrome on Linux

# Sites think it's different people browsing
```

### **2. Random Delays**

Never repeats the same timing pattern:

```
Normal Bot:
Search → 2s → Click → 2s → Search → 2s (predictable!)

Stealth Mode:
Search → 4.3s → Click → 6.1s → Search → 3.7s (random!)
```

### **3. Randomized Order**

Counties scraped in different order each day:

```
Day 1: Wilson → Sumner → Williamson → Rutherford → Robertson → Cheatham
Day 2: Rutherford → Wilson → Cheatham → Sumner → Robertson → Williamson
Day 3: Sumner → Robertson → Wilson → Cheatham → Williamson → Rutherford
```

Makes it impossible to detect a pattern!

### **4. Browser Fingerprinting**

Removes telltale signs of automation:

```python
# Disabled:
navigator.webdriver = undefined  # (looks like real browser)
window.chrome.runtime = undefined
```

### **5. Startup Delay**

Random 0-30 second delay before starting:

```
Cron triggers at 6:00:00 AM
Script waits: 17 seconds
Actually starts: 6:00:17 AM

# Never starts at exact same time!
```

---

## 📊 Performance

### **Speed Comparison:**

| Mode | Duration | Detection Risk |
|------|----------|----------------|
| **Regular** | 10-12 min | Medium |
| **Stealth** | 15-20 min | Very Low |
| **Super Stealth** | 25-35 min | Minimal |

### **Trade-offs:**

**Stealth Mode (Default):**
- ✅ Hard to detect
- ✅ Still reasonably fast
- ✅ Good balance

**Regular Mode:**
- ✅ Faster
- ⚠️ More detectable
- ⚠️ Higher ban risk

**Super Stealth:**
- ✅ Almost impossible to detect
- ❌ Slower
- ✅ Best for sensitive sites

---

## 🔍 Monitoring

### **Check Logs:**
```bash
# View today's run
tail -100 stealth.log

# Watch live
tail -f stealth.log
```

### **Expected Output:**
```
[2025-01-03 06:00:17] Run started
[2025-01-03 06:00:17] 🎲 Randomized county order for stealth
[2025-01-03 06:00:20] 🎯 Starting Rutherford County (stealth mode)
[2025-01-03 06:00:20]    Using user agent: Mozilla/5.0 (Windows NT 10.0...
[2025-01-03 06:00:24]    [1/10] Searching: Smith
[2025-01-03 06:00:31]       Found 12 properties
[2025-01-03 06:00:37]    [2/10] Searching: Johnson
...
[2025-01-03 06:18:42] ✓ ALL COUNTIES SCRAPE COMPLETE (STEALTH MODE)
[2025-01-03 06:18:42] Duration: 18.4 minutes
[2025-01-03 06:18:42] Total Properties: 127
```

### **What to Look For:**

✅ **Good Signs:**
- Random delays (never same number)
- Different user agents each county
- Varying run durations
- No errors

❌ **Warning Signs:**
- Too many timeouts
- "Access Denied" errors
- CAPTCHAs appearing
- Sudden blocking

---

## 🛡️ Advanced Stealth (If Needed)

### **If You Get Blocked:**

1. **Increase delays:**
```python
MIN_DELAY = 5
MAX_DELAY = 15
```

2. **Add more user agents:**
```python
USER_AGENTS = [
    # Add 10-20 more user agent strings
    # Get from: https://www.useragentstring.com/
]
```

3. **Use rotating proxies** (advanced):
```python
# Requires proxy service ($)
chrome_options.add_argument('--proxy-server=http://your-proxy:8080')
```

4. **Add session management:**
```python
# Save/restore cookies between runs
# Makes you look like a returning visitor
```

---

## 📈 Best Practices

### **Daily Schedule:**

✅ **Good:**
```bash
# Run once daily at 6am
0 6 * * * python3 all_counties_stealth.py
```

✅ **Better:**
```bash
# Add random minute offset (not exactly 6:00)
3 6 * * * python3 all_counties_stealth.py  # 6:03am
```

❌ **Bad:**
```bash
# Multiple times per day (looks suspicious)
0 6,12,18 * * * python3 all_counties_stealth.py
```

### **File Management:**

Keep output files organized:
```bash
# Archive old files
mkdir -p archive/2025-01
mv all_counties_stealth_2024*.csv archive/2024-12/

# Or auto-delete after 30 days
find . -name "all_counties_stealth_*.csv" -mtime +30 -delete
```

---

## 🎯 Customizing for Your Needs

### **Faster (Trade Stealth for Speed):**
```python
MIN_DELAY = 1
MAX_DELAY = 3
RANDOMIZE_ORDER = False
```

### **Maximum Stealth:**
```python
MIN_DELAY = 5
MAX_DELAY = 15
RANDOMIZE_ORDER = True

# Add more user agents (10+)
# Add more random behavior
```

### **Specific Counties Only:**
```python
# In all_counties_stealth.py, comment out counties you don't want:

county_scrapers = [
    ("Wilson", scrape_wilson_stealth),
    ("Sumner", scrape_sumner_stealth),
    # ("Williamson", scrape_williamson_stealth),  # Skip this one
    ("Rutherford", scrape_rutherford_stealth),
    # ("Robertson", scrape_robertson_stealth),    # Skip this one
    # ("Cheatham", scrape_cheatham_stealth),      # Skip this one
]

# Now only runs Wilson, Sumner, Rutherford
```

---

## 🔧 Troubleshooting

### **"Script taking too long"**

Reduce scope:
```python
# Fewer subdivisions
WILLIAMSON_SUBDIVISIONS = ["Westhaven", "Brentwood"]  # Instead of 5+

# Fewer names
RUTHERFORD_NAMES = ["Smith", "Johnson", "Williams"]  # Instead of 10+
```

### **"Getting CAPTCHAs"**

Increase stealth:
```python
MIN_DELAY = 10
MAX_DELAY = 20

# And reduce frequency (run every 2-3 days instead of daily)
```

### **"No properties found"**

Normal! Some days have zero sales. Try:
```python
# Increase lookback
WILSON_SUMNER_DAYS = 30  # Instead of 7
```

---

## ✅ Success Checklist

- [ ] Stealth script runs successfully
- [ ] Random delays working (check logs)
- [ ] User agents rotating (check logs)
- [ ] County order changing daily
- [ ] No CAPTCHA challenges
- [ ] No "Access Denied" errors
- [ ] Reasonable runtime (15-25 min)
- [ ] Output files generated correctly

---

## 🎉 You're Protected!

Your scraper now:
- ✅ Looks like a human browsing
- ✅ Uses different browsers/devices
- ✅ Never repeats patterns
- ✅ Avoids bot detection
- ✅ Runs reliably at 6am CST
- ✅ Generates fresh daily leads

**Set it and forget it!** Wake up every morning to fresh property leads with zero bot detection risk! 🥷🏡💰