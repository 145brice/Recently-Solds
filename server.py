"""
Local Pipeline Server - http://localhost:8082
Serves the front-end dashboard + admin panel, the pipeline API,
and the Stripe-powered leads storefront API.
"""

import http.server
import json
import threading
import subprocess
import sys
import os
import io
import csv
import re
import uuid
import sqlite3
import contextlib
from datetime import datetime
from urllib.parse import unquote, parse_qs, urlparse

try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

PORT = 8082
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, '..', 'Property-Managers--Front-End')
RUNNER = os.path.join(PROJECT_ROOT, 'run_daily.py')
MOTIVATED_RUNNER = os.path.join(PROJECT_ROOT, 'run_motivated_sellers.py')
ORDERS_DIR = os.path.join(PROJECT_ROOT, 'orders')
MOTIVATED_DB = os.path.join(PROJECT_ROOT, 'motivated_sellers.db')
MOTIVATED_CSV = os.path.join(FRONTEND_DIR, 'motivated_sellers.csv')

# Stripe config â€” set these environment variables before running
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
SUBSCRIPTION_PRICE_CENTS = 9900  # $99.00/month
# Stripe Price ID for the $99/mo subscription â€” set this env var after creating the price in Stripe dashboard
STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID', '')

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# In-memory store for pending checkout sessions: { session_id: { leads: [...], paid: bool } }
checkout_sessions = {}

# Ensure orders directory exists
os.makedirs(ORDERS_DIR, exist_ok=True)

MIME_TYPES = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.csv': 'text/csv',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.ico': 'image/x-icon',
}

def export_db_to_csv():
    """Export SQLite database to the frontend CSV â€” ensures dashboard always has data."""
    import sqlite3
    db_file = os.path.join(PROJECT_ROOT, 'all_counties_leads.db')
    csv_file = os.path.join(FRONTEND_DIR, 'nashville_cash_leads_clean.csv')
    if not os.path.exists(db_file):
        return
    try:
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute('SELECT "Owner Name", County, Address, Price, "Sold Date", "Agent Phone", "Property Type" FROM all_county_sales')
        rows = c.fetchall()
        conn.close()
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Owner Name', 'County', 'Address', 'Price', 'Sold Date', 'Agent Phone', 'Agent Email', 'Property Type'])
            for row in rows:
                writer.writerow(list(row[:6]) + ['', row[6] or ''])  # Agent Email blank, then Property Type
        return len(rows)
    except Exception:
        return 0

pipeline_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'log': ''
}
pipeline_process = None

motivated_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'log': ''
}
motivated_process = None

enrich_status = {
    'running': False,
    'total': 0,
    'done': 0,
    'current': '',
    'log': '',
    'csv_file': ''
}
_enrich_scraper = None  # holds the active PropertyTypeScraper so we can stop it
ENRICH_OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output', 'property_type_enrichment')


def run_pipeline_thread(config):
    global pipeline_process
    pipeline_status['running'] = True
    pipeline_status['log'] = ''
    pipeline_status['last_result'] = None

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['ENABLED_COUNTIES'] = config.get('enabled_counties', 'all')
    env['DAVIDSON_DAYS'] = str(config.get('davidson_days', 60))
    env['WILSON_SUMNER_DAYS'] = str(config.get('wilson_sumner_days', 7))
    env['WILLIAMSON_DAYS'] = str(config.get('williamson_days', 30))
    env['MIN_PRICE'] = str(config.get('min_price', 0))
    env['MAX_PRICE'] = str(config.get('max_price', 850000))

    try:
        process = subprocess.Popen(
            [sys.executable, '-u', RUNNER],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_ROOT,
            env=env,
            bufsize=1
        )
        pipeline_process = process

        for line in process.stdout:
            pipeline_status['log'] += line

        process.wait()

        if process.returncode == 0:
            pipeline_status['last_result'] = 'success'
            pipeline_status['log'] += '\n--- Pipeline finished successfully ---\n'
        else:
            pipeline_status['last_result'] = 'error'
            pipeline_status['log'] += f'\n--- Pipeline exited with code {process.returncode} ---\n'

    except Exception as e:
        pipeline_status['last_result'] = 'error'
        pipeline_status['log'] += f'\n--- Error: {e} ---\n'

    pipeline_process = None
    pipeline_status['running'] = False
    pipeline_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def kill_pipeline():
    global pipeline_process
    if pipeline_process and pipeline_process.poll() is None:
        pipeline_process.kill()
        pipeline_status['log'] += '\n--- KILLED BY USER ---\n'
        pipeline_status['last_result'] = 'killed'
        pipeline_status['running'] = False
        pipeline_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pipeline_process = None
        return True
    return False


