# -*- coding: utf-8 -*-
"""
Chrome Web Store Auto Submit — API Method
=========================================
User action required: ONE click of "Allow" in the browser (Google security requirement).
Everything else is fully automated.

Run: python cws_submit.py
"""

import sys, os, json, time, pathlib, webbrowser, urllib.request, urllib.parse, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

BASE     = pathlib.Path(__file__).parent
ZIP_PATH = BASE.parent / 'walmart-filter-extension.zip'
CREDS    = BASE / '.cws_creds.json'

# Chrome Web Store API
UPLOAD_URL = 'https://www.googleapis.com/upload/chromewebstore/v1.1/items'
ITEMS_URL  = 'https://www.googleapis.com/chromewebstore/v1.1/items'
TOKEN_URL  = 'https://oauth2.googleapis.com/token'
AUTH_URL   = 'https://accounts.google.com/o/oauth2/v2/auth'
SCOPE      = 'https://www.googleapis.com/auth/chromewebstore'
PORT       = 9005

FULL_DESC = """\
Stop scrolling past third-party sellers. Find real Walmart deals in seconds.

WALMART DIRECT FILTER
Automatically filters search results to Walmart-sold items only. No third-party marketplace sellers. One click to toggle.

DEAL BADGES WITH SAVINGS %
Clearance, Rollback, Reduced Price, and Best Seller items highlighted with colored borders and the exact discount % on each card. Example: "Clearance - 43% off".

LIVE DEAL DASHBOARD
Click the extension icon to see the count of each deal type, average savings % and best savings % on the current page. Hover any count for a preview panel showing product thumbnails, prices, and star ratings sorted best-first.

MIN. SAVINGS FILTER
Set a minimum threshold. Show only deals that are 10%, 20%, or 30% or more off. Cut through the noise.

SHIPPING & PICKUP FILTERS
Filter results to free 2-day shipping or in-store pickup items only.

KEYBOARD SHORTCUT
Press Ctrl+Shift+W (Mac: Cmd+Shift+W) to instantly toggle the Walmart Direct filter.

PRIVACY: Zero data collection. Settings stored locally in your browser only. No external servers. No analytics. No tracking.
Privacy Policy: https://allforyou-bit.github.io/walmart-smart-filter/privacy.html"""

SHORT_DESC = "Filter Walmart search to Walmart Direct only. Highlights Clearance, Rollback & deals with savings % and star ratings."
PRIVACY_URL = 'https://allforyou-bit.github.io/walmart-smart-filter/privacy.html'

# ── OAuth2 server ─────────────────────────────────────────────────────────────

_auth_code = None

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        if 'code' in params:
            _auth_code = params['code'][0]
            html = (
                '<html><body style="font-family:sans-serif;text-align:center;padding:80px;background:#f0f7ff">'
                '<h2 style="color:#0071ce">Authorization Complete</h2>'
                '<p style="font-size:16px">You can close this tab.<br>'
                'The extension is being submitted automatically.</p>'
                '</body></html>'
            )
            self.wfile.write(html.encode('utf-8'))
            threading.Thread(target=self.server.shutdown, daemon=True).start()
        else:
            html = '<html><body>Authorization failed — close and retry.</body></html>'
            self.wfile.write(html.encode('utf-8'))
    def log_message(self, *a): pass

def _get_auth_code(client_id):
    global _auth_code
    _auth_code = None
    params = urllib.parse.urlencode({
        'client_id': client_id, 'redirect_uri': f'http://localhost:{PORT}',
        'scope': SCOPE, 'response_type': 'code',
        'access_type': 'offline', 'prompt': 'consent',
    })
    auth_url = f'{AUTH_URL}?{params}'
    server = HTTPServer(('localhost', PORT), _Handler)
    server.timeout = 600
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f'\n  AUTH URL:\n  {auth_url}\n')
    webbrowser.open(auth_url)
    print('  Waiting up to 10 minutes for authorization...')
    t.join(timeout=610)
    server.server_close()
    return _auth_code

def _exchange(client_id, secret, code):
    data = urllib.parse.urlencode({
        'code': code, 'client_id': client_id, 'client_secret': secret,
        'redirect_uri': f'http://localhost:{PORT}', 'grant_type': 'authorization_code',
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data)) as r:
        return json.loads(r.read())

def _refresh(client_id, secret, refresh_token):
    data = urllib.parse.urlencode({
        'client_id': client_id, 'client_secret': secret,
        'refresh_token': refresh_token, 'grant_type': 'refresh_token',
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data)) as r:
        return json.loads(r.read())['access_token']

def _api(method, url, token, data=None, binary=False):
    headers = {'Authorization': f'Bearer {token}', 'x-goog-api-version': '2'}
    if binary:
        headers['Content-Type'] = 'application/zip'
    elif data is not None:
        data = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='replace')
        print(f'    API error {e.code}: {body[:300]}')
        return None

# ── Google Cloud auto-setup ───────────────────────────────────────────────────

GC_PROJECTS  = 'https://cloudresourcemanager.googleapis.com/v1/projects'
GC_SERVICES  = 'https://serviceusage.googleapis.com/v1/projects/{proj}/services/chromewebstore.googleapis.com:enable'
GC_OAUTH_URL = 'https://console.developers.google.com/apis/credentials'

