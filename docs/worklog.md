# BudgetN Work Logs

## 2026-04-27 - 데이터 스키마 및 파이프라인 연결 검토

### 목적
- 현재 프로젝트에서 `scripts/preProc` 기준 JSON 생성 흐름과 실제 프론트엔드 구동 경로 사이의 누락 구간을 정리한다.
- 최종 산출물이 무엇인지 명확히 정의한다.
- 다른 형태의 `xlsx` 및 `yaml` 데이터를 프론트엔드에서 구동하기 위한 조건을 정리한다.

### 현재 구조 요약
- PDF 계열 전처리는 `scripts/preProc/main_cli.py`가 담당한다.
- 이 경로의 산출물 단계는 `database/raw` -> `database/structure` -> `database/parse_result` 이다.
- `preProc`의 최종 산출물은 문서별 `*_parsed.json`이며, 파일 위치는 `database/parse_result` 이다.
- 실제 웹 프론트엔드는 `web/data/budget_db.json`을 기준 데이터로 로드한다.
- 웹 배포는 `scripts/pipeline/master_builder.py deploy`가 수행하며, `database/output/merged.json`이 존재할 경우 `web/data/budget_db.json`으로 복사한다.
- 현재 워크스페이스에는 `database/output/merged.json`이 없고, 스냅샷 파일 `database/output/individual/merge_20260403_통합.json` 및 배포본 `web/data/budget_db.json`만 존재한다.

### 확인한 핵심 불일치
- `preProc` 문서상 최종본은 `merged.json`처럼 설명되지만, 실제 `main_cli.py`는 문서별 `*_parsed.json`까지만 확정적으로 남긴다.
- `preProc/json_manager.py`는 `parse_result`를 병합해 `database/output/merged.json`을 만들 수 있지만, 현재 운영 파이프라인의 중심은 `scripts/pipeline/convert.py`와 `master_builder.py`이다.
- 프론트 문서 `docs/data_mapping.md`는 `window.DATA.analysis.duplicates`, `window.DATA.analysis.collaboration` 중심으로 설명하지만, 실제 구현은 혼합형이다.
- 중복 탭은 `budget_db.json` 내부 `analysis.duplicates`와 `js/embedded-sim-v10-data.js`를 함께 사용한다.
- 협업 탭은 `data/collaboration_analysis.json`를 별도 fetch하고, 실패 시 `js/embedded-collab-data.js`를 fallback으로 사용한다.

### 결론: 현재 기준 최종본 정의
- 파이프라인 내부 canonical 데이터의 최종본은 `database/output/merged.json`이어야 한다.
- 실제 서비스 배포 최종본은 `web/data/budget_db.json`이다.
- 현재 저장 상태만 보면 실질적으로 가장 최신의 사용 중인 최종본은 `web/data/budget_db.json`이다.
- 날짜 스냅샷 `merge_YYYYMMDD_통합.json`은 이력 보관본으로 보는 것이 맞다.

## 1. Canonical 데이터스키마 정의

### 권고
- 모든 입력 포맷은 최종적으로 하나의 canonical JSON 스키마로 수렴해야 한다.
- 프론트엔드는 원본 포맷을 몰라도 되고, canonical JSON만 알면 된다.
- canonical 파일명은 `database/output/merged.json`으로 고정하는 것이 적절하다.

### 루트 구조
```json
{
  "metadata": {},
  "projects": [],
  "analysis": {}
}
```

### 필수 루트 필드
- `metadata`
- `projects`
- `analysis`

### metadata 최소 요구사항
- `total_projects`
- `total_departments`
- `base_year`
- `extraction_date`
- `source`
- `search_aliases`

### projects 최소 요구사항
- `id`
- `project_name`
- `code`
- `department`
- `budget`
- `project_period`
- `sub_projects`
- `project_managers`
- `ai_domains`
- `ai_tech`
- `rnd_stage`

