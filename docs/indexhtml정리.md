작성하신 `index.html` 파일을 보면 꽤 규모가 있는 대시보드 형태의 플랫폼입니다. 기능이 많아지면서 HTML 파일 하나에 수많은 UI와 차트 캔버스(Canvas)가 몰려 있어, 어디를 지우고 수정해야 할지 막막하게 느껴지시는 것이 당연합니다.

현재 HTML에는 TypeScript(`.ts`) 대신 컴파일된 JavaScript(`.js`) 파일들이 연결되어 있습니다. 프로젝트 구조상 원래 `.ts`로 작업하신 후 `.js`로 빌드하여 연결하셨을 것으로 예상되므로, HTML에 연결된 **`.js` 파일명을 기준**으로 전체 구조와 역할을 쪼개어 설명해 드리겠습니다.

불필요한 부분을 정리(Refactoring)하시기 편하도록 **크게 4가지 영역**으로 나누어 정리했습니다.

---

### 1. 헤더 및 상단 메뉴 영역 (Header)
플랫폼의 제목, 전체 요약 통계, 테마 변경, 내보내기 메뉴가 있는 최상단 영역입니다.

* **HTML 위치:** `<header class="header">`
* **주요 요소:**
    * 총 사업/예산/부처 수 요약 (`#stat-projects`, `#stat-budget` 등)
    * 문서/내보내기 드롭다운 (`#doc-menu`)
    * 테마 선택 및 다크모드 토글 (`#theme-selector`, `#theme-toggle`)
* **연결된 JS 파일:**
    * `js/common.js`: 테마 변경, 메뉴 토글 등 공통 UI 인터랙션
    * `js/app.js`: 요약 통계(KPI) 데이터 초기화 및 바인딩
    * `js/report-logic.js` & `js/notes-pdf.js`: 인쇄용 리포트, PDF, 마크다운 내보내기 및 메모 관리

### 2. 메인 탭 내비게이션 영역 (Tab Navigation)
10개의 메인 분석 탭을 전환하는 버튼들입니다.

* **HTML 위치:** `<nav class="tab-nav">`
* **연결된 JS 파일:** `js/tab-handler.js` (탭 클릭 시 해당하는 `<div class="tab-content">`를 보여주고 숨기는 로직 담당)

---

### 3. 본문 및 차트 영역 (Main Content)
이곳이 가장 복잡한 영역입니다. 탭별로 검색 영역과 차트들이 나뉘어 있습니다. 불필요한 탭이나 차트를 지우시려면 **HTML에서 해당 블록을 지운 뒤, 아래 연결된 JS 파일에서도 해당 차트를 그리는 함수를 지워주시면 됩니다.**

#### ① 개요 탭 (`#tab-overview`)
가장 많은 차트가 모여 있는 대시보드 첫 화면입니다.
* **검색 영역:** `<input id="overview-search">` 통합 텍스트 검색
* **그래프/차트 영역:**
    * `#chart-dept-donut` (부처별 비중), `#chart-type-dist` (유형 분포) 등 기본 차트
    * `#chart-top-increase`, `#chart-waterfall` 등 증감률/워터폴 차트
    * `#chart-field-bubble` (AI 분야 버블 차트)
    * **연결된 JS 파일:** `js/charts.js` (대부분의 Chart.js 기반 그래프 렌더링 담당)
* **심층/분석 영역 (HHI, 이상치 등):**
    * `#domain-heatmap-container`, `#anomaly-list-container`, `#hhi-container` 등
    * **연결된 JS 파일:** `js/budget-advanced.js` (집중도, 이상치 등 고급 분석 로직)

#### ② 부처별 분석 탭 (`#tab-department`)
* **검색/필터:** `<select id="dept-select">` (부처 선택)
* **그래프:** `#chart-dept-bar`, `#scatter-container` 등
* **연결된 JS 파일:** `js/tabs/department.js`

