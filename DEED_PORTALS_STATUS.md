# Tennessee Deed Portal Scraper Status
**Date:** December 18, 2025

## Goal
Scrape 4 public Tennessee deed portals for recent warranty deeds (last 7-30 days) with buyer/grantee names visible.

##Target Counties (Per User Request)

### 1. Shelby County (Memphis) - ⚠️ IN PROGRESS
- **URL:** https://register.shelby.tn.us/
- **Status:** Partially working - complex form structure
- **Findings:**
  - Site uses iframe-based search interface
  - Successfully navigated to search form in iframe
  - Successfully found and clicked warranty deed checkbox (value="WD")
  - Can extract data from results table (tested with 100+ records)
  - **BLOCKER:** Form search returns 0 results with date-only criteria
  - Likely requires additional search criteria (name, address, or parcel number)
  - May not support bulk warranty deed searches by date alone

- **What Works:**
  - Navigation to search page ✅
  - Iframe detection and switching ✅
  - Form element detection ✅
  - Data extraction from results table ✅

- **What Doesn't Work:**
  - Form submission with date + document type filters returns no results ❌
  - May require name/address search criteria ❌

### 2. Knox County (Knoxville) - ❌ NOT WORKING
- **URL:** https://rod.knoxcounty.org/
- **Status:** Initial scraper created, not functional
- **Findings:**
  - Found 0 search links, 0 date inputs, 0 tables
  - Likely JavaScript-heavy interface similar to Shelby
  - Needs investigation and debugging

### 3. Hamilton County (Chattanooga) - 📝 NOT STARTED
- **URL:** https://register.hamiltontn.gov/
- **Status:** Not started
- **Next Step:** Create scraper after resolving Shelby/Knox issues

### 4. Montgomery County (Clarksville) - 📝 NOT STARTED
- **URL:** https://publicrecords.netronline.com/state/TN/county/montgomery
- **Status:** Not started
- **Note:** Uses NETR portal system (different platform)
- **Next Step:** Create scraper after resolving other counties

## Nashville Area Scrapers (Previously Completed)

### ✅ Davidson County - WORKING
- Downloads quarterly Excel files from county website
- Includes owner name lookup functionality
- Output: CSV with Date, Address, Owner Name, Amount

### ✅ Williamson County - WORKING
- Scrapes property search site
- Successfully extracted 10 sales records
- Output: CSV with Date, Address, Owner Name, Amount

### ❌ Wilson County - NOT WORKING
- GeoPowered platform timeout issues
- Site consistently times out even with 90s timeout
- Recommendation: Contact county for alternative data access

### ❌ Rutherford County - NOT WORKING
- Requires specific search criteria (minimum 3 characters)
- No bulk search/export available
- Recommendation: Contact county for bulk data access

## Technical Challenges

### Deed Portal Sites (Shelby, Knox, Hamilton, Montgomery)
1. **Complex JavaScript interfaces** - Heavy client-side rendering
2. **Iframe-based search forms** - Requires iframe detection and switching
3. **Required search criteria** - May not allow date-only searches
4. **No bulk export** - Sites designed for individual record lookup, not bulk scraping

### Potential Solutions
1. **Targeted Searches:** Search by common street names and aggregate results
2. **Contact Counties:** Request bulk data export or API access
3. **Paid Services:** Consider PropStream, DataTree, or RealQuest
4. **Alternative Sources:** Memphis/Tennessee Association of Realtors

## Recommendations

### Immediate Next Steps
1. **Test different search approaches for Shelby County:**
   - Try searching by common street names (Main St, Poplar Ave, etc.)
   - Test with wildcard searches
   - Try searching without dates to see if ANY results return

2. **Debug Knox County scraper:**
   - Add comprehensive page inspection
   - Check for iframes
   - Identify actual form structure

3. **Create Hamilton & Montgomery scrapers:**
   - Learn from Shelby/Knox findings
   - Test different approaches from the start

### Long-term Solutions
1. **Contact County Offices:**
   - Shelby County Register: (901) 222-7000
   - Request bulk data export for recent warranty deeds
   - Ask about API or automated access

2. **Consider Commercial Data Services:**
   - PropStream, DataTree, or RealQuest cover all TN counties
   - Provide standardized data with buyer/seller names
   - May be more reliable than web scraping

## Files Created
- `cron_shelby_county.py` - Shelby County scraper (in progress)
- `cron_knox_county.py` - Knox County scraper (needs debugging)
- `DEED_PORTALS_STATUS.md` - This status file

## Data Format (Target)
All scrapers output CSV with standardized columns:
- Date
- Address
- Buyer/Grantee (new owner)
- Seller/Grantor (previous owner)
- Amount (consideration/sale price)
- Doc Type (e.g., "WARRANTY DEED", "WD")