### project 내부 권장 구조
```json
{
  "id": "stable-id",
  "project_name": "사업명",
  "code": "세부사업코드",
  "department": "부처명",
  "division": "소관부서",
  "implementing_agency": "시행기관",
  "account_type": "회계유형",
  "status": "신규|계속|완료",
  "support_type": [],
  "is_rnd": false,
  "is_informatization": false,
  "budget": {
    "2024_settlement": 0,
    "2025_original": 0,
    "2025_supplementary": 0,
    "2026_request": 0,
    "2026_budget": 0,
    "change_amount": 0,
    "change_rate": 0
  },
  "project_period": {
    "start_year": null,
    "end_year": null,
    "duration": null,
    "raw": null
  },
  "sub_projects": [],
  "project_managers": [],
  "history": [],
  "yearly_budgets": {},
  "ai_domains": [],
  "ai_tech": [],
  "rnd_stage": [],
  "purpose": null,
  "description": null,
  "legal_basis": null
}
```

### analysis 최소 요구사항
- 최소한 빈 오브젝트라도 유지해야 한다.
- 현재 프론트 호환을 위해 아래 키는 유지하는 편이 안전하다.
- `by_department`
- `by_type`
- `by_domain`
- `top_increases`
- `top_decreases`
- `duplicates`
- `duplicate_network`
- `keyword_clusters`
- `same_agency`

### ID 정책 권고
- `preProc/budget_parser.py`의 `base_year_code` 방식보다 `convert.py`의 해시 기반 stable id가 운영에 더 적합하다.
- 이유:
- 연도 변경 시 ID가 바뀌지 않아 프론트 참조 안정성이 높다.
- 유사도/협업 분석 결과와의 조인 안정성이 더 높다.

## 2. 입력 adapter 설계안

### 목표 구조
```text
source adapter
-> normalize
-> canonical merged.json
-> analysis build
-> deploy to web/data
```

### 권장 adapter 분류
- `pdf_preproc_adapter`
  - 입력: PDF
  - 출력: canonical project list 초안
  - 현재 구현 기반: `scripts/preProc/*`
- `summary_xlsx_adapter`
  - 입력: 총괄 XLSX
  - 출력: canonical merged.json
  - 현재 구현 기반: `scripts/pipeline/convert.py`
- `a4_xlsx_adapter`
  - 입력: A4 요약 XLSX
  - 출력: canonical merged.json
  - 현재 구현 기반: `scripts/pipeline/convert_a4.py`
- `json_adapter`
  - 입력: 기존 `projects` 또는 `merged.json`
  - 출력: canonical merged.json
  - 현재 구현 기반: `scripts/pipeline/convert.py`의 `read_json_file`
- `yaml_adapter`
  - 입력: YAML 데이터
  - 출력: canonical merged.json
  - 현재는 미구현

### 운영 단계 권고
1. 입력 포맷별 adapter는 모두 `projects` 배열만 책임진다.
2. metadata 재계산은 공통 builder가 담당한다.
3. analysis 생성은 `generate_ai_analysis.py` 계열 공통 단계로 분리한다.
4. 배포는 `master_builder.py deploy` 한 단계로 고정한다.

### 역할 재정의 권고
- `scripts/preProc`는 PDF 특화 adapter로 위치를 낮춘다.
- `scripts/pipeline`는 canonical build와 deploy의 단일 진입점이 된다.
- `json_manager.py`의 validate/merge 기능은 폐기보다 공통 validator/merger로 흡수하는 편이 낫다.

## 3. YAML 입력 초안 및 validator 방향

### 판단
- 현재 프로젝트에서 YAML은 데이터 포맷이 아니라 설정 포맷이다.
- `config.yaml`, `config_a4.yaml`, `config_export.yaml`, `pattern.yaml`은 모두 규칙/매핑/출력용이다.
- 따라서 “YAML 데이터로 프론트 구동”은 바로 가능하지 않고, 별도 YAML 데이터 어댑터가 필요하다.

