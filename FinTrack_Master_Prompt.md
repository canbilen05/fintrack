# FinTrack — Master Build Prompt
## Step-by-step instructions to recreate this portfolio tracker from scratch

---

## OVERVIEW

Build a **4-page live portfolio tracker** as a **single self-contained HTML file**.
- No framework, no server, no npm — just one `.html` file you double-click to open
- Blue & white design (Google Finance / Bloomberg style)
- Prices simulate live random-walk updates every 1.2 seconds
- Fully editable portfolio saved to localStorage
- Works on desktop and mobile

---

## STEP 1 — Project Setup

Tell Claude:

> "Create a single HTML file called `portfolio_tracker.html`. It should require no server, no npm, no build step — just open in a browser. Use Inter font from Google Fonts. Blue and white color scheme. Use CSS custom properties (variables) for all colors. No frameworks."

**Token system to establish:**
```
--blue:      #2563EB   (primary actions, tabs, tags)
--blue2:     #1D4ED8   (hover states)
--blue-light:#EEF2FF   (badge backgrounds)
--green:     #059669   (gains)
--red:       #DC2626   (losses)
--bg:        #F0F4FF   (page background)
--surface:   #FFFFFF   (cards, table)
--text:      #0F172A   (primary text)
--sub:       #475569   (secondary text)
--muted:     #94A3B8   (labels, placeholders)
--border:    #E2E8F4   (card borders)
```

---

## STEP 2 — Layout Structure

Tell Claude:

> "Build a flex column layout: `#app` fills the full viewport height with `overflow:hidden`. Inside it: 4 `.page` divs (only one visible at a time via `.active` class) + a fixed bottom navigation bar with 4 tabs. Each page scrolls independently with `overflow-y:auto`. Bottom nav height: 64px."

**4 pages to create:**
- `#p-home` — Landing / Welcome
- `#p-investments` — Portfolio table
- `#p-watchlist` — Market indices + watchlist
- `#p-news` — News feed

**Bottom nav tabs:**
- Home (house icon)
- Invest (chart icon)
- Watchlist (3D box icon)
- News (newspaper icon)

---

## STEP 3 — Holdings Data

Tell Claude:

> "Define this holdings array in JavaScript. All prices and costs are in USD. Turkish stocks (THYAO, EKDMR) have been pre-converted from TRY to USD by dividing by 50.42."

```javascript
const H = [
  {t:'MSFT', n:'Microsoft',        s:0.01191362, c:4.21,          b:415.50,      p:'AXP S&I'},
  {t:'META', n:'Meta Platforms',   s:0.00822981, c:4.26,          b:595.20,      p:'AXP S&I'},
  {t:'GOOG', n:'Alphabet C',       s:0.01154736, c:3.85,          b:165.30,      p:'AXP S&I'},
  {t:'NVDA', n:'Nvidia',           s:0.01996277, c:3.85,          b:913.00,      p:'AXP S&I'},
  {t:'QCOM', n:'Qualcomm',         s:0.01988425, c:3.47,          b:174.00,      p:'AXP S&I'},
  {t:'AMD',  n:'AMD',              s:0.00925767, c:3.46,          b:383.60,      p:'AXP S&I'},
  {t:'TSM',  n:'Taiwan Semi',      s:0.00992854, c:3.39,          b:184.20,      p:'AXP S&I'},
  {t:'AMZN', n:'Amazon',           s:0.01518527, c:3.42,          b:227.10,      p:'AXP S&I'},
  {t:'AAPL', n:'Apple',            s:0.01323369, c:3.39,          b:260.10,      p:'AXP S&I'},
  {t:'CSCO', n:'Cisco',            s:0.03417347, c:3.24,          b:60.20,       p:'AXP S&I'},
  {t:'ASML', n:'ASML',             s:0.00263655, c:3.43,          b:790.50,      p:'AXP S&I'},
  {t:'AVGO', n:'Broadcom',         s:0.00714646, c:2.60,          b:232.80,      p:'AXP S&I'},
  {t:'AXP',  n:'American Express', s:0.43,       c:140.32,        b:309.03,      p:'Trading App'},
  {t:'THYAO',n:'Turkish Airlines', s:240,        c:64876.80/50.42, b:295.00/50.42, p:'Turkish App'},
  {t:'EKDMR',n:'Ekinciler Demir',  s:27,         c:1215.00/50.42,  b:45.00/50.42,  p:'Turkish App'},
];
// Field key: t=ticker, n=name, s=shares, c=cost(USD), b=basePrice(USD), p=platform
```

