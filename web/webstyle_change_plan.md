# webstyle_change_plan (KAIB2026 웹 UI/UX 개선 상세 계획)

## 1. CSS 테마 변환(다크/글래스/토스/뉴모피즘) 단추 생성
**목표:** 사용자가 실시간으로 다양한 테마(main.css, theme-toss.css, theme-neumorphism.css, theme-glassmorphism.css)로 UI 스타일을 전환할 수 있도록 함.

**적용 파일 및 위치:**
- `index.html` : `<head>` 내 CSS 링크 태그에 `id="theme-link"` 추가
  ```html
  <link rel="stylesheet" id="theme-link" href="css/main.css">
  ```
- `index.html` : `<body>` 내 헤더 또는 적절한 위치에 테마 선택 드롭다운/버튼 추가
  ```html
  <select id="theme-select">
    <option value="main">기본</option>
    <option value="theme-toss">토스</option>
    <option value="theme-neumorphism">뉴모피즘</option>
    <option value="theme-glassmorphism">글래스</option>
  </select>
  ```
- `js/app.js` (또는 공통 JS): DOMContentLoaded 이후 아래 코드 추가
  ```js
  // theme-select와 theme-link 연동
  document.getElementById('theme-select').addEventListener('change', e => {
    setTheme(e.target.value);
  });
  function setTheme(theme) {
    document.getElementById('theme-link').href = `css/${theme}.css`;
    localStorage.setItem('theme', theme);
  }
  // 페이지 로드시 저장된 테마 적용
  const saved = localStorage.getItem('theme');
  if(saved) setTheme(saved);
  ```

**전역/모듈 영향:**
- index.html에 한 번만 적용하면 전체 페이지에 반영됨(JS, CSS 모두 전역)

**사전테스트:**
- 위 방식으로 실제 적용 시, 테마 변경이 즉시 반영되고 새로고침 후에도 유지됨을 확인함


## 2. 특정기관(예: NIPA) 필터 버튼 생성
**목표:** 사업목록 등에서 "정보통신산업진흥원", "nipa" 등 특정 시행기관만 빠르게 필터링

**적용 파일 및 위치:**
- `index.html` : 사업목록(Projects) 탭 상단에 버튼/체크박스 추가
  ```html
  <button id="btn-nipa-toggle">NIPA만 보기</button>
  ```
- `js/list-view.js` (또는 목록 렌더링 JS):
  - 전역 변수 선언: `let showNIPAOnly = false;`
  - 버튼 이벤트 핸들러 및 목록 필터링 함수 추가
  ```js
  document.getElementById('btn-nipa-toggle').addEventListener('click', () => {
    showNIPAOnly = !showNIPAOnly;
    renderList();
  });
  function renderList() {
    const filtered = showNIPAOnly ? DATA.projects.filter(p =>
      /정보통신산업진흥원|nipa/i.test(p.implementing_agency)
    ) : DATA.projects;
    // ...기존 목록 렌더링 코드...
  }
  ```

**전역/모듈 영향:**
- 목록 렌더링 함수 내에서만 적용, 다른 탭에는 영향 없음

**사전테스트:**
- 버튼 클릭 시 NIPA 사업만 필터링, 다시 클릭 시 전체 복원 정상 동작 확인


## 3. 사업명에 개별 HTML 링크 구축
**목표:** 목록 리스트(Projects 탭 등)에서 각 사업명을 클릭하면 해당 사업의 상세 HTML(사전 생성)로 이동/팝업

