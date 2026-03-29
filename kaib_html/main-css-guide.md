# main.css 디자인 시스템 가이드

## 개요
`main.css`는 KAIB2026 예산분석 대시보드의 글로벌 디자인 시스템입니다.

## CSS 변수 (Design Tokens)

### 배경/텍스트
| 변수 | 라이트 | 다크 | 용도 |
|------|--------|------|------|
| `--bg` | `#f8fafc` | `#0f172a` | 페이지 배경 |
| `--bg-secondary` | `#f1f5f9` | `#1e293b` | 보조 배경 (탭, 서브영역) |
| `--bg-card` | `#ffffff` | `#1e293b` | 카드 배경 |
| `--bg-card-hover` | `#f9fbfc` | `#334155` | 카드 호버 |
| `--text-primary` | `#1e293b` | `#f1f5f9` | 본문 텍스트 |
| `--text-secondary` | `#475569` | `#94a3b8` | 보조 텍스트 |
| `--text-muted` | `#94a3b8` | `#64748b` | 약한 텍스트 |

### 액센트/상태
| 변수 | 값 | 용도 |
|------|-----|------|
| `--accent` | `#4a9eff` | 주요 강조색 (파란색) |
| `--accent-dim` | `rgba(74,158,255,0.1)` | 강조색 배경 |
| `--green` / `--green-dim` | `#10b981` | 증가/긍정 |
| `--red` / `--red-dim` | `#ef4444` | 감소/부정 |
| `--yellow` / `--yellow-dim` | `#f59e0b` | 경고 |
| `--purple` / `--purple-dim` | `#8b5cf6` | 보조 강조 |

### 레이아웃
| 변수 | 값 | 용도 |
|------|-----|------|
| `--border` | `#e2e8f0` | 테두리 |
| `--radius` | `12px` | 카드 둥근 모서리 |
| `--shadow` | box-shadow 값 | 카드 그림자 |

## 다크모드
`[data-theme="dark"]` 선택자로 활성화됩니다. JS에서 `document.documentElement.dataset.theme = 'dark'`로 전환합니다.

## 주요 컴포넌트 클래스

| 클래스 | 용도 |
|--------|------|
| `.header` | 상단 헤더 (그라데이션 배경) |
| `.tab-nav` / `.tab-btn` | 탭 네비게이션 |
| `.card` / `.card-title` | 콘텐츠 카드 |
| `.kpi-grid` / `.kpi-card` | KPI 지표 카드 그리드 |
| `.grid-2` / `.grid-3` / `.grid-2-1` | 반응형 그리드 레이아웃 |
| `.theme-toggle` | 다크모드 토글 버튼 |

## 반응형 브레이크포인트
- **1024px 이하**: 2열 그리드로 축소
- **768px 이하**: 1열 그리드, 패딩 축소

## 테마 교체 방법
`main.css` 대신 아래 테마 파일을 `<link>`로 교체하면 됩니다:
- `theme-toss.css` — 토스 스타일 (깔끔, 카드 중심)
- `theme-neumorphism.css` — 뉴모피즘 (입체 소프트 UI)
- `theme-glassmorphism.css` — 글래스모피즘 (블러, 반투명)

```html
<!-- 기본 -->
<link rel="stylesheet" href="css/main.css">
<!-- 또는 토스 스타일 -->
<link rel="stylesheet" href="css/theme-toss.css">
```
