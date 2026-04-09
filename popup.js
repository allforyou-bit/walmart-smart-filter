// popup.js — Walmart Smart Filter v1.5.0

// ── Affiliate configuration ──────────────────────────────────────────────────
// Set your Impact.com publisher ID to earn commission on product clicks.
// Sign up at: https://www.walmart.com/cp/affiliate-program/1229722
// Your tracking URL format: https://goto.walmart.com/c/YOUR_ID/568844/9383
const AFFILIATE_ID = '';   // ← paste your Impact.com publisher ID here

function wrapAffiliateUrl(url) {
  if (!AFFILIATE_ID || !url || !url.includes('walmart.com/ip/')) return url;
  // Walmart affiliate redirect via Impact.com
  return `https://goto.walmart.com/c/${AFFILIATE_ID}/568844/9383?veh=aff&sourceid=imp_000011112222333344&u=${encodeURIComponent(url)}`;
}

// ── Settings ─────────────────────────────────────────────────────────────────

const DEFAULTS = {
  filterThirdParty:  true,
  highlightDeals:    true,
  showDealBadge:     true,
  freeShippingOnly:  false,
  pickupOnly:        false,
  minSavingsPct:     0,
};
const ids = [
  'filterThirdParty',
  'highlightDeals',
  'showDealBadge',
  'freeShippingOnly',
  'pickupOnly',
];

const statusDot  = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const headerSub  = document.getElementById('headerSub');

// ── Load saved settings ──────────────────────────────────────────────────────

chrome.storage.sync.get(DEFAULTS, (settings) => {
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.checked = settings[id] !== undefined ? settings[id] : DEFAULTS[id];
  });
  const minEl = document.getElementById('minSavingsPct');
  if (minEl) minEl.value = settings.minSavingsPct ?? 0;
});

// ── Query active tab and request live counts ─────────────────────────────────

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  if (!tab || !tab.url) return;

  const isWalmart = tab.url.includes('walmart.com');

  if (!isWalmart) {
    statusDot.className    = 'dot off';
    statusText.textContent = 'Open walmart.com to activate';
    headerSub.textContent  = 'Inactive';
    setCountsInactive();
    return;
  }

  chrome.tabs.sendMessage(tab.id, { type: 'GET_COUNTS' }, (resp) => {
    if (chrome.runtime.lastError || !resp) {
      statusDot.className    = 'dot on';
      statusText.textContent = 'Active on walmart.com';
      headerSub.textContent  = 'Navigate to a search page';
      setCountsInactive();
      return;
    }

    const { counts, deals, stats, isActive, hasFilter } = resp;
    if (deals) allDeals = deals;
    const total = Object.values(counts).reduce((a, b) => a + b, 0);

    // Page-level savings stats bar
    const statsBar = document.getElementById('dealStats');
    if (stats && (stats.avgSavings > 0 || stats.bestSavings > 0) && statsBar) {
      document.getElementById('statAvg').textContent  = `−${stats.avgSavings}%`;
      document.getElementById('statBest').textContent = `−${stats.bestSavings}%`;
      statsBar.classList.add('visible');
    }

    statusDot.className = 'dot on';

    if (isActive && hasFilter) {
      statusText.textContent = 'Walmart Direct filter ON';
      headerSub.textContent  = `${total} deal${total !== 1 ? 's' : ''} found`;
    } else if (isActive) {
      statusText.textContent = 'Search page — filter not applied';
      headerSub.textContent  = `${total} deal${total !== 1 ? 's' : ''} found`;
    } else {
      statusText.textContent = 'Active on walmart.com';
      headerSub.textContent  = 'Go to search results';
    }

    document.getElementById('cntClearance').textContent  = counts.clearance  || '0';
    document.getElementById('cntRollback').textContent   = counts.rollback   || '0';
    document.getElementById('cntReduced').textContent    = counts.reduced    || '0';
    document.getElementById('cntBestseller').textContent = counts.bestseller || '0';
  });
});

function setCountsInactive() {
  ['cntClearance','cntRollback','cntReduced','cntBestseller']
    .forEach(id => { document.getElementById(id).textContent = '—'; });
}

// ── Review nudge (shown after 10 deal-finding sessions) ─────────────────────

chrome.storage.local.get({ sessionCount: 0, reviewDismissed: false }, (data) => {
  if (data.sessionCount >= 10 && !data.reviewDismissed) {
    const nudge = document.getElementById('reviewNudge');
    if (nudge) nudge.style.display = 'flex';
  }
});

document.getElementById('dismissNudge')?.addEventListener('click', () => {
  chrome.storage.local.set({ reviewDismissed: true });
  const nudge = document.getElementById('reviewNudge');
  if (nudge) nudge.style.display = 'none';
});

// ── Deal preview on hover ────────────────────────────────────────────────────

let allDeals = [];
let previewHideTimer = null;

const dealPreview  = document.getElementById('dealPreview');
const previewDot   = document.getElementById('previewDot');
const previewTitle = document.getElementById('previewTitle');
const previewCount = document.getElementById('previewCount');
const previewList  = document.getElementById('previewList');

const DEAL_META = {
  clearance:  { label: 'Clearance',     color: '#e85d04' },
  rollback:   { label: 'Rollback',      color: '#0071ce' },
  reduced:    { label: 'Reduced Price', color: '#007600' },
  bestseller: { label: 'Best Seller',   color: '#6a0dad' },
};

