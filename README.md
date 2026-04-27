# BudgetN
> AI budget data pipeline and web dashboard

본 프로젝트는 정부 예산 자료를 `PDF / XLSX / JSON` 형태로 받아 canonical 데이터베이스인 `merged.json`으로 통합하고, 이를 바탕으로 `budget_db.json`, 분석 결과, 웹 대시보드 배포본까지 생성하는 파이프라인입니다.

## 개요
운영 기준 파이프라인은 아래 7단계로 분리합니다.

1. `PDF -> raw.json -> structured.json -> parsed.json`
2. `parsed / xlsx / yaml -> merged.json`
3. `merged.json -> budget_db.json`
4. `budget_db.json -> metadata / analysis / similarity / collaboration`
5. `web/data`로 배포
6. `embedded-*.js` 재생성
7. `web/` 프론트엔드 구동

핵심 원칙은 단순합니다.
- 내부 canonical master: `database/output/merged.json`
- 프론트 배포본: `web/data/budget_db.json`
- 프론트는 원본 포맷을 직접 읽지 않고 `budget_db.json`과 sidecar 분석 파일만 읽습니다.

## 디렉터리
```text
BudgetN/
├─ config/
│  ├─ config.yaml
│  ├─ config_a4.yaml
│  ├─ config_export.yaml
│  └─ template.json
├─ database/
│  ├─ src/
│  ├─ raw/
│  ├─ structure/
│  ├─ parse_result/
│  └─ output/
├─ scripts/
│  ├─ preProc/
│  ├─ pipeline/
│  └─ analysis/
├─ web/
│  ├─ data/
│  ├─ js/
│  └─ css/
├─ README.md
├─ GUIDE.md
└─ quick_guide.md
```

## 7단계 구조

### 1. PDF 파싱
- 입력: `database/src/*.pdf`
- 스크립트:
  - `scripts/preProc/pdf_to_json.py`
  - `scripts/preProc/json_structurer.py`
  - `scripts/preProc/budget_parser.py`
- 산출물:
  - `database/raw/*_raw.json`
  - `database/structure/*_structured.json`
  - `database/parse_result/*_parsed.json`

### 2. parsed / xlsx / yaml -> merged.json
- 목적: 여러 입력 포맷을 하나의 canonical schema로 통합
- 현재 구현 경로:
  - 총괄 XLSX: `scripts/pipeline/convert.py`
  - A4 XLSX: `scripts/pipeline/convert_a4.py`
  - JSON 마이그레이션: `scripts/pipeline/convert.py`
  - PDF parsed 병합: 현재는 `scripts/preProc/json_manager.py` 또는 별도 후처리 필요
- 목표 산출물:
  - `database/output/merged.json`

### 3. merged.json -> budget_db.json
- 목적: 프론트 배포용 canonical copy 생성
- 현재 구현:
  - `scripts/pipeline/master_builder.py deploy`
- 산출물:
  - `web/data/budget_db.json`

### 4. budget_db.json 기반 metadata / analysis 생성
- 목적: 프론트가 사용할 집계와 sidecar 분석 결과 생성
- 스크립트:
  - `scripts/analysis/generate_ai_analysis.py`
- 산출물:
  - `metadata` 갱신
  - `analysis` 기본 집계 갱신
  - `database/output/similarity_analysis.json`
  - `database/output/collaboration_analysis.json`

### 5. web/data 배포
- 목적: 프론트가 fetch할 JSON 세트 배치
- 산출물:
  - `web/data/budget_db.json`
  - `web/data/similarity_analysis.json`
  - `web/data/collaboration_analysis.json`

### 6. embedded JS 재생성
- 목적: fallback / 정적 배포 / 일부 고급 탭 지원
- 스크립트:
  - `scripts/pipeline/rebuild_embedded.py`
- 산출물:
  - `web/js/embedded-data.js`
  - `web/js/embedded-sim-v10-data.js`
  - `web/js/embedded-collab-data.js`
  - `web/js/embedded-hybrid-data.js`

### 7. web 프론트엔드 구동
- 기본 데이터:
  - `web/data/budget_db.json`
- 추가 데이터:
  - `web/data/collaboration_analysis.json`
  - embedded JS들
- 비고:
  - `index.html`은 `budget_db.json` 중심으로 동작
  - `duplicate.html` 등 고급 기능은 sidecar / embedded 데이터 의존성이 더 큼

## 실행 예시

### PDF 전처리
```bash
python scripts/preProc/main_cli.py -i database/src -y
```

### 총괄 XLSX 템플릿 생성
```bash
python scripts/pipeline/excel_manager.py template
```

### XLSX -> merged.json
```bash
python scripts/pipeline/excel_manager.py import --type both
```

### 통합 빌드
```bash
python scripts/pipeline/master_builder.py build
```

### 웹 배포
```bash
python scripts/pipeline/master_builder.py deploy
```

## XLSX 템플릿 상태
현재는 공식 총괄 XLSX 템플릿을 코드로 생성할 수 있습니다.

생성 명령:
```bash
python scripts/pipeline/excel_manager.py template
```

기본 생성 파일:
- `template_project.xlsx`

참고용 파일:
- `web/template/projects_template.csv`
- `web/template/sub_projects_template.csv`

주의:
- CSV 파일들은 컬럼 참고용 예시입니다.
- `convert.py`는 CSV가 아니라 다중 시트를 가진 XLSX/XLSM을 읽습니다.
- 실제 import는 생성된 `template_project.xlsx` 또는 동일 구조의 파일을 사용해야 합니다.

실제 총괄 XLSX가 만족해야 하는 조건:
- 시트명:
  - `사업목록`
  - `내역사업`
  - `사업관리자`
  - `사업연혁`
  - `연도별예산`
- 헤더 행: 2행
- 데이터 시작 행: 3행
- 필수 필드:
  - `사업코드`
  - `사업명`
  - `부처명`
  - 기준연도 예산 컬럼

A4 XLSX는 별도 규칙입니다.
- `convert_a4.py`는 Named Range 기반 템플릿을 기대합니다.
- `config_a4.yaml`의 `enable_named_ranges: true` 조건이 유지되어야 합니다.

## 현재 확인된 구조 이슈
- `database/output/merged.json`이 항상 남는 구조가 아직 고정되지 않았습니다.
- 기존 산출물에는 `sub_projects[].budget_base`가 없을 수 있으며, 현재 파이프라인은 이를 자동 보정합니다.
- `collaboration_analysis.json`은 프론트가 기대하는 `collaboration_chains`, `collaboration_network`, `summary_statistics`를 아직 생성하지 않습니다.
- `config/template.json`은 flattened 예전 스키마 형태라 실제 nested canonical 데이터와 맞지 않습니다.

## 다음 권장 작업
1. `database/output/merged.json`을 canonical final로 고정
2. 기존 데이터셋을 재빌드해 `sub_projects[].budget_base` 반영
3. 생성된 총괄 XLSX 템플릿을 기준 템플릿으로 운영 고정
4. `collaboration_analysis.json` 구조를 프론트 기대값에 맞게 확장
5. `template.json`을 nested canonical schema 기준으로 재작성
