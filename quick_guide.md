# Quick Guide

자주 쓰는 운영 명령만 빠르게 정리한 문서입니다.

## 1. PDF에서 시작할 때
```bash
python scripts/preProc/main_cli.py -i database/src -y
```

산출물:
- `database/raw/*_raw.json`
- `database/structure/*_structured.json`
- `database/parse_result/*_parsed.json`

## 2. 총괄 XLSX / A4 XLSX를 merged.json으로 반영할 때
먼저 총괄 XLSX 템플릿이 필요하면:
```bash
python scripts/pipeline/excel_manager.py template
```

그 다음 import:
```bash
python scripts/pipeline/excel_manager.py import --type both
```

주의:
- 총괄 XLSX는 다중 시트 구조가 필요합니다.
- A4 XLSX는 Named Range 기반입니다.
- 기본 템플릿 파일은 `template_project.xlsx`입니다.

## 3. 빌드
```bash
python scripts/pipeline/master_builder.py build
```

의도:
- 입력 데이터 통합
- 분석 JSON 생성
- 스냅샷 생성

## 4. 배포
```bash
python scripts/pipeline/master_builder.py deploy
```

산출물:
- `web/data/budget_db.json`
- `web/data/similarity_analysis.json`
- `web/data/collaboration_analysis.json`
- `web/js/embedded-*.js`

## 5. 단일 HTML 번들
```bash
python scripts/pipeline/master_builder.py bundle
```

## 6. 현재 구조 핵심
```text
parsed/xlsx/yaml -> merged.json -> budget_db.json -> analysis -> web/data -> embedded js -> web
```

## 7. 템플릿 체크포인트

### 총괄 XLSX
- 시트명:
  - `사업목록`
  - `내역사업`
  - `사업관리자`
  - `사업연혁`
  - `연도별예산`
- 헤더 행: 2행
- 데이터 시작 행: 3행

### A4 XLSX
- Named Range 필수
- `config/config_a4.yaml` 기준 유지

## 8. 현재 가장 중요한 보완점
1. `database/output/merged.json`을 canonical final로 고정
2. 기존 데이터셋 재빌드로 `sub_projects[].budget_base` 반영
3. 생성 템플릿을 운영 기준으로 고정
4. 협업 분석 JSON 구조 보강
