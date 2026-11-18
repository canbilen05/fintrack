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
import re
import sys
import subprocess
from datetime import datetime, timezone

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

try:
    import feedparser
except ImportError:
    print("Installing feedparser..."); install("feedparser"); import feedparser

# ── config ────────────────────────────────────────────────────────────────────

PORT              = 5001
REFRESH_SECONDS   = 60   # stock price refresh interval
NEWS_REFRESH_SECS = 120  # news refresh interval (2 min)

NEWS_FEEDS = [
    {
        "url":    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT,META,GOOG,NVDA,QCOM,AMD,TSM,AMZN,AAPL,CSCO,ASML,AVGO,AXP&region=US&lang=en-US",
        "source": "Yahoo Finance",
    },
    {
        "url":    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "source": "CNBC",
    },
    {
        "url":    "https://www.investing.com/rss/news.rss",
        "source": "Investing.com",
    },
]

CATEGORY_RULES = [
    ("Crypto",   r"bitcoin|crypto|btc|ethereum|eth|blockchain|coinbase"),
    ("Earnings", r"earnings|revenue|profit|quarterly|q[1-4] |beat|miss|eps"),
    ("FX",       r"dollar|euro|yen|lira|sterling|currency|forex|fx|usd|eur|gbp|try|jpy"),
    ("Economy",  r"fed|federal reserve|gdp|inflation|rate cut|rate hike|jobs|unemployment|imf|ecb|tcmb"),
    ("Tech",     r"nvidia|apple|microsoft|google|meta|amazon|amd|tsmc|asml|broadcom|qualcomm|cisco|ai|chip|semiconductor|cloud"),
    ("Markets",  r"s&p|nasdaq|dow|stock|rally|market|bull|bear|index|ipo|shares"),
]

GRADIENT_PALETTES = [
    "linear-gradient(135deg,#1E3A8A,#7C3AED)",
    "linear-gradient(135deg,#065F46,#059669)",
    "linear-gradient(135deg,#7C2D12,#DC2626)",
    "linear-gradient(135deg,#1E3A8A,#0369A1)",
    "linear-gradient(135deg,#4A1D96,#7C3AED)",
    "linear-gradient(135deg,#052e16,#15803D)",
    "linear-gradient(135deg,#1E3A8A,#2563EB)",
    "linear-gradient(135deg,#78350F,#D97706)",
]

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
    "prices":     {},
    "fx":         {"USD":1,"EUR":0.9077,"GBP":0.7566,"JPY":159.3,"TRY":50.42},
    "updated_at": None,
    "status":     "starting",
    "errors":     [],
    "news":       [],
    "news_updated_at": None,
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


# ── news helpers ──────────────────────────────────────────────────────────────

def categorise(title: str) -> str:
    t = title.lower()
    for cat, pattern in CATEGORY_RULES:
        if re.search(pattern, t):
            return cat
    return "Markets"


def time_ago(dt) -> str:
    if dt is None:
        return ""
    try:
        if hasattr(dt, "timetuple"):
            import calendar
            ts = calendar.timegm(dt.timetuple())
            diff = int(time.time()) - ts
        else:
            return ""
        if diff < 60:
            return "just now"
        if diff < 3600:
            m = diff // 60
            return f"{m}m ago"
        if diff < 86400:
            h = diff // 3600
            return f"{h}h ago"
        d = diff // 86400
        return f"{d}d ago"
    except Exception:
        return ""


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_news():
    articles = []
    seen = set()

    for feed_cfg in NEWS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries[:15]:
                title = strip_html(entry.get("title", "")).strip()
                if not title or title.lower() in seen:
                    continue
                seen.add(title.lower())
                summary = strip_html(entry.get("summary", entry.get("description", "")))
                summary = summary[:200] + "…" if len(summary) > 200 else summary
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                articles.append({
                    "title":     title,
                    "summary":   summary,
                    "url":       entry.get("link", ""),
                    "source":    feed_cfg["source"],
                    "category":  categorise(title),
                    "time_ago":  time_ago(published),
                    "gradient":  GRADIENT_PALETTES[len(articles) % len(GRADIENT_PALETTES)],
                })
        except Exception as e:
            print(f"  News feed error ({feed_cfg['source']}): {e}", flush=True)

    # Sort by recency — articles with "just now" or short "Xm ago" first
    articles.sort(key=lambda a: a["time_ago"])
    return articles[:30]


def news_loop():
    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fetching news...", flush=True)
        articles = fetch_news()
        with cache_lock:
            cache["news"] = articles
            cache["news_updated_at"] = datetime.now().isoformat()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] News — {len(articles)} articles", flush=True)
        time.sleep(NEWS_REFRESH_SECS)

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

@app.route("/api/news")
def api_news():
    with cache_lock:
        return jsonify({
            "articles":   cache["news"],
            "updated_at": cache["news_updated_at"],
            "count":      len(cache["news"]),
        })

@app.route("/health")
def health():
    with cache_lock:
        return jsonify({"ok": True, "updated_at": cache["updated_at"], "news": len(cache["news"])})

# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("╔══════════════════════════════════════╗")
    print("║      FinTrack Price Server            ║")
    print(f"║      http://localhost:{PORT}            ║")
    print(f"║      Refreshes every {REFRESH_SECONDS}s              ║")
    print("╚══════════════════════════════════════╝")
    print()

    # Start price + news background threads
    threading.Thread(target=refresh_loop, daemon=True).start()
    threading.Thread(target=news_loop,    daemon=True).start()

    # Give the first fetches a head-start before Flask starts logging
    time.sleep(1)

    app.run(host="127.0.0.1", port=PORT, debug=False, use_reloader=False)
