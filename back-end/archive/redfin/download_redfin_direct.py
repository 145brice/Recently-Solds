import requests
import os

print("=" * 60)
print("Downloading Redfin Metro Data (includes Nashville)")
print("=" * 60)

# Direct link to Redfin's metro-level data TSV
# This includes all metro areas including Nashville
url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/metro_market_tracker.tsv000.gz"

print(f"\nDownloading from: {url}")

try:
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    # Save the gzipped file
    gz_file = "metro_market_tracker.tsv000.gz"
    with open(gz_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"✓ Downloaded: {gz_file}")
    print(f"  Size: {os.path.getsize(gz_file)} bytes")

    # Decompress the file
    import gzip
    import shutil

    tsv_file = "redfin_download.tsv"
    with gzip.open(gz_file, 'rb') as f_in:
        with open(tsv_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    print(f"✓ Decompressed to: {tsv_file}")
    print(f"  Size: {os.path.getsize(tsv_file)} bytes")

    # Convert TSV to CSV
    import csv
    csv_file = "redfin_download.csv"
    with open(tsv_file, 'r', encoding='utf-8') as tsv_in:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csv_out:
            reader = csv.reader(tsv_in, delimiter='\t')
            writer = csv.writer(csv_out)
            writer.writerows(reader)

    print(f"✓ Converted to CSV: {csv_file}")
    print(f"  Size: {os.path.getsize(csv_file)} bytes")

    # Clean up temp files
    os.remove(gz_file)
    os.remove(tsv_file)

    # Check for Nashville data
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        print(f"\n✓ Columns in dataset: {len(headers)}")
        print(f"  Sample columns: {', '.join(headers[:5])}")

        # Count Nashville records
        nashville_count = 0
        for row in reader:
            if 'Nashville' in row.get('region', '') or 'Nashville' in row.get('city', ''):
                nashville_count += 1

        print(f"\n✓ Found {nashville_count} Nashville records")

    print("\n" + "=" * 60)
    print("SUCCESS! Now run: python3 process_redfin_data.py")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    print("\nTrying alternative URL...")

    # Try the city-level data
    url2 = "https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz"
    print(f"Downloading from: {url2}")

    try:
        response = requests.get(url2, stream=True, timeout=30)
        response.raise_for_status()
        print("✓ Alternative source worked!")

        # Save the gzipped file
        import gzip
        import shutil

        gz_file = "city_market_tracker.tsv000.gz"
        with open(gz_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✓ Downloaded: {gz_file}")
        print(f"  Size: {os.path.getsize(gz_file)} bytes")

        # Decompress the file
        tsv_file = "redfin_download.tsv"
        with gzip.open(gz_file, 'rb') as f_in:
            with open(tsv_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        print(f"✓ Decompressed to: {tsv_file}")
        print(f"  Size: {os.path.getsize(tsv_file)} bytes")

        # Convert TSV to CSV
        import csv
        csv_file = "redfin_download.csv"
        with open(tsv_file, 'r', encoding='utf-8') as tsv_in:
            with open(csv_file, 'w', newline='', encoding='utf-8') as csv_out:
                reader = csv.reader(tsv_in, delimiter='\t')
                writer = csv.writer(csv_out)
                writer.writerows(reader)

        print(f"✓ Converted to CSV: {csv_file}")
        print(f"  Size: {os.path.getsize(csv_file)} bytes")

        # Clean up temp files
        os.remove(gz_file)
        os.remove(tsv_file)

        # Check for Nashville data
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            print(f"\n✓ Columns in dataset: {len(headers)}")
            print(f"  First 10 columns: {', '.join(list(headers)[:10])}")

            # Count Nashville records
            nashville_count = 0
            for row in reader:
                region = row.get('region', '') + row.get('city', '') + row.get('region_name', '')
                if 'Nashville' in region:
                    nashville_count += 1

            print(f"\n✓ Found {nashville_count} Nashville records")

        print("\n" + "=" * 60)
        print("SUCCESS! Now run: python3 process_redfin_data.py")
        print("=" * 60)

    except Exception as e2:
        print(f"✗ Alternative also failed: {e2}")
        print("\nManual download:")
        print("1. Go to: https://www.redfin.com/news/data-center/")
        print("2. Scroll down to 'Download region data here'")
        print("3. Click 'City' or 'Metro' to download")
        print("4. Save as 'redfin_download.csv'")
