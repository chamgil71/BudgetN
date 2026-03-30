# KAIB2026 웹 UI 기능 분석 및 개선 제안

## 1. 개요
본 문서는 `web/index.html`의 상단 헤더 기능 분석과 `kaib_html`의 디자인 시스템을 웹 버전에 적용하기 위한 방안을 정리합니다.

## 2. "문서" 메뉴 오작동 원인 분석

### 현상
*   헤더의 "문서" 버튼을 클릭해도 드롭다운 메뉴가 나타나지 않음.

### 원인
1.  **Missing Script**: `index.html` (Line 1693)에서 `toggleDocMenu(event)` 함수를 호출하고 있으나, 해당 함수의 정의가 프로젝트 내부 어느 JS 파일(`common.js`, `app.js` 등)에도 존재하지 않습니다.
2.  **CSS 구조**: 내부에 하드코딩된 스타일(`style="display:none"`)을 제어할 스크립트가 누락되어 초기 상태(숨김)에서 변화가 없습니다.

### 해결 방안 (제안)
*   `js/common.js` 또는 `index.html` 하단에 메뉴 토글 로직 추가:
    ```javascript
    function toggleDocMenu(event) {
        const menu = document.getElementById('doc-menu');
        if (menu) {
            const isHidden = menu.style.display === 'none';
            menu.style.display = isHidden ? 'block' : 'none';
        }
        event.stopPropagation();
    }
    // 메뉴 외 영역 클릭 시 닫기 로직도 필요
    ```

## 3. CSS 테마 시스템 적용 방안

### 분석 결과
*   `kaib_html/css/` 폴더에 `theme-toss.css`, `theme-neumorphism.css`, `theme-glassmorphism.css` 등 고도화된 테마 파일이 존재함.
*   현재 `web/index.html`은 내부 `<style>` 태그에 디자인이 고정되어 있음.

### UI 추가 제안 (테마 선택기)
*   **위치**: 헤더의 "문서"와 "다크" 버튼 사이 (Line 1733~1734 영역)
*   **형태**: 가독성이 좋은 `select` 박스 또는 아이콘 버튼 그룹.

**삽입 예시 코드:**
```html
<select class="theme-toggle" onchange="changeAppTheme(this.value)" id="theme-selector">
    <option value="default">기본 테마</option>
    <option value="toss">Toss 스타일</option>
    <option value="neumorphism">뉴모피즘</option>
    <option value="glassmorphism">글래스모피즘</option>
</select>
```

### 구현 메커니즘
1.  **파일 복사**: `kaib_html/css/`의 테마 파일들을 `web/css/`로 복사.
2.  **동적 로딩**: 선택된 값에 따라 `<head>` 내의 `<link>` 태그 `href`를 교체하거나, `:root` 변수를 오버라이드하는 방식 사용.
3.  **Local Storage 저장**: 사용자가 선택한 테마를 브라우저에 저장하여 재방문 시에도 유지되도록 구현.

## 4. 향후 작업 로드맵
1.  [ ] `toggleDocMenu` 함수 구현을 통한 문서 메뉴 정상화
2.  [ ] `web/css/` 폴더로 테마 파일 마이그레이션
3.  [ ] 헤더 내 테마 선택 UI 추가 및 로직 연결
