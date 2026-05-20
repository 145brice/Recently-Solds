import csv
from datetime import datetime, timedelta
import random

# Generate sample data for demonstration
cities = ['Nashville', 'Franklin', 'Brentwood', 'Murfreesboro', 'Smyrna', 'Mount-Juliet', 'Hendersonville', 'Gallatin']

data = []

for _ in range(50):  # Generate 50 sample homes
    city = random.choice(cities)
    address = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Elm Rd', 'Pine Ln'])}"
    sold_price = f"${random.randint(200000, 800000):,}"
    sold_date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
    year_built = str(random.randint(1950, 2020))
    estimated_roof_age = str(2025 - int(year_built))
    link = f"https://example.com/{city.lower().replace(' ', '-')}/{address.replace(' ', '-')}"

    data.append({
        'address': address,
        'city': city,
        'sold_price': sold_price,
        'sold_date': sold_date,
        'year_built': year_built,
        'estimated_roof_age': estimated_roof_age,
        'link': link
    })

# Save to CSV
with open('nashville_recent_sales.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['address', 'city', 'sold_price', 'sold_date', 'year_built', 'estimated_roof_age', 'link'])
    writer.writeheader()
    writer.writerows(data)

print(f"Generated {len(data)} sample sold homes - check nashville_recent_sales.csv")