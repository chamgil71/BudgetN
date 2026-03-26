# 📘 KAIB2026 유지보수 종합 가이드라인 (Maintenance Guide)

본 문서는 파이프라인 내부의 스크립트 도구들(`scripts/`)과 프론트엔드(`web/js/`) 파일들이 어떤 역할을 하며, 서로 어떤 DB 파일들(`data/*.json`)과 의존하고 있는지 철저히 해부한 운영자 전용 트러블슈팅 매뉴얼입니다.

---

## 1. 📂 `scripts/` (자동화 스크립트) 파일별 역할 및 연관 데이터

파이프라인의 백엔드를 담당하며 주로 터미널에서 실행되는 파일들입니다. 기능 단위로 서브 디렉토리화 되어있습니다.

### `scripts/pipeline/` (주력 변환 파이프라인)
* **`master_builder.py`**: 시스템의 **핵심 제어 센터**. `build`, `json-build`, `deploy`, `bundle` 4가지 통합 명령어를 수신받아 아래의 서브 스크립트들을 차례로 호출합니다.
* **`excel_manager.py`**: 터미널 명령어를 파싱하여 `convert.py`, `export_xlsx.py` 등으로 제어권을 넘겨주는 라우터 역할을 합니다.
* **`convert.py`**: `input/` 안의 `.xlsx`, `.xlsm`, `.json` 입력 파일들을 쭉 읽어들여 몽땅 파싱한 뒤, 합쳐서 단일 **`output/merged.json`**을 만들어냅니다. `config.yaml` 연도를 기반으로 자동 마이그레이터 엔진이 탑재되어 있으며, `program.code` 해실을 이용해 **영구적인 고정 ID**를 발급합니다.
* **`convert_a4.py`**: A4 요약 양식으로 된 엑셀 특수 포맷을 전담해서 읽는 스크립트입니다. (현재는 `convert.py` 안으로 통합 활용 중)
* **`export_*.py`**: 현재 JSON 상태를 다시 엑셀 포맷으로 역(Reverse) 추출할 때 씁니다.
* **`build_standalone.py`**: 단일 HTML 파일 배포명령(`bundle`)시, HTML 소스를 열어 `<script>`, `<link>` 태그들을 인라인 소스로 압축 삽입해줍니다.
* **`rebuild_embedded.py`**: deploy 명령 시 작동하며, `web/data` 내부의 거대한 JSON 파일 3개를 자바스크립트 변수(`var EMBEDDED_DATA = { ... }`) 파일(`web/js/embedded-*.js`) 형태로 구버전 브라우저 캐싱을 위해 복사/말아줍니다.

### `scripts/analysis/` (AI 텍스트 처리망)
* **`generate_ai_analysis.py`**: `output/merged.json`의 원문 텍스트(사업목적, 키워드, 부서명 등)를 형태소 단위로 분산 스캔하여, TF-IDF 기반의 Jaccard 거리를 계산합니다. 이 파일이 **`similarity_analysis.json`**(중복성 분석)과 **`collaboration_analysis.json`**(협업 분석)을 만들어냅니다.

### `scripts/legacy_tools/` & `utils/` (참고용/잡동사니)
* `data_manager_gui.py` 등 옛날 Streamlit GUI 개발 관련 툴이 보관되어 있으나 현재 파이프라인에선 쓰지 않습니다.
* `refactor_frontend.py` 등은 프론트엔드 연도 하드코딩 일괄 치환 공사에 쓰였던 1회성 스크립트입니다.

---

## 2. 🖥 `web/js/` (프론트엔드 UI) 파일별 역할과 DB 의존성

화면의 각 탭과 차트를 그려내는 브라우저 실행단 코드입니다.

