# 경로 리팩토링 및 데이터 키 정합성 상세 분석

## 1. 개요
최근 `database/` 폴더 기반의 구조 변경과 연도 전환(2026 -> 2027)에 대비하여, 전체 파이프라인의 경로 지정 방식을 표준화하고 웹 대시보드(`web/`)와의 데이터 연동 정합성을 분석합니다.

## 2. 경로 리팩토링 분석

### 2.1 현재 문제점 (구체적 파일 조사 결과)
- **`excel_manager.py` (Line 32)**: 입력 파일 기본값이 `web/data/budget_db.json`으로 하드코딩되어 있습니다.
- **`master_builder.py` (Line 96)**: 배포 대상 경로가 `web/data`로 하드코딩되어 있습니다.
- **`rebuild_embedded.py` (Line 7-10)**: `web/data/`의 JSON을 읽어 `web/js/`의 JS로 변환하는 경로가 하드코딩되어 있습니다.
- **`config.yaml`**: `data/`, `output/` 등 현재 `database/` 하위로 이동된 경로들이 예전 루트 기준 경로로 남아 있습니다.

### 2.2 개선 방안
1.  **`path_config.py` 고도화**:
    - `WEB_DATA_DIR`, `LOGS_DIR` 등 모든 경로를 프로젝트 루트를 기준으로 정의합니다.
    - `ensure_pipeline_dirs()`를 통해 실행 시 필요한 폴더 구조를 자동 생성합니다.
2.  **`config.yaml` 동기화**:
    - 파이프라인에서 참조하는 `input`, `output` 경로를 `database/` 하위로 수정합니다.
3.  **의존성 주입**:
    - 모든 스크립트가 `path_config.py`를 임포트하여 경로를 가져오도록 수정합니다.

---

## 3. 데이터 키(2024, 2025...) 정합성 분석

### 3.1 현재 연도 처리 방식
- **Pipeline (`_years.py`)**: `base_year`를 기준으로 연도를 계산하지만, 결과 JSON 필드명(예: `2024_settlement`)은 일부 하드코딩된 문자열을 포함하고 있습니다.
- **Web (`common.js`)**: `window.BASE_YEAR`를 기준으로 동적 필드명(`budget_${by}`)을 생성하여 데이터를 조회합니다.

### 3.2 핵심 리스크: 연도별 키(Key) 이름 충돌
- **문제**: `_years.py`에서 `col_map`의 값(JSON 필드명)이 `"budget.2024_settlement"` 등으로 **연도 숫자가 포함된 채 하드코딩**되어 있습니다.
- **영상**: 기준 연도가 2027년으로 변경되어도 JSON에는 여전히 `2024_settlement`라는 키로 데이터가 들어갈 수 있으며, 이는 실제 연도(2025년 결산)와 불일치하게 됩니다.
- **Web 영향**: `web/js/common.js`는 `budget_${by}`(예: `budget_2026`) 형태로 데이터를 찾습니다. 파이프라인에서 생성하는 키와 웹에서 기대하는 키 이름 규칙이 다르면 대시보드에 데이터가 표시되지 않습니다.

### 3.3 해결 전략: 완전 자동화(Dynamic) 연도 전환
1.  **`_years.py` 수정**: JSON 필드명 자체도 연도에 따라 변하도록 수정합니다.
    - 예: `2027정부안` -> `budget.2027_budget` (현재는 `2026_budget`으로 고정됨)
2.  **Web JS 하드코딩 제거**: `BASE_YEAR` 기준 상대 연도를 사용하여 라벨을 동적 생성합니다.
    - 수정 대상: `policy-cluster.js`, `charts.js`, `budget-insight.js` 등
    - 예: `'2025 예산'` -> `${window.BASE_YEAR - 1} 예산`
3.  **메타데이터 연동**: `master_builder.py`에서 `config.yaml`의 `base_year`를 `merged.json`의 메타데이터로 정확히 주입하고, 웹 앱이 이를 최우선으로 참조하게 합니다. (현재 이미 일부 구현됨)

---

## 4. 경로 리팩토링 상세 (database/ 중심)
- **`path_config.py`**에 다음 상수 추가:
  - `WEB_DIR = PROJECT_ROOT / "web"`
  - `WEB_DATA_DIR = WEB_DIR / "data"`
  - `LOGS_DIR = PROJECT_ROOT / "logs"`
- **`config.yaml`**의 `paths` 섹션 업데이트:
  - `input: database/src`
  - `output: database/output`
  - `data_dir: database/raw`

## 5. 다음 단계 (예정)
1.  `path_config.py` 수정 (상수 추가 및 구조 정리)
2.  `_years.py` 수정 (하드코딩된 필드명 제거 및 동적 생성)
3.  `config.yaml` 경로 값 일괄 업데이트
4.  파이프라인 전체 동작 테스트
