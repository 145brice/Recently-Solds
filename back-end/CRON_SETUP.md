# County Property Sales Scrapers - Cron Setup

## Summary

Davidson County (Nashville) scraper is ready for daily cron jobs. It downloads recent property sales from the Nashville Property Assessor with the following data:

### Data Fields Captured:
- **Date** - Sale Date
- **Address** - Property Address
- **Amount** - Sale Price
- **Owner Name** - Not available in Davidson County recent sales data

### How It Works:
1. Downloads Excel files from https://www.padctn.org/resources/recent-sales/
2. Filters for most recent quarter (sales posted quarterly)
3. Saves to `output/davidson_sales_[timestamp].csv`
4. Logs to `logs/davidson_[date].log`

## Installation

```bash
# Install dependencies
pip3 install pandas openpyxl beautifulsoup4 requests --user

# Make scripts executable
chmod +x cron_davidson_county.py
```

## Cron Job Setup

Add to crontab (`crontab -e`):

```bash
# Run Davidson County scraper every day at 6 AM
0 6 * * * cd /Users/briceleasure/Desktop/recents && /usr/bin/python3 cron_davidson_county.py >> logs/cron.log 2>&1
```

##Files Created

1. **cron_davidson_county.py** - Davidson County (Nashville) scraper
   - Status: ✅ WORKING (with owner lookup)
   - Downloads Excel files from https://www.padctn.org/resources/recent-sales/
   - Looks up owner names from property assessor for each address
   - Extracts: Date, Address, Owner Name, Amount
   - Note: Sales posted quarterly (3-4 weeks after quarter end)
   - Data lag means recent scrapes may return 0 records until new quarter posted

2. **cron_williamson_county.py** - Williamson County scraper
   - Status: ✅ WORKING
   - URL: https://inigo.williamson-tn.org/property_search/
   - Waits for "Please Wait" message to clear (24+ seconds)
   - Searches all properties (no date filter due to site limitations)
   - Test run: Successfully extracted 10 sales records
   - Sample output: [output/williamson_sales_20251218_154219.csv](output/williamson_sales_20251218_154219.csv)
   - Extracts: Date, Address, Owner Name, Amount
   - Note: Returns properties with various sale dates (2014-2024 range)

3. **cron_wilson_county.py** - Wilson County scraper
   - Status: ❌ NOT WORKING - SITE TIMEOUT
   - URL: https://wilsontn.geopowered.com/propertysearch/
   - Platform: GeoPowered (JavaScript-heavy, very slow)
   - Issue: Site consistently times out even with 90s timeout
   - Page loads blank/empty in headless Chrome
   - Recommendation: Manual download or contact county for alternative data access

4. **cron_rutherford_county.py** - Rutherford County scraper
   - Status: ❌ NOT WORKING - REQUIRES SEARCH CRITERIA
   - URL: https://secured.rutherfordcountytn.gov/propertydata/RealPropertySearch2.aspx
   - Issue: Site requires minimum 3-character search term
   - No dedicated "Recent Sales" search available
   - Blank search returns "No data to display"
   - Recommendation: Would need to search by specific owner names, addresses, or date ranges
   - Potential workaround: Search for common terms like "LLC", "TRUST", etc. and filter results

## Testing

```bash
# Test Davidson County scraper
python3 cron_davidson_county.py

# Check output
ls -lh output/davidson_sales_*.csv
cat logs/davidson_*.log
```

## Important Notes

1. **Data Lag**: Davidson County posts sales quarterly (3rd-4th week after quarter end)
2. **Not Complete**: County notes these reports "should not be considered a complete listing"
3. **Owner Names**: Not included in Davidson's recent sales reports
   - Would need to cross-reference with property assessor database
   - Or use paid service like PropStream

## To Get Owner Names

Option 1: Cross-reference with Davidson County property database
- Use parcel ID from sales data
- Look up in https://www.padctn.org/real-property-search/
- Would require additional scraping

Option 2: Use paid data service
- PropStream
- DataTree
- RealQuest

## Summary

**Working Scrapers (2/4):**
- ✅ Davidson County - Downloads quarterly Excel files, includes owner lookup
- ✅ Williamson County - Scrapes property search site with 24s wait for results

**Not Working (2/4):**
- ❌ Wilson County - GeoPowered site too slow, times out
- ❌ Rutherford County - Requires specific search criteria, no bulk export

**Master Script:**
- ✅ run_all_counties.py created to run all 4 scrapers with error handling
- Each county runs independently with 10-minute timeout
- Logs successes/failures to logs/all_counties_[date].log

**Next Steps:**
1. Run Williamson County scraper on cron (only working scraper besides Davidson)
2. For Wilson County: Try non-headless browser or contact county for data export
3. For Rutherford County: Implement targeted searches (LLC, TRUST, etc.) and aggregate results
4. All scrapers output to: output/[county]_sales_[timestamp].csv with standardized columns: Date, Address, Owner Name, Amount
