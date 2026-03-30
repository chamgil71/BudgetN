# KAIB2026 경로 리팩토링 실행 계획 (Implementation Plan)

이 문서는 `database/` 폴더 기반으로 프로젝트의 경로 지정을 통합 관리하기 위한 실행 계획을 담고 있습니다. 실제 작업은 수행되지 않았으며, 추후 작업 시 가이드로 활용하시기 바랍니다.

## 1. 개요
*   **목표**: `database/` 하위로 이동된 데이터 폴더 구조에 맞춰 모든 스크립트의 경로 참조 방식을 동기화하고, 하드코딩된 경로를 중앙 관리형(`./scripts/utils/path_config.py`)으로 전환합니다.

## 2. 단계별 작업 내용

### Step 1: 중앙 설정 업데이트
*   **`config/config.yaml`**: `paths` 섹션의 모든 경로를 `database/` 하위 경로로 수정합니다.
*   **`scripts/utils/path_config.py`**: 웹 배포용 경로(`WEB_DATA_DIR = PROJECT_ROOT / "web" / "data"`) 등을 추가 정의합니다.

### Step 2: 파이프라인 스크립트 리팩토링
*   **`scripts/pipeline/master_builder.py`**:
    *   코드 내 하드코딩된 `"output/merged.json"`, `"web/data"` 등을 `path_config.py`의 상수로 교체합니다.
*   **`scripts/pipeline/convert.py`**:
    *   입력/출력 기본 디렉토리를 `path_config.py`를 통해 가져오도록 수정합니다.

### Step 3: 전처리 및 레거시 도구 리팩토링
*   **`scripts/preProc/main_cli.py`**:
    *   `__init__` 함수 내부의 중복된 경로 정의를 제거하고 `path_config.py` 참조로 일원화합니다.
*   **`scripts/legacy_tools/sync_data.py`**:
    *   `web/data/budget_db.json` 등 하드코딩된 파일 경로를 `path_config.py` 기반으로 수정합니다.

## 3. 예상 결과 (Expected Outcome)
*   **유지보수성 향상**: 폴더 구조가 변경될 경우 `path_config.py` 한 곳만 수정하면 프로젝트 전체에 반영됩니다.
*   **안정성 확보**: 경로 오타 등으로 인한 파이프라인 실행 에러를 방지합니다.
*   **가독성 증대**: 각 스크립트가 어떤 데이터를 어디서 가져오고 어디에 저장하는지 명확해집니다.

---
**주의**: 이 계획 문서는 참고용이며, 실제 파일 수정은 포함되지 않았습니다.
