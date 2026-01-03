import requests
import gzip
import shutil
import csv
import os

print("=" * 60)
print("Downloading Redfin Neighborhood Data")
print("=" * 60)

# Try neighborhood data (smaller file)
url = "https://redfin-public-data.s3-us-west-2.amazonaws.com/redfin_market_tracker/neighborhood_market_tracker.tsv000.gz"

print(f"\nDownloading from S3...")

try:
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()

    gz_file = "neighborhood_data.tsv.gz"

    # Download with progress
    total_size = int(response.headers.get('content-length', 0))
    print(f"File size: {total_size / 1024 / 1024:.1f} MB")

    downloaded = 0
    with open(gz_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
            f.write(chunk)
            downloaded += len(chunk)
            if total_size:
                pct = (downloaded / total_size) * 100
                print(f"  Progress: {pct:.1f}%", end='\r')

    print(f"\n✓ Downloaded: {os.path.getsize(gz_file) / 1024 / 1024:.1f} MB")

    # Decompress
    print("Decompressing...")
    tsv_file = "redfin_data.tsv"
    with gzip.open(gz_file, 'rb') as f_in:
        with open(tsv_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    print(f"✓ Decompressed: {os.path.getsize(tsv_file) / 1024 / 1024:.1f} MB")

    # Convert to CSV and filter for Nashville
    print("Extracting Nashville data...")
    csv_file = "nashville_redfin.csv"
    nashville_rows = []

    with open(tsv_file, 'r', encoding='utf-8') as tsv_in:
        reader = csv.DictReader(tsv_in, delimiter='\t')
        headers = reader.fieldnames

        for row in reader:
            # Look for Nashville in various fields
            region_text = (row.get('region', '') + row.get('city', '') +
                          row.get('region_name', '') + row.get('table_id', '')).lower()
            if 'nashville' in region_text or 'davidson' in region_text:
                nashville_rows.append(row)

    print(f"✓ Found {len(nashville_rows)} Nashville records")

    if nashville_rows:
        with open(csv_file, 'w', newline='', encoding='utf-8') as csv_out:
            writer = csv.DictWriter(csv_out, fieldnames=headers)
            writer.writeheader()
            writer.writerows(nashville_rows)

        print(f"✓ Saved to: {csv_file}")
        print(f"\nColumns: {', '.join(list(headers)[:15])}")

        # Show sample
        print(f"\nSample row:")
        if nashville_rows:
            sample = nashville_rows[0]
            for key in list(sample.keys())[:10]:
                print(f"  {key}: {sample[key]}")

    # Cleanup
    os.remove(gz_file)
    os.remove(tsv_file)

    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
