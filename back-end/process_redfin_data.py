import csv
from datetime import datetime, timedelta
import re

# Configuration
INPUT_CSV = "redfin_download.csv"  # Name of CSV downloaded from data.redfin.com
OUTPUT_CSV = "hot_investor_leads.csv"
DAYS_BACK = 60  # Filter for sales in last 60 days

print("=" * 60)
print("Processing Redfin Data for Investor Leads")
print("=" * 60)

# Read the downloaded Redfin CSV
try:
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    print(f"\n✓ Loaded {len(data)} properties from {INPUT_CSV}")
except FileNotFoundError:
    print(f"\n✗ Error: {INPUT_CSV} not found!")
    print("\nInstructions:")
    print("1. Go to data.redfin.com")
    print("2. Select Nashville")
    print("3. Click on any neighborhood")
    print("4. Click 'Download Report' button")
    print("5. Save as 'redfin_download.csv' in this folder")
    exit(1)

# Process data
hot_leads = []
cutoff_date = datetime.now() - timedelta(days=DAYS_BACK)

for row in data:
    # Extract key fields (adjust column names based on actual Redfin CSV)
    address = row.get("PROPERTY ADDRESS", row.get("Address", ""))
    property_zip = row.get("PROPERTY ZIP", row.get("ZIP OR POSTAL CODE", ""))
    mailing_zip = row.get("MAILING ZIP", row.get("OWNER MAIL ZIP", ""))
    owner_name = row.get("OWNER NAME", row.get("Owner", ""))
    sold_date_str = row.get("SOLD DATE", row.get("Sale Date", ""))
    price = row.get("PRICE", row.get("Sale Price", ""))
    beds = row.get("BEDS", "")
    baths = row.get("BATHS", "")
    sqft = row.get("SQUARE FEET", "")

    # Skip if missing critical data
    if not address or not sold_date_str:
        continue

    # Parse sold date
    try:
        # Try common date formats
        for fmt in ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"]:
            try:
                sold_date = datetime.strptime(sold_date_str, fmt)
                break
            except:
                continue
        else:
            continue  # Skip if date couldn't be parsed
    except:
        continue

    # Filter: Only last 60 days
    if sold_date < cutoff_date:
        continue

    # Identify absentee owners (mailing zip != property zip)
    is_absentee = "Yes" if (mailing_zip and property_zip and mailing_zip != property_zip) else "No"

    # Identify LLCs (investor signal)
    is_llc = "Yes" if (owner_name and re.search(r'\b(LLC|L\.L\.C\.|INC|CORP|LP|TRUST)\b', owner_name, re.IGNORECASE)) else "No"

    # Calculate days since sold
    days_since_sold = (datetime.now() - sold_date).days

    # Add to leads list
    hot_leads.append({
        "Address": address,
        "Sold Date": sold_date_str,
        "Days Since Sold": days_since_sold,
        "Price": price,
        "Beds": beds,
        "Baths": baths,
        "Sqft": sqft,
        "Owner Name": owner_name,
        "Property Zip": property_zip,
        "Mailing Zip": mailing_zip,
        "Absentee Owner": is_absentee,
        "LLC/Corp": is_llc,
    })

# Sort by date (most recent first)
hot_leads.sort(key=lambda x: x["Days Since Sold"])

# Separate into tiers
tier_1 = [lead for lead in hot_leads if lead["Absentee Owner"] == "Yes" and lead["LLC/Corp"] == "Yes"]
tier_2 = [lead for lead in hot_leads if lead["Absentee Owner"] == "Yes" and lead["LLC/Corp"] == "No"]
tier_3 = [lead for lead in hot_leads if lead["Absentee Owner"] == "No" and lead["LLC/Corp"] == "Yes"]

# Save all leads
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    if hot_leads:
        writer = csv.DictWriter(f, fieldnames=hot_leads[0].keys())
        writer.writeheader()
        writer.writerows(hot_leads)

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")
print(f"Total properties in last {DAYS_BACK} days: {len(hot_leads)}")
print(f"\nTIER 1 (Absentee + LLC): {len(tier_1)} leads")
print(f"TIER 2 (Absentee only): {len(tier_2)} leads")
print(f"TIER 3 (LLC only): {len(tier_3)} leads")
print(f"\n✓ Saved to: {OUTPUT_CSV}")
print(f"{'='*60}")

# Show sample of Tier 1 leads
if tier_1:
    print("\nSample TIER 1 Leads (Hottest):")
    print("-" * 60)
    for lead in tier_1[:5]:
        print(f"  • {lead['Address']}")
        print(f"    Owner: {lead['Owner Name']}")
        print(f"    Sold: {lead['Days Since Sold']} days ago | Price: {lead['Price']}")
        print()
