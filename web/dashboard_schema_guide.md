# KAIB2026 대시보드 데이터 스키마 가이드

이 문서는 KAIB2026 웹 대시보드의 각 탭이 어떤 데이터 스키마를 사용하는지, 그리고 관련 로직이 어떤 파일에 정의되어 있는지 상세히 정리합니다.

---

## 1. 개요 (Overview) 탭

개요 탭은 전체 예산 현황과 주요 지표를 시각화하여 보여주는 대시보드의 메인 화면입니다.

### 1-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `metadata.base_year` | 화면 곳곳의 연도 표기, 지표 계산 기준 연도 설정 |
| | `projects[].department` | 부처별 예산 비중(도넛), 부처별 포트폴리오, 히트맵 등 모든 부처별 분류의 기준 |
| | `projects[].budget.2026_budget` | (기준 연도 확정 예산) KPI 총액, 모든 차트의 Y축/비중 계산의 기본값 |
| | `projects[].budget.2025_original` | (전년도 본예산) 예산 증감액/증감률 계산의 기준값 |
| | `projects[].is_rnd` | R&D 사업 여부 판별 (KPI 카드, 사업 유형 분포 차트 등) |
| | `projects[].is_informatization` | 정보화 사업 여부 판별 (사업 유형 분포 차트 등) |
| | `projects[].status` | '신규' 사업 여부 판별 (신규 vs 계속 분포 차트) |
| | `projects[].account_type` | 회계유형별 예산 구성 차트 분류 |
| | `projects[].ai_domains` | AI 도메인별 버블 차트 및 부처별 히트맵 데이터 구성 |
| | `projects[].sub_projects` | 내역사업 관련 위젯 (집중도, 규모 분포 등) 데이터 구성 |
| | `projects[].purpose`, `description`, `keywords` | 상단 검색바(Overview Search)의 검색 대상 텍스트 |

### 1-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/index.html` | 개요 탭의 HTML 구조 (KPI 그리드, 차트 Canvas 컨테이너) 정의 |
| `web/js/app.js` | 데이터 로드 (`loadData`), 대시보드 초기화 (`initDashboard`), 검색 이벤트 핸들링 |
| `web/js/charts.js` | 개요 탭의 **모든 차트 렌더링 로직** 포함 (`renderOverviewCharts` 등) |

---

## 2. 부처별 분석 (Department Analysis) 탭

부처별 예산 규모, 사업 수, 증감률 등을 심층 비교하고 특정 부처의 사업 목록을 조회합니다.

### 2-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].department` | 데이터 그룹화의 핵심 키. 모든 집계 및 필터링의 기준 |
| | `projects[].budget.2026_budget` | 부처별 총 예산액 합산 및 바 차트/산점도 Y축 |
| | `projects[].budget.2025_original` | 부처별 전년도 예산 합산 및 증감률 계산 |
| | `projects[].name` / `project_name` | 부처별 사업 목록 테이블의 사업명 |

### 2-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/tabs/department.js` | `renderDepartment`, `renderScatterPlot`, `showDeptProjects` 구현 |

---

## 3. 분야별 분석 (Field Analysis) 탭

AI 기술 분야별 예산 비중과 부처별 투자 현황을 트리맵과 히트맵으로 분석합니다.

### 3-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].ai_domains` | 사업이 속한 AI 분야 분류 (트리맵 영역, 히트맵 열) |
| | `projects[].budget.2026_budget` | 분야별 예산 규모 계산 (다중 분야 시 Pro-rata 배분) |

### 3-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/tabs/field.js` | `renderTreemap` (D3.js), `renderFieldHeatmap` 구현 |

---

## 4. 유사성 분석 (Similarity Analysis) 탭

사업명/내용 유사도를 기반으로 부처 간 중복 투자 의심 사업을 그룹화합니다.

