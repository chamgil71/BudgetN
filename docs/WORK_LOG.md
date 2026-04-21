# 📝 BudgetN 작업 일지 (Work Log)

이 파일은 BudgetN 프로젝트의 개발 진척 상황과 주요 변경 사항을 기록합니다.

---

## 2026-04-21 — Vite 빌드 누락 문제 수정 (프로덕션 JS/데이터 전체 미서빙)

### 문제 현상
- Vercel 배포 사이트에서 그래프가 빈 박스로만 표시됨
- 탭/버튼이 동작하지 않음
- `budget_db.json` 업데이트 후 재배포해도 데이터가 반영되지 않음

### 근본 원인
`web/vite.config.js`에 `publicDir`가 미설정 상태였음.

- Vite의 기본 `publicDir`는 프로젝트 루트의 `public/` 폴더를 가리키는데, `web/public/`가 존재하지 않음
- `index.html`의 `<script src="js/app.js">` 등 **`type="module"` 없는 스크립트는 Vite가 번들링 불가** → 빌드 출력에서 제외됨
- 결과: `dist/`에는 CSS 파일 1개만 생성되고 JS 전체(`app.js`, `charts.js`, `embedded-data.js` 등 18개)와 `data/budget_db.json`이 모두 누락

```
# 수정 전 dist/ 구조
dist/
├── login.html
├── index.html
└── assets/main-*.css  ← CSS 하나뿐, JS 없음!
```

### 수정 내용 (`web/vite.config.js`)

`writeBundle` 훅에서 `js/`, `css/`, `data/` 디렉토리를 `dist/`로 복사하는 커스텀 플러그인 추가:

```js
import { cpSync, existsSync } from 'fs'

function copyStaticDirs() {
  return {
    name: 'copy-static-dirs',
    writeBundle(options) {
      const outDir = options.dir || resolve(__dirname, 'dist')
      for (const dir of ['js', 'css', 'data']) {
        const src = resolve(__dirname, dir)
        const dest = resolve(outDir, dir)
        if (existsSync(src)) cpSync(src, dest, { recursive: true })
      }
    }
  }
}
```

### 수정 후 dist/ 구조

```
dist/
├── index.html
├── login.html
├── assets/main-*.css
├── js/          ← app.js, charts.js, embedded-data.js 등 18개
├── css/         ← main.css, theme-*.css 등
└── data/        ← budget_db.json, collaboration_analysis.json, similarity_analysis.json
```

### 영향
- `fetch('data/budget_db.json')` 프로덕션에서 정상 응답 → 최신 데이터 로드
- 모든 JS 파일 서빙 → 버튼/탭/차트 정상 동작
- 이후 `budget_db.json` 업데이트 후 푸시하면 사이트에 즉시 반영

### 커밋
- `382e61b` fix(build): copy js/, css/, data/ to dist/ so non-module scripts are served in production

---

## 2026-04-20~21 — Vercel 배포 환경 구성

### 변경 사항
- `vite.config.js`: `base: '/BudgetN/'` → `base: '/'` 변경 (Vercel 루트 서빙 대응)
- `vite.config.js`: `login.html`을 멀티 엔트리로 추가하여 빌드에 포함
- `vercel.json`: 프로젝트 루트 → `web/` 폴더 내로 이동 (Vercel Root Directory = `web/`)
- `index.html`: Supabase 인증 체크 추가 (body `visibility:hidden` → 인증 성공 후 표시)
- `docs/github_deployment_guide.md`: 배포 구성 가이드 문서화

### vercel.json 설정 (`web/vercel.json`)
```json
{
  "buildCommand": "npm install && npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/login", "destination": "/login.html" },
    { "source": "/((?!login\\.html$|assets/|data/|js/|css/).*)", "destination": "/index.html" }
  ]
}
```
