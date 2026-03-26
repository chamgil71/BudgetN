# KAIB2026 데이터 소스 매핑 가이드

본 문서는 대시보드의 각 탭이 어떤 데이터 파일(JSON/JS)을 참조하는지 정리한 가이드입니다.

## 1. 전역 공통 데이터 (`window.DATA`)

대시보드의 거의 모든 기능은 `window.DATA` 객체를 기반으로 동작합니다. 이 객체는 다음 순서로 로드됩니다.

1. **`data/budget_db.json` (우선)**: 서버에서 직접 `fetch`를 통해 로드하는 최신 데이터 파일입니다.
2. **`js/embedded-data.js` (백업)**: 네트워크 문제로 JSON 로드가 실패할 경우를 대비한 하드코딩된 백업 데이터입니다.

### 탭별 데이터 참조 현황

| 탭 이름 (메뉴) | 참조 데이터 필드 (in `window.DATA`) | 비고 |
| :--- | :--- | :--- |
| **개요 (Overview)** | `projects`, `metadata` | 수치 합산 및 차트 생성 |
| **부처별 분석** | `projects` | 부처별 예산 집계 |
| **분야별 분석** | `projects` (ai_domains) | 분야별 트리맵/히어맵 생성 |
| **사업 목록** | `projects` | 상세 필터링 및 테이블 출력 |
| **유사사업 분석** | `analysis.duplicates` | AI 기반 중복 가능성 데이터 |
| **협업 잠재성** | `analysis.collaboration` | 네트워크 분석 및 협업 시나리오 |
| **사업 흐름** | `analysis.flow` | 예산 이동 및 흐름 데이터 |
| **정책 클러스터** | `projects`, `analysis.clusters` | 정책 테마별 그룹화 |
| **AI 기술 분석** | `projects` (ai_tech) | 기술 스택별 현황 |

## 2. 특수 기능용 데이터

일부 고급 시뮬레이션이나 무거운 분석 데이터는 성능을 위해 별도의 임베디드 JS 파일을 사용할 수 있습니다.

- **`js/embedded-sim-v10-data.js`**: 미래 시뮬레이션(Future Sim) 탭의 예측 모델링 데이터.
- **`js/embedded-collab-data.js`**: 협업 분석 탭의 노드/링크 상세 데이터.
- **`js/embedded-hybrid-data.js`**: 교차 분석 및 하이브리드 추천 엔진용 데이터.

## 3. 데이터 수정 사항이 반영되지 않을 때 (FAQ)

### Q: `budget_db.json`을 수정했는데 대시보드에는 옛날 데이터가 나옵니다.
**A: 브라우저의 강한 캐싱 기능 때문입니다.**
브라우저는 성능을 위해 한 번 불러온 JSON 파일을 메모리에 저장해두고 재사용합니다. 이를 해결하려면 다음 방법 중 하나를 시도하세요.

1. **강력 새로고침**: `Ctrl + F5` (Windows) 또는 `Cmd + Shift + R` (Mac)
2. **개발자 도구 설정**: `F12` -> `Network` 탭 -> `Disable cache` 체크박스 활성화 (창이 열려있는 동안만 적용)
3. **코드 수정 (권장)**: `app.js`에서 파일을 불러올 때 타임스탬프를 추가하여 캐시를 무효화할 수 있습니다. (예: `fetch('data/budget_db.json?v=' + Date.now())`)
