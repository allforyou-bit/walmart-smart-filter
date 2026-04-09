"""
Automated tests for Walmart Smart Filter logic.
Mirrors the JavaScript logic from content.js and detector.js.
"""
import re
from urllib.parse import urlparse, parse_qs, urlencode, quote, unquote, urlunparse

FACET_VALUE = 'retailer_type:Walmart'
FACET_ENCODED = 'retailer_type%3AWalmart'

passed = []
failed = []

def test(name, fn):
    try:
        fn()
        passed.append(name)
        print(f'  PASS  {name}')
    except AssertionError as e:
        failed.append(name)
        print(f'  FAIL  {name}')
        print(f'     {e}')

# ── URL helpers (mirror content.js) ─────────────────────────────────────────

def build_url(base, facet_value):
    """Build URL with given facet, preserving || unencoded."""
    parsed = urlparse(base)
    params = parse_qs(parsed.query, keep_blank_values=True)
    if facet_value:
        params['facet'] = [facet_value]
    else:
        params.pop('facet', None)

    # urlencode encodes || as %7C%7C — fix that back
    query = urlencode({k: v[0] for k, v in params.items()}, quote_via=quote)
    query = query.replace('%7C%7C', '||')

    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', query, ''))

def has_filter(href):
    return FACET_ENCODED in href or FACET_VALUE in href

def apply_filter(href):
    parsed = urlparse(href)
    if parsed.path != '/search':
        return href
    if has_filter(href):
        return href
    params = parse_qs(parsed.query, keep_blank_values=True)
    existing = params.get('facet', [''])[0]
    new_facet = f'{existing}||{FACET_VALUE}' if existing else FACET_VALUE
    return build_url(href, new_facet)

def remove_filter(href):
    parsed = urlparse(href)
    params = parse_qs(parsed.query, keep_blank_values=True)
    existing = unquote(params.get('facet', [''])[0])
    parts = [f for f in existing.split('||') if f.strip() != FACET_VALUE]
    cleaned = '||'.join(parts)
    return build_url(href, cleaned if cleaned else None)

# ── Deal detection (mirror detector.js) ──────────────────────────────────────

DEAL_PATTERNS = [
    ('clearance',  re.compile(r'\bclearance\b',    re.I), 'Clearance'),
    ('rollback',   re.compile(r'\brollback\b',     re.I), 'Rollback'),
    ('reduced',    re.compile(r'\breduced price\b', re.I), 'Reduced Price'),
    ('bestseller', re.compile(r'\bbest seller\b',  re.I), 'Best Seller'),
]

def get_deal(text):
    for dtype, pattern, label in DEAL_PATTERNS:
        if pattern.search(text):
            return {'type': dtype, 'label': label}
    return None

def parse_price(text):
    # Strip commas so $1,299.99 doesn't parse as $1
    text = text.replace(',', '')
    dec = re.search(r'\$(\d+\.\d{2})', text)
    if dec:
        return float(dec.group(1))
    any_ = re.search(r'\$(\d+)', text)
    return float(any_.group(1)) if any_ else None

# ── Tests ─────────────────────────────────────────────────────────────────────

print('\n[URL Filter Tests]')

def t1():
    result = apply_filter('https://www.walmart.com/search?q=toy+cars')
    assert 'retailer_type%3AWalmart' in result or 'retailer_type:Walmart' in result, result
test('adds Walmart facet to clean search URL', t1)

def t2():
    url = 'https://www.walmart.com/search?q=toy+cars&facet=retailer_type%3AWalmart'
    assert apply_filter(url) == url, 'should not modify already-filtered URL'
test('does not double-add if filter already present', t2)

def t3():
    result = apply_filter('https://www.walmart.com/search?q=toys&facet=brand%3ASamsung')
    assert 'brand%3ASamsung' in result or 'brand:Samsung' in result, f'should keep brand facet: {result}'
    assert has_filter(result), f'should add walmart facet: {result}'
    assert '%7C%7C' not in result, f'should NOT encode || as %7C%7C: {result}'
test('preserves existing facet, no %7C%7C encoding', t3)

def t4():
    url = 'https://www.walmart.com/search?q=toys&facet=retailer_type%3AWalmart'
    result = remove_filter(url)
    assert not has_filter(result), f'should remove filter: {result}'