const CELL_TYPE_MAP = {
  cntClearance:  'clearance',
  cntRollback:   'rollback',
  cntReduced:    'reduced',
  cntBestseller: 'bestseller',
};

function showPreview(type) {
  clearTimeout(previewHideTimer);
  const meta = DEAL_META[type];

  // Sort by savings % descending — best deals first
  const items = allDeals.filter(d => d.type === type)
    .slice()
    .sort((a, b) => (b.savings?.pct ?? 0) - (a.savings?.pct ?? 0));

  const total = parseInt(document.getElementById(
    Object.keys(CELL_TYPE_MAP).find(k => CELL_TYPE_MAP[k] === type)
  )?.textContent) || items.length;

  previewDot.style.background = meta.color;
  previewTitle.textContent    = meta.label;
  previewTitle.style.color    = meta.color;
  previewCount.textContent    = `${total} item${total !== 1 ? 's' : ''}`;

  previewList.innerHTML = '';

  if (!items.length) {
    const empty = document.createElement('div');
    empty.className   = 'preview-empty';
    empty.textContent = 'No preview data — reload the page.';
    previewList.appendChild(empty);
  } else {
    items.forEach((item, idx) => {
      const a = document.createElement('a');
      a.className = 'preview-item';
      a.href      = wrapAffiliateUrl(item.url) || '#';
      a.target    = '_blank';
      a.rel       = 'noopener';

      // Thumbnail
      if (item.image) {
        const img = document.createElement('img');
        img.className = 'preview-thumb';
        img.src       = item.image;
        img.alt       = '';
        img.onerror   = () => { img.replaceWith(makePlaceholder()); };
        a.appendChild(img);
      } else {
        a.appendChild(makePlaceholder());
      }

      // Info
      const info = document.createElement('div');
      info.className = 'preview-info';

      const name = document.createElement('div');
      name.className   = 'preview-name';
      name.textContent = item.name || 'Unknown product';

      const price = document.createElement('div');
      price.className   = 'preview-price';
      price.textContent = item.price || '';
      price.style.color = meta.color;

      info.appendChild(name);
      if (item.price) info.appendChild(price);

      // Meta row: BEST DEAL badge + savings % + rating
      const hasSavings = item.savings && item.savings.pct >= 1;
      const hasRating  = item.rating  && item.rating.label;
      const isBest     = idx === 0 && hasSavings && item.savings.pct >= 10;

      if (hasSavings || hasRating || isBest) {
        const metaRow = document.createElement('div');
        metaRow.className = 'preview-meta';

        if (isBest) {
          const badge = document.createElement('span');
          badge.className   = 'preview-best-deal';
          badge.textContent = 'Best Deal';
          metaRow.appendChild(badge);
        }
        if (hasSavings) {
          const sav = document.createElement('span');
          sav.className   = 'preview-savings';
          sav.textContent = `−${item.savings.pct}%`;
          metaRow.appendChild(sav);
        }
        if (hasRating) {
          const rat = document.createElement('span');
          rat.className   = 'preview-rating';
          rat.textContent = item.rating.label;
          metaRow.appendChild(rat);
        }

        info.appendChild(metaRow);
      }

      a.appendChild(info);
      previewList.appendChild(a);
    });
  }

  dealPreview.classList.add('visible');
}

function makePlaceholder() {
  const div = document.createElement('div');
  div.className   = 'preview-thumb-placeholder';
  div.textContent = '🏷️';
  return div;
}

function hidePreview() {
  previewHideTimer = setTimeout(() => {
    dealPreview.classList.remove('visible');
  }, 800);
}

document.querySelectorAll('.deal-cell').forEach(cell => {
  const countEl = cell.querySelector('.count');
  if (!countEl) return;
  const type = CELL_TYPE_MAP[countEl.id];
  if (!type) return;
  cell.addEventListener('mouseenter', () => showPreview(type));
});

const dealSummaryEl = document.getElementById('dealSummary');
if (dealSummaryEl) dealSummaryEl.addEventListener('mouseleave', hidePreview);

dealPreview.addEventListener('mouseenter', () => clearTimeout(previewHideTimer));
dealPreview.addEventListener('mouseleave', hidePreview);

// ── Min savings select change ────────────────────────────────────────────────

const minSavingsEl = document.getElementById('minSavingsPct');
if (minSavingsEl) {
  minSavingsEl.addEventListener('change', () => {
    const val = parseInt(minSavingsEl.value) || 0;
    chrome.storage.sync.set({ minSavingsPct: val });
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (tab?.url?.includes('walmart.com')) {
        chrome.tabs.sendMessage(tab.id, { type: 'SETTINGS_UPDATED', settings: { minSavingsPct: val } });
        statusText.textContent = 'Settings applied';
      }
    });
  });
}

// ── Toggle changes ───────────────────────────────────────────────────────────

ids.forEach(id => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('change', () => {
    const updated = {};
    ids.forEach(key => { updated[key] = document.getElementById(key).checked; });
    chrome.storage.sync.set(updated);
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (tab?.url?.includes('walmart.com')) {
        chrome.tabs.sendMessage(tab.id, { type: 'SETTINGS_UPDATED', settings: updated });
        statusText.textContent = 'Settings applied';
      }
    });
  });
});
