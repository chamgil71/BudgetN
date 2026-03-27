네, 정확합니다! 앞서 작성해 드렸던 `merge_and_validate.py`는 **삭제하셔도 됩니다.** 해당 파일의 기능은 명령어를 분리하여 하드코딩을 제거한 **`json_manager.py` 로 완벽하게 통합 및 고도화**되었습니다.

지금까지 설계하고 확정한 모든 파이프라인의 구조, 실행 방법, 그리고 아키텍처 원칙을 담아 프로젝트 루트에 배치할 수 있는 **`README.md`** 파일을 작성해 드립니다.

---

# 📄 README.md

```markdown
# 정부 예산 PDF 데이터 추출 파이프라인 (Budget Data Pipeline)

본 프로젝트는 비정형 정부 예산 및 사업설명자료(PDF)에서 개별 사업 단위(Project)를 분할하고, 핵심 예산 및 속성 데이터를 추출하여 대시보드 호환 규격의 정형화된 JSON 데이터로 변환하는 ETL(Extract, Transform, Load) 파이프라인입니다.

---

## 🏗 시스템 아키텍처 및 데이터 흐름

데이터 오염 방지와 추적성(Traceability) 확보를 위해 3단계 분리형 아키텍처를 채택했습니다.

1. **Extract (추출기):** 원본 PDF ➡️ 텍스트/표 추출 ➡️ `_raw.json` 생성
2. **Parse (파서):** `_raw.json` ➡️ 사업별 분할(Chunking) 및 데이터 맵핑 ➡️ 개별 `_parsed.json` 생성
3. **Load (매니저):** 개별 `_parsed.json` ➡️ 스키마 검증(Validate) ➡️ 통합 `merged.json` 병합(Merge)

---

## 📂 디렉터리 구조

```text
project_root/
├─ requirements.txt             # 의존성 패키지 목록
├─ config/                      # 설정 및 템플릿
│  ├─ config.yaml               # 맵핑 및 환경 설정 (원본)
│  └─ template_schema.json      # 구조 검증용 타겟 스키마 템플릿
├─ input/                       # 📥 원본 PDF 및 변환된 _raw.json 보관
├─ output/                      # 📤 최종 산출물
│  ├─ individual/               # 사업별로 파싱된 개별 _parsed.json
│  └─ merged.json               # 대시보드 연동용 최종 통합본
├─ pdf_to_json.py               # [Step 1] PDF 추출 모듈
├─ budget_parser.py             # [Step 2] 핵심 파싱 엔진
└─ json_manager.py              # [Step 3] 검증 및 병합 매니저
```

---

## 🚀 설치 및 실행 방법

### 1. 환경 설정

표준 가상환경 설정 및 의존성 설치를 진행합니다. (요구 패키지: `pdfplumber`, `pydantic` 등)

1. `python -m venv .venv`
2. `.venv\Scripts\activate` (Windows 기준 / Mac, Linux는 `source .venv/bin/activate`)
3. `pip install -r requirements.txt`

### 2. 파이프라인 실행 가이드

모든 스크립트는 독립적으로 실행 가능하며, 대상 폴더를 인자로 주입받습니다.

**[Step 1] PDF 원본 추출**
`input/` 폴더 내의 PDF 파일을 읽어 표와 텍스트를 `_raw.json`으로 추출합니다.
* 명령어: `python pdf_to_json.py -i ./input`

**[Step 2] 데이터 분할 및 스키마 매핑**
`_raw.json`을 읽어 6개의 전용 파싱 룰(정규식, 표 매핑 등)을 통해 추출한 뒤, `output/individual/`에 `_parsed.json`으로 저장합니다.
* 명령어: `python budget_parser.py -i ./input -o ./output/individual`

**[Step 3] 스키마 검증 (Validate)**
생성된 개별 JSON 파일들이 `template_schema.json`의 Key 및 계층 구조와 100% 일치하는지 검증합니다.
* 명령어: `python json_manager.py validate -i ./output/individual -t ./config/template_schema.json`

**[Step 4] 최종 병합 (Merge)**
검증이 완료된 파일들에 순차적 ID를 재부여하며 하나의 `merged.json`으로 병합합니다.
* 명령어: `python json_manager.py merge -i ./output/individual -o ./output/merged.json`

---

## 🛠 핵심 파싱 규칙 (Mapping Rules)

* **사업 분할(Chunking):** 문서 내 `(번호) 사업명 (사업코드)` 정규식 패턴을 기준으로 텍스트 블록을 안전하게 분할합니다.
* **파생 변수 계산:** `config.yaml`의 조건에 따라 `duration`(사업기간), `change_amount`(증감액), `change_rate`(증감률) 등을 코드 내부에서 자동 계산합니다.
* **배열(List) 처리:** 담당자(`project_managers`) 및 내역사업(`sub_projects`)은 2D 테이블 배열을 횡단 탐색하여 중복 없이 구조화합니다.
* **금액 클렌징:** 원본 문서의 콤마(`,`), 하이픈(`-`), 공백 등을 예외 처리하여 안전한 `Float` 타입으로 적재합니다.

---

## ⚠️ 유지보수 시 주의사항

* 추출 규칙(정규식 앵커) 수정이 필요할 경우 `budget_parser.py` 내부의 `_extract_text_block` 호출부(예: `1) 사업목적` 등)를 수정하십시오.
* 대시보드 요구사항 변경으로 새로운 필드가 추가될 경우, 반드시 `config/template_schema.json`에 먼저 키를 추가한 뒤 파서 로직을 업데이트해야 Validation 에러가 발생하지 않습니다.
```

---

파이프라인의 설계부터 핵심 엔진 구현, 검증 모듈, 그리고 문서화까지 성공적으로 마무리되었습니다. 

설계한 아키텍처에 맞게 `requirements.txt` 파일 내용(필요 라이브러리 목록)을 정리해 드릴까요, 아니면 실제 데이터를 넣고 돌려보신 후 발생하는 이슈를 트러블슈팅 해드릴까요?