test('removes Walmart facet from URL', t4)

def t5():
    url = 'https://www.walmart.com/search?q=toys&facet=brand%3ASamsung||retailer_type:Walmart'
    result = remove_filter(url)
    assert not has_filter(result), f'walmart filter should be gone: {result}'
    assert 'brand' in result, f'should keep brand facet: {result}'
test('removes only Walmart facet, keeps others', t5)

def t6():
    url = 'https://www.walmart.com/ip/some-product/123456'
    assert apply_filter(url) == url, 'should not touch product pages'
test('does not apply filter on product pages (/ip/)', t6)

def t6b():
    url = 'https://www.walmart.com/browse/electronics/3944'
    result = apply_filter(url)
    # browse pages: pathname is /browse, not /search — our apply_filter only targets /search
    # This is correct — browse pages use a different URL structure
    assert result == url or has_filter(result), f'unexpected: {result}'
test('browse page handling is safe', t6b)

print('\n[Deal Detection Tests]')

def t7():
    d = get_deal('Clearance Toy Car Set $20.69 Was $22.99')
    assert d and d['label'] == 'Clearance', d
test('detects Clearance', t7)

def t8():
    d = get_deal('Rollback onn USB Cable 6ft $4.88')
    assert d and d['label'] == 'Rollback', d
test('detects Rollback', t8)

def t9():
    d = get_deal('Reduced price TOP BRIGHT Car Ramp Toy $22.39 Was $27.99')
    assert d and d['label'] == 'Reduced Price', d
test('detects Reduced Price', t9)

def t10():
    d = get_deal('Best seller 150Pcs Magnetic Car Track Set $43.99')
    assert d and d['label'] == 'Best Seller', d
test('detects Best Seller', t10)

def t11():
    d = get_deal('JBL Tune Flex 2 True Wireless Earbuds $59.95')
    assert d is None, f'should be None, got {d}'
test('returns None for no deal', t11)

print('\n[Price Parsing Tests]')

def t12():
    p = parse_price('Now$5995current price Now $59.95, Was $109.95')
    assert p == 59.95, f'expected 59.95 got {p}'
test('parses decimal price (ignores cents-concatenated format)', t12)

def t13():
    p = parse_price('$2499current price $24.99')
    assert p == 24.99, f'expected 24.99 got {p}'
test('parses price from mixed text', t13)

def t14():
    p = parse_price('Now $40.41, Was $69.95')
    assert p == 40.41, f'expected 40.41 got {p}'
test('picks first decimal price when multiple exist', t14)

def t15():
    p = parse_price('Add to cart')
    assert p is None, f'expected None got {p}'
test('returns None when no price found', t15)

def t16():
    p = parse_price('Now$1,29999current price Now $1,299.99, Was $1,699.99')
    assert p == 1299.99, f'expected 1299.99 got {p}'
test('parses comma-formatted price $1,299.99 correctly', t16)

# ── Savings detection (mirror detector.js getSavings) ────────────────────────

def get_savings(card_text, was_price, now_price):
    """
    Simulate getSavings(): given was/now prices (already parsed),
    return savings dict or None.
    """
    if not was_price or not now_price or was_price <= now_price:
        return None
    saved = was_price - now_price
    pct   = round(saved / was_price * 100)
    if pct < 1:
        return None
    return {'wasPrice': was_price, 'nowPrice': now_price, 'saved': round(saved, 2), 'pct': pct}

def get_was_price(text):
    """Strategy 3 mirror: text-based 'Was $X.XX'"""
    m = re.search(r'\bwas\s+\$(\d[\d,]*(?:\.\d{2})?)', text, re.I)
    return float(m.group(1).replace(',', '')) if m else None

# ── Rating detection (mirror detector.js getRating) ────────────────────────

def get_rating(aria_labels):
    """Mirror strategy 1: aria-label 'X.X out of 5 stars'"""
    for label in aria_labels:
        m = re.search(r'(\d+\.?\d*)\s*(?:out\s+of\s+5|stars)', label, re.I)
        if m:
            val = float(m.group(1))
            if 0 < val <= 5:
                return {'value': val, 'label': f'★ {val:.1f}'}
    return None

print('\n[Savings Detection Tests]')