#### ③ 분야별 분석 탭 (`#tab-field`)
* **그래프:** `#treemap-container` (트리맵), `#field-heatmap-container` (히트맵)
* **연결된 JS 파일:** `js/tabs/field.js` (D3.js 기반의 트리맵/히트맵을 그릴 확률이 높음)

#### ④ 유사성 분석 탭 (`#tab-duplicate`)
이 탭은 내부에 또 여러 서브 탭(Sub-tab)을 가지고 있는 매우 복잡한 구조입니다.
* **서브 탭 종류:** 개요, 키워드 검색, 자동 스캔, 네트워크, 하이브리드 등
* **주요 그래프:**
    * `#dup-heatmap-container`, `#chart-dup-radar` (개요 차트들)
    * `#network-svg` (사업 네트워크 시각화)
* **연결된 JS 파일:**
    * `js/tabs/duplicate.js`: 유사성 분석 관련 전반적인 검색, 스캔, 서브 탭 전환 로직
    * `js/network-viz.js`: 노드와 엣지로 이루어진 네트워크 그래프(Network SVG) 렌더링 담당

#### ⑤ 사업 목록 탭 (`#tab-projects`)
* **검색 영역:** `#project-search` 및 각종 다중 필터(부처, 유형, 분야 등)
* **리스트 영역:** `#project-list-container` (데이터 표 및 카드 뷰)
* **연결된 JS 파일:** `js/app.js` 내부의 리스트 렌더링 함수 또는 전용 목록 관리 JS

#### ⑥ 기타 확장 탭 (빈 깡통 형태)
* `#tab-policy`, `#tab-cross-compare`, `#tab-future`, `#tab-insight`, `#tab-ai-tech`
* HTML에는 컨테이너만 있고, 차트나 내용은 JS에서 동적으로 주입하고 있습니다.
* **연결된 JS 파일:** `js/policy-cluster.js`, `js/cross-compare.js`, `js/future-sim.js`, `js/budget-insight.js`, `js/ai-tech.js`

---

### 4. 하단 모달 및 팝업 영역 (Modals)
특정 항목을 클릭했을 때 화면 위로 뜨는 창들입니다.

* **HTML 위치:** 파일 최하단의 `<div class="modal-overlay">` 태그들
* **종류:** `#project-modal` (사업 상세), `#chart-expand-modal` (차트 확대), `#compare-modal` (비교 분석) 등
* **연결된 JS 파일:** 공통 UI이므로 `js/common.js`나 뷰를 생성하는 `js/app.js`에서 제어됩니다.

---

### 💡 깔끔하게 정리(삭제)하는 작업 가이드

만약 특정 탭이나 기능(예: '미래 예산 시뮬레이터' 탭)을 삭제하고 싶으시다면 다음 순서로 작업하시면 에러를 방지할 수 있습니다.

1.  **HTML 삭제:**
    * 상단 탭 내비게이션에서 `<button data-tab="future">` 삭제
    * 본문 영역에서 `<div class="tab-content" id="tab-future">` 전체 블록 삭제
    * 맨 아래 `<script src="js/future-sim.js"></script>` 줄 삭제
2.  **JS 파일 분리/삭제:**
    * 해당 기능 전용 JS 파일(`js/future-sim.js` 및 연관 `.ts` 파일)을 프로젝트 폴더에서 삭제하거나 백업용으로 이동
3.  **의존성(Error) 확인:**
    * 브라우저 개발자 도구(F12)의 Console 창을 열어, 삭제한 HTML 요소(ID)를 찾지 못해 발생하는 Javascript 에러(`null` 에러 등)가 `app.js` 나 `tab-handler.js`에 없는지 확인하고, 해당 호출부도 지워줍니다.

제시하신 구조는 전형적인 **SPA(Single Page Application)** 방식의 화면 전환 구조입니다. 결론부터 말씀드리면, **탭을 클릭할 때마다 새로운 HTML 파일을 불러오는 것이 아니라, 이미 한 페이지(index.html)에 다 들어있는 내용을 Javascript로 보여주거나 숨기는 방식**입니다.