| 파일명 | 역할 및 렌더링 범위 | 구동에 필수적인 DB 파일 (의존성) |
| :--- | :--- | :--- |
| **`app.js`** | `index.html` 최초 로딩 시 전역 변수(`window.DATA`, `window.BASE_YEAR` 등)를 할당하고, 각 탭 클릭 이벤트를 분기해주는 프론트엔드의 **메인 허브**입니다. | `budget_db.json` (가장 먼저 Fetch 시도, 실패시 `embedded-data.js`의 fallback 캐시 작동) |
| **`common.js`** | `getBudgetBase()`, 포배터, 툴팁 표시기능 등 모든 스크립트가 공통으로 가져다 쓰는 유틸 함수 꾸러미입니다. | 없음 (독립 유틸리티) |
| **`dashboard.js`** | **대시보드 개요** 탭. 상단 4개 KPI 박스와, 부처별/분야별 트리맵을 그려냅니다. | `budget_db.json` |
| **`list-view.js`** | **사업 목록** 탭. DataTables를 이용해 수천건의 사업 리스트와 상세 모달창을 띄워줍니다. | `budget_db.json` |
| **`cross-compare.js`** | **상세 비교 설계** 탭. 두 부처를 비교하는 방사형 차트 등을 동적 렌더링합니다. | `budget_db.json` |
| **`future-sim.js`** | **미래 예산 시뮬레이터** 탭. 예산 삭감/증액 시뮬레이션 인터페이스 담당입니다. | `budget_db.json` |
| **`duplicate-sim.js`** | **유사/중복성 분석** 탭. 카드를 펼치고 중복사유 텍스트와 레이더 차트를 동기화하여 그립니다. | `similarity_analysis.json` (필수) + `budget_db.json` |
| **`policy-cluster.js`** | **부처 간 협업분석** 탭. 협업 적합도 랭킹과 추천 리스트를 시각화합니다. | `collaboration_analysis.json` (필수) |
| **`network-viz.js`** | **기술·산업 분포망** 탭. 노드 간의 Force-Directed 그래프 애니메이션을 제어합니다. | `budget_db.json` (가공 없는 자체 로직) |
| **`ai-insight.js`** | **예산 인사이트** 탭. 챗봇 형태의 LLM 인터페이스를 그려줍니다. | 없음 (UI 스크립트 전용) |

> 📌 **UI 색상 규칙**: `budget_db.json`만 순수하게 사용하는 단일 연동 탭(개요, 사업목록 등)은 좌측 메뉴 버튼 색상이 **진한 파란색(`pure-db`)**으로 스타일링되어 있어 유지보수 직관성을 제공합니다.

---

## 3. 🚨 자주 발생하는 문제 상황 및 해결 (Troubleshooting)

### Q1. 파이프라인(`master_builder.py build`) 실행 시 "ID 참조 에러" 혹은 "키가 없습니다"가 뜹니다.
* **원인**: `input/` 의 엑셀이나 구형 JSON 데이터 안에 **"사업코드"(`code`)**, **"사업명"(`project_name`)**, **"부처명"(`department`)** 등 코어 기준 속성이 통째로 비어있기 때문입니다.
* **해결**: 새로 패치된 `convert.py`는 이 3개의 필드를 조합해 MD5 해시로 **영구 고정 ID(`PRJ-ABC...`)**를 안전하게 부여합니다. 엑셀의 원본 셀 값이 누락되지 않았는지 1차로 확인하십시오.

### Q2. 2027년도로 `config.yaml`을 바꿨는데, 화면의 탭 내용 일부가 옛날 연도(2026)로 깨져서 나옵니다!
* **원인**: JSON 연도 필드 마이그레이션과 프론트엔드의 `getBudgetBase()` 동기화가 아직 브라우저 내부 캐시망에 온전히 갱신되지 않은 현상입니다.
* **해결**:
  1. `master_builder.py deploy`를 한 번 더 날려 웹서버 내부 로컬 덮어쓰기를 확실히 수행합니다.
  2. 크롬 기준 브라우저 탭에서 **`Ctrl + F5` (강력 새로고침)** 혹은 **개발자 도구(F12) > Application > Clear storage** 후 새로고침하십시오.

### Q3. "유사/중복성 분석(Duplicate)" 이나 "협업분석(Cluster)" 탭을 클릭했는데 아무것도 나오지 않고 하얀 화면이 유지됩니다.
* **원인**: `similarity_analysis.json` 등의 파일을 브라우저가 읽어오지 못했거나 포맷이 손상되었습니다.
* **해결**:
  1. `master_builder.py json-build`를 실행해 AI 알고리즘망(`generate_ai_analysis.py`)을 강제 재기동시킵니다.
  2. 에러가 복구되지 않는다면 엑셀(`budget_db.json`의 원본)에 빈 텍스트(엔터키 무한반복 등)가 입력되어 NLP 토큰 분석기가 뻗었을 확률이 농후하므로 `logs/` 폴더 내의 변환 에러 로그를 확인합니다.
