# KAIB2026 대시보드 기술 구조 및 연관관계 분석

본 문서는 `index.html`의 각 탭과 `web/js` 폴더의 스크립트, 그리고 `web/data`의 JSON 데이터 간의 상세 연관관계를 정리합니다. 추가로 프로젝트 내의 TypeScript(`ts`, `tsx`) 파일들의 역할도 포함합니다.

---

## 1. 대시보드 탭별 연관관계 (JS & JSON)

각 탭은 특정 비즈니스 로직 파일과 연결되어 있으며, 공통적으로 `data/budget_db.json`을 기본 데이터 소스로 사용합니다.

| 탭 이름 (ID) | 관련 JS 파일 | 주요 사용 데이터 (JSON) | 주요 기능 및 역할 |
|:---|:---|:---|:---|
| **개요 (overview)** | `js/app.js`, `js/charts.js` | `budget_db.json` | 대시보드 초기화, KPI 카드 계산, 요약 차트 렌더링 |
| **부처별 분석 (department)** | `js/tabs/department.js` | `budget_db.json` | 부처별 예산 규모 비교, 산점도 분석, 부처별 사업 목록 |
| **분야별 분석 (field)** | `js/tabs/field.js` | `budget_db.json` | AI 분야별 예산 트리맵, 부처-분야 교차 히트맵 |
| **유사성 분석 (duplicate)** | `js/tabs/duplicate.js`, `js/network-viz.js` | `similarity_analysis.json`, `hybrid_similarity.json` | 사업간 유사도 분석, 중복 투자 리스크 탐색, 네트워크 그래프 |
| **사업 목록 (projects)** | `js/tab-handler.js`, `js/common.js` | `budget_db.json` | 전체 사업 데이터 테이블, 실시간 검색 및 필터링 |
| **정책 클러스터 (policy)** | `js/policy-cluster.js` | `budget_db.json` | 국가 전략 키워드 기반 사업 그룹화 및 시각화 |
| **비교 분석 (cross-compare)** | `js/cross-compare.js` | `budget_db.json` | 사용자 선택 사업(최대 10개) 간의 1:1 상세 비교 |
| **미래 예산 시뮬레이터 (future)** | `js/future-sim.js` | `budget_db.json` | 연도별 시계열 데이터 기반 향후 5~10년 예산 예측 |
| **예산 인사이트 (insight)** | `js/budget-insight.js` | `budget_db.json` | 이상치 탐지, 예산 집중도(HHI) 분석, 낭비 리스크 도출 |
| **AI 기술 분석 (ai-tech)** | `js/ai-tech.js` | `budget_db.json` | 세부 AI 기술(LLM, Vision 등) 적용 현황 분석 |

---

## 2. 공통 지원 스크립트 (Core JS)

전체 탭에서 공통적으로 참조하는 핵심 파일들입니다.

- **`js/common.js`**: 전역 상태(`window.DATA`), 공통 유틸리티(예산 포맷팅, 데이터 추출 함수 `getBudgetBase` 등), 테마 전환 로직 포함.
- **`js/app.js`**: 애플리케이션 엔트리 포인트. 데이터를 로드(`loadData`)하고 대시보드 구조를 초기화(`initDashboard`).
- **`js/charts.js`**: Chart.js 기반의 모든 시큐리티/시각화 엔진. 필터링된 데이터를 받아 차트로 변환.

---

## 3. TypeScript (`ts`, `tsx`) 파일 분석

`kaib_html` 및 관련 폴더에 위치한 TS/TSX 파일들은 대시보드와 병행하여 운영되는 **개별 상세 페이지 생성 시스템** 또는 **차세대 UI**의 구성 요소입니다.

### 3-1. 핵심 로직 및 인터페이스
- **`kaib_html/project.ts`**: 전체 시스템에서 사용하는 `Project` 객체의 타입을 정의합니다. 사업명, 부처, 예산, 담당자 등 모든 필드에 대한 인터페이스를 제공하여 데이터 안정성을 보장합니다.

### 3-2. 페이지 컴포넌트 (`kaib_html/pages/`)
TypeScript와 React(TSX)를 기반으로 하는 개별 사업 상세 페이지의 UI 템플릿입니다.

| 파일명 | 역할 및 기능 |
|:---|:---|
| **`ProjectList.tsx`** | TSX 기반의 사업 목록 템플릿. 필터링 및 검색 기능 포함. |
| **`ProjectDetail.tsx`** | 특정 사업의 모든 세부 정보를 보여주는 상세 뷰 템플릿. (기본정보, 예산, 담당자, 개요 등) |
| **`Index.tsx`** | TSX 시스템의 메인 엔트리 또는 레이아웃 정의. |
| **`NotFound.tsx`** | 잘못된 접근 시 표시되는 404 페이지. |

---

## 4. 데이터 연계 흐름 (Data Flow)

1. **빌드 단계**: `scripts/pipeline/*.py` 스크립트가 원본 엑셀/PDF를 가공하여 `web/data/*.json` 파일을 생성합니다.
2. **로드 단계**: 브라우저에서 `index.html`이 실행되면 `app.js`가 `fetch`를 통해 JSON 데이터를 `window.DATA`에 저장합니다.
3. **처리 단계**: 각 탭의 JS 파일이 `getOverviewProjects()`와 같은 함수를 통해 필터링된 데이터를 가져옵니다.
4. **시각화 단계**: `charts.js` 또는 개별 탭 JS가 데이터를 Chart.js/D3.js를 사용하여 시각화합니다.
5. **개별 페이지**: `kaib_html`의 로직 또는 `generate_html.py`가 TS/TSX 구조를 참고하여 개별 사업별 정적 HTML을 생성하거나 팝업으로 제공합니다.
