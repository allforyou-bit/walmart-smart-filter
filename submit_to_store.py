"""
Chrome Web Store 자동 제출 스크립트
====================================
실행: python submit_to_store.py
필요한 사용자 액션: 브라우저에서 "허용" 클릭 1번
"""

import os, sys, json, time, threading, webbrowser
import urllib.request, urllib.parse, urllib.error
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── 경로 설정 ────────────────────────────────────────────────────────────────

BASE_DIR   = Path(__file__).parent
ZIP_PATH   = BASE_DIR.parent / 'walmart-filter-extension.zip'
CREDS_FILE = BASE_DIR / '.cws_credentials.json'

# ── API 엔드포인트 ────────────────────────────────────────────────────────────

AUTH_URL    = 'https://accounts.google.com/o/oauth2/auth'
TOKEN_URL   = 'https://oauth2.googleapis.com/token'
UPLOAD_URL  = 'https://www.googleapis.com/upload/chromewebstore/v1.1/items'
ITEMS_URL   = 'https://www.googleapis.com/chromewebstore/v1.1/items'
SCOPE       = 'https://www.googleapis.com/auth/chromewebstore'
REDIRECT    = 'http://localhost:9004'

# ── 스토어 등록 내용 ──────────────────────────────────────────────────────────

STORE_DESCRIPTION = """Stop scrolling past third-party sellers. Find the real Walmart deals in seconds.

Walmart Smart Filter is a lightweight browser extension that transforms your Walmart shopping experience:

🔵 WALMART DIRECT FILTER
Automatically filters search results to show only items sold and shipped by Walmart — not third-party marketplace sellers.

🏷️ DEAL BADGES WITH SAVINGS %
Clearance, Rollback, Reduced Price, and Best Seller items are instantly flagged with colored borders and badges showing the exact discount percentage (e.g., "Clearance · −43%").

📊 LIVE DEAL DASHBOARD
Click the extension icon to see:
• How many Clearance / Rollback / Reduced / Best Seller items are on the current page
• Average savings % and best savings % across all deals on the page
• Hover over any count to see a deal preview panel with product thumbnail, name, price, savings %, and star rating — sorted best deal first

✂️ MIN. SAVINGS FILTER
Set a minimum discount threshold: show only deals that are ≥ 10%, ≥ 20%, or ≥ 30% off.

🚚 SHIPPING & PICKUP FILTERS
Filter search results to show only items with free 2-day shipping or in-store pickup available.

⌨️ KEYBOARD SHORTCUT
Press Ctrl+Shift+W (Mac: Cmd+Shift+W) to instantly toggle the Walmart Direct filter.

PRIVACY: Zero data collection. Settings stored locally. No external servers. No tracking.
Privacy Policy: https://allforyou-bit.github.io/walmart-smart-filter/privacy.html"""

# ── OAuth2 Helper ─────────────────────────────────────────────────────────────

auth_code_received = None

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code_received
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in params:
            auth_code_received = params['code'][0]
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = '<!DOCTYPE html><html><body style="font-family:sans-serif;text-align:center;padding:60px"><h2 style="color:#0071ce">Authorization complete!</h2><p>Close this tab and return to the terminal.</p></body></html>'
            self.wfile.write(html.encode('utf-8'))
        else:
            self.send_response(400)
            self.end_headers()
    def log_message(self, *args): pass  # 로그 출력 억제

def get_auth_code(client_id):
    global auth_code_received
    auth_code_received = None
    url = (f'{AUTH_URL}?client_id={urllib.parse.quote(client_id)}'
           f'&redirect_uri={urllib.parse.quote(REDIRECT)}'
           f'&scope={urllib.parse.quote(SCOPE)}'
           f'&response_type=code&access_type=offline&prompt=consent')
    server = HTTPServer(('localhost', 9004), OAuthCallbackHandler)
    t = threading.Thread(target=server.handle_request)
    t.start()
    print('\n[브라우저] Google 계정 로그인 후 "허용" 클릭하세요...')
    webbrowser.open(url)
    t.join(timeout=120)
    server.server_close()
    return auth_code_received

def exchange_code(client_id, client_secret, code):
    data = urllib.parse.urlencode({
        'code': code, 'client_id': client_id, 'client_secret': client_secret,
        'redirect_uri': REDIRECT, 'grant_type': 'authorization_code',
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data, method='POST')) as r:
        return json.loads(r.read())

def get_access_token(client_id, client_secret, refresh_token):
    data = urllib.parse.urlencode({
        'client_id': client_id, 'client_secret': client_secret,
        'refresh_token': refresh_token, 'grant_type': 'refresh_token',
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data, method='POST')) as r:
        return json.loads(r.read())['access_token']

def api_request(method, url, token, data=None, content_type='application/json'):
    headers = {'Authorization': f'Bearer {token}', 'x-goog-api-version': '2'}
    if data is not None and content_type == 'application/json':
        data = json.dumps(data).encode()
        headers['Content-Type'] = 'application/json'
    elif data is not None:
        headers['Content-Type'] = content_type
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f'  API 오류 {e.code}: {body}')
        return None