---

## STEP 4 — Live Price Simulation Engine

Tell Claude:

> "Create a tick() function that runs every 1200ms using setInterval. Each tick: (1) save previous prices, (2) apply random walk shock to each price: `price * (1 + (Math.random()-0.5) * 2 * 0.0015)`, (3) append new price to a 40-item rolling history array per stock, (4) update all UI components."

**State variables needed:**
```javascript
let prices    = H.map(h => h.b);      // current simulated prices
let prev      = [...prices];           // prices from last tick (for flash direction)
let opens     = [...prices];           // session open prices (never change)
let hist      = H.map(() => []);       // 40-tick rolling price history per stock
let portHist  = [];                    // portfolio total value history (for mini chart)
let paused    = false;
let ticks     = 0;
```

**Pause/Resume button:** toggles `paused` boolean, button text changes between "⏸ Pause" and "▶ Resume".

---

## STEP 5 — Currency Conversion

Tell Claude:

> "Add a currency switcher with 5 options. All internal prices are stored in USD. When displaying, multiply by the selected rate. The `fmtN(usdValue)` helper converts and formats automatically."

```javascript
const FX  = { USD:1, EUR:0.9086, GBP:0.7571, JPY:159.3, TRY:50.42 };
const SYM = { USD:'$', EUR:'€', GBP:'£', JPY:'¥', TRY:'₺' };

function fmtN(usd) {
  const v = usd * FX[ccy];
  const s = SYM[ccy];
  if (Math.abs(v) >= 1e6) return s + (v/1e6).toFixed(3) + 'M';
  if (Math.abs(v) >= 1000) return s + v.toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
  return s + v.toFixed(2);
}
```

Currency selector: 5 pill buttons (USD / EUR / GBP / JPY / TRY). Active button gets blue background. Changing currency instantly re-renders the table and all cards.

---

## STEP 6 — Page 1: Home / Landing

Tell Claude:

> "Build the home page with: (1) gradient hero (dark blue to purple, `135deg`) with total portfolio value large, all-time P&L chip (green/red), today's gain, and an 'Open Dashboard' CTA button. (2) Mini sparkline SVG chart of portfolio session history below the hero. (3) 2×2 feature cards grid: Live Prices, 5 Currencies, Watchlist, News."

**Hero stats to show:**
- Total Portfolio Value (large, font-variant-numeric: tabular-nums)
- All-time P&L chip: `▲ +X.XX%` in green or `▼ -X.XX%` in red
- Today's Gain amount + %
- Number of positions (15) and platforms (3)

**Mini chart:** SVG `<polygon>` for fill + `<polyline>` for line, drawn from `portHist[]` array. Updates every tick.

---

## STEP 7 — Page 2: Investments Table

Tell Claude:

> "Build the investments page with: a gradient header showing total value + P&L chip + pause button. Below: 3 sub-tabs (Holdings / Summary / Platforms) as pill tabs. Holdings tab has: currency row, filter row, sortable table."

**Table columns:**
1. Ticker (blue badge)
2. Details (name + platform subtitle)
3. Live Price (green if up, red if down vs prev tick)
4. Day % (badge: green bg/text if positive, red if negative)
5. Value (shares × current price, in display currency)
6. Invested (cost basis, in display currency)
7. P&L % (return since invested)
8. Chart (40-tick sparkline SVG)
9. ✏️ Edit button

**Flash effect:** on each tick, add class `fl-up` or `fl-down` to `<tr>`, then remove after 700ms. CSS:
```css
tbody tr.fl-up   td { background: rgba(5,150,105,.07) !important; transition: background 0s; }
tbody tr.fl-down td { background: rgba(220,38,38,.07)!important; transition: background 0s; }
tbody tr         { transition: background .5s; }
```

**Sortable columns:** Ticker, Price, Day %, P&L %, Value. Click header toggles asc/desc.

**Filter buttons:** ALL / AXP S&I / Trading App / Turkish App

**Summary tab:** 4 stat cards (Total Invested, Current Value, Day Gain, All-time P&L) + FX rates info box.

**Platforms tab:** 3 cards (AXP S&I, Trading App, Turkish App) each showing: Invested, Value, P&L amount+%, Today's change, animated progress bar (green/red, width = `min(|P&L%| × 3, 100)%`).