def run_motivated_thread(config):
    global motivated_process
    motivated_status['running'] = True
    motivated_status['log'] = ''
    motivated_status['last_result'] = None

    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['MOTIVATED_ENABLED'] = config.get('enabled_types', 'all')
    env['MOTIVATED_DAYS'] = str(config.get('days_back', 60))

    try:
        process = subprocess.Popen(
            [sys.executable, '-u', MOTIVATED_RUNNER],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=PROJECT_ROOT,
            env=env,
            bufsize=1
        )
        motivated_process = process
        for line in process.stdout:
            motivated_status['log'] += line
        process.wait()
        if process.returncode == 0:
            motivated_status['last_result'] = 'success'
            motivated_status['log'] += '\n--- Motivated sellers pipeline finished successfully ---\n'
        else:
            motivated_status['last_result'] = 'error'
            motivated_status['log'] += f'\n--- Pipeline exited with code {process.returncode} ---\n'
    except Exception as e:
        motivated_status['last_result'] = 'error'
        motivated_status['log'] += f'\n--- Error: {e} ---\n'

    motivated_process = None
    motivated_status['running'] = False
    motivated_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def kill_motivated():
    global motivated_process
    if motivated_process and motivated_process.poll() is None:
        motivated_process.kill()
        motivated_status['log'] += '\n--- KILLED BY USER ---\n'
        motivated_status['last_result'] = 'killed'
        motivated_status['running'] = False
        motivated_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        motivated_process = None
        return True
    return False


DB_FILE = os.path.join(PROJECT_ROOT, 'all_counties_leads.db')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')


