# Scripts 폴더 구조 및 역할

> 작성일: 2026-04-28

`scripts/` 하위 3개 폴더는 모두 **운영 코드가 아니라 마이그레이션·리팩터링 과정에서 사용한 유틸리티**입니다.

---

## 1. `scripts/legacy_tools/` — 데이터 변환 및 관리 도구

이전 KAIB2026 프로젝트에서 사용하던 데이터 처리 스크립트 모음입니다.

| 파일 | 역할 |
|------|------|
| `convert_csv_to_json.py` | CSV 템플릿(projects, sub-projects)을 `budget_raw.json` / `budget_db.json`으로 변환 |
| `data_manager_gui.py` | Streamlit 기반 GUI — JSON/CSV 데이터를 브라우저에서 조회·편집 |
| `filter_budget_by_dept.py` | `budget_db.json`에서 특정 부서(department)만 필터링해 별도 JSON으로 저장 |
| `json_to_csv_xlsx.py` | `budget_db.json`을 CSV 또는 XLSX로 내보내기 |
| `sync_data.py` | `budget_db.json` ↔ `similarity_analysis.json` 동기화 (웹 데이터 일관성 유지) |

---

## 2. `scripts/refactor_tools/` — HTML 분리 리팩터링 도구

거대한 단일 `index.html`에서 JS 코드·데이터를 외부 파일로 분리할 때 사용한 일회성 도구들입니다.

| 파일 | 역할 |
|------|------|
| `clean_html.py` | HTML 내 인라인 `<script>` 블록을 제거하고 외부 JS 파일 `<script src="...">` 태그로 교체 |
| `extract_all_data.py` | `EMBEDDED_*` 상수들을 각각 별도 `.js` 파일로 일괄 추출 |
| `extract_data.py` | `EMBEDDED_SIM_V10_DATA`, `EMBEDDED_COLLAB_DATA` 두 개를 특정 라인 번호 기준으로 추출 |
| `extract_logic.py` | `<script>` 블록에서 데이터 상수를 제외한 로직 코드만 추출해 `all-logic-extracted.js`로 저장 |
| `find_large_lines.py` | 100KB 이상인 초대형 라인을 찾아 출력 (리팩터링 대상 탐색용) |

---

## 3. `scripts/utils/` — 코드 일괄 치환 유틸리티

JS/HTML/CSS의 연도 하드코딩을 동적 변수로 교체하는 리팩터링 헬퍼들입니다.

| 파일 | 역할 |
|------|------|
| `merge_configs.py` | 루트의 구 `config.yaml`을 `config/config.yaml`로 병합 (설정 구조 정리 시 사용) |
| `refactor_common.py` | `common.js`에서 `getBudget2026` → `getBudgetBase`, `budget_2026` → `budget_base` 등으로 치환해 연도 독립적으로 변경 |
| `refactor_frontend.py` | `web/js/` 전체 JS 파일에 같은 연도 치환을 일괄 적용 (`common.js` 제외) |
| `replace_json.py` | YAML 설정에 정의된 regex 규칙을 읽어 JSON 파일의 필드 값을 일괄 정규화 |

---

## 요약

| 폴더 | 성격 | 현재 필요 여부 |
|------|------|---------------|
| `legacy_tools` | 데이터 파이프라인 (CSV→JSON, 필터, 내보내기) | 데이터 재처리 시 참고용 |
| `refactor_tools` | index.html 분리 작업 잔재 | 리팩터링 완료 후 보존용 |
| `utils` | 연도 하드코딩 제거 리팩터링 헬퍼 | 추가 연도 변경 시 재사용 가능 |