---

## STEP 8 — Sparklines

Tell Claude:

> "Build a `spark(histArray, isUp, width, height)` function that returns an inline SVG string. It draws a filled area polygon + a line polyline + a dot at the latest price point. Colors: green (#059669) if up, red (#DC2626) if down."

```javascript
function spark(h, up, W=56, H=22) {
  if (h.length < 2) return `<svg width="${W}" height="${H}"></svg>`;
  const mn = Math.min(...h), mx = Math.max(...h), rng = mx - mn || 1;
  const pts = h.map((v,i) =>
    `${((i/(h.length-1))*W).toFixed(1)},${(H-((v-mn)/rng)*H).toFixed(1)}`
  ).join(' ');
  const lx = W, ly = H - ((h[h.length-1]-mn)/rng)*H;
  const fill = pts + ` ${W},${H} 0,${H}`;
  const c = up ? '#059669' : '#DC2626';
  return `<svg width="${W}" height="${H+2}" viewBox="0 0 ${W} ${H+2}">
    <polygon points="${fill}" fill="${c}" opacity=".10"/>
    <polyline points="${pts}" fill="none" stroke="${c}" stroke-width="1.4" stroke-linejoin="round"/>
    <circle cx="${lx}" cy="${ly.toFixed(1)}" r="2" fill="${c}"/>
  </svg>`;
}
```

---

## STEP 9 — Page 3: Watchlist

Tell Claude:

> "Build the watchlist page with two sections: (1) 'Major Indices' — a 2×4 grid of index cards, each showing name, region, current price, % change from base, mini sparkline. (2) 'Your Watchlist' — a vertical list of individual stocks with icon, name, ticker, price, % change."

**Index data:**
```javascript
const INDICES = [
  {name:'S&P 500',   region:'United States', base:4567.23,  sym:'SPX'},
  {name:'NASDAQ',    region:'United States', base:14234.56, sym:'IXIC'},
  {name:'Dow Jones', region:'United States', base:36789.01, sym:'DJI'},
  {name:'FTSE 100',  region:'United Kingdom',base:7634.45,  sym:'UKX'},
  {name:'DAX',       region:'Germany',       base:17123.78, sym:'DAX'},
  {name:'CAC 40',    region:'France',        base:7456.89,  sym:'CAC'},
  {name:'BIST 100',  region:'Turkey',        base:9234.56,  sym:'XU100'},
  {name:'Nikkei',    region:'Japan',         base:33567.89, sym:'NKY'},
];
```

Indices also get random-walk price updates each tick (±0.1% volatility). Show green/red for direction vs base.

---

## STEP 10 — Page 4: News

Tell Claude:

> "Build a static news page with: (1) gradient header with search bar (non-functional, just UI). (2) Horizontal scrollable category chips: All / Markets / Tech / Economy / Crypto / Earnings / FX. (3) Featured article card with gradient image, tag, title, meta. (4) 2-column news grid with 6 cards (each has gradient image, category, title, source + time). (5) Vertical list of additional headlines."

Use realistic-looking financial headlines. Example headlines to include:
- "Fed Signals Three Rate Cuts in 2025 as Inflation Eases Toward Target"
- "NVIDIA Surpasses $3T Market Cap on AI Chip Demand"
- "S&P 500 Hits Record High as Earnings Beat Expectations"
- "Turkish Lira Stabilizes After TCMB Rate Decision"
- "Meta Reports 22% Revenue Growth in Q3 2025"
- "ASML Orders Surge as Chipmakers Expand Capacity"
- "Bitcoin Consolidates Above $95,000 Ahead of ETF Decision"
- "IMF Raises Global Growth Forecast to 3.4% for 2025"

---

## STEP 11 — Editable Portfolio (Add / Edit / Delete)

Tell Claude:

> "Add a slide-up modal for adding and editing positions. Triggered by: (1) '+ Add Position' button in filter bar, (2) ✏️ button on each table row. The modal has fields: Ticker, Company Name, Shares, Cost Basis (USD), Current Price (USD), Platform (dropdown). Buttons: Save (blue) + Delete (red, hidden when adding new). Save updates the H[] array and re-renders. Delete removes the position. All changes are saved to localStorage so they persist on refresh."

