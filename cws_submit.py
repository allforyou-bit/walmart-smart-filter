# -*- coding: utf-8 -*-
"""
Chrome Web Store Playwright Automation
Google login 1 time only — everything else is automated.
Run: python cws_submit.py
"""

import sys, time, pathlib, json
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Paths & Content ───────────────────────────────────────────────────────────

ZIP_PATH    = pathlib.Path('C:/Users/kayky/Desktop/walmart-filter-extension.zip')
STATE_FILE  = pathlib.Path('C:/Users/kayky/Desktop/walmart-filter-extension/.browser_state.json')
DASHBOARD   = 'https://chromewebstore.google.com/devconsole'

SHORT_DESC = (
    "Filter Walmart search to Walmart Direct only. "
    "Highlights Clearance, Rollback & deals with savings % and star ratings."
)

FULL_DESC = """\
Stop scrolling past third-party sellers. Find the real Walmart deals in seconds.

WALMART DIRECT FILTER
Automatically filters search results to show only items sold and shipped by Walmart.
No third-party marketplace sellers.

DEAL BADGES WITH SAVINGS %
Clearance, Rollback, Reduced Price, and Best Seller items are flagged with colored
borders and badges showing the exact discount percentage (e.g., "Clearance - 43% off").

LIVE DEAL DASHBOARD
Click the extension icon to see:
- Count of Clearance / Rollback / Reduced / Best Seller items on the current page
- Average savings % and best savings % across all deals
- Hover any count for a deal preview with thumbnail, price, savings %, and star rating

MIN. SAVINGS FILTER
Show only deals that are 10%, 20%, or 30% or more off. Cut through noise.

SHIPPING & PICKUP FILTERS
Filter to free 2-day shipping or in-store pickup items only.

KEYBOARD SHORTCUT
Press Ctrl+Shift+W (Mac: Cmd+Shift+W) to instantly toggle the Walmart Direct filter.

PRIVACY: Zero data collection. Settings stored locally in your browser only.
No external servers. No analytics. No tracking.
Privacy Policy: https://allforyou-bit.github.io/walmart-smart-filter/privacy.html"""

PRIVACY_URL = 'https://allforyou-bit.github.io/walmart-smart-filter/privacy.html'

# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg): print(f'  {msg}', flush=True)
def step(n, msg): print(f'\n[{n}] {msg}', flush=True)

def try_click(page, selectors, timeout=8000):
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout)
            if el and el.is_visible():
                el.click()
                return True
        except Exception:
            continue
    return False

def try_fill(page, selectors, value, timeout=6000):
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout)
            if el:
                el.click()
                el.fill(value)
                return True
        except Exception:
            continue
    return False

def wait_for_login(page):
    step(1, 'Browser opened. Please log in to your Google account.')
    log('Waiting up to 3 minutes...')
    try:
        page.wait_for_function(
            "!window.location.href.includes('accounts.google.com')",
            timeout=180_000
        )
        time.sleep(2)
        log('Login detected. Continuing...')
    except PWTimeout:
        log('Timed out waiting for login.')
        sys.exit(1)

def wait_for_dashboard(page):
    try:
        page.wait_for_load_state('networkidle', timeout=20_000)
    except PWTimeout:
        pass

# ── Main Automation ───────────────────────────────────────────────────────────

