# BudgetN Guide

본 문서는 현재 운영 기준의 BudgetN 데이터 파이프라인, 입출력 파일, 프론트 의존성, 템플릿 조건을 정리한 기술 가이드입니다.

## 1. 운영 기준 7단계

### 1단계. PDF -> raw -> structured -> parsed
- 입력: `database/src/*.pdf`
- 스크립트:
  - `scripts/preProc/pdf_to_json.py`
  - `scripts/preProc/json_structurer.py`
  - `scripts/preProc/budget_parser.py`
- 산출물:
  - `database/raw/*_raw.json`
  - `database/structure/*_structured.json`
  - `database/parse_result/*_parsed.json`

### 2단계. parsed / xlsx / yaml -> merged.json
- 목적: 모든 입력 포맷을 canonical schema로 통합
- canonical master: `database/output/merged.json`
- 현재 구현 경로:
  - 총괄 XLSX: `scripts/pipeline/convert.py`
  - A4 XLSX: `scripts/pipeline/convert_a4.py`
  - JSON 마이그레이션: `scripts/pipeline/convert.py`
  - PDF parsed 병합: 현재 별도 정리 필요

### 3단계. merged.json -> budget_db.json
- 목적: 프론트 배포본 생성
- 현재 구현:
  - `scripts/pipeline/master_builder.py deploy`
- 산출물:
  - `web/data/budget_db.json`

### 4단계. budget_db.json 기반 metadata / analysis 생성
- 스크립트:
  - `scripts/analysis/generate_ai_analysis.py`
- 산출물:
  - `metadata` 갱신
  - `analysis` 기본 집계 갱신
  - `similarity_analysis.json`
  - `collaboration_analysis.json`

### 5단계. web/data 배포
- 복사 대상:
  - `budget_db.json`
  - `similarity_analysis.json`
  - `collaboration_analysis.json`

### 6단계. embedded JS 재생성
- 스크립트:
  - `scripts/pipeline/rebuild_embedded.py`
- 산출물:
  - `web/js/embedded-data.js`
  - `web/js/embedded-sim-v10-data.js`
  - `web/js/embedded-collab-data.js`
  - `web/js/embedded-hybrid-data.js`

### 7단계. web 프론트 구동
- 기본 페이지:
  - `web/index.html`
  - `web/duplicate.html`
- 핵심 입력:
  - `web/data/budget_db.json`
  - sidecar JSON 및 embedded JS

## 2. canonical 데이터 기준

### 루트 구조
```json
{
  "metadata": {},
  "projects": [],
  "analysis": {}
}
```

### 최소 필수 필드
- `metadata.base_year`
- `metadata.total_projects`
- `projects[*].id`
- `projects[*].project_name`
- `projects[*].code`
- `projects[*].department`
- `projects[*].budget`
- `projects[*].sub_projects`
- `projects[*].project_period`

### ID 정책
- 권장: `convert.py`의 stable hash id
- 이유:
  - 연도 변경 시에도 ID 안정성 유지
  - 프론트 참조와 sidecar 분석 조인 안정성 확보

## 3. XLSX -> merged.json 템플릿 조건

### 현재 상태
현재 저장소에는 공식 총괄 XLSX 템플릿 생성 경로가 있습니다.

생성 명령:
```bash
python scripts/pipeline/excel_manager.py template
```

기본 출력 파일:
- `template_project.xlsx`

존재하는 템플릿 관련 파일:
- `web/template/projects_template.csv`
- `web/template/sub_projects_template.csv`

이 파일들의 성격:
- CSV는 컬럼 참고용 예시
- 공식 import 템플릿은 `template_project.xlsx`
- `convert.py` 입력 파일로는 생성된 XLSX를 사용

### 총괄 XLSX 입력 조건
`convert.py`는 아래 구조를 가진 XLSX/XLSM을 기대합니다.

#### 시트명
- `사업목록`
- `내역사업`
- `사업관리자`
- `사업연혁`
- `연도별예산`

#### 시트별 구조
- 헤더 행: 2행
- 데이터 시작 행: 3행
- 기본 데이터 시트: `사업목록`

#### 최소 필수 컬럼
- `사업코드`
- `사업명`
- `부처명`
- 기준연도 예산 컬럼

#### 주요 매핑 기준
- 실제 컬럼명은 `config/config.yaml`의 `xlsx.column_mapping`을 따른다.
- 연도 관련 컬럼은 `years.base_year`와 `_years.py` 치환 결과에 따라 달라진다.

### A4 XLSX 입력 조건
`convert_a4.py`는 일반 총괄표와 다른 입력 규칙을 쓴다.

- Named Range 기반
- 각 시트가 project 1건 또는 project 단위 블록 역할
- `config/config_a4.yaml`의 `enable_named_ranges: true` 유지 필요

### 템플릿 점검 결론
- 총괄 XLSX 실템플릿은 코드로 생성 가능
- CSV 예시는 참고용으로만 유지
- 운영 기준 템플릿은 `config/config.yaml`의 시트명, 헤더 행, 데이터 시작 행을 그대로 따른다

## 4. 프론트 의존성 점검

### budget_db.json만으로 대체로 되는 영역
- 개요
- 부처별 분석
- 분야별 분석
- 사업 목록 기본 출력

### 추가 데이터가 필요한 영역
- 유사성 분석
- 협업 분석
- 일부 중복 분석
- 일부 고급 시각화

### 현재 확인된 구조 이슈
- 기존 배포 산출물에는 `sub_projects[].budget_base`가 없을 수 있음
- `collaboration_analysis.json`에 프론트가 기대하는 필드 부족
  - `collaboration_chains`
  - `collaboration_network`
  - `summary_statistics`
- `budget_db.json.analysis`에 아래 키 없음
  - `flow`
  - `clusters`
  - `collaboration`

## 5. 권장 보완 작업
1. `database/output/merged.json`을 항상 남기도록 빌드 구조 고정
2. `sub_projects[].budget_base` 생성
3. 총괄 XLSX import용 공식 `.xlsx` 템플릿 추가
4. `collaboration_analysis.json` 구조를 프론트 기대값에 맞게 확장
5. `config/template.json`을 실제 nested canonical schema 기준으로 갱신
