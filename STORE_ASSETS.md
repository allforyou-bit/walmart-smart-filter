# Walmart Smart Filter — Chrome Web Store Submission Assets

---

## Short Description (132 chars max)
Filter Walmart search to Walmart Direct only. Highlights Clearance, Rollback & deals with savings % and star ratings.

---

## Full Description (Chrome Web Store)

**Stop scrolling past third-party sellers. Find the real Walmart deals in seconds.**

Walmart Smart Filter is a lightweight browser extension that transforms your Walmart shopping experience:

### 🔵 Walmart Direct Filter
Automatically filters search results to show only items **sold and shipped by Walmart** — not third-party marketplace sellers. One click to toggle on/off.

### 🔴 Deal Highlighting
Clearance, Rollback, Reduced Price, and Best Seller items are instantly flagged with colored borders and badges showing the **exact discount percentage** (e.g., "Clearance · −43%").

### 📊 Live Deal Dashboard
Click the extension icon to see:
- How many Clearance / Rollback / Reduced / Best Seller items are on the current page
- **Average savings %** and **best savings %** across all deals on the page
- Hover over any count to see a deal preview panel with product thumbnail, name, price, savings %, and star rating — sorted best deal first

### ✂️ Min. Savings Filter
Set a minimum discount threshold: show only deals that are **≥ 10%, ≥ 20%, or ≥ 30% off**. Cut through noise and see only the deals worth your time.

### 🚚 Shipping & Pickup Filters
Filter search results to show only items with **free 2-day shipping** or **in-store pickup available**.

---

### How It Works
1. Install the extension
2. Go to any Walmart.com search page
3. The extension automatically applies your filters and highlights deals
4. Click the icon to see your deal dashboard

No account required. No data collected. Works instantly.

---

### Privacy
- **Zero data collection.** Settings are stored locally in your browser.
- No external servers. No analytics. No tracking.
- [Full Privacy Policy](https://allforyou-bit.github.io/walmart-smart-filter/privacy.html)

---

## Category
Shopping

## Tags / Keywords
walmart, deal finder, clearance, rollback, price filter, shopping, discount, savings, deal highlighter, walmart direct

---

## Pricing Options (choose one)

### Option A — Free with Ko-fi support
- List as free on Chrome Web Store
- Include Ko-fi link in popup for voluntary donations ($3–$5)
- Projected: $50–$200/month with 1,000+ active users

### Option B — One-Time Purchase ($2.99)
- List as paid on Chrome Web Store
- Chrome handles payment and license enforcement
- Projected: $150–$500/month with 100–200 sales/month

### Option C — Freemium (Recommended)
- Free: Walmart Direct filter + deal highlights
- Pro ($1.99 one-time via Gumroad): Min savings filter + preview panel + deal stats
- Projected: $200–$800/month with 500+ installs and 10–15% conversion

---

## Affiliate Revenue Setup

1. Sign up for the **Walmart Affiliate Program**:
   https://www.walmart.com/cp/affiliate-program/1229722

2. Apply through **Impact.com** (Walmart's affiliate network)

3. Once approved, get your Publisher ID from Impact.com dashboard

4. Open `popup.js` and set:
   ```js
   const AFFILIATE_ID = 'YOUR_PUBLISHER_ID_HERE';
   ```

5. Product links in the deal preview panel will now route through your affiliate link.
   You earn **1–4% commission** on any purchase made after a click.

**Realistic projection:** With 500 monthly active users clicking through 2–3 deals each,
and a 5% purchase rate at ~$30 average order value = ~$15–60/month in commissions.
Scales linearly with user base.

---

## Ko-fi Setup

1. Create account at https://ko-fi.com
2. Set up your page (takes 5 minutes)
3. Open `popup.html` and replace `YOURUSERNAME` in the support bar link:
   ```html
   <a href="https://ko-fi.com/YOURUSERNAME" ...>♥ Support this extension</a>
   ```
4. Suggested donation page text:
   > "Walmart Smart Filter is free to use. If it's saved you money on a deal, consider buying me a coffee! Your support helps keep the extension updated."

---

## Review Link Setup

1. Submit the extension to Chrome Web Store and note the Extension ID
   (looks like: `abcdefghijklmnopqrstuvwxyz123456`)
2. Replace `EXTENSION_ID` in two places in `popup.html`:
   - In the `#reviewNudge` div
   - In the `.support-bar` div

---

## Screenshots Needed (Chrome Web Store requires 1280×800 or 640×400)

1. **Before/After** — Walmart search without extension (mixed sellers) vs. with extension (Walmart Direct only, highlighted deals)
2. **Deal badges** — Close-up of Clearance/Rollback badges with savings % ("Clearance · −43%")
3. **Popup dashboard** — Extension popup showing deal counts, stats bar, and deal preview panel
4. **Min savings filter** — Popup with "≥ 20% off" selected, fewer but better deals highlighted

---

## Promotional Tile Text (440×280 small promo tile)
**Walmart Smart Filter**
Find real deals. Skip the noise.
Clearance · Rollback · Reduced Price