def run():
    print('\n' + '='*54)
    print('  Walmart Smart Filter -- Chrome Web Store Submit')
    print('='*54)

    if not ZIP_PATH.exists():
        print(f'\nERROR: ZIP not found at {ZIP_PATH}')
        sys.exit(1)

    with sync_playwright() as p:
        # Restore saved browser state (stays logged in after first run)
        ctx_kwargs = {'slow_mo': 400, 'viewport': {'width': 1280, 'height': 900}}
        if STATE_FILE.exists():
            ctx_kwargs['storage_state'] = str(STATE_FILE)
            log('Restoring saved session...')

        browser = p.chromium.launch(headless=False, **{})
        context = browser.new_context(**ctx_kwargs)
        page    = context.new_page()

        # ── Navigate to dashboard ──────────────────────────────────────────
        page.goto(DASHBOARD, wait_until='domcontentloaded')
        time.sleep(2)

        if 'accounts.google.com' in page.url or 'signin' in page.url:
            wait_for_login(page)
            page.goto(DASHBOARD, wait_until='domcontentloaded')

        wait_for_dashboard(page)

        # Save session so next run skips login
        context.storage_state(path=str(STATE_FILE))
        log('Session saved.')

        # ── Check developer registration ($5 fee) ─────────────────────────
        step(2, 'Checking developer registration...')
        if 'registration' in page.url or page.query_selector('text=registration fee'):
            log('Developer registration needed.')
            log('Please complete the $5 one-time registration in the browser.')
            log('Waiting for you to finish...')
            page.wait_for_url('**/devconsole**', timeout=300_000)
            wait_for_dashboard(page)
            log('Registration complete.')
        else:
            log('Already registered.')

        # ── Click "New item" ───────────────────────────────────────────────
        step(3, 'Opening new item upload...')
        new_item_selectors = [
            'text=New item',
            'a[href*="new-item"]',
            'button:has-text("New")',
            '[aria-label*="New item"]',
            'text=Add new item',
        ]
        if not try_click(page, new_item_selectors):
            log('Cannot find "New item" button automatically.')
            log('Please click "New item" in the browser.')
            page.pause()

        wait_for_dashboard(page)
        time.sleep(1)

        # ── Upload ZIP ─────────────────────────────────────────────────────
        step(4, f'Uploading {ZIP_PATH.name} ({ZIP_PATH.stat().st_size // 1024} KB)...')
        upload_selectors = [
            'input[type=file]',
            'input[accept=".zip"]',
            'input[accept*="zip"]',
        ]
        uploaded = False
        for sel in upload_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=10_000)
                if el:
                    page.set_input_files(sel, str(ZIP_PATH))
                    uploaded = True
                    log('ZIP selected.')
                    break
            except Exception:
                continue

        if not uploaded:
            log('Cannot find file upload field automatically.')
            log('Please upload the ZIP manually:')
            log(f'  {ZIP_PATH}')
            page.pause()

        # Wait for upload to finish
        time.sleep(4)
        try:
            page.wait_for_selector('text=Upload complete', timeout=30_000)
            log('Upload complete.')
        except PWTimeout:
            log('Continuing (upload may still be processing)...')

        # ── Fill in listing details ────────────────────────────────────────
        step(5, 'Filling in store listing details...')

        # Short description
        short_selectors = [
            '[name*="short"]', 'textarea[placeholder*="short"]',
            '[aria-label*="short description" i]', '[maxlength="132"]',
        ]
        if try_fill(page, short_selectors, SHORT_DESC):
            log('Short description filled.')
        else:
            log(f'Please paste short description manually: "{SHORT_DESC}"')

        time.sleep(0.5)

        # Full description
        full_selectors = [
            '[name*="description"]:not([maxlength="132"])',
            'textarea[aria-label*="description" i]',
            '[data-field="description"] textarea',
        ]
        if try_fill(page, full_selectors, FULL_DESC):
            log('Full description filled.')
        else:
            log('Please paste full description manually (see STORE_ASSETS.md).')

        time.sleep(0.5)

        # Category — Shopping
        cat_selectors = [
            'select[name*="category"]', '[aria-label*="category" i]',
        ]
        for sel in cat_selectors:
            try:
                el = page.query_selector(sel)
                if el:
                    el.select_option(label='Shopping')
                    log('Category set to Shopping.')
                    break
            except Exception:
                continue

        # Privacy policy URL
        priv_selectors = [
            '[name*="privacy"]', 'input[placeholder*="privacy"]',
            '[aria-label*="privacy policy" i]',
        ]
        if try_fill(page, priv_selectors, PRIVACY_URL):
            log('Privacy policy URL filled.')
        else:
            log(f'Please paste privacy URL manually: {PRIVACY_URL}')

        time.sleep(0.5)

        # ── Save draft ─────────────────────────────────────────────────────
        step(6, 'Saving draft...')
        save_selectors = [
            'button:has-text("Save")', 'text=Save draft',
            '[aria-label*="save" i]',
        ]
        if try_click(page, save_selectors):
            time.sleep(3)
            log('Draft saved.')
        else:
            log('Please click Save manually.')
            page.pause()

        # ── Submit for review ──────────────────────────────────────────────
        step(7, 'Submitting for review...')
        submit_selectors = [
            'button:has-text("Submit for review")',
            'text=Submit for review',
            '[aria-label*="Submit" i]',
        ]
        if try_click(page, submit_selectors):
            time.sleep(2)
            # Confirm dialog if it appears
            try_click(page, ['button:has-text("Submit")', 'text=Confirm'], timeout=4000)
            time.sleep(3)
            log('Submitted for review!')
        else:
            log('Please click "Submit for review" manually.')
            page.pause()

        # ── Get Extension ID ───────────────────────────────────────────────
        step(8, 'Reading Extension ID from URL...')
        current_url = page.url
        ext_id = ''
        parts = current_url.split('/')
        for part in parts:
            if len(part) == 32 and part.isalnum():
                ext_id = part
                break

        context.storage_state(path=str(STATE_FILE))

        print(f'''
{"="*54}
  DONE!

  Extension ID : {ext_id if ext_id else "(check dashboard URL)"}
  Dashboard    : {DASHBOARD}
  Review time  : 2-7 business days

  Tell Claude the Extension ID to finish setup.
{"="*54}
''')

        if ext_id:
            id_path = pathlib.Path('C:/Users/kayky/Desktop/walmart-filter-extension/.extension_id')
            id_path.write_text(ext_id)
            log(f'ID saved. Applying to all files...')
            import subprocess
            subprocess.run([sys.executable, 'apply_extension_id.py'],
                           cwd=str(pathlib.Path(__file__).parent))

        input('\nPress Enter to close browser...')
        browser.close()

if __name__ == '__main__':
    run()
