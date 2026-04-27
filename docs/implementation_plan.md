# BudgetN Implementation Plan

## 목표
현재 BudgetN을 아래 운영 기준 구조에 맞게 정리한다.

1. `PDF -> raw -> structured -> parsed`
2. `parsed / xlsx / yaml -> merged.json`
3. `merged.json -> budget_db.json`
4. `budget_db.json -> metadata / analysis / similarity / collaboration`
5. `web/data` 배포
6. `embedded-*.js` 재생성
7. `web/` 프론트엔드 구동

## 현재 상태 진단

### 정리된 점
- `README.md`는 7단계 구조 기준으로 갱신됨
- `GUIDE.md`는 현재 canonical / 프론트 의존성 / XLSX 조건 중심으로 재작성됨
- `quick_guide.md`는 현재 운영 명령 기준으로 재작성됨
- 레거시 문서는 `docs/backup/`으로 이동됨

### 아직 남은 구조 문제
- `database/output/merged.json`이 항상 canonical final로 남는 흐름이 아직 약함
- PDF parsed 결과를 canonical `merged.json`으로 흡수하는 경로가 일관되지 않음
- 기존 배포 데이터에는 `sub_projects[].budget_base`가 없을 수 있음
- `collaboration_analysis.json`이 프론트 기대 구조를 만족하지 않음
- `config/template.json`이 실제 nested canonical 구조와 맞지 않음

## 구현 우선순위

### Phase 1. Canonical build 고정
목표:
- `merged.json`을 내부 최종본으로 고정

작업:
1. `master_builder.py` 또는 별도 builder에서 `database/output/merged.json` 존재를 강제
2. PDF parsed 병합 경로와 XLSX import 경로를 동일 canonical schema로 수렴
3. `budget_db.json` 생성은 `merged.json` 복사 단계로 명시

완료 조건:
- 어떤 입력 포맷이 들어와도 마지막 내부 산출물은 `database/output/merged.json`

### Phase 2. Canonical schema 정비
목표:
- 실제 운영 스키마와 validator 스키마 일치

작업:
1. `config/template.json`을 nested canonical schema 기준으로 재작성
2. 필수 필드와 optional 필드 구분
3. `sub_projects`, `project_managers`, `history`, `kpi`, `yearly_budgets` 규격 재정의

완료 조건:
- validator가 실제 데이터 구조와 같은 계층 구조를 기준으로 동작

### Phase 3. XLSX import 템플릿 정비
목표:
- 총괄 XLSX에서 바로 `merged.json`을 생성할 수 있는 공식 템플릿 확보

작업:
1. `config/config.yaml`의 `xlsx.column_mapping` 기준 공식 `.xlsx` 템플릿 정의
2. 최소 시트 구성 확정
   - `사업목록`
   - `내역사업`
   - `사업관리자`
   - `사업연혁`
   - `연도별예산`
3. 현재 `web/template/*.csv`를 참고용 예시로 유지할지 폐기할지 결정
4. `scripts/pipeline/generate_summary_template.py`로 `template_project.xlsx` 생성 경로 유지

완료 조건:
- 운영자가 공식 `.xlsx` 템플릿 하나를 받아 바로 import 가능

### Phase 4. sub_projects / 프론트 호환 필드 보강
목표:
- 프론트가 기대하는 내역사업 관련 필드 보강

작업:
1. `sub_projects[].budget_base` 생성
   - 기준: `budget_{base_year}` 또는 `budget_2026`
2. `budget_prev` 보조 필드 유지
3. 프론트에서 실제 사용하는 필드와 canonical 필드의 이름 일치 여부 정리

완료 조건:
- 내역사업 히스토그램, 집중도, 비교 모달 수치가 정상 동작

### Phase 5. 분석 sidecar 구조 보강
목표:
- 프론트 협업/유사도 탭이 기대하는 데이터 구조 충족

작업:
1. `similarity_analysis.json`의 실제 사용 영역 정리
2. `collaboration_analysis.json`에 아래 구조 추가
   - `summary_statistics`
   - `collaboration_chains`
   - `collaboration_network`
3. `budget_db.json.analysis` 내부 기본 집계와 sidecar 역할 경계 정의

완료 조건:
- 협업 탭, 유사도 탭이 fallback 없이도 정상 동작

### Phase 6. YAML adapter 초안
목표:
- YAML 입력도 canonical `merged.json`으로 흡수 가능하게 설계

작업:
1. YAML project schema 초안 확정
2. loader / normalizer / validator 분리
3. metadata / analysis는 입력 YAML을 신뢰하지 않고 재계산

완료 조건:
- YAML -> merged.json 경로 문서화 및 구현 가능 상태

## 추천 실행 순서
1. Canonical build 고정
2. template.json 재작성
3. 공식 XLSX 템플릿 추가
4. sub_projects 호환 필드 보강
5. collaboration_analysis 구조 확장
6. YAML adapter 착수

## 산출물 기준

### 내부 canonical
- `database/output/merged.json`

### 프론트 데이터
- `web/data/budget_db.json`
- `web/data/similarity_analysis.json`
- `web/data/collaboration_analysis.json`

### fallback / 정적 배포 지원
- `web/js/embedded-data.js`
- `web/js/embedded-sim-v10-data.js`
- `web/js/embedded-collab-data.js`
- `web/js/embedded-hybrid-data.js`

## 완료 기준
- 문서상 7단계 구조와 실제 코드 경로가 일치
- 공식 XLSX 템플릿으로 `merged.json` 생성 가능
- `budget_db.json`과 sidecar 데이터만으로 프론트 주요 페이지가 정상 동작