**localStorage logic:**
```javascript
function savePortfolio() {
  localStorage.setItem('fintrack_portfolio', JSON.stringify(H));
}
function loadPortfolio() {
  const saved = localStorage.getItem('fintrack_portfolio');
  if (saved) {
    const arr = JSON.parse(saved);
    H.length = 0;
    arr.forEach(h => H.push(h));
    prices = H.map(h => h.b);
    prev = [...prices];
    opens = [...prices];
    hist = H.map(() => []);
  }
}
// Call loadPortfolio() before first render
```

**Modal CSS pattern:** fixed overlay with `backdrop-filter:blur(2px)`, modal slides up from bottom (`align-items:flex-end`), `border-radius:20px 20px 0 0`.

---

## STEP 12 — Navigation

Tell Claude:

> "Build the `goPage(name)` function. It removes `.active` from all `.page` divs and all `.nav-item` buttons, then adds `.active` to `#p-{name}` and `#nav-{name}`. Each `.page` has `display:none` by default; `.page.active` has `display:block`."

---

## STEP 13 — Finishing Touches

Tell Claude to add:

1. **Animated live dot** in header: `width:6px; height:6px; border-radius:50%; background:#4ADE80; animation:blink 1.2s ease-in-out infinite` — changes to grey when paused
2. **Tick counter** shown in header: "Live · Tick 42"
3. **Timestamp** showing last update time: `new Date().toLocaleTimeString()`
4. **Responsive breakpoints:** at ≥640px wide, platform grid becomes 3 columns, news grid becomes 3 columns, index grid becomes 4 columns
5. **Hover states** on table rows: `background: var(--blue-light)` on hover
6. **Font variant:** `font-variant-numeric: tabular-nums` on all price/number cells so digits don't shift width

---

## CUSTOMIZATION GUIDE

| What to change | Where |
|---|---|
| Your stock holdings | The `H` array in Step 3 |
| TRY/USD conversion rate | `50.42` in `c:` and `b:` for THYAO/EKDMR |
| Price volatility | The `0.0015` in the tick function (Step 4) |
| Update speed | `1200` ms in `setInterval(tick, 1200)` |
| FX rates | The `FX` object in Step 5 |
| Index prices | The `INDICES` array in Step 9 |
| News headlines | The HTML in Step 10 |
| Colors | The CSS variables in Step 1 |

---

## FINAL PROMPT (copy-paste ready)

```
Build a 4-page live portfolio tracker as a single self-contained HTML file 
(no server, no npm). Blue (#2563EB) and white design. Inter font from Google Fonts.

PAGES (bottom tab nav — Home / Invest / Watchlist / News):

PAGE 1 HOME: Gradient hero (dark blue→purple) showing total value, all-time P&L 
chip, today's gain, mini session sparkline chart. 2×2 feature cards below.

PAGE 2 INVESTMENTS: Gradient header with total value + pause button. 3 sub-tabs: 
Holdings (sortable table with ticker, name, live price in green/red, day%, value, 
invested, P&L%, 40-tick sparkline, edit button), Summary (4 stat cards + FX info), 
Platforms (3 cards with progress bars). Currency switcher USD/EUR/GBP/JPY/TRY. 
Platform filter: ALL / AXP S&I / Trading App / Turkish App.

PAGE 3 WATCHLIST: 2×4 grid of global indices (S&P500, NASDAQ, DOW, FTSE, DAX, 
CAC40, BIST100, Nikkei) all with live simulated prices. Vertical watchlist below.

PAGE 4 NEWS: Search bar, category chips, featured article card, 2-col news grid 
(6 cards), vertical headlines list. Static/hardcoded content.

FEATURES:
- Prices update every 1200ms via random walk (±0.15% per tick)
- Green/red flash on price tick (CSS transition on table rows)
- Pause/Resume button
- Sortable table columns (ticker, price, day%, P&L%, value)
- Add/Edit/Delete positions via slide-up modal (fields: ticker, name, shares, 
  cost USD, base price USD, platform dropdown). Saved to localStorage.
- FX rates: EUR=0.9086 GBP=0.7571 JPY=159.3 TRY=50.42
- TL stocks pre-converted: cost÷50.42, price÷50.42
- Platform breakdown cards with animated progress bars
- Responsive (mobile + desktop)

HOLDINGS DATA:
[paste your H array here]
```

---

*Save this file. Use it whenever you want to rebuild or extend the tracker.*
