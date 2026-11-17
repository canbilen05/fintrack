#!/usr/bin/env python3
"""
FinTrack Price Updater
Pulls today's closing prices from Yahoo Finance (yfinance) and rewrites
portfolio_tracker.html with real prices + current FX rates.

Run once daily after market close (~22:00 Istanbul time for US stocks,
~18:30 Istanbul time for BIST stocks).

Usage:
    python3 update_prices.py
"""

import re
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# ── config ────────────────────────────────────────────────────────────────────

HTML_FILE = Path.home() / "Desktop" / "portfolio_tracker.html"

# ticker → (Yahoo Finance symbol, is TRY-denominated)
STOCKS = {
    "MSFT":  ("MSFT",     False),
    "META":  ("META",     False),
    "GOOG":  ("GOOG",     False),
    "NVDA":  ("NVDA",     False),
    "QCOM":  ("QCOM",     False),
    "AMD":   ("AMD",      False),
    "TSM":   ("TSM",      False),
    "AMZN":  ("AMZN",     False),
    "AAPL":  ("AAPL",     False),
    "CSCO":  ("CSCO",     False),
    "ASML":  ("ASML",     False),
    "AVGO":  ("AVGO",     False),
    "AXP":   ("AXP",      False),
    "THYAO": ("THYAO.IS", True),   # Borsa Istanbul — price in TRY
    "EKDMR": ("EKDMR.IS", True),   # Borsa Istanbul — price in TRY
}

# Yahoo Finance FX tickers → key in const FX={...}
# USDTRY=X  → 1 USD = X TRY  (store directly)
# USDJPY=X  → 1 USD = X JPY  (store directly)
# EURUSD=X  → 1 EUR = X USD  → store inverted (USD per EUR)
# GBPUSD=X  → 1 GBP = X USD  → store inverted (USD per GBP)
FX_TICKERS = {
    "USDTRY=X": ("TRY", False),
    "USDJPY=X": ("JPY", False),
    "EURUSD=X": ("EUR", True),   # True = invert
    "GBPUSD=X": ("GBP", True),
}

# ── auto-install ──────────────────────────────────────────────────────────────

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yfinance", "-q"])
    import yfinance as yf

# ── fetch helpers ─────────────────────────────────────────────────────────────

def fetch_price(yf_symbol: str):
    """Return the most recent closing price for a Yahoo Finance ticker."""
    try:
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period="2d", interval="1d", auto_adjust=True)
        if hist.empty:
            return None
        return float(hist["Close"].iloc[-1])
    except Exception as exc:
        print(f"    ✗ {yf_symbol} — {exc}")
        return None

# ── HTML patch helpers ────────────────────────────────────────────────────────

def patch_stock_price(html: str, ticker: str, price: float,
                      is_try: bool, try_rate: float) -> str:
    if is_try:
        pattern     = rf"(t:'{re.escape(ticker)}'[^}}]*\bb:)[\d.]+/[\d.]+"
        replacement = rf"\g<1>{price:.2f}/{try_rate:.2f}"
    else:
        pattern     = rf"(t:'{re.escape(ticker)}'[^}}]*\bb:)[\d.]+"
        replacement = rf"\g<1>{price:.2f}"
    new_html, n = re.subn(pattern, replacement, html)
    if n == 0:
        print(f"    ✗ Could not locate b: for {ticker} in HTML")
    return new_html


def patch_fx_object(html: str, rates: dict) -> str:
    """Update const FX={USD:1,EUR:...,GBP:...,JPY:...,TRY:...}"""
    for key, value in rates.items():
        pattern = rf"({re.escape(key)}:)[\d.]+"
        html, _ = re.subn(pattern, rf"\g<1>{value:.4f}", html)
    return html


def patch_fx_display(html: str, rates: dict) -> str:
    """Update the human-readable FX info box in the Summary tab."""
    eur  = rates.get("EUR",  0)
    gbp  = rates.get("GBP",  0)
    jpy  = rates.get("JPY",  0)
    try_ = rates.get("TRY",  0)
    if not all([eur, gbp, jpy, try_]):
        return html
    pattern = (r'(<strong[^>]*>FX Rates</strong>[^·]*·\s*EUR\s*)[\d.]+'
               r'(\s*·\s*GBP\s*)[\d.]+'
               r'(\s*·\s*JPY\s*)[\d.]+'
               r'(\s*·\s*TRY\s*)[\d.]+')
    repl = (rf'\g<1>{eur:.4f}'
            rf'\g<2>{gbp:.4f}'
            rf'\g<3>{jpy:.4f}'
            rf'\g<4>{try_:.4f}')
    html, _ = re.subn(pattern, repl, html)
    html = re.sub(r'₺[\d.]+\s*=\s*\$1',    f'₺{try_:.2f} = $1',  html)
    html = re.sub(r'converted at ₺[\d.]+',  f'converted at ₺{try_:.2f}', html)
    return html

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    if not HTML_FILE.exists():
        print(f"ERROR: {HTML_FILE} not found.")
        sys.exit(1)

    print()
    print("╔══════════════════════════════════════╗")
    print("║      FinTrack Price Updater           ║")
    print(f"║      {datetime.now().strftime('%Y-%m-%d  %H:%M')}                  ║")
    print("╚══════════════════════════════════════╝")

    html = HTML_FILE.read_text(encoding="utf-8")

    # ── 1. FX rates ────────────────────────────────────────────────────────────
    print("\n── FX rates ──────────────────────────────")
    fx_rates = {}

    for yf_sym, (key, invert) in FX_TICKERS.items():
        price = fetch_price(yf_sym)
        if price is None:
            print(f"  {key:<4}  SKIPPED")
            continue
        stored = round(1 / price, 4) if invert else round(price, 4)
        fx_rates[key] = stored
        print(f"  {key:<4}  {stored:.4f}  (1 USD = {price:.4f} {key} raw)" if not invert
              else f"  {key:<4}  {stored:.4f}  (1 USD = {1/price:.4f} {key})")

    if fx_rates:
        html = patch_fx_object(html, fx_rates)
        html = patch_fx_display(html, fx_rates)

    try_rate = fx_rates.get("TRY", 50.42)

    # ── 2. Stock prices ────────────────────────────────────────────────────────
    print("\n── Stock prices ──────────────────────────")
    ok = 0
    for ticker, (yf_sym, is_try) in STOCKS.items():
        label = f"{yf_sym:<10}"
        print(f"  {label}", end="  ", flush=True)
        price = fetch_price(yf_sym)
        if price is None:
            print("SKIPPED")
            continue
        html = patch_stock_price(html, ticker, price, is_try, try_rate)
        if is_try:
            print(f"₺{price:>10,.2f}  →  ${price/try_rate:.2f}")
        else:
            print(f"${price:>10,.2f}")
        ok += 1

    # ── 3. Save ────────────────────────────────────────────────────────────────
    HTML_FILE.write_text(html, encoding="utf-8")

    total = len(STOCKS) + len(FX_TICKERS)
    print()
    print("─" * 44)
    print(f"✓  {ok + len(fx_rates)}/{total} values updated → {HTML_FILE.name}")
    print(f"   Open the file in your browser to see real prices.")
    print()


if __name__ == "__main__":
    main()
