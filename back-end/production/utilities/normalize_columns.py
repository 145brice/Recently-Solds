"""
Column Normalization Utility
=============================
Maps any county scraper's output to the front-end's expected schema.
"""

import pandas as pd
from datetime import datetime


def normalize_to_frontend_schema(df, county_name):
    """
    Normalize a scraper DataFrame to the front-end's 6-column schema:
    Owner Name, County, Address, Price, Sold Date, Agent Phone

    Args:
        df: pandas DataFrame from any county scraper
        county_name: string like 'Davidson', 'Wilson', etc.

    Returns:
        pandas DataFrame with exactly 6 columns
    """
    if df.empty:
        return pd.DataFrame(columns=[
            'Owner Name', 'County', 'Address', 'Price', 'Sold Date', 'Agent Phone'
        ])

    normalized = pd.DataFrame(index=df.index)

    # --- Owner Name ---
    owner_col = _find_column(df, ['owner_name', 'Owner Name', 'owner', 'Owner'])
    normalized['Owner Name'] = df[owner_col].fillna('N/A').astype(str) if owner_col else 'N/A'

    # --- County ---
    normalized['County'] = county_name

    # --- Address ---
    addr_col = _find_column(df, ['address', 'Address', 'property_address', 'Property Address'])
    city_col = _find_column(df, ['city', 'City'])

    if addr_col:
        addresses = df[addr_col].fillna('').astype(str)
        if city_col:
            cities = df[city_col].fillna('').astype(str)
            # Only append city if it's not already in the address
            normalized['Address'] = addresses.combine(cities, lambda a, c:
                f"{a}, {c}, TN" if c and c.lower() not in a.lower() else a
            )
        else:
            normalized['Address'] = addresses
    else:
        normalized['Address'] = 'N/A'

    # --- Price ---
    # Prefer the clean numeric column for formatting, fall back to raw string
    price_clean_col = _find_column(df, ['sale_price_clean', 'total_value_clean', 'total_assessed_clean'])
    price_raw_col = _find_column(df, ['sale_price', 'Sale Price', 'Amount', 'price', 'Price'])

    if price_clean_col:
        normalized['Price'] = df[price_clean_col].apply(_format_price)
    elif price_raw_col:
        normalized['Price'] = df[price_raw_col].apply(_format_price)
    else:
        normalized['Price'] = 'N/A'

    # --- Sold Date ---
    date_col = _find_column(df, ['sale_date', 'Sale Date', 'Date', 'sold_date', 'Sold Date', 'sale_date_parsed'])
    if date_col:
        normalized['Sold Date'] = df[date_col].apply(_format_date)
    else:
        normalized['Sold Date'] = 'N/A'

    # --- Agent Phone ---
    normalized['Agent Phone'] = 'N/A'

    return normalized


def _find_column(df, candidates):
    """Find the first matching column name from a list of candidates."""
    for col in candidates:
        if col in df.columns:
            return col
    # Case-insensitive fallback
    df_cols_lower = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in df_cols_lower:
            return df_cols_lower[col.lower()]
    return None


def _format_price(value):
    """Format a price value as $X,XXX string."""
    if pd.isna(value) or value == '' or value == 'N/A':
        return 'N/A'
    try:
        num = float(str(value).replace('$', '').replace(',', '').strip())
        if num <= 0:
            return 'N/A'
        return f"${num:,.0f}"
    except (ValueError, TypeError):
        return str(value) if value else 'N/A'


def _format_date(value):
    """Format a date value as MM/DD/YYYY string."""
    if pd.isna(value) or value == '' or value == 'N/A':
        return 'N/A'

    # Already a datetime object
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.strftime('%m/%d/%Y')

    # String parsing - try common formats
    date_str = str(value).strip()
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y', '%Y-%m-%d %H:%M:%S', '%B %d, %Y']:
        try:
            return datetime.strptime(date_str, fmt).strftime('%m/%d/%Y')
        except ValueError:
            continue

    return date_str  # Return as-is if no format matches