def _ensure_property_type_cache():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS property_type_cache (
            address TEXT PRIMARY KEY,
            property_type TEXT,
            looked_up_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def _normalize_addr_key(addr):
    s = (addr or '').upper().strip()
    s = ' '.join(s.replace(',', ' ').split())
    return s


def _flip_street_num(addr_key):
    m = re.match(r"^(.+)\s+(\d+[A-Z\-]*)$", addr_key or "")
    if not m:
        return addr_key
    return f"{m.group(2)} {m.group(1)}"


def _canonical_enrichment_address(address):
    key = _normalize_addr_key(address)
    flipped = _flip_street_num(key)
    return flipped if flipped and flipped != key else (address or '').strip()


def _latest_county_csv(county):
    county_dir = os.path.join(OUTPUT_DIR, county.lower())
    if not os.path.isdir(county_dir):
        return None
    files = [os.path.join(county_dir, f) for f in os.listdir(county_dir) if f.lower().endswith('.csv')]
    if not files:
        return None
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files[0]


def _load_county_type_map(csv_file):
    out = {}
    with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            addr = row.get('Address') or row.get('address') or ''
            ptype = row.get('Property Type') or row.get('property_type') or ''
            ptype = (ptype or '').strip()
            if not addr or not ptype or ptype.upper() in ('N/A', 'UNKNOWN'):
                continue
            out[_normalize_addr_key(addr)] = ptype
    return out


def backfill_property_types_from_county_csv(county, address_items):
    """
    Fast county-first backfill from latest county CSV (no scraper rerun).
    address_items: [{address, county}] or [address]
    """
    _ensure_property_type_cache()
    csv_file = _latest_county_csv(county)
    if not csv_file:
        return {'updated': 0, 'checked': 0, 'csv_file': '', 'message': f'No CSV found for {county}'}

    type_map = _load_county_type_map(csv_file)
    checked = 0
    updated = 0
    conn = sqlite3.connect(DB_FILE)
    try:
        for item in address_items:
            if isinstance(item, dict):
                address = (item.get('address') or '').strip()
            else:
                address = str(item).strip()
            if not address:
                continue
            checked += 1
            ptype = type_map.get(_normalize_addr_key(address), '')
            if not ptype:
                continue
            conn.execute(
                'INSERT OR REPLACE INTO property_type_cache (address, property_type, looked_up_at) VALUES (?, ?, ?)',
                (address, ptype, datetime.now().isoformat())
            )
            updated += 1
        conn.commit()
    finally:
        conn.close()
    return {'updated': updated, 'checked': checked, 'csv_file': csv_file, 'message': 'ok'}


def run_enrich_thread(addresses):
    global _enrich_scraper
    sys.path.insert(0, PROJECT_ROOT)
    from production.scrapers.property_type_scraper import PropertyTypeScraper

    enrich_status['running'] = True
    enrich_status['total'] = len(addresses)
    enrich_status['done'] = 0
    enrich_status['log'] = f'Starting enrichment for {len(addresses)} addresses...\n'
    enrich_status['csv_file'] = ''

    _ensure_property_type_cache()
    conn = sqlite3.connect(DB_FILE)
    scraper = PropertyTypeScraper()
    _enrich_scraper = scraper

    os.makedirs(ENRICH_OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_csv_file = os.path.join(ENRICH_OUTPUT_DIR, f'property_type_enrichment_{ts}.csv')
    latest_csv_file = os.path.join(ENRICH_OUTPUT_DIR, 'property_type_enrichment_latest.csv')
    enrich_status['csv_file'] = run_csv_file

    try:
        with open(run_csv_file, 'w', newline='', encoding='utf-8') as run_f, \
             open(latest_csv_file, 'w', newline='', encoding='utf-8') as latest_f:
            run_writer = csv.writer(run_f)
            latest_writer = csv.writer(latest_f)
            headers = ['timestamp', 'input_address', 'address', 'property_type']
            run_writer.writerow(headers)
            latest_writer.writerow(headers)
            run_f.flush()
            latest_f.flush()

            for i, item in enumerate(addresses):
                if isinstance(item, dict):
                    address = (item.get('address') or '').strip()
                    county = (item.get('county') or '').strip()
                else:
                    address = str(item).strip()
                    county = ''
                if not address:
                    continue
                if scraper._stop:
                    enrich_status['log'] += '\n--- STOPPED BY USER ---\n'
                    break
                enrich_status['current'] = address
                meta_address = ''
                if hasattr(scraper, 'lookup_with_meta'):
                    result = scraper.lookup_with_meta(address, county=county)
                    ptype = (result.get('property_type') or 'Unknown').strip()
                    meta_address = (result.get('meta_address') or '').strip()
                else:
                    ptype = scraper.lookup(address, county=county)
                canonical_address = _canonical_enrichment_address(address)
                display_address = meta_address or canonical_address or address
                now_iso = datetime.now().isoformat()
                enrich_status['done'] = i + 1
                if meta_address and _normalize_addr_key(meta_address) != _normalize_addr_key(address):
                    enrich_status['log'] += f'[{i+1}/{len(addresses)}] {display_address}  ->  {ptype}  (Google meta from {address})\n'
                elif _normalize_addr_key(display_address) != _normalize_addr_key(address):
                    enrich_status['log'] += f'[{i+1}/{len(addresses)}] {display_address}  ->  {ptype}  (normalized from {address})\n'
                else:
                    enrich_status['log'] += f'[{i+1}/{len(addresses)}] {display_address}  ->  {ptype}\n'
                conn.execute(
                    'INSERT OR REPLACE INTO property_type_cache (address, property_type, looked_up_at) VALUES (?, ?, ?)',
                    (address, ptype, now_iso)
                )
                if _normalize_addr_key(display_address) != _normalize_addr_key(address):
                    # Also cache by the display address so UI lookups can resolve either form.
                    conn.execute(
                        'INSERT OR REPLACE INTO property_type_cache (address, property_type, looked_up_at) VALUES (?, ?, ?)',
                        (display_address, ptype, now_iso)
                    )
                conn.commit()

                row = [now_iso, address, display_address, ptype]
                run_writer.writerow(row)
                latest_writer.writerow(row)
                run_f.flush()
                latest_f.flush()
    except Exception as e:
        enrich_status['log'] += f'\n--- ERROR: {e} ---\n'
    finally:
        conn.close()
        _enrich_scraper = None

    enrich_status['running'] = False
    enrich_status['log'] += f'\n--- Done. {enrich_status["done"]}/{enrich_status["total"]} addresses enriched. ---\n'
    if enrich_status.get('csv_file'):
        enrich_status['log'] += f'\n--- CSV saved incrementally: {enrich_status["csv_file"]} ---\n'


def run_true_county_thread(county, addresses, days_back=120):
    global _enrich_scraper
    sys.path.insert(0, PROJECT_ROOT)
    from production.scrapers.wilson_sumner_scraper import CountyPropertyScraper

    county = (county or '').strip().lower()
    if county not in ('wilson', 'sumner'):
        enrich_status['running'] = False
        enrich_status['log'] = f'Unsupported county for true lookup: {county}'
        return

    enrich_status['running'] = True
    enrich_status['total'] = len(addresses)
    enrich_status['done'] = 0
    enrich_status['current'] = ''
    enrich_status['log'] = f'Starting TRUE county detail enrichment for {county.title()} ({len(addresses)} addresses)...\n'
    enrich_status['csv_file'] = ''

    _ensure_property_type_cache()
    conn = sqlite3.connect(DB_FILE)
    os.makedirs(ENRICH_OUTPUT_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_csv_file = os.path.join(ENRICH_OUTPUT_DIR, f'property_type_true_{county}_{ts}.csv')
    enrich_status['csv_file'] = run_csv_file

    try:
        clean_addresses = []
        for item in addresses:
            if isinstance(item, dict):
                a = (item.get('address') or '').strip()
            else:
                a = str(item).strip()
            if a:
                clean_addresses.append(a)

        with open(run_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'address', 'property_type', 'source'])
            f.flush()

            # Silence scraper stdout/stderr (contains unicode symbols that can break on cp1252 consoles)
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                 CountyPropertyScraper(county=county, headless=True) as scraper:
                _enrich_scraper = scraper
                scraper.navigate_to_search()
                enrich_status['log'] += f'County rows scanned: live per-address lookup | matched: pending\n'

                for i, orig_addr in enumerate(clean_addresses, 1):
                    if getattr(scraper, '_stop', False):
                        enrich_status['log'] += '\n--- STOPPED BY USER ---\n'
                        break
                    enrich_status['current'] = orig_addr
                    ptype = scraper.lookup_property_type(orig_addr)
                    now_iso = datetime.now().isoformat()
                    conn.execute(
                        'INSERT OR REPLACE INTO property_type_cache (address, property_type, looked_up_at) VALUES (?, ?, ?)',
                        (orig_addr, ptype, now_iso)
                    )
                    conn.commit()
                    writer.writerow([now_iso, orig_addr, ptype, 'county_live'])
                    f.flush()
                    enrich_status['done'] = i
                    enrich_status['log'] += f'[{i}/{len(clean_addresses)}] {orig_addr}  ->  {ptype}\n'

            if enrich_status['done'] == 0:
                enrich_status['log'] += 'No live county matches found; trying latest county CSV backfill...\n'
                backfill = backfill_property_types_from_county_csv(county, clean_addresses)
                enrich_status['log'] += f"Backfill checked: {backfill.get('checked', 0)} | updated: {backfill.get('updated', 0)}\n"
                enrich_status['done'] = backfill.get('updated', 0)
                enrich_status['current'] = ''
    except Exception as e:
        enrich_status['log'] += f'\n--- ERROR: {e} ---\n'
    finally:
        conn.close()
        _enrich_scraper = None

    enrich_status['running'] = False
    enrich_status['log'] += f'\n--- Done. {enrich_status["done"]}/{enrich_status["total"]} addresses enriched. ---\n'
    if enrich_status.get('csv_file'):
        enrich_status['log'] += f'\n--- CSV saved incrementally: {enrich_status["csv_file"]} ---\n'

def build_leads_csv(leads):
    """Build a CSV string from a list of lead dicts."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Owner Name', 'County', 'Address', 'Price', 'Sold Date', 'Agent Phone'])
    for lead in leads:
        writer.writerow([
            lead.get('ownerName', ''),
            lead.get('county', ''),
            lead.get('address', ''),
            lead.get('price', ''),
            lead.get('soldDate', ''),
            lead.get('agentPhone', ''),
        ])
    return output.getvalue()


def save_order(session_id, leads):
    """Save purchased leads to a CSV file in the orders directory."""
    csv_content = build_leads_csv(leads)
    filepath = os.path.join(ORDERS_DIR, f'order_{session_id}.csv')
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        f.write(csv_content)
    return filepath


class Handler(http.server.BaseHTTPRequestHandler):

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)

        # API: pipeline status
        if path == '/api/status':
            self._json_response(200, pipeline_status)
            return

        # API: motivated sellers status
        if path == '/api/motivated-status':
            self._json_response(200, motivated_status)
            return

        # API: property type enrichment status
        if path == '/api/enrich-status':
            self._json_response(200, enrich_status)
            return

        # API: property type cache (address -> type map)
        if path == '/api/property-types':
            try:
                _ensure_property_type_cache()
                conn = sqlite3.connect(DB_FILE)
                rows = conn.execute('SELECT address, property_type FROM property_type_cache').fetchall()
                conn.close()
                self._json_response(200, {r[0]: r[1] for r in rows})
            except Exception as e:
                self._json_response(500, {'error': str(e)})
            return

        # Serve front-end files
        if path == '/':
            path = '/index.html'

        file_path = os.path.normpath(os.path.join(FRONTEND_DIR, path.lstrip('/')))

        # Security: don't serve outside FRONTEND_DIR
        if not file_path.startswith(os.path.normpath(FRONTEND_DIR)):
            self.send_response(403)
            self.end_headers()
            return

        if os.path.isfile(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            content_type = MIME_TYPES.get(ext, 'application/octet-stream')

            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self._cors_headers()
            self.end_headers()

            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')

    def do_POST(self):
        if self.path == '/api/run':
            body = self._read_body()
            if pipeline_status['running']:
                self._json_response(200, {'error': 'Pipeline already running'})
            else:
                thread = threading.Thread(target=run_pipeline_thread, args=(body,), daemon=True)
                thread.start()
                self._json_response(200, {'status': 'started'})

        elif self.path == '/api/kill':
            killed = kill_pipeline()
            self._json_response(200, {'killed': killed})

        elif self.path == '/api/motivated-run':
            body = self._read_body()
            if motivated_status['running']:
                self._json_response(200, {'error': 'Already running'})
            else:
                thread = threading.Thread(target=run_motivated_thread, args=(body,), daemon=True)
                thread.start()
                self._json_response(200, {'status': 'started'})

        elif self.path == '/api/motivated-kill':
            killed = kill_motivated()
            self._json_response(200, {'killed': killed})

        elif self.path == '/api/enrich':
            body = self._read_body()
            addresses = body.get('addresses', [])
            if enrich_status['running']:
                self._json_response(200, {'error': 'Enrichment already running'})
            elif not addresses:
                self._json_response(400, {'error': 'No addresses provided'})
            else:
                thread = threading.Thread(target=run_enrich_thread, args=(addresses,), daemon=True)
                thread.start()
                self._json_response(200, {'status': 'started', 'total': len(addresses)})

        elif self.path == '/api/enrich-county-backfill':
            body = self._read_body()
            county = (body.get('county') or '').strip()
            addresses = body.get('addresses', [])
            if not county:
                self._json_response(400, {'error': 'No county provided'})
            elif not addresses:
                self._json_response(400, {'error': 'No addresses provided'})
            else:
                try:
                    data = backfill_property_types_from_county_csv(county, addresses)
                    self._json_response(200, data)
                except Exception as e:
                    self._json_response(500, {'error': str(e)})

        elif self.path == '/api/enrich-county-true':
            body = self._read_body()
            county = (body.get('county') or '').strip()
            addresses = body.get('addresses', [])
            days_back = int(body.get('days_back', 120))
            if enrich_status['running']:
                self._json_response(200, {'error': 'Enrichment already running'})
            elif not county:
                self._json_response(400, {'error': 'No county provided'})
            elif not addresses:
                self._json_response(400, {'error': 'No addresses provided'})
            else:
                thread = threading.Thread(target=run_true_county_thread, args=(county, addresses, days_back), daemon=True)
                thread.start()
                self._json_response(200, {'status': 'started', 'total': len(addresses), 'mode': 'county_true', 'county': county})

        elif self.path == '/api/enrich-kill':
            if _enrich_scraper:
                _enrich_scraper.stop()
                enrich_status['log'] += '\n--- Kill signal sent ---\n'
                self._json_response(200, {'killed': True})
            else:
                self._json_response(200, {'killed': False})

        elif self.path == '/api/create-subscription-session':
            self._handle_create_subscription(self._read_body())

        else:
            self.send_response(404)
            self.end_headers()

    # ---- Stripe: Create Subscription Checkout Session ----
    def _handle_create_subscription(self, body):
        if not STRIPE_AVAILABLE:
            self._json_response(500, {'error': 'Stripe is not installed. Run: pip install stripe'})
            return

        if not STRIPE_SECRET_KEY:
            self._json_response(500, {'error': 'STRIPE_SECRET_KEY environment variable is not set'})
            return

        host = self.headers.get('Host', f'localhost:{PORT}')
        base_url = f'http://{host}'

        try:
            if STRIPE_PRICE_ID:
                # Use a pre-created recurring Price from the Stripe dashboard (preferred)
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{'price': STRIPE_PRICE_ID, 'quantity': 1}],
                    mode='subscription',
                    success_url=f'{base_url}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{base_url}/storefront.html',
                )
            else:
                # Fallback: create an inline recurring price on the fly
                session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'usd',
                            'product_data': {
                                'name': 'Nashville Metro Property Leads',
                                'description': 'All 7 counties â€” fresh daily leads, unlimited access',
                            },
                            'unit_amount': SUBSCRIPTION_PRICE_CENTS,
                            'recurring': {'interval': 'month'},
                        },
                        'quantity': 1,
                    }],
                    mode='subscription',
                    success_url=f'{base_url}/checkout-success.html?session_id={{CHECKOUT_SESSION_ID}}',
                    cancel_url=f'{base_url}/storefront.html',
                )

            self._json_response(200, {'url': session.url, 'session_id': session.id})

        except stripe.error.StripeError as e:
            self._json_response(500, {'error': str(e)})
        except Exception as e:
            self._json_response(500, {'error': str(e)})

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    # Export database to CSV on startup only if the CSV is missing or older than the DB
    db_file = os.path.join(PROJECT_ROOT, 'all_counties_leads.db')
    csv_file = os.path.join(FRONTEND_DIR, 'nashville_cash_leads_clean.csv')
    db_newer = (
        os.path.exists(db_file) and
        (not os.path.exists(csv_file) or os.path.getmtime(db_file) > os.path.getmtime(csv_file))
    )
    if db_newer:
        count = export_db_to_csv()
        if count:
            print(f"  Leads loaded from database: {count}")
    else:
        print(f"  Dashboard CSV is up to date â€” skipping database export")

    server = http.server.HTTPServer(('localhost', PORT), Handler)
    print(f"Server running at http://localhost:{PORT}")
    print(f"  Dashboard:   http://localhost:{PORT}/")
    print(f"  Storefront:  http://localhost:{PORT}/storefront.html")
    print(f"  Admin:       http://localhost:{PORT}/admin.html")
    print(f"  Serving:     {FRONTEND_DIR}")
    if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
        print(f"  Stripe:      CONFIGURED")
    else:
        print(f"  Stripe:      NOT CONFIGURED â€” set STRIPE_SECRET_KEY env var")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()

