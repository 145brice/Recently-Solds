#!/usr/bin/env python3
"""
Master script to run all 4 county scrapers
Run this daily via cron
"""

import subprocess
import logging
from datetime import datetime
import os

# Setup logging
log_file = f"logs/all_counties_{datetime.now().strftime('%Y%m%d')}.log"
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

counties = [
    ("Davidson", "cron_davidson_county.py"),
    ("Williamson", "cron_williamson_county.py"),
    ("Wilson", "cron_wilson_county.py"),
    ("Rutherford", "cron_rutherford_county.py")
]

logging.info("="*60)
logging.info("Running All County Scrapers")
logging.info("="*60)

results = {}

for county_name, script in counties:
    logging.info(f"\n{'-'*60}")
    logging.info(f"Running {county_name} County...")
    logging.info(f"{'-'*60}")

    try:
        result = subprocess.run(
            ["python3", script],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per county
        )

        if result.returncode == 0:
            logging.info(f"✓ {county_name} completed successfully")
            results[county_name] = "SUCCESS"
        else:
            logging.error(f"✗ {county_name} failed with code {result.returncode}")
            logging.error(result.stderr[:500])
            results[county_name] = "FAILED"

    except subprocess.TimeoutExpired:
        logging.error(f"✗ {county_name} timed out after 10 minutes")
        results[county_name] = "TIMEOUT"

    except Exception as e:
        logging.error(f"✗ {county_name} error: {e}")
        results[county_name] = "ERROR"

# Summary
logging.info("\n" + "="*60)
logging.info("SUMMARY")
logging.info("="*60)
for county, status in results.items():
    logging.info(f"  {county:15s}: {status}")
logging.info("="*60)
