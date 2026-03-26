import csv

# Read the original CSV
with open("nashville_cash_leads.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    data = list(reader)

# Remove duplicates and clean prices
seen_addresses = set()
clean_data = []

for row in data:
    address = row["Address"].strip()

    # Skip if we've already seen this address
    if address in seen_addresses:
        continue

    seen_addresses.add(address)

    # Clean up price - remove "Last sold price" text and newlines
    price = row["Price"].replace("\n", "").replace("Last sold price", "").strip()

    clean_data.append({
        "Address": address,
        "Price": price,
        "Sold Date": row["Sold Date"].strip(),
        "Agent Phone": row["Agent Phone"].strip()
    })

# Save cleaned data
with open("nashville_cash_leads_clean.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["Address", "Price", "Sold Date", "Agent Phone"])
    writer.writeheader()
    writer.writerows(clean_data)

print(f"Original: {len(data)} rows")
print(f"After removing duplicates: {len(clean_data)} rows")
print(f"Saved to: nashville_cash_leads_clean.csv")
