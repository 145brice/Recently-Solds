"""
Wilson County Quick Test
========================

This script tests the Wilson County scraper with a small sample
to make sure everything is working before running the full scraper.

Run this first to verify your setup!
"""

import sys

print("\n" + "="*60)
print("WILSON COUNTY SCRAPER - QUICK TEST")
print("="*60 + "\n")

# Check Python version
print("1. Checking Python version...")
if sys.version_info < (3, 8):
    print("❌ Python 3.8+ required")
    print(f"   You have: {sys.version}")
    sys.exit(1)
else:
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

# Check dependencies
print("\n2. Checking dependencies...")
required_packages = {
    'selenium': 'selenium',
    'pandas': 'pandas',
    'webdriver_manager': 'webdriver-manager',
    'openpyxl': 'openpyxl'
}

missing = []
for module, package in required_packages.items():
    try:
        __import__(module)
        print(f"✓ {package}")
    except ImportError:
        print(f"❌ {package} - MISSING")
        missing.append(package)

if missing:
    print(f"\n❌ Missing packages. Install with:")
    print(f"   pip install {' '.join(missing)}")
    sys.exit(1)

# Try to import the scraper
print("\n3. Loading Wilson County scraper...")
try:
    from wilson_sumner_scraper import CountyPropertyScraper
    print("✓ Scraper loaded successfully")
except Exception as e:
    print(f"❌ Error loading scraper: {str(e)}")
    sys.exit(1)

# Run a quick test
print("\n4. Running quick test...")
print("   This will open a browser and test the page load")
print("   (Browser will close automatically)\n")

try:
    with CountyPropertyScraper(county="wilson", headless=False) as scraper:
        print("✓ Browser opened")
        scraper.navigate_to_search()
        print("✓ Page loaded successfully")
        print("✓ Test complete!")
        
    print("\n" + "="*60)
    print("SUCCESS! Everything is working correctly.")
    print("="*60)
    print("\nNext steps:")
    print("1. Run: python wilson_scraper_full.py")
    print("2. Get your data!")
    print("="*60 + "\n")

except Exception as e:
    print(f"\n❌ Test failed: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Make sure Chrome browser is installed")
    print("2. Check your internet connection")
    print("3. Try running with headless=True")
    sys.exit(1)
