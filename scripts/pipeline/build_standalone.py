import os, re
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
WEB_DIR = ROOT / "web"
OUT_DIR = ROOT / "output"

def build_standalone():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        print(f"❌ {index_path.name} 파일이 없습니다.")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 인라인 CSS 변환 (로컬 파일만)
    # <link href="css/style.css" rel="stylesheet"> 등 매칭
    def replace_css(match):
        href = match.group(1)
        if href.startswith("http") or href.startswith("//"): return match.group(0)
        
        css_path = WEB_DIR / href
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as css_f:
                return f"<style>\n/* inline: {href} */\n{css_f.read()}\n</style>"
        return match.group(0)
    
    html = re.sub(r'<link[^>]*href="([^"]+\.css)"[^>]*rel="stylesheet"[^>]*>', replace_css, html, flags=re.IGNORECASE)
    # 순서가 다른 경우 지원: <link rel="stylesheet" href="...">
    html = re.sub(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+\.css)"[^>]*>', replace_css, html, flags=re.IGNORECASE)

    # 2. 인라인 JS 변환 (로컬 파일만)
    # <script src="js/app.js"></script> 매칭
    def replace_js(match):
        src = match.group(1)
        if src.startswith("http") or src.startswith("//"): return match.group(0)
        
        js_path = WEB_DIR / src
        if js_path.exists():
            with open(js_path, "r", encoding="utf-8") as js_f:
                return f"<script>\n/* inline: {src} */\n{js_f.read()}\n</script>"
        return match.group(0)

    html = re.sub(r'<script[^>]*src="([^"]+\.js)"[^>]*>\s*</script>', replace_js, html, flags=re.IGNORECASE)

    # 결과물 저장
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUT_DIR / "KAIB2026_Standalone.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f" ✅ 성공적으로 단일 HTML을 빌드했습니다.")
    print(f" 📂 저장 위치: {out_file.absolute()}")
    print(f" 🗜 파일 크기: {out_file.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    build_standalone()
