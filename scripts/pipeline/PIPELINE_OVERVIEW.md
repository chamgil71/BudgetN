# KAIB2026 파이프라인 스크립트 구조 및 사용법 정리

본 문서는 `scripts/pipeline` 폴더(및 analysis/utils/refactor_tools) 내 주요 스크립트들의 역할, 사용법, 그리고 전체 파이프라인의 연관관계를 정리한 것입니다. (legacy_tools 폴더 제외)

---

## 1. 전체 파이프라인 개요 (master_builder.py 중심)

### master_builder.py
- **역할**: 데이터 통합, AI 분석, 스냅샷 생성, 웹 배포까지 한 번에 실행하는 마스터 파이프라인
- **실행법**:
  - `python scripts/pipeline/master_builder.py build` : 전체 빌드 (엑셀→JSON→AI분석→스냅샷)
  - `python scripts/pipeline/master_builder.py deploy` : 분석 결과를 웹 데이터 폴더로 배포
- **내부 절차**:
  1. **run_import**: 엑셀(혹은 A4) 데이터를 통합하여 merged.json 생성 (`excel_manager.py` 호출)
  2. **run_ai_analysis**: AI 유사도/협업 분석 (`analysis/generate_ai_analysis.py` 호출)
  3. **create_unified_snapshot**: 결과물 스냅샷 파일 생성
  4. **wrap_up**: 완료 메시지
  5. **deploy**: 웹 데이터 폴더로 결과 JSON 복사 및 임베디드 JS 생성(`rebuild_embedded.py`)

---

## 2. 주요 스크립트별 역할 및 사용법

### excel_manager.py
- **역할**: 엑셀 <-> JSON 변환의 메인 진입점
- **사용법**:
  - `python scripts/pipeline/excel_manager.py import --type both` : 엑셀→merged.json
  - `python scripts/pipeline/excel_manager.py export --type both` : merged.json→엑셀
- **내부적으로** `convert.py`, `convert_a4.py`, `export_xlsx.py`, `export_a4.py` 등 호출

### convert.py
- **역할**: 일반 엑셀(xlsx) → merged.json 변환
- **특징**: config.yaml 기반 컬럼 매핑, 유효성 검사, 개별/통합 JSON 저장 지원

### convert_a4.py
- **역할**: A4 요약표 양식 엑셀 → merged.json 변환 (Named Range 활용)
- **특징**: 여러 파일/폴더 일괄 처리, 부서/유형별 분리 저장 지원

### export_xlsx.py
- **역할**: merged.json → 전체 요약/목록 엑셀 변환
- **특징**: config_export.yaml 기반, 스타일/컬럼/필터 등 커스텀 가능

### export_a4.py
- **역할**: merged.json → A4 요약표 엑셀 변환 (프로젝트별 시트)
- **특징**: 부서/상태/R&D별 필터, 개별/일괄 출력 지원

### analysis/generate_ai_analysis.py
- **역할**: merged.json을 입력받아 AI 유사도/협업 분석 결과 생성
- **출력**: similarity_analysis.json, collaboration_analysis.json
- **특징**: TF-IDF, Jaccard, 도메인/키워드 기반 분석, LLM 확장 가능성

### rebuild_embedded.py
- **역할**: 주요 JSON 결과를 JS 임베디드 데이터로 변환 (웹 UI 렌더링 속도 개선)
- **사용법**: `python scripts/pipeline/rebuild_embedded.py`

---

## 3. 전체 연관관계 및 절차 흐름

1. **엑셀/요약표 데이터 준비**
2. **excel_manager.py import** → (convert.py/convert_a4.py) → merged.json 생성
3. **master_builder.py build**
   - 1) excel_manager.py import
   - 2) analysis/generate_ai_analysis.py (AI 분석)
   - 3) 스냅샷 생성
4. **master_builder.py deploy**
   - output/merged.json, similarity_analysis.json, collaboration_analysis.json → web/data/ 복사
   - rebuild_embedded.py로 JS 데이터 변환
5. **export_xlsx.py / export_a4.py** : 필요시 엑셀로 재가공

---

## 4. 리팩토링/구조 개선 제안

- **중복/유사 기능 통합**: 
  - convert.py/convert_a4.py, export_xlsx.py/export_a4.py 등 유사 로직(컬럼 매핑, 유효성, 로깅 등) 함수/클래스화하여 공통 모듈로 분리
- **입출력 경로/설정 일원화**: config.yaml, config_export.yaml 등 설정파일 구조 통합 및 경로 상수화
- **로깅/에러처리 일관성**: setup_logger 등 로깅 함수 통일, 예외처리 방식 표준화
- **파이프라인 자동화**: master_builder.py에서 각 단계별 상태/에러 리포트, dry-run/step별 실행 옵션 추가
- **테스트/유닛테스트 추가**: 주요 변환 함수별 단위테스트 코드 작성 권장

---

## 5. 기타
- `refactor_tools`, `utils` 폴더는 데이터 전처리/정제, 코드 리팩토링 등 보조 스크립트로, 메인 파이프라인과 직접 연결되진 않음.
- `pdfto` 폴더는 향후 PDF→JSON 변환 등 신규 파이프라인에 활용 예정(현재 독립적).

---

> 본 문서는 2026-03-28 기준, KAIB2026 프로젝트의 파이프라인 구조를 기준으로 작성되었습니다.