### 4-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].project_name` | Jaccard 유사도 분석을 위한 텍스트 토큰화 및 비교 |
| | `analysis.duplicates` | 백엔드(Python)에서 미리 계산된 중복 사업 그룹 데이터 |

### 4-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/tabs/duplicate.js` | `analyzeDuplicates` (실시간 유사도 계산), `renderDupGroups` |
| `web/js/network-viz.js` | 중복 사업 간 관계를 보여주는 네트워크 그래프 시각화 |

---

## 5. 사업 목록 (Project List) 탭

전체 사업을 상세하게 조회, 검색하고 여러 필터(부처, 유형, 분야 등)를 적용합니다.

### 5-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].code` | 사업 코드 표시 및 정렬 |
| | `projects[].project_name` / `name` | 검색 및 목록 표시 (대표 명칭) |
| | `projects[].department` | 소관 부처 필터링 및 그룹화 |
| | `projects[].division` | 담당 실국 표시 |
| | `projects[].implementing_agency` | 주관 시행기관 표시 |
| | `projects[].budget` | 2024~26 예산, 증감액, 증감률 표시 및 정렬 |
| | `projects[].status` | 사업 상태(신규/계속) 필터링 및 표시 |
| | `projects[].sub_projects[]` | 내역사업 모드에서 `name`, `budget_2026` 등 하위 정보 전개 |
| | `projects[].project_managers[]` | 내역사업별 담당 부처 및 시행기관 상세 매핑 |
| | `projects[].ai_domains` / `ai_tech` | 기술 분야 및 AI 기술 태그 필터링 |
| | `projects[].purpose` 외 텍스트 필드 | 상세 내용 기반 다중 키워드 검색 (OR/AND 지원) |

### 5-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/tab-handler.js` | `renderProjects`, `updateProjectList`, `buildFlatRows` 등 목록 관리 핵심 로직 |
| `web/js/common.js` | `getBudgetBase`, `getProjectType`, `formatBillion` 등 공통 유틸리티 |

---

## 6. 정책 클러스터 (Policy Cluster) 탭

AI 국가 전략 및 정책 목표와 사업 간의 연관성을 클러스터 형태로 분석합니다.

### 6-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].name` / `project_name` | 클러스터 내 사업 식별 |
| | `projects[].purpose`, `description` | 테마별 키워드 매칭을 통한 점수 계산 및 분류 |
| | `projects[].keywords`, `ai_domains` | AI 전략 분야와의 연관성 강화 |
| | `projects[].budget.2026_budget` | 테마별 가중 예산 규모 산출 (Pro-rata 배분) |
| | `analysis.keyword_clusters` | (Optional) 백엔드 추출 클러스터링 데이터 활용 |

### 6-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/policy-cluster.js` | `classifyProject` (내부 키워드 엔진), `renderStrategicPortfolio`, `initPolicyClusterTab` |
| `web/css/policy-cluster.css` | 테마별 전용 색상 및 애니메이션 정의 |

---

## 7. 비교 분석 (Cross-Compare) 탭

사용자가 선택한 여러 사업(최대 10개)을 테이블 형태로 1:1 비교합니다.

### 7-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].id` | 선택된 사업 식별용 고유 키 |
| | `projects[].budget` | 3개년 예산 전 시계열 비교 (결산, 본예산, 확정안) |
| | `projects[].purpose` | 사업 목적 텍스트 1:1 비교 (요약본 표시) |
| | `projects[].sub_projects[]` | 하위 내역사업 구성 및 예산 비교 |
| | `projects[].account_type`, `status` | 기본 속성 정보 비교 |

### 7-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/cross-compare.js` | `toggleCompare` (Set 기반 관리), `openCompareModal` (비교 매트릭스 생성) |
| `web/js/tab-handler.js` | 전역 `compareSet` 상태 관리 및 툴바 UI 갱신 |

---

## 8. 미래 예산 시뮬레이터 (Future Simulator) 탭

