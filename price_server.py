#!/usr/bin/env python3
"""
FinTrack Price Server
Fetches real prices from Yahoo Finance every 60 seconds and serves them
to portfolio_tracker.html at http://localhost:5001/api/prices

Usage:
    python3 price_server.py

Keep this running in the background while you use the tracker.
"""

import threading
import time
import json
import sys
import subprocess
from datetime import datetime

# ── auto-install ──────────────────────────────────────────────────────────────

def install(pkg):
    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

try:
    import yfinance as yf
except ImportError:
    print("Installing yfinance..."); install("yfinance"); import yfinance as yf

try:
    from flask import Flask, jsonify
except ImportError:
    print("Installing flask..."); install("flask"); from flask import Flask, jsonify

# ── config ────────────────────────────────────────────────────────────────────

PORT            = 5001
REFRESH_SECONDS = 60   # how often to re-fetch from Yahoo Finance

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
    "THYAO": ("THYAO.IS", True),
    "EKDMR": ("EKDMR.IS", True),
}

FX_TICKERS = {
    "USDTRY=X": ("TRY", False),
    "USDJPY=X": ("JPY", False),
    "EURUSD=X": ("EUR", True),
    "GBPUSD=X": ("GBP", True),
}

# ── shared state ──────────────────────────────────────────────────────────────

cache = {
    "prices":     {},    # ticker → USD price
    "fx":         {"USD":1,"EUR":0.9077,"GBP":0.7566,"JPY":159.3,"TRY":50.42},
    "updated_at": None,
    "status":     "starting",
    "errors":     [],
}
cache_lock = threading.Lock()

# ── fetch logic ───────────────────────────────────────────────────────────────

def get_price(yf_sym):
    try:
        t = yf.Ticker(yf_sym)
        # fast_info is quickest; fall back to history if needed
        p = t.fast_info.get("lastPrice") or t.fast_info.get("last_price")
        if p:
            return float(p)
        hist = t.history(period="2d", interval="1d", auto_adjust=True)
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception as e:
        return None
    return None


def fetch_all():
    prices = {}
    fx     = {"USD": 1}
    errors = []

    # FX rates
    for sym, (key, invert) in FX_TICKERS.items():
        p = get_price(sym)
        if p:
            fx[key] = round(1/p if invert else p, 4)
        else:
            errors.append(f"FX:{key}")

    try_rate = fx.get("TRY", 50.42)

    # Stock prices
    for ticker, (yf_sym, is_try) in STOCKS.items():
        p = get_price(yf_sym)
        if p is not None:
            usd_price = p / try_rate if is_try else p
            prices[ticker] = round(usd_price, 4)
        else:
            errors.append(ticker)

    return prices, fx, errors


def refresh_loop():
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching prices...", flush=True)
        prices, fx, errors = fetch_all()

        with cache_lock:
            cache["prices"]     = prices
            cache["fx"]         = fx
            cache["updated_at"] = datetime.now().isoformat()
            cache["status"]     = "ok" if not errors else "partial"
            cache["errors"]     = errors

        ok = len(prices)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Done — {ok}/{len(STOCKS)} stocks"
              + (f", skipped: {errors}" if errors else ""), flush=True)

        time.sleep(REFRESH_SECONDS)

# ── Flask app ─────────────────────────────────────────────────────────────────

app = Flask(__name__)

@app.after_request
def cors(resp):
    # Allow the HTML file (file://) to call this server
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/api/prices")
def api_prices():
    with cache_lock:
        return jsonify({
            "prices":     cache["prices"],
            "fx":         cache["fx"],
            "updated_at": cache["updated_at"],
            "status":     cache["status"],
            "errors":     cache["errors"],
        })

@app.route("/health")
def health():
    with cache_lock:
        return jsonify({"ok": True, "updated_at": cache["updated_at"]})

# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║      FinTrack Price Server            ║")
    print(f"║      http://localhost:{PORT}            ║")
    print(f"║      Refreshes every {REFRESH_SECONDS}s              ║")
    print("╚══════════════════════════════════════╝")
    print()

    # Fetch once immediately in a background thread before server starts
    t = threading.Thread(target=refresh_loop, daemon=True)
    t.start()

    # Give the first fetch a head-start before Flask starts logging
    time.sleep(1)

    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