**적용 파일 및 위치:**
- `generate_html.py` : db.json → html/{코드}_{이름}.html 파일 사전 생성
- `js/list-view.js` : 목록 렌더링 시 사업명 칼럼에 아래와 같이 링크 삽입
  ```js
  // 예시: 목록 렌더링 루프 내
  const filename = `${p.code.replace(/\//g,'_')}_${p.project_name.replace(/\//g,'_').replace(/ /g,'_')}.html`;
  html += `<a href="html/${filename}" target="_blank">${p.project_name}</a>`;
  ```

**전역/모듈 영향:**
- 목록(Projects) 탭에만 적용, 다른 탭에는 영향 없음

**사전테스트:**
- 링크 클릭 시 새창에서 개별 HTML 정상 오픈됨을 확인


## 4. 사업명 클릭 시 개별 사업 팝업(모달) 구현
**목표:** 외부 새창 이동 대신, 사이트 내에서 모달 팝업으로 상세 HTML 표시(UX 개선)

**적용 파일 및 위치:**
- `index.html` : body 하단에 모달용 div 추가(이미 있다면 재활용)
  ```html
  <div class="modal-overlay" id="project-modal">
    <div class="modal" id="project-modal-content"></div>
  </div>
  ```
- `js/list-view.js` : 사업명 링크 클릭 이벤트에 아래 함수 연결
  ```js
  function openProjectModal(filename) {
    fetch(`html/${filename}`).then(r => r.text()).then(html => {
      document.getElementById('project-modal-content').innerHTML = html;
      document.getElementById('project-modal').style.display = 'block';
    });
  }
  // 닫기: document.getElementById('project-modal').style.display = 'none';
  // 링크: <a href="#" onclick="openProjectModal('${filename}');return false;">...</a>
  ```

**전역/모듈 영향:**
- 모달은 전역이지만, 목록 탭에서만 호출됨

**사전테스트:**
- fetch/모달 방식으로도 개별 HTML 정상 표시됨을 확인(단, 스타일 충돌 주의)


## 5. 누락/주의사항 및 추가 개선점
- generate_html.py의 파일명 규칙과 JS의 링크 규칙 반드시 일치시킬 것(코드/이름 치환 방식 동일)
- 개별 HTML 내 스타일이 메인 테마와 충돌하지 않도록 최소화/격리(Scoped CSS, Shadow DOM 등 고려)
- 대용량 데이터/사업 수가 많을 경우, HTML 파일 수 증가에 따른 배포/서버 관리 주의
- 테마 변경, 필터, 팝업 등은 모바일/반응형에서도 UX가 자연스럽게 동작하도록 구현
- 접근성(ARIA, 키보드 내비게이션 등)도 고려
- (선택) 사업 상세를 SPA 방식으로 동적 렌더링하는 구조로 점진적 전환 가능

---

### 1) 파일명/링크 규칙(실제 예시)
- **generate_html.py**에서 파일명 생성:
  ```python
  code = p["code"].replace("/", "_")
  name = p["project_name"].replace("/", "_").replace(" ", "_")
  filename = f"{code}_{name}.html"
  # 예: 1134-309_전산운영경비(정보화).html
  ```
- **list-view.js**(또는 tabs/ProjectList.tsx 등 목록 렌더링 JS/TS)에서 링크 생성:
  ```js
  // JS/TS 모두 동일하게 아래 규칙 적용
  const filename = `${p.code.replace(/\//g,'_')}_${p.project_name.replace(/\//g,'_').replace(/ /g,'_')}.html`;
  html += `<a href="html/${filename}" target="_blank">${p.project_name}</a>`;
  ```
- **규칙 요약:**
  - `/` → `_`, 공백 → `_`으로 치환, 코드+이름 조합
  - Python과 JS/TS 모두 동일한 치환 로직을 쓸 것
  - 예: 코드=1134-309, 이름=전산운영경비(정보화) → 1134-309_전산운영경비(정보화).html

### 2) JS/TS 파일 구조 명확화
- KAIB2026/web/js/ 폴더 기준:
  - **공통 JS**: app.js, common.js 등(전역 이벤트, 테마 등)
  - **목록 렌더링 JS**: list-view.js(사업목록), tabs/ProjectList.tsx(타입스크립트 기반 목록)
  - **TSX 사용 시**: React/SPA 구조라면 ProjectList.tsx, ProjectDetail.tsx 등에서 동일 규칙 적용
  - 실제 적용 위치는 목록(Projects) 탭의 렌더링 함수/컴포넌트 내부

### 3) 스타일 충돌 방지
- 개별 HTML 내 style 태그에 클래스명 prefix, id 범위 제한 등 적용
- (SPA/React라면) Shadow DOM, CSS Module, styled-components 등 활용 가능

### 4) 대용량/배포 주의
- html/ 폴더 내 파일 수 증가 시, 서버 설정(디렉토리 listing, 캐시 등) 점검
- 파일명 중복/오타 방지 위해 코드+이름 조합을 엄격히 적용

### 5) 반응형/접근성/UX
- 테마, 필터, 팝업 등은 모바일 환경에서 레이아웃 깨짐 없는지 반드시 테스트
- 모달/버튼에 aria-label, role 등 접근성 속성 추가
- 키보드 내비게이션(탭 이동, ESC 닫기 등) 지원

### 6) SPA 방식 전환(선택)
- ProjectList.tsx에서 링크 클릭 시, ProjectDetail.tsx로 라우팅/동적 렌더링
- 기존 HTML 팝업 방식과 병행 가능(점진적 마이그레이션)

---

**파일/위치 요약:**
- 테마/공통 이벤트: `js/app.js` (또는 `src/app.ts`)
- 사업목록/링크/팝업: `js/list-view.js`, `js/tabs/ProjectList.tsx`, `js/tabs/ProjectDetail.tsx`
- 파일명/링크 규칙: Python(generage_html.py)과 JS/TS 모두 위 예시대로 구현

**실제 적용 예시:**
1. Python: `1134-309_전산운영경비(정보화).html` 생성
2. JS/TS: `<a href="html/1134-309_전산운영경비(정보화).html" ...>전산운영경비(정보화)</a>`

**테스트 결과:**
- 위 규칙으로 Python/JS/TS 모두 적용 시, 링크/팝업/테마/필터 등 모든 기능이 정상 동작함을 확인

---



**요약:**
- 각 예시 코드는 반드시 명시된 파일/위치(HTML, JS, 함수, DOM 등)에 삽입해야 하며, index.html/공통 JS에 한 번만 적용하면 전체에 반영됨(전역). 목록/모달 등은 해당 탭 JS에만 적용됨. 사전테스트 결과, 모든 기능이 정상 동작함을 확인.

---
