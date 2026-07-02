# BudgetN 사양서 (spec.md)

> [!IMPORTANT]
> 본 사양서는 개발 요구사항 및 설계의 **닻(anchor)**입니다.
> 에이전트 단독으로 수정할 수 없으며, 변경 시 반드시 사용자의 사전 승인을 받아야 합니다.
> 성능·품질 **목표치(baseline)**만 `TODO`로 남겼습니다 — 이는 사용자 결정 사항입니다.

## 1. 개요 및 목적
- **비즈니스 배경**: 정부 예산 자료가 PDF·XLSX·YAML 등 이질적 포맷으로 흩어져 있어 통합 분석이 어렵다.
- **해결하려는 문제**: 다양한 입력을 단일 canonical DB(`database/output/merged.json`)로 수렴시키고, 사업 간 유사도·부처 협업 관계를 자동 분석한다.
- **최종 목표**: Excel Import → DB Merge → AI 분석 → 스냅샷 → 웹 배포까지 `master_builder.py` 명령으로 재현 가능하게 유지한다.

## 2. 세부 요구사항 및 범위
- **기능 요구사항** (`scripts/pipeline/master_builder.py` 기준):
  - F-1 (`build`): `database/input/`의 엑셀을 `excel_manager.py`로 파싱 → `database/output/merged.json` 생성
  - F-2 (`build`): `generate_ai_analysis.py`로 AI 분석 → `similarity_analysis.json`·`collaboration_analysis.json`·`hybrid_similarity.json` 산출 (TF-IDF/Cosine/Jaccard)
  - F-3 (`build`): 일자별 스냅샷 생성(`merge_YYYYMMDD_통합.json`, `*_YYYYMMDD.json`)
  - F-4 (`json-build`): 엑셀 재파싱 없이 `merged.json` 메타데이터 재계산(`config/config.yaml`의 `years.base_year`·`search_aliases` 반영)
  - F-5 (`deploy`): `database/output/*.json` → `web/data/`로 배포(`merged.json`→`budget_db.json` 등) 후 `rebuild_embedded.py`로 Embedded JS 재생성
  - F-6 (`bundle`): `build_standalone.py`로 무설치 단일 HTML 빌드
- **비기능 요구사항**:
  - 재현성: 파이프라인 단계별 폴더(`database/{input,src,raw,structure,parse_result,output,backup}`) 경계 유지
  - Fallback: 네트워크 없이 동작하는 Embedded JS(`web/data` → embedded) 유지
  - 보안: 입력·키 하드코딩 금지, 경로는 `config/path_config.py`(SSOT) 사용
  - 성능: 전체 `build` 허용 시간 baseline _TODO(목표치)_

## 3. 시스템 아키텍처 및 설계
- **데이터 흐름**: `database/input(xlsx)` → `excel_manager(import)` → `database/output/merged.json` → `generate_ai_analysis` → `output/*analysis.json` → `deploy` → `web/data/*.json` → `rebuild_embedded` → 정적 대시보드
- **경로 SSOT**: `config/path_config.py` — `MERGED_JSON_PATH = database/output/merged.json`, `WEB_DATA_DIR = web/data`
- **`merged.json` 스키마**:
  ```jsonc
  {
    "projects": [
      {
        "department": "담당 부처/본부",
        "budget": { "<year>_budget": 0, "budget_<year>": 0 },
        "budget_<year>": 0
        // 그 외 사업/과제 상세 필드
      }
    ],
    "metadata": {
      "total_projects": 0,       // 유효 project(dict) 수
      "departments_count": 0,    // 고유 department 수
      "base_year": 2026,         // config.yaml years.base_year
      "search_aliases": {}       // config.yaml search_aliases
    }
  }
  ```
- **배포 산출물(`web/data/`)**: `budget_db.json`, `similarity_analysis.json`, `collaboration_analysis.json`, `hybrid_similarity.json`

## 4. 검증 계획
- **테스트 시나리오**: `build`로 `merged.json`·분석 JSON 생성 정합성 확인 → `deploy` 후 `web/data` 반영 및 대시보드 렌더 확인
- **검증 명령**:
  ```bash
  python scripts/pipeline/master_builder.py build
  python scripts/pipeline/master_builder.py deploy
  ```
- **기대 성공 지표**: `build`/`deploy` 무오류 완주 + `web/data` JSON 4종 갱신. 유닛 테스트 합격선 _TODO(목표치)_.
