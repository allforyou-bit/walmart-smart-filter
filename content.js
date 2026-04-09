// content.js — Walmart Smart Filter (depends on detector.js)

'use strict';

(function () {

  let settings = {
    filterThirdParty:  true,
    highlightDeals:    true,
    showDealBadge:     true,
    freeShippingOnly:  false,
    pickupOnly:        false,
    minSavingsPct:     0,   // 0 = all deals; 10/20/30 = only show deals ≥ X% off
  };

  // Persistent counts + deal summaries — updated by processCards(), served to popup instantly
  let lastCounts = { clearance: 0, rollback: 0, reduced: 0, bestseller: 0 };
  let lastDeals  = [];
  let lastStats  = { avgSavings: 0, bestSavings: 0 };

  // ── URL facet constants ──────────────────────────────────────────────────────

  const FACETS = {
    filterThirdParty: 'retailer_type:Walmart',
    freeShippingOnly: 'pickup_and_delivery:2-Day Shipping',
    pickupOnly:       'pickup_and_delivery:In-store Pickup',
  };

  // ── URL helpers ─────────────────────────────────────────────────────────────

  function isSearchPage()  { return window.location.pathname === '/search'; }
  function isBrowsePage()  { return window.location.pathname.startsWith('/browse'); }
  function isProductPage() { return window.location.pathname.startsWith('/ip/'); }
  function isActivePage()  { return isSearchPage() || isBrowsePage(); }

  function buildUrl(facetValue) {
    const params = new URLSearchParams(window.location.search);
    if (facetValue) params.set('facet', facetValue);
    else            params.delete('facet');
    const search = params.toString().replace(/%7C%7C/g, '||');
    return `${window.location.origin}${window.location.pathname}${search ? '?' + search : ''}`;
  }

  function getCurrentFacets() {
    const decoded = new URLSearchParams(window.location.search).get('facet') || '';
    return decoded ? decoded.split('||').map(f => f.trim()).filter(Boolean) : [];
  }

  function hasFacet(value) {
    return getCurrentFacets().some(f => f === value);
  }

  function addFacet(value) {
    if (!isActivePage()) return;
    if (hasFacet(value)) return;
    const parts = getCurrentFacets();
    parts.push(value);
    window.location.replace(buildUrl(parts.join('||')));
  }

  function removeFacet(value) {
    if (!hasFacet(value)) return;
    const parts = getCurrentFacets().filter(f => f !== value);
    window.location.replace(buildUrl(parts.length ? parts.join('||') : null));
  }

  function applyWalmartFilter()  { addFacet(FACETS.filterThirdParty); }
  function removeWalmartFilter() { removeFacet(FACETS.filterThirdParty); }
  function applyFreeShipping()   { addFacet(FACETS.freeShippingOnly); }
  function removeFreeShipping()  { removeFacet(FACETS.freeShippingOnly); }
  function applyPickupFilter()   { addFacet(FACETS.pickupOnly); }
  function removePickupFilter()  { removeFacet(FACETS.pickupOnly); }

  // ── Badge injection ─────────────────────────────────────────────────────────

  function injectBadge(card, deal, savings) {
    if (card.querySelector('.wsf-deal-badge')) return;
    const badge = document.createElement('div');
    badge.className       = 'wsf-deal-badge';
    badge.style.background = deal.color;
    // Show savings % alongside deal type if available: "Clearance · −43%"
    badge.textContent = savings ? `${deal.label} · −${savings.pct}%` : deal.label;
    card.style.position = 'relative';
    card.insertBefore(badge, card.firstChild);
  }

  function clearBadges(card) {
    card.querySelectorAll('.wsf-deal-badge').forEach(b => b.remove());
  }

  // ── Update persistent counts + push badge to background ────────────────────

  function updateCounts(cards) {
    const counts      = { clearance: 0, rollback: 0, reduced: 0, bestseller: 0 };
    const typeMax     = 5;
    const typeSeen    = { clearance: 0, rollback: 0, reduced: 0, bestseller: 0 };
    const deals       = [];
    const savingsPcts = [];

    cards.forEach(card => {
      const summary = WalmartDetector.getCardSummary(card);
      if (!summary) return;
      counts[summary.type] = (counts[summary.type] || 0) + 1;
      if (typeSeen[summary.type] < typeMax) {
        typeSeen[summary.type]++;
        deals.push(summary);
      }
      if (summary.savings?.pct) savingsPcts.push(summary.savings.pct);
    });

    lastCounts = counts;
    lastDeals  = deals;
    lastStats  = {
      avgSavings:  savingsPcts.length
        ? Math.round(savingsPcts.reduce((a, b) => a + b, 0) / savingsPcts.length)
        : 0,
      bestSavings: savingsPcts.length ? Math.max(...savingsPcts) : 0,
    };

    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    chrome.runtime.sendMessage({ type: 'DEAL_COUNT', count: total, counts })
      .catch(() => {});
  }

  // ── Card processing ─────────────────────────────────────────────────────────

  function processCards() {
    const cards = WalmartDetector.findCards();
    updateCounts(cards);
    if (!cards.length) return;

    cards.forEach(card => {
      const deal = WalmartDetector.getDealType(card);
      if (!deal) return;

      const savings = WalmartDetector.getSavings(card);

      // Min savings threshold — skip cards that don't meet the minimum % off
      if (settings.minSavingsPct > 0) {
        const pct = savings?.pct ?? 0;
        if (pct < settings.minSavingsPct) {
          // Clean up in case setting was just raised
          card.classList.remove('wsf-deal-highlight');
          clearBadges(card);
          delete card.dataset.wsfDone;
          return;
        }
      }

      if (card.dataset.wsfDone === deal.type) return;

      card.dataset.wsfDone = deal.type;
      card.classList.remove('wsf-deal-highlight');
      clearBadges(card);

      if (settings.highlightDeals) {
        card.classList.add('wsf-deal-highlight');
        card.style.setProperty('--wsf-deal-color', deal.color);
      }
      if (settings.showDealBadge) {
        injectBadge(card, deal, savings);
      }
    });
  }

  function resetCards() {
    document.querySelectorAll('[data-wsf-done]').forEach(card => {
      delete card.dataset.wsfDone;
      card.classList.remove('wsf-deal-highlight');
      clearBadges(card);
    });
    lastCounts = { clearance: 0, rollback: 0, reduced: 0, bestseller: 0 };
    scheduleProcess();
  }

  // ── Scheduler + Observer ────────────────────────────────────────────────────

  let timer = null;
  function scheduleProcess() {
    clearTimeout(timer);
    timer = setTimeout(processCards, 350);
  }

  function startObserver() {
    new MutationObserver(() => scheduleProcess())
      .observe(document.body, { childList: true, subtree: true });
  }

  // ── Init ────────────────────────────────────────────────────────────────────

  chrome.storage.sync.get(settings, (saved) => {
    settings = { ...settings, ...saved };
    if (isProductPage()) return;

    if (settings.filterThirdParty) applyWalmartFilter();
    if (settings.freeShippingOnly)  applyFreeShipping();
    if (settings.pickupOnly)        applyPickupFilter();

    processCards();
    scheduleProcess();
    startObserver();
  });

  // ── Messages from popup ─────────────────────────────────────────────────────

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === 'SETTINGS_UPDATED') {
      const prev = { ...settings };
      settings = { ...settings, ...msg.settings };

      // Immediate visual cleanup on toggle-off
      if (!settings.highlightDeals && prev.highlightDeals) {
        document.querySelectorAll('.wsf-deal-highlight')
          .forEach(el => el.classList.remove('wsf-deal-highlight'));
      }
      if (!settings.showDealBadge && prev.showDealBadge) {
        document.querySelectorAll('.wsf-deal-badge').forEach(b => b.remove());
      }

      if ( settings.filterThirdParty && !prev.filterThirdParty) applyWalmartFilter();
      if (!settings.filterThirdParty &&  prev.filterThirdParty) removeWalmartFilter();
      if ( settings.freeShippingOnly && !prev.freeShippingOnly) applyFreeShipping();
      if (!settings.freeShippingOnly &&  prev.freeShippingOnly) removeFreeShipping();
      if ( settings.pickupOnly       && !prev.pickupOnly)       applyPickupFilter();
      if (!settings.pickupOnly       &&  prev.pickupOnly)       removePickupFilter();

      resetCards();
    }

    if (msg.type === 'GET_COUNTS') {
      scheduleProcess();
      sendResponse({
        counts:    lastCounts,
        deals:     lastDeals,
        stats:     lastStats,
        isActive:  isActivePage(),
        hasFilter: hasFacet(FACETS.filterThirdParty),
      });
      return true;
    }
  });

})();
