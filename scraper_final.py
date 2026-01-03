import requests
import pdfplumber
import csv
from io import BytesIO
from datetime import datetime
import re

URL = "https://www.padctn.org/real-property-sales-reports/"  # Adjust if needed; check site for exact path

response = requests.get(URL)
if response.status_code != 200:
    print("Failed to fetch page")
    exit()

# Find latest PDF link (assumes pattern like "Q3-2025-Property-Sales.pdf")
pdf_match = re.search(r'href="([^"]*\.pdf[^"]*Q[1-4]-\d{4}[^"]*)"', response.text)
if not pdf_match:
    print("No recent sales PDF found")
    exit()

pdf_url = "https://www.padctn.org/" + pdf_match.group(1).lstrip("/")
pdf_resp = requests.get(pdf_url)
pdf_data = BytesIO(pdf_resp.content)

with pdfplumber.open(pdf_data) as pdf:
    all_text = ""
    for page in pdf.pages:
        all_text += page.extract_text() or ""
    
    # Debug: print first 1000 chars to inspect format
    print(all_text[:1000])
    
    # Parse sales data (adjust regex based on PDF format, e.g., lines like "Address,Price,Date,YearBuilt")
    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
    sales_data = []
    for line in lines:
        # Example regex; inspect PDF to refine
        match = re.match(r'(.+?),\s*\$?([\d,]+),\s*(\d{4}-\d{2}-\d{2}),\s*(\d{4})', line)
        if match:
            addr, price, date, year_built = match.groups()
            roof_age = datetime.now().year - int(year_built) if year_built.isdigit() else "N/A"
            sales_data.append([addr, "Nashville", price, date, year_built, roof_age, pdf_url])

with open("nashville_recent_sales.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["address", "city", "sold_price", "sold_date", "year_built", "estimated_roof_age", "link"])
    writer.writerows(sales_data)

print(f"Extracted {len(sales_data)} sales to nashville_recent_sales.csv")