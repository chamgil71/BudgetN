# 실행 계획: index.html 모듈화 및 성능 리팩토링

현재 `index.html` 파일은 약 23MB로, 대부분의 용량이 내장된 거대한 JSON 데이터 세트 때문입니다. 본 계획은 데이터와 로직을 외부로 분리하여 효율성과 성능을 개선하는 것을 목표로 합니다.

## 제안하는 변경 사항

### 데이터 계층 (Data Layer)
- **[신규] [projects.json](file:///c:/ai/KAIB2026/data/projects.json)**: `index.html`의 `EMBEDDED_DATA`를 추출합니다.
- **[신규] [similarity_v10.json](file:///c:/ai/KAIB2026/data/similarity_v10.json)**: `index.html`의 `EMBEDDED_SIM_V10_DATA`를 추출합니다.
- **[수정] [loadData](file:///c:/ai/KAIB2026/index.html)**: `fetch()`를 사용하여 JSON 파일들을 비동기 로드하도록 수정합니다.

### 프레젠테이션 계층 (Presentation Layer)
- **[신규] [main.css](file:///c:/ai/KAIB2026/css/main.css)**: `index.html` 내의 거대한 `<style>` 블록 내용을 이동합니다.
- **[수정] [index.html](file:///c:/ai/KAIB2026/index.html)**: 외부 CSS를 링크하고 내부 스타일을 제거합니다.

### 로직 계층 (Logic Layer)
- **[신규] [constants.js](file:///c:/ai/KAIB2026/js/constants.js)**: 글로벌 상수 및 테마 설정을 정의합니다.
- **[신규] [utils.js](file:///c:/ai/KAIB2026/js/utils.js)**: 공통 유틸리티 함수를 이동합니다.
- **[신규] [app-core.js](file:///c:/ai/KAIB2026/js/app-core.js)**: 메인 실행 및 탭 전환 로직을 추출합니다.
- **[신규] [tab-duplicate.js](file:///c:/ai/KAIB2026/js/tab-duplicate.js)**: 중복 분석 렌더링 로직을 분리합니다.
- **[신규] [tab-projects.js](file:///c:/ai/KAIB2026/js/tab-projects.js)**: 프로젝트 리스트 및 검색 로직을 분리합니다.
- **[수정] [index.html](file:///c:/ai/KAIB2026/index.html)**: 모듈형 JS 파일들을 링크하고 내부 스크립트를 제거합니다.

## 검증 계획
1. **로딩 확인**: 페이지 로드 시 데이터가 성공적으로 페치되는지 확인합니다.
2. **탭 기능**: 개요, 중복 분석 등 모든 탭이 정상 작동하는지 확인합니다.
3. **상호작용**: 필터, 검색, 모달 등이 이전과 동일하게 작동하는지 확인합니다.
4. **파일 크기**: `index.html` 용량이 획기적으로 줄었는지 확인합니다.