### YAML 입력 포맷 초안
```yaml
metadata:
  source: "manual yaml input"
  base_year: 2026

projects:
  - code: "2602-367"
    project_name: "AI AGENT 선도 국가 사업"
    department: "과학기술정보통신부"
    division: "정보통신정책관"
    account_type: "일반회계"
    status: "신규"
    support_type: ["출연"]
    implementing_agency: "NIPA"
    is_rnd: false
    is_informatization: false
    budget:
      2024_settlement: 0
      2025_original: 0
      2025_supplementary: 0
      2026_request: 3000
      2026_budget: 2500
    project_period:
      start_year: 2026
      end_year: 2028
      duration: "3년"
      raw: "2026~2028"
    ai_domains: ["행정", "플랫폼"]
    ai_tech: ["Agent", "LLM"]
    rnd_stage: ["실증"]
    sub_projects:
      - name: "AI Agent 플랫폼 구축"
        budget_2024: 0
        budget_2025: 0
        budget_2026: 2500
    project_managers: []
    history: []
    yearly_budgets:
      "2026": 2500
    purpose: "..."
    description: "..."
    legal_basis: null
```

### YAML adapter 구현 조건
- YAML 로더는 `projects` 배열을 읽어 canonical project 구조로 normalize 해야 한다.
- 누락 필드는 defaults로 채워야 한다.
- `base_year`에 따라 budget 키를 동적으로 검사해야 한다.
- `id`는 공통 ID 생성기를 통해 재부여해야 한다.
- metadata와 analysis는 입력 YAML을 그대로 신뢰하지 말고 재계산하는 편이 안전하다.

### validator 최소 규칙
- 루트에 `projects`가 존재해야 한다.
- 각 project에 `code`, `project_name`, `department`가 있어야 한다.
- `budget.{base_year}_budget` 또는 동등 필드가 있어야 한다.
- `sub_projects`, `project_managers`, `history`는 없으면 빈 배열로 보정한다.
- `ai_domains`, `ai_tech`, `rnd_stage`는 없으면 빈 배열로 보정한다.
- `status`, `account_type`, `support_type`는 허용값 검사를 둔다.
- 숫자 필드는 문자열 입력도 허용하되 normalize 과정에서 float/int로 변환한다.

### validator 구현 위치 권고
- 새 파일 예시: `scripts/pipeline/validate_canonical.py`
- 역할:
- 입력 JSON/YAML/XLSX adapter 결과를 canonical 구조로 검사
- 누락 필드 보정
- 연도 키 정합성 검증
- 프론트 구동 최소 조건 검증

## 실행 우선순위 권고

### 1차
- `database/output/merged.json`을 canonical 최종본으로 다시 복구한다.
- `master_builder.py`가 항상 이 파일을 만들거나 검증하도록 수정한다.

### 2차
- `docs/data_mapping.md`를 실제 구현 기준으로 갱신한다.
- 특히 `duplicates`, `collaboration`이 단일 `window.DATA.analysis`가 아니라 sidecar JSON과 혼용되는 점을 반영한다.

### 3차
- YAML adapter 초안과 validator를 구현한다.
- 목표는 “원본 포맷이 무엇이든 프론트는 `web/data/budget_db.json`만 읽는다”는 규칙을 강제하는 것이다.

## 이번 검토의 결론
- 현재 프로젝트의 누락 지점은 데이터 생성보다 “canonical 최종본의 정의와 단계 연결”이다.
- 프론트 구동 자체는 JSON canonicalization만 보장되면 입력 포맷과 무관하다.
- 따라서 앞으로의 핵심 작업은 새 포맷을 직접 프론트에 붙이는 것이 아니라, 새 포맷을 `merged.json` 스키마로 안정적으로 수렴시키는 adapter와 validator를 만드는 일이다.

## 2026-04-27 - merged.json, budget_db.json, 프론트 의존성 정밀 점검

### 요청 사항 재정리
- `sub_projects`가 여러 개일 수 있는지 확인
- 기존 `merged.json`, `budget_db.json`에 컬럼 누락이 있는지 확인
- `merged -> budget_db -> meta/analysis` 단계 분리를 정확히 정의
- 프론트엔드가 실제로 정상 동작하려면 추가 데이터셋이 필요한지 확인

