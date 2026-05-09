"""
Google Snippet Property Type Scraper
===================================
Searches Google only and classifies property type from search snippets/meta text.
It does NOT open Zillow/Redfin (or any result pages).

Query format used for each address:
    "<address>" (single family OR duplex OR triplex OR fourplex OR "multi family" OR multifamily)
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import os
import random
import re
import time
import urllib.parse
import urllib.request
from typing import Iterable, List, Dict

logger = logging.getLogger(__name__)

MULTI_PATTERNS = [
    (re.compile(r"\bfour[\s-]?plex\b|\b4[\s-]?unit\b|\b4[\s-]?family\b", re.I), "4-Unit"),
    (re.compile(r"\btriplex\b|\b3[\s-]?unit\b|\b3[\s-]?family\b", re.I), "Triplex"),
    (re.compile(r"\bduplex\b|\b2[\s-]?unit\b|\b2[\s-]?family\b", re.I), "Duplex"),
    (re.compile(r"\bmulti[\s-]?family\b|\bmultifamily\b|\bapartment\b|\bapartments\b", re.I), "Multi Family"),
]
SINGLE_PATTERN = re.compile(r"\bsingle[\s-]?family\b|\bsfh\b", re.I)
CONDO_PATTERN = re.compile(r"\bcondo(?:minium)?\b|\bco[- ]?op\b", re.I)
TOWNHOUSE_PATTERN = re.compile(r"\btown\s?house\b|\btownhome\b", re.I)
LAND_PATTERN = re.compile(r"\bvacant land\b|\bresidential lot\b|\blot/land\b|\braw land\b|\bunimproved\b", re.I)
MOBILE_PATTERN = re.compile(r"\bmobile home\b|\bmanufactured home\b", re.I)
COMMERCIAL_PATTERN = re.compile(r"\bcommercial\b|\boffice\b|\bretail\b|\bindustrial\b", re.I)
RESIDENTIAL_PATTERN = re.compile(r"\bresidential\b|\buse description[:\s]+res\b|\bpt[:\s]+res\b", re.I)


class PropertyTypeScraper:
    """
    Backward-compatible class used by server.py for Type Admin enrichment.
    """

    def __init__(self, headless: bool = True, min_delay: float = 5.0, max_delay: float = 8.0):
        self._stop = False
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.headless = headless
        self._driver = None
        self._ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )

    def stop(self):
        self._stop = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return None

    def close(self):
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
        return None

    def lookup(self, address: str, delay: float | None = None, county: str | None = None) -> str:
        """
        Run one Google search and classify using only snippets/meta text.
        """
        if self._stop:
            return "Stopped"

        detected = "Unknown"
        for query in build_query_candidates(address, county=county):
            snippet_text = self._google_snippet_text(query)
            detected = classify_property_type(snippet_text)
            if detected != "Unknown":
                break

        pause = random.uniform(self.min_delay, self.max_delay) if delay is None else delay
        if pause > 0:
            time.sleep(pause)

        return detected

    def lookup_with_meta(self, address: str, delay: float | None = None, county: str | None = None) -> Dict[str, str]:
        """
        Run one Google search and return both detected type and best address
        parsed from Google search metadata/snippets.
        """
        if self._stop:
            return {"property_type": "Stopped", "meta_address": "", "query": ""}

        detected = "Unknown"
        matched_address = ""
        used_query = ""
        for query in build_query_candidates(address, county=county):
            search_data = self._google_search_data(query)
            snippet_text = search_data.get("snippet_text", "")
            meta_addr = search_data.get("meta_address", "")
            if meta_addr and not matched_address:
                matched_address = meta_addr
                used_query = query
            detected = classify_property_type(snippet_text)
            if detected != "Unknown":
                if not used_query:
                    used_query = query
                break

        pause = random.uniform(self.min_delay, self.max_delay) if delay is None else delay
        if pause > 0:
            time.sleep(pause)

        return {"property_type": detected, "meta_address": matched_address, "query": used_query}

    def lookup_many(self, addresses: Iterable[str]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        for address in addresses:
            if self._stop:
                break
            ptype = self.lookup(address)
            results.append({"address": address, "property_type": ptype})
        return results

    def _google_snippet_text(self, query: str) -> str:
        """
        Fetch Google search HTML and extract result snippets only.
        Does not request result URLs.
        """
        params = {"q": query, "hl": "en", "num": "10", "pws": "0"}
        url = "https://www.google.com/search?" + urllib.parse.urlencode(params)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self._ua,
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            logger.debug('Google lookup failed for query "%s": %s', query, exc)
            return self._google_snippet_text_browser(query)

        text_chunks = extract_google_snippets(raw)
        snippet_text = " ".join(text_chunks)
        return snippet_text or self._google_snippet_text_browser(query)

    def _google_search_data(self, query: str) -> Dict[str, str]:
        """
        Fetch Google HTML once and return snippet text plus the best address-like
        string found in Google metadata/snippets.
        """
        params = {"q": query, "hl": "en", "num": "10", "pws": "0"}
        url = "https://www.google.com/search?" + urllib.parse.urlencode(params)

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self._ua,
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "no-cache",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
        except Exception as exc:
            logger.debug('Google lookup failed for query "%s": %s', query, exc)
            return self._google_search_data_browser(query)

        text_chunks = extract_google_snippets(raw)
        if not text_chunks:
            return self._google_search_data_browser(query)
        return {
            "snippet_text": " ".join(text_chunks),
            "meta_address": best_address_from_chunks(text_chunks),
        }

    def _get_browser_driver(self):
        if self._driver:
            return self._driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception as exc:
            logger.debug("Selenium Google fallback unavailable: %s", exc)
            return None

        opts = Options()
        if self.headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1600,1200")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_argument(f"user-agent={self._ua}")
        try:
            self._driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        except Exception as exc:
            logger.debug("Could not start Selenium Google fallback: %s", exc)
            self._driver = None
        return self._driver

    def _google_search_data_browser(self, query: str) -> Dict[str, str]:
        driver = self._get_browser_driver()
        if not driver:
            return {"snippet_text": "", "meta_address": ""}
        try:
            params = {"q": query, "hl": "en", "num": "10", "pws": "0"}
            driver.get("https://www.google.com/search?" + urllib.parse.urlencode(params))
            time.sleep(2.0)
            page_text = ""
            try:
                page_text = driver.find_element("tag name", "body").text
            except Exception:
                pass
            chunks = extract_google_snippets(driver.page_source)
            if page_text:
                chunks.insert(0, page_text)
            return {
                "snippet_text": " ".join(chunks),
                "meta_address": best_address_from_chunks(chunks),
            }
        except Exception as exc:
            logger.debug('Browser Google lookup failed for query "%s": %s', query, exc)
            return {"snippet_text": "", "meta_address": ""}

    def _google_snippet_text_browser(self, query: str) -> str:
        return self._google_search_data_browser(query).get("snippet_text", "")


def build_query(address: str) -> str:
    cleaned = normalize_address_for_google(address)
    return f"{cleaned} property type"


def build_query_candidates(address: str, county: str | None = None) -> List[str]:
    """
    Generate Google queries that match a normal manual search first.
    """
    base = normalize_address_for_google(address)
    flipped = flip_street_number_order(base)
    with_state = ensure_state_suffix(base)
    flipped_with_state = ensure_state_suffix(flipped)

    county_name = simple_county_name(county)
    variants = []
    for v in [base, flipped, with_state, flipped_with_state]:
        if v and v not in variants:
            variants.append(v)

    queries = []
    for v in variants:
        if county_name:
            queries.append(f"{county_name} {v} property type")
        queries.append(f"{v} property type")
    for v in variants:
        queries.append(f"{v} single family duplex triplex multifamily property type")
    return dedupe_keep_order(queries)


def dedupe_keep_order(values: List[str]) -> List[str]:
    out = []
    seen = set()
    for value in values:
        key = re.sub(r"\s+", " ", value or "").strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def simple_county_name(county: str | None) -> str:
    c = (county or "").strip()
    c = re.sub(r"\s+county\b", "", c, flags=re.I)
    c = re.sub(r",\s*[A-Z]{2}\b", "", c)
    return c.strip()


def normalize_address_for_google(address: str) -> str:
    a = (address or "").strip()
    a = re.sub(r"\(\d+\)", "", a)
    a = re.sub(r"\bUnincorporated\b", "", a, flags=re.I)
    a = re.sub(r"\s*,\s*", ", ", a)
    a = re.sub(r"\s{2,}", " ", a)
    a = re.sub(r",\s*,", ", ", a)
    a = a.strip(" ,")
    return a


def flip_street_number_order(address: str) -> str:
    """
    Convert 'STREET NAME 123' to '123 STREET NAME' for better map/listing match.
    Keeps city/state suffix if present.
    """
    if not address:
        return address
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if not parts:
        return address
    street = parts[0]
    m = re.match(r"^(.+?)\s+(\d+[A-Za-z\-]*)$", street)
    if not m:
        return address
    flipped_street = f"{m.group(2)} {m.group(1)}"
    rest = ", ".join(parts[1:])
    return f"{flipped_street}, {rest}" if rest else flipped_street


def ensure_state_suffix(address: str) -> str:
    """
    If no US state token is present, append TN as local fallback.
    """
    if not address:
        return address
    if re.search(r"\b[A-Z]{2}\b$", address):
        return address
    return f"{address}, TN"


def county_context_suffix(county: str | None) -> str:
    c = (county or "").strip()
    if not c:
        return ""
    if not re.search(r"county$", c, flags=re.I):
        c = f"{c} County"
    return f"\"{c}, TN\""


def extract_google_snippets(page_html: str) -> List[str]:
    """
    Parse likely Google snippet/meta containers from search HTML.
    """
    chunks: List[str] = []
    patterns = [
        # Common snippet containers
        r'<div class="VwiC3b[^"]*"[^>]*>(.*?)</div>',
        r'<span class="aCOpRe[^"]*"[^>]*>(.*?)</span>',
        # Result title text
        r'<h3[^>]*>(.*?)</h3>',
        # Common result-block containers (fallback)
        r'<div class="[^"]*yXK7lf[^"]*"[^>]*>(.*?)</div>',
        r'<div class="[^"]*MjjYud[^"]*"[^>]*>(.*?)</div>',
        # Meta description fallback
        r'<meta name="description" content="(.*?)"',
    ]
    for pat in patterns:
        for m in re.findall(pat, page_html, flags=re.I | re.S):
            txt = clean_html_text(m)
            if txt:
                chunks.append(txt)
    body = re.search(r"<body[^>]*>(.*?)</body>", page_html, flags=re.I | re.S)
    if body:
        fallback_text = clean_html_text(body.group(1))
        if fallback_text:
            chunks.append(fallback_text[:20000])
    return chunks


def clean_html_text(raw: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", raw)
    txt = html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


ADDRESS_PATTERNS = [
    re.compile(
        r"\b\d{1,6}\s+[A-Za-z0-9.\-#' ]+?\s(?:ST|STREET|AVE|AVENUE|RD|ROAD|DR|DRIVE|LN|LANE|BLVD|BOULEVARD|CT|COURT|PL|PLACE|PKWY|PARKWAY|TRL|TRAIL|WAY|CIR|CIRCLE)\b(?:,\s*[A-Za-z.\- ]+)?(?:,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?)?",
        re.I,
    ),
    re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.\-#' ]+?,\s*[A-Za-z.\- ]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?\b", re.I),
]


def _clean_address_candidate(text: str) -> str:
    s = re.sub(r"\s+", " ", (text or "")).strip(" ,.-|")
    # Trim obvious non-address tails from snippets.
    s = re.split(r"\s+(?:for sale|sold|zillow|redfin|realtor|trulia|mls)\b", s, flags=re.I)[0].strip(" ,.-|")
    return s


def best_address_from_chunks(chunks: List[str]) -> str:
    """
    Prefer the most complete address found in Google result metadata/snippets.
    """
    best = ""
    best_score = -1
    for chunk in chunks:
        txt = clean_html_text(chunk)
        if not txt:
            continue
        for pat in ADDRESS_PATTERNS:
            for m in pat.finditer(txt):
                cand = _clean_address_candidate(m.group(0))
                if not cand:
                    continue
                score = len(cand)
                if re.search(r"\b[A-Z]{2}\s*\d{5}(?:-\d{4})?\b", cand, flags=re.I):
                    score += 25
                if "," in cand:
                    score += 10
                if score > best_score:
                    best = cand
                    best_score = score
    return best


def classify_property_type(snippet_text: str) -> str:
    if not snippet_text:
        return "Unknown"

    for pattern, label in MULTI_PATTERNS:
        if pattern.search(snippet_text):
            return label

    if TOWNHOUSE_PATTERN.search(snippet_text):
        return "Townhouse"

    if CONDO_PATTERN.search(snippet_text):
        return "Condo"

    if MOBILE_PATTERN.search(snippet_text):
        return "Mobile Home"

    if LAND_PATTERN.search(snippet_text):
        return "Land"

    if COMMERCIAL_PATTERN.search(snippet_text):
        return "Commercial"

    if SINGLE_PATTERN.search(snippet_text):
        return "Single Family"

    if RESIDENTIAL_PATTERN.search(snippet_text):
        return "Single Family"

    return "Unknown"


def load_addresses(path: str) -> List[str]:
    """
    Supports:
    - .txt (one address per line)
    - .csv (column: address or Address)
    - .json (array of strings or objects with address)
    """
    lower = path.lower()
    if lower.endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]

    if lower.endswith(".csv"):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        addrs = []
        for r in rows:
            addr = (r.get("address") or r.get("Address") or "").strip()
            if addr:
                addrs.append(addr)
        return addrs

    if lower.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            out = []
            for item in data:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip())
                elif isinstance(item, dict):
                    addr = str(item.get("address") or item.get("Address") or "").strip()
                    if addr:
                        out.append(addr)
            return out
    raise ValueError(f"Unsupported input format: {path}")


def save_results_csv(path: str, rows: List[Dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["address", "property_type"])
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Google snippet property-type classifier.")
    default_input = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "Property-Managers--Front-End", "nashville_cash_leads_clean.csv")
    )
    parser.add_argument(
        "--input",
        default=default_input,
        help="Input .txt/.csv/.json with addresses (defaults to shared frontend leads CSV)",
    )
    parser.add_argument("--output", default="property_types_google.csv", help="Output CSV path")
    parser.add_argument("--min-delay", type=float, default=5.0, help="Min seconds between searches")
    parser.add_argument("--max-delay", type=float, default=8.0, help="Max seconds between searches")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    addresses = load_addresses(args.input)
    logger.info("Loaded %s addresses", len(addresses))

    scraper = PropertyTypeScraper(min_delay=args.min_delay, max_delay=args.max_delay)
    rows = scraper.lookup_many(addresses)
    save_results_csv(args.output, rows)

    logger.info("Saved %s rows to %s", len(rows), args.output)
    for row in rows[:10]:
        logger.info("%s -> %s", row["address"], row["property_type"])


if __name__ == "__main__":
    main()
