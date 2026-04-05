# KAIB AI 재정사업 분석 플랫폼 (KAIB2026)
> **AI-Driven Budget Data Pipeline & Web Dashboard**

본 프로젝트는 정부 예산자료(PDF) 및 관리용 엑셀(XLSX) 데이터의 **추출-가공-분석-배포**를 자동화하는 End-to-End 데이터 파이프라인과 이를 시각화하는 웹 대시보드 시스템입니다. 

단순한 데이터 시각화를 넘어, 부처 간 사업의 유사도를 분석하고 협업 가능성을 도출하는 AI 엔진을 내장하고 있으며, 매년 반복되는 예산 분석 작업을 `config.yaml` 설정 하나로 차년도 체계에 즉각 대응할 수 있도록 설계되었습니다.

---

## 🏗 시스템 아키텍처 및 데이터 흐름

데이터의 무결성과 추적성(Traceability)을 위해 **4단계 분리형 아키텍처**를 채택했습니다.

### 1단계: Extraction (추출)
- `pdf_to_json.py`: 비정형 PDF(예산서)에서 표와 텍스트를 구조적으로 추출하여 `_raw.json`을 생성합니다.
- `convert.py`: 엑셀(XLSX, XLSM) 원본 파일을 행 단위로 읽어들입니다.

### 2단계: Processing (정제 및 파싱)
- `budget_parser.py`: 정규식 앵커와 맵핑 룰을 통해 `_raw.json`을 개별 프로젝트(Project) 단위로 분할하고 예산/속성 값을 추출합니다.
- `excel_manager.py`: 엑셀 데이터의 스키마를 검증하고 `merged.json`으로 통합 병합을 수행합니다.

### 3단계: AI Analysis (분석)
- `generate_ai_analysis.py`: 통합된 `merged.json`을 입력받아 TF-IDF 및 Cosine Similarity 알고리즘을 통해 **사업 유사도** 및 **부처 협업 모델**을 자동 생성합니다.

### 4단계: Deploy (웹 배포)
- `master_builder.py deploy`: 분석 결과를 `web/data`로 배포하고, 구형 브라우저 대응을 위한 `rebuild_embedded.py`가 연쇄 구동됩니다.

---

## 📂 디렉토리 상세 구조

```text
KAIB2026/
├─ config/                # [핵심] 파이프라인 및 UI 설정 (Year, Alias, Schema)
│  └─ config.yaml         # 기준 연도(Base Year) 및 컬럼 맵핑 정의
├─ input/                 # 원본 데이터 투입처 (PDF, XLSX)
├─ output/                # 파이프라인 중간 산출물 및 빌드 스냅샷
│  └─ merged.json         # 모든 데이터가 집약된 마스터 DB
├─ scripts/               # 파이프라인 자동화 엔진
│  ├─ preProc/            # [NEW] PDF 추출 및 원시 데이터 정제 (Step 1~2)
│  ├─ pipeline/           # 엑셀 변환 및 빌드 프로세스 제어 (Step 3~4)
│  └─ analysis/           # AI 알고리즘 및 텍스트 분석 로직
├─ database/              # 업무용 원본 DB 및 백업 보관소
├─ web/                   # 대시보드 프론트엔드 (Pure HTML/CSS/JS)
│  ├─ data/               # 대시보드가 실제 참조하는 배포용 JSON
│  └─ js/ / css/          # 기능별 모듈화된 UI 스크립트 및 스타일
├─ README.md              # 프로젝트 메인 안내서
├─ GUIDE.md               # 기술 세부 가이드 및 트러블슈팅
└─ quick_guide.md         # 운영자를 위한 퀵 명령어 가이드
```

---

## 🚀 주요 기능 특장점

1. **Static Year Configuration**: `config.yaml`에서 `base_year: 2027`로 변경하는 순간, 모든 엑셀 임포트 로직과 웹 UI의 레이블(차트, KPI)이 즉각 차년도 체계로 전환됩니다.
2. **Stable ID Hashing**: 부처명, 사업명, 사업코드를 조합한 **MD5 해시 ID**를 발급하여, 데이터가 업데이트되더라도 프로젝트 간 고유 연결성을 영구적으로 유지합니다.
3. **Multi-Step Search**: `AND`, `OR`, `NOT`, `구문 검색`을 지원하는 커스텀 검색 엔진이 탑재되어 대용량(수천 건) 사업 데이터를 실시간 필터링합니다.
4. **Zero-API-Cost AI**: 외부 유료 LLM API 없이도 `scikit-learn` 기반의 자체 분석망을 통해 사업 중복성과 협업 필요성을 도출합니다.

---

## 🛠 실행 방법

### 환경 구축
```bash
python -m venv .venv
source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

### 빌드 및 배포 일괄 실행
```bash
# 엑셀/JSON 통합 빌드 및 AI 분석
python scripts/pipeline/master_builder.py build

# 분석 결과 웹 대시보드 반영
python scripts/pipeline/master_builder.py deploy
```

---

## 🤝 유지보수 원칙
- **Data First**: 모든 변경은 `config.yaml`의 스키마 정의를 우선 확인한 후 코드를 수정합니다.
- **Pure Web**: 프레임워크 의존성 없이 순수 JS/CSS를 유지하여 오프라인 배포 시 호환성을 극대화합니다.
- **Traceable Logging**: 모든 변환 작업은 `logs/` 폴더에 타임스탬프와 함께 기록되어 데이터 누락을 추적합니다.