def t17():
    s = get_savings('', 22.99, 20.69)
    assert s and s['pct'] == 10, f'expected pct=10, got {s}'
test('calculates clearance savings %', t17)

def t18():
    s = get_savings('', 27.99, 22.39)
    assert s and s['pct'] == 20, f'expected pct=20, got {s}'
test('calculates reduced price savings %', t18)

def t19():
    was = get_was_price('Rollback onn USB Cable Was $6.99 Now $4.88')
    assert was == 6.99, f'expected 6.99 got {was}'
    s = get_savings('', was, 4.88)
    assert s and s['pct'] == 30, f'expected pct=30, got {s}'
test('parses Was price from text and computes savings', t19)

def t20():
    s = get_savings('', 100.00, 99.50)
    assert s is None, f'<1% savings should return None: {s}'
test('returns None when savings < 1%', t20)

def t21():
    s = get_savings('', 50.00, 50.00)
    assert s is None, f'no discount should return None: {s}'
test('returns None when was == now (no discount)', t21)

def t22():
    s = get_savings('', 1699.99, 1299.99)
    assert s and s['pct'] == 24, f'expected pct=24 got {s}'
    assert abs(s['saved'] - 400.0) < 0.1, f'expected saved~400 got {s}'
test('handles high-value item savings', t22)

print('\n[Rating Detection Tests]')

def t23():
    r = get_rating(['4.5 out of 5 stars, 128 reviews'])
    assert r and r['value'] == 4.5, f'expected 4.5 got {r}'
    assert r['label'] == '★ 4.5', f'wrong label: {r}'
test('detects rating from "X.X out of 5 stars" aria-label', t23)

def t24():
    r = get_rating(['3 stars'])
    assert r and r['value'] == 3.0, f'expected 3.0 got {r}'
test('detects integer star rating', t24)

def t25():
    r = get_rating(['Add to cart', 'Free shipping'])
    assert r is None, f'expected None, got {r}'
test('returns None when no rating in aria-labels', t25)

def t26():
    r = get_rating(['6 out of 5 stars'])   # invalid — > 5
    assert r is None, f'should reject val>5: {r}'
test('rejects rating value > 5', t26)

def t27():
    r = get_rating(['0 out of 5 stars'])   # invalid — 0
    assert r is None, f'should reject val=0: {r}'
test('rejects rating value of 0', t27)

# ── Min savings threshold logic ───────────────────────────────────────────────

print('\n[Min Savings Filter Tests]')

def min_savings_passes(savings_pct, threshold):
    """Mirror of processCards threshold check: skip if pct < minSavingsPct"""
    if threshold == 0:
        return True   # all deals pass when threshold is 0
    return savings_pct >= threshold

def t28():
    assert min_savings_passes(43, 0),  'all deals pass at threshold 0'
    assert min_savings_passes(0,  0),  'no-savings deals pass at threshold 0'
test('threshold 0 passes all deals', t28)

def t29():
    assert min_savings_passes(20, 10),  '20% passes ≥10% threshold'
    assert not min_savings_passes(5, 10), '5% fails ≥10% threshold'
test('threshold 10 filters correctly', t29)

def t30():
    assert min_savings_passes(30, 20),  '30% passes ≥20%'
    assert not min_savings_passes(15, 20), '15% fails ≥20%'
test('threshold 20 filters correctly', t30)

def t31():
    assert min_savings_passes(30, 30),  'exactly 30% passes ≥30%'
    assert not min_savings_passes(29, 30), '29% fails ≥30%'
test('threshold 30 boundary is inclusive', t31)

def t32():
    # Best Seller has no savings (pct=0); should be filtered when threshold > 0
    assert not min_savings_passes(0, 10), 'bestseller (no savings) filtered at threshold 10'
test('bestseller (0% savings) filtered when threshold > 0', t32)

# ── Summary ───────────────────────────────────────────────────────────────────

print(f'\n{"-" * 42}')
print(f'  Total: {len(passed)+len(failed)}  Passed: {len(passed)}  Failed: {len(failed)}')
if not failed:
    print('  All tests passed OK')
else:
    print('  Failed tests:')
    for f in failed:
        print(f'    - {f}')
print()

exit(1 if failed else 0)
