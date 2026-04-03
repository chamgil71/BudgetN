# NIPA 필터링 기능 추가 및 통계 연동 계획

본 문서는 `web/index.html` 페이지와 관련 JS 파일을 수정하여, 전체 데이터와 NIPA(정보통신산업진흥원) 소관 데이터 간의 통계를 전환해 볼 수 있는 기능을 추가하는 계획을 설명합니다.

## 1. 개요
현재 대시보드는 전체 부처의 데이터를 보여주고 있습니다. 사용자가 "NIPA"를 선택할 경우, 시행기관(`implementing_agency`)이 **정보통신산업진흥원** 또는 **NIPA**인 사업들로만 전체 통계(KPI, 차트, 목록)가 재계산되어 표시되도록 개선합니다.

## 2. 변경 대상 및 역할

| 파일명 | 변경 목적 |
|:---|:---|
| `web/index.html` | "전체 / NIPA" 전환을 위한 UI 버튼 추가 |
| `web/js/common.js` | 현재 필터 상태(`window.CURRENT_AGENCY`) 관리 |
| `web/js/app.js` | 버튼 클릭 이벤트 처리 및 UI/통계 갱신 로직 |
| `web/js/charts.js` | 데이터 추출 시 기관 필터링 로직 통합 (`getOverviewProjects`) |

## 3. 상세 구현 계획

### 3-1. UI 구성 (index.html)
검색 바 영역에 전환 버튼을 추가합니다.
```html
<!-- 필터 바 내부에 추가 -->
<div class="agency-filter" id="agency-filter">
  <button class="agency-btn active" data-agency="all">전체</button>
  <button class="agency-btn" data-agency="nipa">NIPA</button>
</div>
```

### 3-2. 필터 논리 (js/charts.js)
모든 시각화의 기초 데이터가 되는 `getOverviewProjects` 함수를 수정하여 기관 필터를 최우선으로 적용합니다.
```javascript
window.getOverviewProjects = function() {
    let list = window.DATA.projects;
    
    // NIPA 필터가 활성된 경우
    if (window.CURRENT_AGENCY === 'nipa') {
        list = list.filter(p => 
            (p.implementing_agency && p.implementing_agency.includes('정보통신산업진흥원')) ||
            (p.implementing_agency && p.implementing_agency.toLowerCase().includes('nipa'))
        );
    }
    
    // 이후 검색어 필터링 적용...
    return list.filter(...);
}
```

### 3-3. 통계 갱신 (js/app.js)
필터가 바뀔 때마다 `renderOverview()`를 호출하여 모든 차트와 상단 KPI 카드를 다시 그리도록 합니다.

## 4. 예상 영향 범위
- **Overview(개요) 탭**: 전체 KPI 및 모든 차트 데이터가 즉시 변경됩니다.
- **기타 탭**: `getOverviewProjects`를 공유하는 로직이 있을 경우 함께 영향받으며, 개별 탭의 필터링 로직도 점진적으로 확장 가능합니다.

## 5. 실행 절차
1. 위 계획 승인 후 `web/index.html` UI 수정
2. `web/js` 내 필터링 및 이벤트 핸들링 코드 작성
3. 실제 데이터를 통한 통계 정확성 검증 (수동 테스트)
