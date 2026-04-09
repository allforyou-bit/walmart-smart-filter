// detector.js — Deal badge detection only (seller detection removed: not in search card DOM)

'use strict';

const WalmartDetector = (() => {

  // ── Card strategies ─────────────────────────────────────────────────────────

  const CARD_STRATEGIES = [
    // Strategy 1: official automation-id (most precise)
    { name: 'data-automation-id=product',
      fn: () => [...document.querySelectorAll('[data-automation-id="product"]')] },

    // Strategy 2: gpt-tile containers scoped inside the search results grid only
    // This avoids grabbing recommendation carousels outside the main results area
    { name: 'gpt-tile in search grid',
      fn: () => {
        // Find the main search results container first
        const grid = document.querySelector(
          '[data-testid="search-result-listview-container"], ' +
          '[data-testid="list-view"], ' +
          '[class*="search-result-gridview"], ' +
          'section[aria-label*="search"], ' +
          'main'
        );
        if (!grid) return [];
        const tiles = grid.querySelectorAll(
          '[data-test-id="gpt-product-tile-grid-container"], ' +
          '[data-test-id="gpt-product-tile-list-container"]'
        );
        const cards = new Set();
        tiles.forEach(el => {
          let node = el.parentElement;
          for (let i = 0; i < 6; i++) {
            if (!node) break;
            if (node.getAttribute('data-item-id') || node.tagName === 'LI' || node.tagName === 'ARTICLE') {
              cards.add(node); break;
            }
            node = node.parentElement;
          }
        });
        return [...cards];
      }
    },

    // Strategy 3: data-item-id scoped inside search grid (fallback)
    { name: 'data-item-id in search grid',
      fn: () => {
        const grid = document.querySelector(
          '[data-testid="search-result-listview-container"], ' +
          '[data-testid="list-view"], ' +
          'main'
        );
        if (!grid) return [...document.querySelectorAll('[data-item-id]')];
        return [...grid.querySelectorAll('[data-item-id]')];
      }
    },
  ];

  // ── Deal type detection (from card text — confirmed working) ────────────────
  // Walmart shows deal labels in card textContent: Clearance, Rollback, Reduced price

  const DEAL_PATTERNS = [
    { type: 'clearance',      pattern: /\bclearance\b/i,      label: 'Clearance',      color: '#e85d04' },
    { type: 'rollback',       pattern: /\brollback\b/i,       label: 'Rollback',        color: '#0071ce' },
    { type: 'reduced',        pattern: /\breduced price\b/i,  label: 'Reduced Price',   color: '#007600' },
    { type: 'bestseller',     pattern: /\bbest seller\b/i,    label: 'Best Seller',     color: '#6a0dad' },
  ];

  // ── Savings detection ────────────────────────────────────────────────────────
  // Reliable for Clearance / Rollback / Reduced Price — these always have a "Was" price.

  function getSavings(card) {
    let wasPrice = null;

    // Strategy 1: DOM element (most precise)
    const wasEl = card.querySelector(
      '[data-automation-id="product-was-price"], ' +
      '[data-testid="product-was-price"], ' +
      '[aria-label*="Was"]'
    );
    if (wasEl) {
      const m = wasEl.textContent.match(/\$(\d[\d,]*(?:\.\d{2})?)/);
      if (m) wasPrice = parseFloat(m[1].replace(/,/g, ''));
    }

    // Strategy 2: strikethrough element containing a price
    if (!wasPrice) {
      for (const el of card.querySelectorAll('s, del, strike')) {
        const m = el.textContent.match(/\$(\d[\d,]*(?:\.\d{2})?)/);
        if (m) { wasPrice = parseFloat(m[1].replace(/,/g, '')); break; }
      }
    }

    // Strategy 3: text-based "Was $X.XX"
    if (!wasPrice) {
      const m = card.textContent.match(/\bwas\s+\$(\d[\d,]*(?:\.\d{2})?)/i);
      if (m) wasPrice = parseFloat(m[1].replace(/,/g, ''));
    }

    if (!wasPrice) return null;

    const nowPrice = parsePrice(card);
    if (!nowPrice || wasPrice <= nowPrice) return null;

    const saved = wasPrice - nowPrice;
    const pct   = Math.round((saved / wasPrice) * 100);
    if (pct < 1) return null;

    return { wasPrice, nowPrice, saved, pct };
  }

  // ── Rating detection ─────────────────────────────────────────────────────────

  function getRating(card) {
    // Strategy 1: aria-label "X.X out of 5 stars"
    for (const el of card.querySelectorAll('[aria-label]')) {
      const label = el.getAttribute('aria-label') || '';
      const m = label.match(/(\d+\.?\d*)\s*(?:out\s+of\s+5|stars)/i);
      if (m) {
        const val = parseFloat(m[1]);
        if (val > 0 && val <= 5) return { value: val, label: `★ ${val.toFixed(1)}` };
      }
    }

    // Strategy 2: itemprop="ratingValue"
    const ratingEl = card.querySelector('[itemprop="ratingValue"]');
    if (ratingEl) {
      const val = parseFloat(ratingEl.getAttribute('content') || ratingEl.textContent);
      if (!isNaN(val) && val > 0 && val <= 5) return { value: val, label: `★ ${val.toFixed(1)}` };
    }

    // Strategy 3: text fallback
    const m = card.textContent.match(/(\d+\.?\d*)\s+out\s+of\s+5/i);
    if (m) {
      const val = parseFloat(m[1]);
      if (val > 0 && val <= 5) return { value: val, label: `★ ${val.toFixed(1)}` };
    }

    return null;
  }

  // ── Price strategies ────────────────────────────────────────────────────────

  const PRICE_STRATEGIES = [
    card => card.querySelector('[data-automation-id="product-price"]'),
    card => card.querySelector('[itemprop="price"]'),
    card => {
      for (const el of card.querySelectorAll('span, div')) {
        if (/^\$[\d,]+(\.\d{2})?$/.test(el.textContent.trim())) return el;
      }
      return null;
    },
  ];

  // ── Core finders ─────────────────────────────────────────────────────────────

  let _activeCardStrategy = null;

  function findCards() {
    if (_activeCardStrategy) {
      const cards = _activeCardStrategy.fn();
      if (cards.length > 0) return cards;
      _activeCardStrategy = null;
    }
    for (const s of CARD_STRATEGIES) {
      const cards = s.fn();
      if (cards.length > 0) {
        _activeCardStrategy = s;
        console.log(`[WSF] Card strategy: "${s.name}" → ${cards.length} cards`);
        return cards;
      }
    }
    return [];
  }

  function getDealType(card) {
    const text = card.textContent;
    for (const d of DEAL_PATTERNS) {
      if (d.pattern.test(text)) return d;
    }
    return null;
  }

  function parsePrice(card) {
    for (const s of PRICE_STRATEGIES) {
      const el = s(card);
      if (!el) continue;
      // Strip commas first so $1,299.99 doesn't parse as $1
      const text = el.textContent.replace(/,/g, '');
      const dec = text.match(/\$(\d+\.\d{2})/);
      if (dec) return parseFloat(dec[1]);
    }
    return null;
  }

  // ── Diagnostic ───────────────────────────────────────────────────────────────

  function runDiagnostic() {
    const cards = findCards();
    const onSearch = window.location.pathname === '/search';
    const hasFilter = window.location.href.includes('retailer_type%3AWalmart') ||
                      window.location.href.includes('retailer_type:Walmart');

    console.group('%c[WSF Diagnostic]', 'color:#0071ce;font-weight:bold;font-size:13px');
    console.log('Script loaded    :', '✓');
    console.log('Page type        :', onSearch ? 'Search page' : window.location.pathname);
    console.log('Walmart filter   :', hasFilter ? 'ACTIVE ✓' : 'not applied');
    console.log('Cards found      :', cards.length);
    console.log('Card strategy    :', _activeCardStrategy?.name ?? 'none');

    cards.slice(0, 5).forEach((card, i) => {
      const deal    = getDealType(card);
      const savings = getSavings(card);
      const rating  = getRating(card);
      console.log(`Card ${i + 1}: deal=${deal?.label ?? 'none'} | savings=${savings ? `-${savings.pct}% ($${savings.saved.toFixed(2)})` : 'none'} | rating=${rating?.label ?? 'none'}`);
    });
    console.groupEnd();
  }

  setTimeout(runDiagnostic, 2000);

  // ── Card summary (for popup preview) ────────────────────────────────────────

  const NAME_SELECTORS = [
    '[data-automation-id="product-title"]',
    '[itemprop="name"]',
    'span[data-automation-id*="title"]',
  ];

  function getCardSummary(card) {
    const deal = getDealType(card);
    if (!deal) return null;

    // Name
    let name = '';
    for (const sel of NAME_SELECTORS) {
      const el = card.querySelector(sel);
      if (el && el.textContent.trim()) { name = el.textContent.trim(); break; }
    }
    if (!name) {
      const link = card.querySelector('a[href*="/ip/"]');
      if (link) name = link.textContent.trim().replace(/\s+/g, ' ').split('\n')[0].trim();
    }

    // Price
    const priceNum = parsePrice(card);
    const price = priceNum != null ? `$${priceNum.toFixed(2)}` : '';

    // Savings
    const savings = getSavings(card);

    // Rating
    const rating = getRating(card);

    // Image — prefer Walmart CDN, resize to 80px for efficiency
    const img = card.querySelector('img[src*="walmartimages"]') || card.querySelector('img');
    let image = img?.src || '';
    if (image && image.includes('walmartimages')) {
      image = image.replace(/odnHeight=\d+/, 'odnHeight=80').replace(/odnWidth=\d+/, 'odnWidth=80');
    }

    // Product URL
    const linkEl = card.querySelector('a[href*="/ip/"]');
    const url = linkEl ? linkEl.href : '';

    return { type: deal.type, label: deal.label, color: deal.color, name, price, savings, rating, image, url };
  }

  return { findCards, getDealType, parsePrice, getSavings, getRating, getCardSummary };
})();