# ── 메인 실행 ─────────────────────────────────────────────────────────────────

def main():
    print('\n' + '='*52)
    print('  Walmart Smart Filter — Chrome 웹스토어 제출')
    print('='*52)

    # 1. 인증 정보 로드 또는 신규 취득
    creds = {}
    if CREDS_FILE.exists():
        creds = json.loads(CREDS_FILE.read_text())
        print('\n✓ 저장된 인증 정보 발견')
    else:
        print('''
[준비] Google Cloud Console에서 OAuth2 자격증명 만들기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 브라우저에서 아래 URL 접속:
   https://console.cloud.google.com/projectcreate

2. 프로젝트 이름: "WalmartSmartFilter" → 만들기

3. 왼쪽 메뉴 → API 및 서비스 → 라이브러리
   검색: "Chrome Web Store API" → 사용 설정

4. 왼쪽 메뉴 → API 및 서비스 → 사용자 인증 정보
   → + 사용자 인증 정보 만들기 → OAuth 클라이언트 ID
   → 애플리케이션 유형: 데스크톱 앱
   → 이름: WalmartFilter → 만들기

5. 클라이언트 ID와 클라이언트 보안 비밀 복사
''')
        creds['client_id']     = input('Client ID 붙여넣기: ').strip()
        creds['client_secret'] = input('Client Secret 붙여넣기: ').strip()

        code = get_auth_code(creds['client_id'])
        if not code:
            print('✗ 인증 실패. 다시 시도하세요.')
            sys.exit(1)

        tokens = exchange_code(creds['client_id'], creds['client_secret'], code)
        creds['refresh_token'] = tokens.get('refresh_token', '')
        CREDS_FILE.write_text(json.dumps(creds, indent=2))
        print('\n✓ 인증 완료. 자격증명 저장됨.')

    # 2. 액세스 토큰 발급
    print('\n[1/4] 액세스 토큰 발급...')
    token = get_access_token(creds['client_id'], creds['client_secret'], creds['refresh_token'])
    print('  ✓ 완료')

    # 3. ZIP 업로드
    if not ZIP_PATH.exists():
        print(f'✗ ZIP 파일 없음: {ZIP_PATH}')
        sys.exit(1)

    item_id = creds.get('item_id', '')
    zip_data = ZIP_PATH.read_bytes()

    if item_id:
        print(f'\n[2/4] 기존 아이템 업데이트 (ID: {item_id})...')
        url = f'{UPLOAD_URL}/{item_id}?uploadType=media'
        result = api_request('PUT', url, token, data=zip_data, content_type='application/zip')
    else:
        print('\n[2/4] 새 아이템 업로드...')
        url = f'{UPLOAD_URL}?uploadType=media'
        result = api_request('POST', url, token, data=zip_data, content_type='application/zip')

    if not result:
        print('✗ 업로드 실패')
        sys.exit(1)

    item_id = result.get('id', item_id)
    creds['item_id'] = item_id
    CREDS_FILE.write_text(json.dumps(creds, indent=2))
    state = result.get('uploadState', '')
    print(f'  ✓ 업로드 완료 | ID: {item_id} | 상태: {state}')

    if state == 'FAILURE':
        for err in result.get('itemError', []):
            print(f'  오류: {err}')
        sys.exit(1)

    # 4. 스토어 등록 정보 업데이트
    print('\n[3/4] 스토어 등록 정보 입력...')
    listing_data = {
        'item': {
            'kind': 'chromewebstore#item',
            'id': item_id,
            'listing': {
                'en-US': {
                    'description': STORE_DESCRIPTION,
                    'website': 'https://allforyou-bit.github.io/walmart-smart-filter/',
                }
            }
        }
    }
    update_url = f'{ITEMS_URL}/{item_id}?projection=DRAFT'
    upd = api_request('PUT', update_url, token, data=listing_data['item'])
    if upd:
        print('  ✓ 등록 정보 업데이트 완료')
    else:
        print('  ⚠ 등록 정보 업데이트 실패 (수동으로 입력 가능)')

    # 5. 검토 제출
    print('\n[4/4] Chrome 웹스토어 검토 제출...')
    pub_url = f'{ITEMS_URL}/{item_id}/publish'
    pub = api_request('POST', pub_url, token)
    if pub:
        status = pub.get('status', [])
        print(f'  ✓ 제출 완료 | 상태: {status}')
    else:
        print('  ⚠ 자동 제출 실패 — 아래에서 수동 제출하세요:')
        print(f'  https://chrome.google.com/webstore/devconsole')

    print(f'''
{"="*52}
  완료!

  Extension ID : {item_id}
  대시보드     : https://chrome.google.com/webstore/devconsole
  검토 기간    : 보통 2~7 영업일

  Extension ID를 Claude에게 알려주시면
  popup.html과 README에 자동 반영합니다.
{"="*52}
''')

if __name__ == '__main__':
    main()
