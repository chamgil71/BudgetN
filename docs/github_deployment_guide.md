# KAIB2026 Dashboard GitHub 배포 가이드

프로젝트가 백엔드/데이터 스크립트와 프론트엔드(`web/`) 뷰로 완벽히 분리되었습니다. 
해당 폴더 구조를 기반으로 GitHub Pages 또는 Vercel을 통해 매우 쉽게 무료 호스팅/배포가 가능합니다.

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