### 0. 핵심 결과 요약
- `sub_projects`는 다건 구조가 맞다.
- 실제 데이터에서 `sub_projects`가 2건 이상인 프로젝트가 149건 확인되었다.
- 최다 내역사업 수는 17건이다.
- `merged` 스냅샷과 `budget_db.json`의 프로젝트 키 구조는 동일했다.
- 다만 “컬럼 자체가 없는 문제”와 “컬럼은 있으나 값이 거의 비어 있는 문제”를 구분해야 한다.
- 프론트 코드 기준으로는 `sub_projects[].budget_base`가 필요한데, 실제 데이터에는 이 컬럼이 없다.
- 협업 탭은 `collaboration_analysis.json` 안에 `collaboration_chains`, `collaboration_network`, `summary_statistics`를 기대하지만 실제 파일에는 없다.
- `budget_db.json` 내부 `analysis.flow`, `analysis.clusters`, `analysis.collaboration`도 현재 없다.

### 1. sub_projects 다건 여부

#### 확인 결과
- `sub_projects`는 배열 구조이며 다건 저장이 가능하다.
- 실제 데이터 기준:
- `projects_with_multi_subprojects = 149`
- `max_subproject_count = 17`

#### 실제 sub_project 구조
```json
{
  "parent_id": "1035-401",
  "name": "연구보안 체계 내실화",
  "budget_2024": 0.0,
  "budget_2025": 0.0,
  "budget_2026": 0.0
}
```

#### 판단
- `sub_projects` 다건 구조 자체는 정상이다.
- 문제는 프론트 일부가 `budget_base`를 기대하는데 실제 데이터는 `budget_2026`만 가진다는 점이다.

### 2. merged.json / budget_db.json 컬럼 누락 점검

### 2-1. merged 스냅샷 vs budget_db.json
- `database/output/individual/merge_20260403_통합.json`과 `web/data/budget_db.json`의 프로젝트 키 수는 동일했다.
- 두 파일 모두 프로젝트 키 수는 61개였다.
- 즉 `budget_db.json`은 `merged` 스냅샷의 단순 복사본에 가깝고, 이 단계에서 추가 컬럼 손실은 없었다.

### 2-2. 컬럼 누락이 아니라 “구조 불일치”인 항목

#### sub_projects
- 실제 키:
- `name`
- `parent_id`
- `budget_2024`
- `budget_2025`
- `budget_2026`

#### 프론트 기대 키
- 일부 프론트 코드는 `sub_projects[].budget_base`를 사용한다.
- 실제 데이터에는 `budget_base`가 0건이다.

#### 영향
- 내역사업 히스토그램, 집중도 분석, 비교 모달 일부 수치가 0 또는 빈 값으로 보일 가능성이 높다.

### 2-3. 컬럼은 있으나 값이 거의 비어 있는 항목

#### 값 누락 현황
- `division` 비어 있음: 255건
- `implementing_agency` 비어 있음: 1478건
- `status` 비어 있음: 149건
- `ai_domains` 비어 있음: 237건
- `ai_tech_types` 비어 있음: 1275건
- `rnd_stage` 비어 있음: 1289건

#### 판단
- 이건 스키마 누락이 아니라 추출률 문제다.
- 특히 `implementing_agency`, `ai_tech_types`, `rnd_stage`는 프론트 분류/요약 정확도에 큰 영향을 준다.

### 2-4. template.json과의 불일치
- `config/template.json`은 flattened schema 스타일이다.
- 예:
- `program_code`, `unit_project_code`, `detail_project_code`
- `budget_2026_budget`
- `start_year`, `duration`
- 실제 데이터는 nested schema 스타일이다.
- 예:
- `program.code`
- `budget.2026_budget`
- `project_period.start_year`

#### 판단
- `template.json`은 현재 canonical validator 기준으로 쓰기 어렵다.
- 실제 운영 스키마와 validator 스키마를 다시 맞춰야 한다.

### 3. 단계 분리 - 운영 기준 파이프라인 정의

### 3-1. 1단계: PDF -> JSON 파싱

#### 목적
- 비정형 PDF를 프로젝트 단위 JSON으로 변환

