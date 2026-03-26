"""
Daily Pipeline Launcher
========================
Double-click this file or run: python run_daily.py

Sets up import paths and runs the master scraper for all 7 Nashville-area counties.
Results are saved to the front-end dashboard automatically.
"""

import sys
import os

# Set up paths so all imports resolve correctly
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'production', 'runners'))
sys.path.insert(0, os.path.join(project_root, 'production', 'scrapers'))
sys.path.insert(0, os.path.join(project_root, 'production', 'utilities'))
os.chdir(os.path.join(project_root, 'production', 'runners'))

from all_counties_daily import main

if __name__ == "__main__":
    sys.exit(main())
