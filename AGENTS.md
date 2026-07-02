# AGENTS.md — BudgetN

정부 예산 데이터 파이프라인 & 웹 대시보드 프로젝트. 이 문서는 이 레포에서 AI 에이전트가 수행하는 모든 작업의 **최상위 진입점(SSOT)**입니다.

- **적용 프로필**: `standard` — [`agent/profiles/standard.md`](./agent/profiles/standard.md)
- **오케스트레이션**: 복수 단계 작업 전 [`agent/orchestration.md`](./agent/orchestration.md)의 라우팅·의존성·롤백 규칙을 따릅니다.
- **거버넌스 엔진**: 구현/검증 패턴이 필요할 때 [`agent/knowledge/`](./agent/knowledge/)를 물리적으로 읽어(`view_file`) 적용합니다.

## Facts (무엇을 만드는가)

- 제품 사양·설계의 1차 앵커는 [`docs/spec.md`](./docs/spec.md)입니다. 보조 컨텍스트는 [`README.md`](./README.md)·[`docs/`](./docs/)를 참조합니다.
- 세션 진행 로그는 루트 [`worklog.md`](./worklog.md)에 누적합니다.

## Project Shape

- `backend/`, `scripts/` — PDF/XLSX/YAML 파싱 → canonical JSON(`merged.json`) 통합 → TF-IDF 분석 파이프라인 (7단계)
- `database/`, `data.xlsx` — 통합 데이터/입력 자산 (로컬 생성물로 취급, Git 커밋 최소화)
- `web/` — 정적 대시보드 (GitHub Pages 자동 배포)
- `config/`, `docs/` — 설정 및 설계 문서

## Local Rules

- 파이프라인 단계별 입·출력 파일 경계를 유지하고, 한 단계가 다른 단계의 중간 산출물을 우회 참조하지 않습니다.
- 하드코딩 금지: 경로·상수·키는 `config/` 또는 환경변수로 주입합니다.
- 단일 파일 200라인 초과 시 도메인·유틸 단위로 분리합니다. Python은 `pathlib.Path`·타입힌트를 준수합니다.

## Verification

변경 범위에 맞는 최소 검증을 수행하고, 실행 불가 시 정확한 사유를 보고합니다.

```bash
python master_builder.py        # 전체 파이프라인 재생성
cd web && npm run build         # 대시보드 정적 빌드
```
