# FinTrack

A live stock portfolio tracker — single HTML file frontend with a lightweight Python price server.

## Features

- **4-page app**: Home dashboard, Investments table, Watchlist, News
- **Live prices**: Real prices from Yahoo Finance, refreshed every 60 seconds
- **Smooth simulation**: Random-walk animation between real price fetches (every 1.2s)
- **5 currencies**: USD, EUR, GBP, JPY, TRY — all converted live
- **Editable portfolio**: Add, edit, delete positions — saved to localStorage
- **Sortable table**: Click any column header to sort
- **Platform breakdown**: AXP S&I / Trading App / Turkish App cards with P&L bars
- **Sparklines**: 40-tick rolling price history per stock
- **Market indices**: S&P 500, NASDAQ, FTSE, DAX, BIST 100, Nikkei and more

## Files

| File | Purpose |
|------|---------|
| `portfolio_tracker.html` | The full app — open this in your browser |
| `price_server.py` | Local Flask server that serves real prices |
| `update_prices.py` | One-shot script to update prices in the HTML file |
| `FinTrack_Master_Prompt.md` | Step-by-step guide to rebuild from scratch |

## Quick Start

**1. Install dependencies**
```bash
pip3 install -r requirements.txt
```

**2. Start the price server** (keep this running)
```bash
python3 price_server.py
```

**3. Open the tracker**
```bash
open portfolio_tracker.html
```

The badge in the top-right switches from **Sim** (grey) to **Real** (green) once the server connects.

## Without the server

Just open `portfolio_tracker.html` directly — it works standalone with simulated prices. The server is optional.

## Update prices once (no server)

```bash
python3 update_prices.py
```

This rewrites the base prices in `portfolio_tracker.html` with today's closing prices.

## Stocks tracked

| Ticker | Name | Platform |
|--------|------|----------|
| MSFT | Microsoft | AXP S&I |
| META | Meta Platforms | AXP S&I |
| GOOG | Alphabet C | AXP S&I |
| NVDA | Nvidia | AXP S&I |
| QCOM | Qualcomm | AXP S&I |
| AMD | AMD | AXP S&I |
| TSM | Taiwan Semi | AXP S&I |
| AMZN | Amazon | AXP S&I |
| AAPL | Apple | AXP S&I |
| CSCO | Cisco | AXP S&I |
| ASML | ASML | AXP S&I |
| AVGO | Broadcom | AXP S&I |
| AXP | American Express | Trading App |
| THYAO | Turkish Airlines | Turkish App |
| EKDMR | Ekinciler Demir | Turkish App |

## FX Rates (auto-updated by server)

Rates sourced from Yahoo Finance and refreshed every 60 seconds.
