#!/bin/bash
# RANDOM TIME DAILY SCRAPER WRAPPER
# Runs at fixed time but sleeps random 0-60 minutes before executing

# Generate random sleep time (0-60 minutes = 0-3600 seconds)
RANDOM_SLEEP=$((RANDOM % 3600))

echo "$(date): Sleeping ${RANDOM_SLEEP} seconds before running scraper..."
sleep $RANDOM_SLEEP

echo "$(date): Starting property scraper..."
cd /Users/briceleasure/Desktop/recents
python3 all_counties_daily.py >> daily.log 2>&1

echo "$(date): Scraper completed."