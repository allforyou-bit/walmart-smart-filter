// Automated tests for Walmart Smart Filter logic
// Run with: node test/run_tests.js

'use strict';

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓  ${name}`);
    passed++;
  } catch (e) {
    console.error(`  ✗  ${name}`);
    console.error(`     ${e.message}`);
    failed++;
  }
}

function assert(condition, msg) {
  if (!condition) throw new Error(msg || 'assertion failed');
}

function assertEqual(a, b) {
  if (a !== b) throw new Error(`expected "${b}" but got "${a}"`);
}

// ── Simulate browser URL helpers (mirrors content.js logic) ─────────────────

const FACET_VALUE = 'retailer_type:Walmart';

function buildUrl(base, facetValue) {
  const url = new URL(base);
  const params = new URLSearchParams(url.search);
  if (facetValue) params.set('facet', facetValue);
  else params.delete('facet');
  const search = params.toString().replace(/%7C%7C/g, '||');
  return `${url.origin}${url.pathname}${search ? '?' + search : ''}`;
}

function applyFilter(href) {
  const url = new URL(href);
  if (url.pathname !== '/search') return href;
  const existing = new URLSearchParams(url.search).get('facet') || '';
  if (existing.includes('retailer_type%3AWalmart') || existing.includes('retailer_type:Walmart')) return href;
  const newFacet = existing ? `${existing}||${FACET_VALUE}` : FACET_VALUE;
  return buildUrl(href, newFacet);
}

function removeFilter(href) {
  const url = new URL(href);
  const params = new URLSearchParams(url.search);
  const existing = params.get('facet') || '';
  const cleaned = existing.split('||').filter(f => f.trim() !== FACET_VALUE).join('||');
  return buildUrl(href, cleaned || null);
}

function hasFilter(href) {
  return href.includes('retailer_type%3AWalmart') || href.includes('retailer_type:Walmart');
}

// ── Deal detection (mirrors detector.js logic) ───────────────────────────────

const DEAL_PATTERNS = [
  { type: 'clearance',  pattern: /\bclearance\b/i,     label: 'Clearance' },
  { type: 'rollback',   pattern: /\brollback\b/i,       label: 'Rollback' },
  { type: 'reduced',    pattern: /\breduced price\b/i,  label: 'Reduced Price' },
  { type: 'bestseller', pattern: /\bbest seller\b/i,    label: 'Best Seller' },
];

function getDeal(text) {
  for (const d of DEAL_PATTERNS) {
    if (d.pattern.test(text)) return d;
  }
  return null;
}

function parsePrice(text) {
  // Strip commas so $1,299.99 doesn't truncate
  const cleaned = text.replace(/,/g, '');
  const dec = cleaned.match(/\$(\d+\.\d{2})/);
  if (dec) return parseFloat(dec[1]);
  const any = cleaned.match(/\$(\d+)/);
  return any ? parseFloat(any[1]) : null;
}

// ── Run tests ────────────────────────────────────────────────────────────────

console.log('\n[URL Filter Tests]');

test('adds Walmart facet to clean search URL', () => {
  const result = applyFilter('https://www.walmart.com/search?q=toy+cars');
  assert(result.includes('facet=retailer_type%3AWalmart'), result);
});

test('does not double-add if filter already present (encoded)', () => {
  const url = 'https://www.walmart.com/search?q=toy+cars&facet=retailer_type%3AWalmart';
  assertEqual(applyFilter(url), url);
});

test('preserves existing facet when adding Walmart filter', () => {
  const result = applyFilter('https://www.walmart.com/search?q=toys&facet=brand%3ASamsung');
  assert(result.includes('brand%3ASamsung'), 'should keep brand facet: ' + result);
  assert(result.includes('retailer_type%3AWalmart'), 'should add walmart facet: ' + result);
  assert(!result.includes('%7C%7C'), 'should NOT encode || as %7C%7C: ' + result);
});

test('removes Walmart facet from URL', () => {
  const url = 'https://www.walmart.com/search?q=toys&facet=retailer_type%3AWalmart';
  const result = removeFilter(url);
  assert(!hasFilter(result), 'should remove filter: ' + result);
});

test('removes Walmart facet while keeping other facets', () => {
  const url = 'https://www.walmart.com/search?q=toys&facet=brand%3ASamsung||retailer_type:Walmart';
  const result = removeFilter(url);
  assert(!hasFilter(result), 'walmart filter should be gone: ' + result);
  assert(result.includes('brand%3ASamsung'), 'should keep brand facet: ' + result);
});

test('does not apply filter on non-search pages', () => {
  const url = 'https://www.walmart.com/ip/some-product/123456';
  assertEqual(applyFilter(url), url);
});

console.log('\n[Deal Detection Tests]');

test('detects Clearance', () => {
  const d = getDeal('Clearance Toy Car Set $20.69 Was $22.99');
  assertEqual(d?.label, 'Clearance');
});

test('detects Rollback', () => {
  const d = getDeal('Rollback onn USB Cable 6ft $4.88');
  assertEqual(d?.label, 'Rollback');
});

test('detects Reduced Price', () => {
  const d = getDeal('Reduced price TOP BRIGHT Car Ramp Toy $22.39 Was $27.99');
  assertEqual(d?.label, 'Reduced Price');
});

test('detects Best Seller', () => {
  const d = getDeal('Best seller 150Pcs Magnetic Car Track Set $43.99');
  assertEqual(d?.label, 'Best Seller');
});

test('returns null for no deal', () => {
  const d = getDeal('JBL Tune Flex 2 True Wireless Earbuds $59.95');
  assert(d === null, 'should be null');
});

console.log('\n[Price Parsing Tests]');

test('parses decimal price correctly', () => {
  const p = parsePrice('Now$5995current price Now $59.95, Was $109.95');
  assertEqual(p, 59.95);
});

test('parses price without cents', () => {
  const p = parsePrice('$2499current price $24.99');
  assertEqual(p, 24.99);
});

test('picks first decimal price when multiple exist', () => {
  const p = parsePrice('Now $40.41, Was $69.95');
  assertEqual(p, 40.41);
});

test('returns null when no price', () => {
  const p = parsePrice('Add to cart');
  assert(p === null, 'should be null');
});

// ── Summary ──────────────────────────────────────────────────────────────────

console.log(`\n${'─'.repeat(40)}`);
console.log(`  Total: ${passed + failed}  Passed: ${passed}  Failed: ${failed}`);
if (failed === 0) console.log('  All tests passed ✓');
console.log('');

process.exit(failed > 0 ? 1 : 0);
