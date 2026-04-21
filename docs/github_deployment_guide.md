# BudgetN Dashboard GitHub 배포 가이드

> 저장소: `https://github.com/chamgil71/BudgetN.git`  
> 배포 URL: `https://budget-n.vercel.app`  
> 인증: Supabase 이메일 로그인 (프로젝트 ID: `syxpwvmniwzohmxmvlyl`)

프로젝트가 백엔드/데이터 스크립트와 프론트엔드(`web/`) 뷰로 완벽히 분리되었습니다. 
해당 폴더 구조를 기반으로 GitHub Pages 또는 Vercel을 통해 매우 쉽게 무료 호스팅/배포가 가능합니다.

---

## 현재 설정 (2026-04-21 기준)

### 구조

```
BudgetN/ (git 루트)
├── web/                        ← Vercel Root Directory
│   ├── index.html              ← 메인 앱 (로그인 후 진입, visibility:hidden으로 시작)
│   ├── login.html              ← 로그인 페이지 (Supabase Auth)
│   ├── vercel.json             ← Vercel 빌드/라우팅 설정 (web/ 안에 위치)
│   ├── vite.config.js          ← login.html 멀티 엔트리 빌드 설정
│   ├── js/, css/, data/        ← 정적 리소스
│   └── dist/                   ← 빌드 출력 (Vercel 서빙)
└── backend/, docs/, ...
```

### vercel.json (`web/vercel.json`)

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

> **핵심**: Vercel Root Directory = `web` 이면 vercel.json도 반드시 `web/` 안에 있어야 한다.

### Vercel 대시보드 설정

| 항목 | 값 |
|---|---|
| Root Directory | `web` |
| Build Command | `npm install && npm run build` |
| Output Directory | `dist` |

### Vercel 환경변수

| Key | Value |
|---|---|
| `VITE_SUPABASE_URL` | `https://syxpwvmniwzohmxmvlyl.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | Supabase 콘솔에서 확인 |

---

## 인증 흐름 (Supabase)

```
사용자 접속 (/)
    ↓
index.html 로드 → Supabase getUser() 호출 (body visibility:hidden 상태)
    ↓
미로그인 → login.html 리다이렉트
    ↓
이메일 + 비밀번호 입력 → signInWithPassword()
    ↓
성공 → index.html (body visibility 복원, 앱 표시)
```

- `window._client`: index.html 인라인 스크립트에서 생성한 Supabase 클라이언트
- `window.authClient`: login.html에서 사용하는 Supabase 클라이언트
- 로그아웃: `window._client.auth.signOut().then(() => location.reload())`

### Supabase URL Configuration

[Supabase 콘솔 → Authentication → URL Configuration](https://supabase.com/dashboard/project/syxpwvmniwzohmxmvlyl/auth/url-configuration)

| 항목 | 값 |
|---|---|
| Site URL | `https://budget-n.vercel.app` |
| Redirect URLs | `https://budget-n.vercel.app/**` |

> 3개 사이트가 동일 Supabase 프로젝트를 공유하므로 `auth.users`에 등록된 사용자는 모든 사이트 로그인 가능

---

## 빈 화면 문제 원인 및 해결 (2026-04-21 해결)

| 원인 | 증상 | 해결 |
|---|---|---|
| `vercel.json` 없음 | Vercel이 빌드 방법을 모름 | `web/vercel.json` 생성 |
| `%VITE_SUPABASE_URL%` 미치환 | Supabase 초기화 실패 → `visibility:hidden` 유지 → 빈 화면 | Vercel 환경변수 등록 |
| `vercel.json` 위치 오류 | Root Directory=`web`인데 루트에 파일 위치 | `web/` 안으로 이동 |

---

## 방법 1. Vercel 을 이용한 강력하고 빠른 배포 (추천)
Vite 기반 프로젝트의 경우, Vercel을 연동하면 클릭 몇 번만으로 브랜치에 코드를 푸시할 때마다 자동 배포가 이루어집니다.

1. 현재 구조(`c:\ai\KAIB2026`) 전체를 GitHub Repository에 Push 합니다.
2. [Vercel](https://vercel.com/) 에 접속하여 GitHub 계정으로 로그인한 뒤 **"Add New Project"** 버튼을 클릭합니다.
3. 방금 Push한 GitHub Repository를 Import 합니다.
4. Import 시 Framework Preset은 **"Vite"** 로 자동 인식됩니다.
5. **[중요] Root Directory 설정**: 
   - `Build and Output Settings` 아래에 있는 **Root Directory** 설정 창에 펜(Edit) 아이콘을 눌러 `web` 으로 지정합니다.
6. "Deploy" 버튼을 누릅니다. (`npm run build` 가 자동으로 Vercel 서버에서 실행되어 `web/dist` 결과물이 배포됩니다.)

## 방법 2. GitHub Pages 와 GitHub Actions 를 이용한 배포
GitHub 자체 안에서 모두 해결하며 무료로 서빙하고 싶을 때 사용합니다.

1. GitHub 리포지토리 루트 공간에 아래 파일을 생성합니다. (`.github/workflows/deploy.yml`)
```yaml
name: Deploy web to GitHub Pages

on:
  push:
    branches: ["main"]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./web
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: 20
      - name: Install dependencies
        run: npm ci
      - name: Build
        run: npm run build
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./web/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

2. 변경사항을 `main` 브랜치에 Push 합니다.
3. GitHub Repository 의 **Settings > Pages** 메뉴로 이동합니다.
4. **Build and deployment > Source** 옵션을 `GitHub Actions` 로 변경합니다.
5. Push 된 코드가 Actions 에 의해 스스로 `web/` 내에서 빌드되고 자동으로 Pages에 배포됩니다.