#### 세부 단계
1. `database/src/*.pdf`
2. `scripts/preProc/pdf_to_json.py`
3. 산출물: `database/raw/*_raw.json`
4. `scripts/preProc/json_structurer.py`
5. 산출물: `database/structure/*_structured.json`
6. `scripts/preProc/budget_parser.py`
7. 산출물: `database/parse_result/*_parsed.json`

#### 비고
- 이 단계의 결과는 “문서별 파싱 결과”다.
- 아직 canonical DB가 아니다.

### 3-2. 2단계: parsed / xlsx -> merged.json -> budget_db.json -> meta/analysis

#### 2-A. 원천 입력 정규화
- 입력 소스는 세 갈래다.
- PDF 파싱 결과(`*_parsed.json`)
- 총괄 XLSX
- A4 XLSX

#### 2-B. canonical 병합
- 모든 소스를 하나의 canonical 스키마로 병합한 결과가 `database/output/merged.json`이어야 한다.
- 이 파일이 내부 기준 마스터다.

#### 2-C. budget_db.json 생성
- `budget_db.json`은 프론트 배포용 복사본으로 정의한다.
- 권장 관계:
```text
merged.json = 내부 canonical master
budget_db.json = 프론트 배포용 canonical copy
```

#### 2-D. metadata / analysis 생성
- 요청하신 구성대로라면 `budget_db.json` 또는 그와 동일한 canonical 데이터를 기준으로 아래가 생성되어야 한다.
- `metadata` 재계산
- `analysis` 기본 집계 생성
- `similarity_analysis.json`
- `collaboration_analysis.json`

#### 권장 순서
```text
parsed/xlsx 입력
-> merged.json 생성
-> budget_db.json 생성
-> budget_db.json 기반 metadata 재계산
-> budget_db.json 기반 analysis 기본 집계 생성
-> sidecar 분석 파일 생성
```

#### 현재 구현과의 차이
- 현재는 `merged.json`과 `budget_db.json`이 사실상 같은 구조다.
- `master_builder.py deploy`가 `merged.json`을 그대로 `budget_db.json`으로 복사한다.
- 따라서 논리적으로는 분리되어야 하지만 구현상으로는 아직 “복사 단계” 수준이다.

### 3-3. 3단계: 프론트엔드로 이동

#### 현재 경로
1. `database/output/merged.json`
2. `scripts/pipeline/master_builder.py deploy`
3. `web/data/budget_db.json` 복사
4. `web/data/similarity_analysis.json` 복사
5. `web/data/collaboration_analysis.json` 복사
6. `scripts/pipeline/rebuild_embedded.py`
7. `web/js/embedded-data.js`
8. `web/js/embedded-sim-v10-data.js`
9. `web/js/embedded-collab-data.js`
10. `web/js/embedded-hybrid-data.js`

#### 판단
- `web/data/*.json`은 실데이터 파일
- `web/js/embedded-*.js`는 fallback 또는 보조 분석 파일
- 배포 단계에서는 둘 다 관리해야 한다

### 3-4. 4단계: 기존 프론트엔드 정상작동 여부

#### index.html
- `index.html`은 `js/embedded-data.js`와 `data/budget_db.json` 기반으로 동작한다.
- 이 페이지는 현재 `overview`, `department`, `field`, `projects` 탭 중심이다.
- 이 범위에서는 `budget_db.json`만으로 대부분 동작 가능하다.

#### duplicate.html
- `duplicate.html`은 아래 보조 데이터까지 로드한다.
- `embedded-data.js`
- `embedded-sim-v10-data.js`
- `embedded-collab-data.js`
- `embedded-hybrid-data.js`

#### 실제 추가 데이터셋 필요 여부
- 필요하다.
- `budget_db.json`만으로는 전체 프론트가 완전하게 동작하지 않는다.

### 4. 프론트엔드 의존성 점검 결과

### 4-1. budget_db.json만으로 되는 부분
- 개요 탭
- 부처별 분석
- 분야별 분석
- 사업 목록 기본 출력

### 4-2. budget_db.json만으로 부족한 부분

#### 내역사업 관련 차트
- `charts.js`는 `sub_projects[].budget_base`를 사용한다.
- 실제 데이터에는 `budget_base`가 없다.
- 영향:
- 내역사업 히스토그램
- 내역사업 집중도
- 비교 모달 일부 금액 표기

