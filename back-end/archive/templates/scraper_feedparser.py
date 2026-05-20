import feedparser
import csv
from datetime import datetime

# CHANGE THIS CITY
CITY = "Nashville"
STATE_ABBR = "TN"  # for Zillow RSS URL
ZILLOW_RSS = f"https://www.zillow.com/rss/{CITY.lower().replace(' ', '-')}-{STATE_ABBR.lower()}/sold/"

OUTPUT_FILE = f"{CITY.lower()}_recent_sales.csv"

feed = feedparser.parse(ZILLOW_RSS)

with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["address", "city", "sold_price", "sold_date", "year_built", "estimated_roof_age", "link"])

    for entry in feed.entries:
        address = entry.title.strip()
        link = entry.link
        price = entry.get("zillow:price", "N/A")
        sold_date = entry.get("zillow:solddate", "N/A")
        
        year_built_tag = next((t.content for t in entry.get("tags", []) if t.term == "BuildYear"), None)
        year_built = year_built_tag if year_built_tag else "N/A"
        
        roof_age = datetime.now().year - int(year_built) if year_built != "N/A" and year_built.isdigit() else "N/A"
        
        writer.writerow([address, CITY, price, sold_date, year_built, roof_age, link])

print(f"Scraped {len(feed.entries)} sold homes → {OUTPUT_FILE}")