이들이 어떻게 연결되고 작동하는지 핵심 원리를 3가지 포인트로 정리해 드립니다.

### 1. 연결의 핵심: `data-tab`과 `id`의 매핑
HTML에서 버튼과 본문 영역은 이름(값)을 통해 서로를 찾아냅니다.
* **버튼(Trigger):** `<button data-tab="future">`에서 `data-tab`이라는 사용자 정의 속성에 `"future"`라는 이름을 부여했습니다.
* **본문(Target):** `<div class="tab-content" id="tab-future">`에서 `id`를 `"tab-future"`(또는 로직에 따라 `"future"`)로 설정하여 이 구역이 해당 버튼과 짝궁임을 명시합니다.

### 2. 브레인 역할: `js/tab-handler.js`
이 파일 안에 있는 코드가 "연결 고리" 역할을 수행합니다. 대략적인 동작 순서는 다음과 같습니다.
1.  사용자가 `data-tab="future"` 버튼을 클릭합니다.
2.  스크립트가 클릭된 버튼의 `data-tab` 값(`future`)을 읽어옵니다.
3.  화면에 있는 모든 `.tab-content` 클래스를 가진 div들을 찾아 `display: none`으로 숨깁니다.
4.  방금 읽어온 값과 일치하는 `id="tab-future"`를 가진 div만 찾아 `display: block`(또는 active 클래스 추가)으로 화면에 표시합니다.

### 3. 기능의 완성: `js/future-sim.js`
본문 영역(`div`)은 단순히 "그릇"일 뿐입니다. 그 안에 복잡한 그래프를 그리거나 시뮬레이션 로직을 돌리는 실제 기능은 하단에 연결된 `js/future-sim.js`가 담당합니다. 이 스크립트는 로드될 때 `id="tab-future"` 내부의 캔버스나 요소를 찾아가서 데이터를 채웁니다.

---

### 💡 삭제 및 정리 방법 확인
질문하신 대로 특정 기능을 완전히 제거하고 싶다면, 아래 **3단계**를 모두 수행하는 것이 정확합니다.

* **HTML 버튼 삭제:** 사용자가 클릭할 입구를 없앱니다.
* **HTML 본문 영역(div) 삭제:** 화면에 표시될 "그릇"과 메모리를 차지하는 DOM 요소를 없앱니다.
* **JS 스크립트 삭제:** 해당 기능을 실행하기 위해 백그라운드에서 돌아가는 로직(이벤트 리스너, 차트 생성 코드 등)을 제거하여 에러를 방지하고 속도를 높입니다.

이러한 "탭-컨텐츠" 시스템이 내부적으로 어떻게 상태를 관리하는지 시뮬레이션으로 확인해 보세요.

```json?chameleon
{"component":"LlmGeneratedComponent","props":{"height":"600px","prompt":"SPA 탭 시스템의 작동 원리를 시각화하는 시뮬레이터를 제작해줘. \n1. 상단에는 '개요', '부처별', '미래 예측' 세 개의 버튼이 있고, 각각 data-tab='overview', 'dept', 'future' 속성을 가짐.\n2. 버튼을 클릭하면 Javascript 핸들러가 어떻게 작동하는지(모든 컨텐츠 숨기기 -> 특정 ID 보여주기)를 코드 흐름과 함께 시각적으로 보여줘.\n3. 본문 영역은 id='tab-overview', 'tab-dept', 'tab-future'로 구분되어 활성화된 탭만 강조됨.\n4. 하단에는 연결된 전용 JS 파일(예: future-sim.js)이 해당 영역을 제어하고 있다는 관계도를 표시해줘.\n5. 모든 레이블과 설명은 한국어로 작성해줘.","id":"im_7da15510cd338f86"}}
```

이 시뮬레이션을 통해 버튼의 `data-tab` 값이 어떻게 본문의 `id`를 찾아가 활성화하는지 흐름을 이해하실 수 있습니다. 만약 `future` 기능을 삭제한다면, 이 연결 고리 전체(버튼-ID 영역-전용 JS)를 끊어내는 과정이라고 이해하시면 됩니다.