def setup_google_cloud():
    """
    Guide user through minimal Google Cloud setup.
    Returns (client_id, client_secret).
    """
    print("""
  Google Cloud OAuth2 Setup (one-time, ~3 minutes)
  ─────────────────────────────────────────────────
  Opening browser to Google Cloud Console...
  Follow these steps:

  1. Create project named "WalmartFilter" → click Create
  2. Left menu → APIs & Services → Library
     Search "Chrome Web Store API" → Enable
  3. Left menu → APIs & Services → Credentials
     → + Create Credentials → OAuth client ID
     → Application type: Desktop app
     → Name: WalmartFilter → Create
  4. Copy the Client ID and Client Secret shown
  5. Paste them below
  ─────────────────────────────────────────────────
""")
    webbrowser.open('https://console.cloud.google.com/projectcreate')
    time.sleep(2)
    webbrowser.open('https://console.cloud.google.com/apis/library/chromewebstore.googleapis.com')

    client_id     = input('  Paste Client ID     : ').strip()
    client_secret = input('  Paste Client Secret : ').strip()
    return client_id, client_secret

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print('\n' + '='*56)
    print('  Walmart Smart Filter — Chrome Web Store Submit')
    print('='*56)

    if not ZIP_PATH.exists():
        print(f'\n  ERROR: ZIP not found: {ZIP_PATH}')
        sys.exit(1)
    print(f'\n  ZIP: {ZIP_PATH.name} ({ZIP_PATH.stat().st_size // 1024} KB)')

    # Load or create credentials
    creds = json.loads(CREDS.read_text()) if CREDS.exists() else {}

    if not creds.get('client_id'):
        creds['client_id'], creds['client_secret'] = setup_google_cloud()

    # Get access token
    if creds.get('refresh_token'):
        print('\n  [Auth] Refreshing token...')
        try:
            token = _refresh(creds['client_id'], creds['client_secret'], creds['refresh_token'])
            print('  [Auth] Token refreshed.')
        except Exception as e:
            print(f'  [Auth] Refresh failed ({e}). Re-authorizing...')
            creds.pop('refresh_token', None)
            token = None
    else:
        token = None

    if not token:
        print('\n  [Auth] Opening browser for Google authorization...')
        print('  ACTION NEEDED: Click "Allow" in the browser window.')
        print('  This is required once by Google. All else is automatic.\n')
        code = _get_auth_code(creds['client_id'])
        if not code:
            print('  ERROR: Authorization not received. Please try again.')
            sys.exit(1)
        tokens = _exchange(creds['client_id'], creds['client_secret'], code)
        creds['refresh_token'] = tokens.get('refresh_token', '')
        token = tokens.get('access_token', '')
        CREDS.write_text(json.dumps(creds, indent=2))
        print('  [Auth] Authorized. Session saved for future runs.')

    CREDS.write_text(json.dumps(creds, indent=2))

    # ── Upload ZIP ─────────────────────────────────────────────────────────
    print('\n  [1/4] Uploading ZIP to Chrome Web Store...')
    zip_bytes = ZIP_PATH.read_bytes()
    item_id = creds.get('item_id', '')

    if item_id:
        url    = f'{UPLOAD_URL}/{item_id}?uploadType=media'
        result = _api('PUT', url, token, data=zip_bytes, binary=True)
    else:
        url    = f'{UPLOAD_URL}?uploadType=media'
        result = _api('POST', url, token, data=zip_bytes, binary=True)

    if not result:
        print('  ERROR: Upload failed.')
        sys.exit(1)

    item_id = result.get('id', item_id)
    state   = result.get('uploadState', '')
    creds['item_id'] = item_id
    CREDS.write_text(json.dumps(creds, indent=2))
    print(f'  [1/4] Upload complete. ID: {item_id} | State: {state}')

    if state == 'FAILURE':
        for err in result.get('itemError', []):
            print(f'         Error: {err}')
        sys.exit(1)

    # ── Update listing ─────────────────────────────────────────────────────
    print('\n  [2/4] Updating store listing...')
    listing = {
        'kind': 'chromewebstore#item',
        'id':   item_id,
        'listing': {
            'en-US': {
                'description':       FULL_DESC,
                'detailedDescription': FULL_DESC,
            }
        }
    }
    upd = _api('PUT', f'{ITEMS_URL}/{item_id}?projection=DRAFT', token, data=listing)
    if upd:
        print('  [2/4] Listing updated.')
    else:
        print('  [2/4] Listing update skipped (fill in Chrome Web Store dashboard).')

    # ── Submit for review ──────────────────────────────────────────────────
    print('\n  [3/4] Submitting for review...')
    pub = _api('POST', f'{ITEMS_URL}/{item_id}/publish', token)
    if pub:
        status = pub.get('status', [])
        print(f'  [3/4] Submitted. Status: {status}')
    else:
        print('  [3/4] Submit via API failed.')
        print(f'         Complete manually: https://chrome.google.com/webstore/devconsole')

    # ── Apply Extension ID to files ────────────────────────────────────────
    print('\n  [4/4] Applying Extension ID to project files...')
    import subprocess
    subprocess.run([sys.executable, 'apply_extension_id.py', item_id], cwd=str(BASE))

    print(f"""
{"="*56}
  DONE!

  Extension ID : {item_id}
  Dashboard    : https://chrome.google.com/webstore/devconsole
  Review time  : 2-7 business days

  Extension URL (after approval):
  https://chromewebstore.google.com/detail/{item_id}
{"="*56}
""")

if __name__ == '__main__':
    main()
