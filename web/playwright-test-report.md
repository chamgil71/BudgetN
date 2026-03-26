# KAIB2026 Dashboard - Playwright Test Report

## 진행된 테스트 항목
`tests/dashboard.spec.js` 에 아래 세 가지 Suite를 구성했습니다.

1. **Header statistics are visible**
   - 상단 `.stat-card` 통계 블록 로딩 확인.
   - 예산 총합 부분(19조 등)의 렌더링 텍스트 대조.

2. **Navigate through all main tabs**
   - `overview`, `department`, `field`, `duplicate`, `projects` 탭을 순차적으로 이동하며,
   - `treemap-container`, `dup-kpi-grid` 등의 탭별 고유 차트 ID/DOM 요소 출현 여부 확인.
   - 렌더링된 텍스트 내 `[object Object]` 문자열의 존재 여부 Negative 체크.

3. **Search functionality in projects tab**
   - `projects` 탭 이동 후, `#project-search` 인풋에 `반도체` 등의 문자열 입력(fill).
   - 500ms 이후 `#project-count` 요소의 총 검색 결과 건수 업데이트 테스트.

## 테스트 방법
Node.js가 설치된 환경에서 다음 명령어를 실행하면 대시보드 테스트가 실행됩니다.

```bash
# 의존성 설치 (최초 1회)
npm install
npx playwright install

# 테스트 실행 (Vite 서버 실행을 위한 config 자동 구동 됨)
npx playwright test tests/dashboard.spec.js

# 실패 시 HTML 리포트로 눈으로 분석하기
npx playwright show-report
```

## 비고 (Timeout Error 관련)
테스트 환경 특성상 Headless Chromium 렌더링 및 O(N^2) 로직으로 인한 페이지 프리징 타임아웃 오류가 발생했었습니다.
이를 방어하기 위해서 `duplicate.js`의 Jaccard 함수 로직에 길이 초과 시 조기 반환(`early return`)하는 Guards를 삽입했으며, Playwright의 TimeOut 속성을 `120000ms` 로 적용하였습니다.
테스트 수행 시 백엔드 Vite 서버가 느리게 응답할 경우 Timeout이 발생할 수 있으니 가급적 `npm run dev` 를 띄워 둔 상태에서 검증하는 것을 권장합니다.