향후 5~10년간의 예산 변화 추이를 시뮬레이션하고 예측합니다.

### 8-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].yearly_budgets[]` | 과거 시계열 데이터 (2024~26) 기반 추세 분석 |
| | `projects[].department` | 부처별 미래 예산 증가율 시나리오 적용 |
| | `projects[].ai_domains` | AI 기술 분야별 성장률 가중치 계산 |
| | `projects[].budget` | 시뮬레이션 시작점(Base Year) 기준값 제공 |

### 8-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/future-sim.js` | `linearRegression`, `forecast` (예측 엔진), 시나리오 매니저 |
| `web/js/charts.js` | 시뮬레이션 결과 라인 차트 및 영역 차트 렌더링 |

---

## 9. 예산 인사이트 (Budget Insight) 탭

AI 분석을 통해 도출된 예산 운용의 병목 구간, 효율성 개선 제안 등을 보여줍니다.

### 9-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].budget` | 이상치 탐지 (전년 대비 급증/급감 사업 추출) |
| | `analysis.duplicates` | 정책 유사성/중복 투자 리스크 분석 |
| | `projects[].project_period` | 장기 사업의 연차별 예산 투입 효율성 분석 |
| | `projects[].department`, `ai_domains` | 예산 집중도(HHI 지수) 분석 및 산키 다이어그램 흐름 생성 |

### 9-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/budget-insight.js` | `renderAnomaly`, `renderConcentration`, `renderWaste` (인사이트 엔진) |
| `web/js/network-viz.js` | 예산 흐름 산키(Sankey) 및 중복 분석 레이아웃 |

---

## 10. AI 기술 분석 (AI Tech) 탭

사업에 적용된 세부 AI 기술(LLM, Vision, RAG 등)을 분류하고 현황을 분석합니다.

### 10-1. 사용 데이터 및 목적

| 데이터 소스 | 주요 필드 (Schema Key) | 사용 목적 |
|:---|:---|:---|
| `budget_db.json` | `projects[].ai_tech` | 특정 AI 기술의 적용 빈도 및 예산 규모 분석 |
| | `projects[].is_rnd` | R&D 단계(기초/응용/개발) 분류 및 분석 |
| | `projects[].budget.2026_budget` | 기술별 투자 규모 시각화 |

### 10-2. 관련 파일 및 역할

| 파일명 | 역할 및 담당 로직 |
|:---|:---|
| `web/js/ai-tech.js` | `renderTechOverview`, `renderRndStage`, 기술 부처 매트릭스 렌더링 |

---

## 11. `config/template.json`과의 일관성 검증

모든 웹 기능은 `config/template.json`을 기준으로 설계되어 있으며, 데이터 무결성을 위해 다음 원칙을 준수합니다.

| 검증 항목 | 체크포인트 | 일관성 상태 |
|:---|:---|:---:|
| **메타데이터 정합성** | `metadata.base_year`와 프론트엔드 `window.BASE_YEAR` 일치 여부 | ✅ 일치 |
| **사업 필수 필드** | `id`, `name`, `department`, `budget` 필드의 존재 확인 | ✅ 필수 |
| **다차원 분류체계** | `ai_domains`, `ai_tech`, `is_rnd` 필드가 모든 분석 탭의 기초 자료로 활용 | ✅ 활용 중 |
| **시계열 데이터 구조** | `budget` 객체 내부 연도별 키 (`2024_settlement` 등) 명명 규칙 | ✅ 표준화 |
| **분석 데이터 연결** | `analysis.duplicates`, `analysis.keyword_clusters` 등 백엔드 계산값 매핑 | ✅ 연동 완료 |

> [!NOTE]
> `budget_db.json` 생성 시 `template.json`에 정의되지 않은 임의의 키를 추가할 경우, 프론트엔드 logic(`web/js/*.js`)에서 해당 키를 명시적으로 참조하도록 수정해야 시각화에 반영됩니다.
