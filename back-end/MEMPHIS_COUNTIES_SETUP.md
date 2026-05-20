# Memphis Area County Property Sales Scrapers

## Summary

Created scrapers for Memphis (Shelby County) and surrounding counties to get recent property sales data.

## Counties Covered

### 1. **Shelby County (Memphis)** - cron_shelby_county.py
   - Status: ⚠️ LIMITED - Requires Address Input
   - URLs:
     - Assessor Neighborhood Sales: https://www.assessormelvinburgess.com/neighborhoodSales
     - Register of Deeds: https://search.register.shelby.tn.us/search/index.php
   - Issue: Both sites require specific search criteria (street name/number or parcel)
   - No bulk export for recent sales available
   - Recommendation: Would need to search by known addresses or contact county for data export
   - Extracts: Date, Address, Owner Name, Amount (when data available)

### 2. **Fayette County** - cron_fayette_county.py
   - Status: ⚠️ NEEDS FIXING
   - URL: https://assessment.cot.tn.gov/ (Tennessee state database)
   - Issue: CSS selector error in scraper code
   - Platform: State-level Tennessee Property Assessment Database
   - Recommendation: May need to use dedicated Fayette County assessor site or state database API
   - Extracts: Date, Address, Owner Name, Amount (when working)

### 3. **Tipton County** - cron_tipton_county.py
   - Status: ❌ TIMEOUT ISSUES (like Wilson County)
   - URL: https://tiptontn.geopowered.com/PropertySearch/
   - Platform: GeoPowered (JavaScript-heavy, very slow)
   - Issue: Site consistently times out even with 90s timeout
   - Page loads blank/empty in headless Chrome
   - Recommendation: Contact county for alternative data access or use non-headless browser

## Comparison with Nashville Area

**Nashville Area (2/4 working):**
- ✅ Davidson County - Downloads quarterly Excel files
- ✅ Williamson County - Scrapes search site (24s wait)
- ❌ Wilson County - GeoPowered timeout
- ❌ Rutherford County - Requires search criteria

**Memphis Area (0/3 working reliably):**
- ⚠️ Shelby County - Requires specific address input
- ⚠️ Fayette County - Code error (fixable)
- ❌ Tipton County - GeoPowered timeout

## Recommendations

### For Memphis Area Data:
1. **Contact Counties Directly**: Ask for bulk data exports or API access
2. **Use Paid Services**: PropStream, DataTree, or RealQuest cover Memphis area
3. **Manual Download**: Some counties may offer manual CSV downloads
4. **Alternative Sources**: Memphis Area Association of Realtors may have sales data

### For Shelby County Specifically:
- The assessor's neighborhood sales search requires a street name
- Could implement searches for common street names (Main St, Poplar Ave, etc.)
- Aggregate results from multiple street searches
- Contact Assessor Melvin Burgess office at 901-222-7001 for bulk data access

## Files Created

- `cron_shelby_county.py` - Shelby County (Memphis) scraper
- `cron_fayette_county.py` - Fayette County scraper
- `cron_tipton_county.py` - Tipton County scraper

All scrapers output to: `output/[county]_sales_[timestamp].csv` with standardized columns: Date, Address, Owner Name, Amount

## Installation

```bash
# Install dependencies (same as Nashville counties)
pip3 install pandas openpyxl beautifulsoup4 requests selenium --user

# Make scripts executable
chmod +x cron_shelby_county.py cron_fayette_county.py cron_tipton_county.py
```

## Testing

```bash
# Test Shelby County
python3 cron_shelby_county.py

# Test Fayette County
python3 cron_fayette_county.py

# Test Tipton County
python3 cron_tipton_county.py
```

## Next Steps

1. Fix CSS selector error in Fayette County scraper
2. Implement targeted street searches for Shelby County
3. Contact counties for bulk data export options
4. Consider paid data services for comprehensive Memphis area coverage
