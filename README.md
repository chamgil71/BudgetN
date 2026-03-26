# KAIB AI 재정사업 분석 플랫폼
(KAIB Data Pipeline & Web Dashboard)

본 프로젝트는 AI 재정사업 데이터의 **Excel 작성/수정부터 웹 대시보드 배포까지의 End-to-End 파이프라인**을 제공하며, 데이터를 시각화하는 프론트엔드 대시보드를 포함하고 있습니다. 연도 하드코딩을 제거하여 매년 `config.yaml`의 기준 연도 환경변수만 교체하면 즉각 차년도 분석 체계로 전환될 수 있는 유연한 아키텍처를 자랑합니다.

## 디렉토리 구조 

```text
KAIB2026/
├─ input/                 # 관리자가 수정/작성한 원본 Excel(총괄표, A4요약 등) 파일 투입처
├─ output/                # 파이프라인 처리를 거쳐 생성된 빌드 산출물 폴더 (merged.json 등)
├─ web/                   # 대시보드 프론트엔드 시스템 (HTML, CSS, JS)
│  ├─ data/               # (핵심) 대시보드가 실제 바라보는 배포용 JSON 파일들
│  └─ js/                 # 차트, 탭 렌더링 등 화면 UI 구동 스크립트
├─ scripts/               # 자동화 스크립트 구역
│  ├─ pipeline/           # 엑셀 파싱 단 및 파이프라인 조율 스크립트 (master_builder 등)
│  ├─ analysis/           # AI 텍스트 분석(유사도/협업망) 처리 스크립트
│  └─ legacy_tools/       # 기존 CSV/JSON 파편화 스크립트 등 보관
├─ config/                # 파이프라인 공통 환경 설정 (`config.yaml`에서 기준 Year 지정)
├─ backend/               # 향후 API 기반 서비스 확장에 대비한 서버 스켈레톤
├─ GUIDE.md               # 데이터 의존성 맵 및 트러블슈팅 매뉴얼 (본 문서를 이은 상세 가이드)
└─ docs/backup/           # 미사용 구형 모듈 격리
```

## 빠른 시작 (Quick Start)

### 1. 데이터 업데이트
1. `input/` 디렉토리에 수정된 엑셀 파일(`_총괄_`, `_A4요약_` 형태 등)을 넣습니다.
2. 터미널을 열고 다음 빌드 스크립트를 실행합니다:
   ```bash
   python scripts/pipeline/master_builder.py build
   ```
3. `output/` 폴더에 `merge_{date}_통합.json`을 비롯한 스냅샷 및 유사도 분석 결과가 올바르게 생성되었는지 확인합니다.

### 2. 웹 배포 (Deploy)
1. 결과물에 문제가 없다면, 바로 배포 명령어를 실행합니다:
   ```bash
   python scripts/pipeline/master_builder.py deploy
   ```
2. 이를 통해 `web/data` 내부로 파일들이 덮어씌워지며, `rebuild_embedded.py`가 연쇄 구동되어 빠른 웹 로딩을 위한 백업 설정도 함께 전개됩니다.
3. 브라우저에서 `web/index.html`을 열어 즉시 갱신된 데이터를 확인합니다.

## 주요 특징
* **Zero Cost AI Analysis**: API 연동 비용을 발생시키지 않고도, 자체 TF-IDF 기반 Jaccard 유사도 분석을 이용해 협업 가능성과 중복도를 계산합니다.
* **Dynamic Year UI**: `config.yaml` 내용 한 번 변경으로 JS 상의 차트 연도 레이블, 집계 KPI가 모두 "2027 예산", "2027년도" 등으로 동적 치환됩니다.
* **One-Click Deploy**: 엑셀 수기 관리와 웹 개발 단절을 극복하는 `master_builder.py`로 운영 복잡도를 크게 낮췄습니다.

---
자세한 운용 팁과 데이터 연관 매핑은 `GUIDE.md`를 참고해 주세요.