#### 협업 탭
- `tab-handler.js`는 아래 필드를 기대한다.
- `summary_statistics`
- `collaboration_chains`
- `collaboration_network`
- 실제 `collaboration_analysis.json`에는 `metadata`, `pairs`만 있다.
- 영향:
- KPI 일부가 `?` 또는 0으로 표시될 수 있다.
- 체인/허브 영역은 “발견된 협업 체인이 없습니다” 식으로 보일 가능성이 높다.

#### flow / clusters / collaboration in budget_db.analysis
- 프론트 문서상 기대는 존재하지만 실제 `budget_db.json.analysis`에는 없다.
- 현재 상태:
- `analysis.flow` 없음
- `analysis.clusters` 없음
- `analysis.collaboration` 없음
- `analysis.duplicates`는 존재하지만 빈 배열

#### similarity sidecar 사용
- 유사도 데이터는 `data/similarity_analysis.json`보다 `embedded-sim-v10-data.js` 쪽이 더 직접적으로 쓰인다.
- 즉 `rebuild_embedded.py` 단계가 사실상 필요하다.

### 5. 최종 판단

### 정상 동작 범위
- `index.html`의 기본 분석 화면은 `budget_db.json`만으로 대체로 동작 가능
- 단, 내역사업 기반 일부 차트는 수치가 부정확할 수 있음

### 비정상 또는 불완전 동작 범위
- `duplicate.html`
- 협업 탭
- 내역사업 예산 기반 고급 시각화
- 문서가 기대하는 `analysis.flow`, `analysis.clusters`, `analysis.collaboration`

### 즉시 수정이 필요한 항목
1. `sub_projects[].budget_base` 생성 로직 추가
2. `database/output/merged.json`을 canonical final로 항상 생성
3. `budget_db.json` 생성 단계를 명시적으로 분리
4. `collaboration_analysis.json` 구조를 프론트 기대값에 맞게 확장
5. `template.json`을 실제 nested canonical schema 기준으로 재작성

### 권장 최종 단계 정의
```text
1. PDF -> raw.json -> structured.json -> parsed.json
2. parsed/xlsx/yaml -> merged.json
3. merged.json -> budget_db.json
4. budget_db.json 기반 metadata / analysis 기본 집계
5. budget_db.json 기반 similarity_analysis / collaboration_analysis 생성
6. web/data 로 복사
7. embedded js 재생성
8. index.html / duplicate.html 구동
```

## 2026-04-27 - 파이프라인 보강 1차 반영

### 반영 내용
- `scripts/pipeline/convert.py`에 `normalize_sub_projects()`를 추가했다.
- 총괄 XLSX 입력, JSON 마이그레이션, merged 저장 직전에 모두 `sub_projects`를 canonical 형태로 보정하도록 연결했다.
- 보정 필드:
  - `sub_projects[*].parent_id`
  - `sub_projects[*].budget_prev`
  - `sub_projects[*].budget_base`
- `scripts/preProc/budget_parser.py`도 PDF parsed 단계에서 `budget_prev`, `budget_base`를 함께 생성하도록 수정했다.

### 템플릿 생성 경로 추가
- 새 스크립트:
  - `scripts/pipeline/generate_summary_template.py`
- 새 명령:
  - `python scripts/pipeline/excel_manager.py template`
- 생성 결과:
  - `template_project.xlsx`

### 생성 템플릿 구조
- 시트:
  - `사업목록`
  - `내역사업`
  - `사업관리자`
  - `사업연혁`
  - `연도별예산`
- 규칙:
  - 1행 안내문
  - 2행 헤더
  - 3행부터 데이터 입력
- 헤더는 `config/config.yaml` 매핑을 그대로 사용하므로 `convert.py`와 직접 정합된다.

### 남은 후속 작업
1. 기존 `merged.json`, `budget_db.json`, sidecar 데이터셋을 재빌드해 새 필드 반영
2. `collaboration_analysis.json`을 프론트 기대 구조에 맞게 확장
3. `config/template.json`을 nested canonical schema 기준으로 재작성
