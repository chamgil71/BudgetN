# KAIB2026 상세 기술 가이드 및 운영 매뉴얼
> **Advanced Technical Reference for Budget Data Infrastructure**

본 문서는 파이프라인의 내부 작동 원리, 데이터 정합성 유지 방법, 그리고 프론텍엔드와 백엔드 간의 의존성 전반을 다룹니다.

---

## 1. 📂 스크립트 도구함 (Scripts Toolbox)

파이프라인은 기능에 따라 3개의 주요 디렉토리로 나뉩니다.

### 1-1. `scripts/preProc/` (전처리 레이어)
비정형 PDF 데이터를 정형 JSON으로 변환하는 초기 단계입니다.
- **`pdf_to_json.py`**: `pdfplumber`를 이용해 PDF 내의 텍스트 상자와 2D 테이블 구조를 원시 형태(`_raw.json`)로 추출합니다.
- **`budget_parser.py`**: 전처리 엔진의 핵심입니다. 정규식을 통해 (번호-사업명-코드) 패턴을 찾아 사업을 분할하고, `budget_2026` 등 핵심 예산을 추출합니다.
- **`json_manager.py`**: 개별 파싱된 JSON 파일들을 `template_schema.json` 기준으로 검증(Validate)하고 하나로 병합(Merge)합니다.

### 1-2. `scripts/pipeline/` (빌드 및 배포 레이어)
데이터 통합 및 웹 배포를 제어합니다.
- **`master_builder.py`**: 전체 파이프라인의 **오케스트레이터**입니다. `build`, `deploy`, `bundle` 명령을 통합 관리합니다.
- **`excel_manager.py`**: XLSX 파일과 JSON 간의 변환을 라우팅하며, `convert.py`를 호출하여 엑셀 데이터를 임포트합니다.
- **`rebuild_embedded.py`**: `web/data`의 거대 JSON을 JS 변수 형태(`web/js/embedded-data.js`)로 변환하여 브라우저 로딩 속도를 최적화합니다.

### 1-3. `scripts/analysis/` (AI 분석 레이어)
데이터 간의 논리적 연결을 생성합니다.
- **`generate_ai_analysis.py`**: `scikit-learn`의 TF-IDF 벡터라이저를 사용하여 사업 목적과 키워드 간의 유사도를 계산합니다. `similarity_analysis.json`과 `collaboration_analysis.json`을 생성하며, 이는 대시보드의 '유사성'/'협업' 탭에서 시각화됩니다.

---

## 2. ⚙️ 설정 가이드 (Configuration: `config.yaml`)

`config/config.yaml`은 시스템의 모든 환경변수와 맵핑 룰을 정의합니다.

- **`years` 섹션**:
  - `base_year`: 2026 (현재 기준 연도 설정)
  - `label_*`: 엑셀 헤더에서 찾을 연도 레이블 정의
- **`xlsx.column_mapping`**: 엑셀 컬럼명과 JSON 필드 간의 1:1 매칭 정의.
  - `{base}`, `{prev}` 등의 플레이스홀더를 사용하여 연도 변경 시 자동 대응합니다.
- **`search_aliases`**: "과기부" 검색 시 "과학기술정보통신부"가 결과에 포함되도록 하는 동의어 사전입니다.
- **`validation`**: 필수 필드(`code`, `project_name` 등) 누락 시 에러 발생 조건을 설정합니다.

---

## 3. 📊 데이터 스키마 및 ID 발급 규칙

시스템은 데이터 정합성을 위해 다음과 같은 고정 ID 체계를 따릅니다.

### ID 발급 메커니즘 (`id` 필드)
- 원본의 `code`, `project_name`, `department`를 조합하여 MD5 해시를 생성합니다.
- 결과값: `PRJ-A1B2C3D4` 형태
- **장점**: 엑셀의 행 순서가 바뀌거나 파일명이 변경되어도, 사업 내용이 같다면 동일한 고정 ID를 유지하여 AI 분석 결과 및 메모 기능을 보존합니다.

### 핵심 예산 필드 규격
- `budget.2026_budget`: 올해 본예산 (확정/요구)
- `budget.2025_original`: 전년도 본예산
- `budget.2024_settlement`: 전전년도 결산액
- `budget.change_amount`: 증감액 (자동 계산)
- `budget.change_rate`: 증감률 (자동 계산)

---

## 🖥 4. 웹 대시보드 구조 및 의존성

웹 대시보드(`web/`)는 서버 없이도 동작 가능한 **Zero-Server SPA** 구조입니다.

| 탭 / 기능 | 담당 JS 파일 | 필수 데이터 |
| :--- | :--- | :--- |
| **전체 초기화** | `app.js` | `budget_db.json` |
| **사업 목록** | `list-view.js` | `budget_db.json` |
| **유사성 분석** | `duplicate-sim.js` | `similarity_analysis.json` |
| **협업 분석** | `policy-cluster.js` | `collaboration_analysis.json` |
| **미래 시뮬** | `future-sim.js` | `budget_db.json` |

---

## 🚨 5. 트러블슈팅 (Troubleshooting)

### Q1. "Duplicate ID" 또는 "Key Error" 발생 시
- **원인**: 엑셀 내에 동일한 `code`를 가진 행이 존재하거나, 필수 컬럼이 누락됨.
- **해결**: `logs/` 폴더 내의 최신 로그 파일을 확인하여 중복된 코드나 비어있는 셀을 수정하십시오.

### Q2. 연도 변경 후 대시보드 레이블이 바뀌지 않음
- **원인**: 브라우저 강력 캐시 또는 `rebuild_embedded.py` 미실행.
- **해결**: `master_builder.py deploy`를 재실행하고, 브라우저에서 `Ctrl + F5`를 눌러 캐시를 초기화하십시오.

### Q3. PDF 추출 시 표 데이터가 깨짐
- **원인**: PDF 내 표 구조가 복합 셀(Merged)로 구성되어 있어 `pdfplumber`가 인식을 실패함.
- **해결**: `budget_parser.py`의 `clean_table()` 함수 내 예외 처리 로직에 해당 패턴을 추가하거나, 원본 데이터를 엑셀 형태로 변환하여 투입하십시오.
