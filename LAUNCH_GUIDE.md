# Walmart Smart Filter — Launch Guide
## 순서대로 따라하면 30분 안에 완료됩니다

---

## STEP 1 — GitHub 저장소 만들기 (5분)
> 프라이버시 정책 URL을 위해 필요합니다. Chrome 웹스토어 제출 필수 사항.

1. https://github.com/new 접속
2. Repository name: `walmart-smart-filter`
3. Public 선택 → Create repository
4. 아래 명령어 실행 (터미널/CMD):

```bash
cd "C:\Users\kayky\Desktop\walmart-filter-extension"
git init
git add .
git commit -m "Initial release v1.5.0"
git branch -M main
git remote add origin https://github.com/allforyou-bit/walmart-smart-filter.git
git push -u origin main
```

5. GitHub 저장소 → Settings → Pages → Source: `main` branch, `/docs` folder → Save
6. 2분 후 접속 확인: `https://allforyou-bit.github.io/walmart-smart-filter/`
7. 프라이버시 정책 URL: `https://allforyou-bit.github.io/walmart-smart-filter/privacy.html`

**popup.html 2곳, docs/index.html 1곳의 `EXTENSION_ID` 및 `YOURUSERNAME`을 나중에 교체**

---

## STEP 2 — Ko-fi 계정 만들기 (5분)

1. https://ko-fi.com 접속 → Sign Up (Google 계정으로 빠르게)
2. Username 설정 (예: `walmartsmartfilter`)
3. Page title: `Walmart Smart Filter`
4. **Description (아래 내용 그대로 붙여넣기):**

```
Walmart Smart Filter is a free Chrome extension that helps you find the
best Walmart deals instantly — Clearance, Rollback, and Reduced Price items
highlighted with exact discount %, filtered to Walmart-sold items only.

If the extension saved you money on a purchase, consider buying me a coffee!
Your support helps keep it updated and ad-free.

☕ $3 — "Nice, this is useful"
☕☕ $5 — "I saved $20 on a clearance item!"
☕☕☕ $10 — "Keep adding features!"
```

5. Goal 설정 (선택): "Keep the extension running" → $50/month
6. 완료 후 URL 확인: `https://ko-fi.com/YOUR_USERNAME`

7. **popup.html 수정:**
```
YOURUSERNAME → 실제 Ko-fi 사용자명으로 교체 (2곳)
```

---

## STEP 3 — Walmart 어필리에이트 신청 (15분)

1. https://www.walmart.com/cp/affiliate-program/1229722 접속
2. "Join Now" 또는 Impact.com으로 리다이렉트
3. Impact.com 계정 생성
4. 신청서 작성 시 아래 내용 사용:

**Website URL:** `https://allforyou-bit.github.io/walmart-smart-filter/`

**Traffic source description:**
```
Chrome browser extension "Walmart Smart Filter" with [X] active users.
The extension helps users find clearance, rollback, and reduced-price deals
on Walmart.com. Product links in the deal preview panel drive users directly
to Walmart product pages, resulting in high purchase intent clicks.
```

**Monthly visitors:** 확장 설치 수 (처음엔 100 정도로 시작)

5. 승인 이메일 수신 후 (보통 2~5 영업일) Publisher ID 확인
6. **popup.js 수정:**
```javascript
const AFFILIATE_ID = 'YOUR_PUBLISHER_ID_HERE'; // ← 여기에 입력
```

---

## STEP 4 — Chrome 웹스토어 제출 (15분)

**준비물 체크리스트:**
- [ ] `walmart-filter-extension.zip` (데스크탑에 있음)
- [ ] 프라이버시 정책 URL (STEP 1 완료 후)
- [ ] 스크린샷 4장 (1280×800) — 아래 촬영 가이드 참고
- [ ] 개발자 계정 등록비 $5 (최초 1회)

### 스크린샷 촬영 가이드
Chrome DevTools → 팝업 우클릭 → Inspect → 사이즈 1280×800 설정

| 번호 | 내용 | 방법 |
|------|------|------|
| 1 | Walmart 검색 결과 (필터 ON, 딜 배지 표시) | walmart.com/search?q=clearance |
| 2 | 팝업 화면 전체 (딜 카운트 + 통계 바) | 확장 아이콘 클릭 |
| 3 | 미리보기 패널 (Best Deal 배지 + 별점) | Clearance 셀에 호버 |
| 4 | Min Savings 필터 사용 (≥20% 선택 후 결과) | 설정 변경 후 캡처 |

### 제출 순서
1. https://chrome.google.com/webstore/devconsole 접속
2. $5 개발자 등록비 결제 (최초 1회)
3. "New item" → ZIP 파일 업로드
4. 아래 정보 입력:

**Category:** Shopping
**Language:** English

**Short description (그대로 복사):**
```
Filter Walmart search to Walmart Direct only. Highlights Clearance, Rollback & deals with savings % and star ratings.
```

**Full description:** `STORE_ASSETS.md` 파일의 "Full Description" 섹션 그대로 복사

**Privacy Policy URL:** STEP 1에서 만든 URL
`https://allforyou-bit.github.io/walmart-smart-filter/privacy.html`

5. Submit for review → 보통 2~7 영업일 후 승인
6. 승인 후 Extension ID 확인 → `popup.html` 2곳, `docs/index.html` 1곳 교체

---

## STEP 5 — 제출 후 할 일 (승인 이후)

### Extension ID 교체
```
popup.html  →  EXTENSION_ID 2곳 교체
docs/index.html  →  EXTENSION_ID 1곳 교체
git add . && git commit -m "Add extension ID" && git push
```

### 수익 추적
| 채널 | 확인 위치 | 주기 |
|------|-----------|------|
| Ko-fi 후원 | ko-fi.com/dashboard | 실시간 |
| 어필리에이트 커미션 | impact.com/dashboard | 주간 |
| 설치 수 | chrome.google.com/webstore/devconsole | 일간 |

---

## 완료 후 예상 수익 (보수적 기준)

| 시점 | 설치 수 | Ko-fi | 어필리에이트 | 합계 |
|------|---------|-------|------------|------|
| 1개월 | 50~200 | $0~15 | $0~5 | $0~20 |
| 3개월 | 200~800 | $10~40 | $5~25 | $15~65 |
| 6개월 | 500~2000 | $20~80 | $15~60 | $35~140 |
| 12개월 | 1000~5000 | $40~150 | $30~120 | $70~270 |

**성장 가속 포인트:**
- Reddit r/frugal, r/deals, r/walmart 에 포스팅 (무료, 즉시)
- ProductHunt 런칭
- Chrome 웹스토어 리뷰 10개 넘으면 자연 검색 노출 급증