말씀하신 4개 탭(**개요, 부처별 분석, 분야별 분석, 사업 목록**)만 남기고 나머지를 깔끔하게 정리하실 수 있도록, 유지해야 할 부분과 삭제해야 할 부분을 표로 명확하게 정리해 드립니다.

### 🟢 남겨야 할 탭 (유지 목록)

이 4개의 탭과 관련된 HTML 태그 및 스크립트는 **절대 지우시면 안 됩니다.**

| 탭 이름 (화면 표시) | 탭 버튼 속성 (`nav` 영역) | 본문 영역 ID (`main` 영역) | 연관된 핵심 스크립트 (`<script>`) |
| :--- | :--- | :--- | :--- |
| **개요** | `data-tab="overview"` | `id="tab-overview"` | `js/charts.js`<br>`js/budget-advanced.js` |
| **부처별 분석** | `data-tab="department"` | `id="tab-department"` | `js/tabs/department.js` |
| **분야별 분석** | `data-tab="field"` | `id="tab-field"` | `js/tabs/field.js` |
| **사업 목록** | `data-tab="projects"` | `id="tab-projects"` | 별도 파일 없음<br>(`js/app.js`에서 직접 렌더링) |

*(참고: `js/common.js`, `js/app.js`, `js/tab-handler.js`, `js/embedded-data.js` 같은 코어/데이터 파일은 모든 탭이 공통으로 사용하므로 무조건 유지해야 합니다.)*

---

### 🔴 지워야 할 탭 (삭제 목록)

4개만 남기기 위해 `index.html`에서 **삭제해야 할 3가지 요소(버튼, 본문, 스크립트)**입니다. 아래 표를 보시고 HTML 파일에서 해당 줄들을 찾아 과감히 지워주시면 됩니다.

| 삭제 대상 기능 | 1. 탭 버튼 삭제 (`<nav>`) | 2. 본문 영역 삭제 (`<main>`) | 3. 스크립트 삭제 (하단) |
| :--- | :--- | :--- | :--- |
| **유사성 분석** | `<button ... data-tab="duplicate">` | `<div ... id="tab-duplicate">` 전체 | `js/tabs/duplicate.js`<br>`js/network-viz.js`<br>`js/embedded-sim-v10-data.js`<br>`js/embedded-collab-data.js`<br>`js/embedded-hybrid-data.js` |
| **정책 클러스터** | `<button ... data-tab="policy">` | `<div ... id="tab-policy">` | `js/policy-cluster.js` |
| **비교 분석** | `<button ... data-tab="cross-compare">` | `<div ... id="tab-cross-compare">` | `js/cross-compare.js` |
| **미래 예산 시뮬** | `<button ... data-tab="future">` | `<div ... id="tab-future">` | `js/future-sim.js` |
| **예산 인사이트** | `<button ... data-tab="insight">` | `<div ... id="tab-insight">` | `js/budget-insight.js` |
| **AI 기술 분석** | `<button ... data-tab="ai-tech">` | `<div ... id="tab-ai-tech">` | `js/ai-tech.js` |

### 🛠️ 추가 정리 팁
* **유사성 분석(Duplicate) 탭 관련 모달 삭제:** 유사성 분석 기능이 워낙 컸기 때문에, 해당 탭을 지우신다면 HTML 하단부에 있는 `<div class="modal-overlay" id="sim-compare-modal">` 과 `<div class="compare-toolbar" id="compare-toolbar">` 부분도 사용되지 않으므로 함께 지워주시면 코드가 훨씬 가벼워집니다.
* **저장 후 테스트:** HTML에서 코드 블록을 지울 때는 `<div ...>`로 시작해서 짝이 맞는 `</div>`까지 정확하게 지워야 레이아웃이 깨지지 않습니다. 하나씩 지우고 새로고침하여 에러가 없는지 확인하면서 진행하시는 것을 추천합니다.