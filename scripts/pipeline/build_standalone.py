from pathlib import Path
import sys, re
import sys
from pathlib import Path

# 1. 시스템 길 터주기 (가장 먼저 실행되어야 함)
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# 2. 이제 파이썬이 최상위 폴더를 아니까, 마음 편하게 중앙 통제소(config)를 부릅니다.
from config.path_config import LOGS_DIR, INPUT_DIR, OUTPUT_DIR, RAW_DIR, MERGED_JSON_PATH, WEB_DIR
from scripts.pipeline._years import get_years


Y = get_years()

def build_standalone():
    index_path = WEB_DIR / "index.html"
    if not index_path.exists():
        print(f"❌ {index_path.name} 파일이 없습니다.")
        return

    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # WEB_DIR 정의
    web_dir = WEB_DIR
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
        
        js_path = web_dir / src
        if js_path.exists():
            with open(js_path, "r", encoding="utf-8") as js_f:
                return f"<script>\n/* inline: {src} */\n{js_f.read()}\n</script>"
        return match.group(0)

    html = re.sub(r'<script[^>]*src="([^"]+\.js)"[^>]*>\s*</script>', replace_js, html, flags=re.IGNORECASE)

    # 결과물 저장
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"KAIB{Y['base_year']}_Standalone.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f" ✅ 성공적으로 단일 HTML을 빌드했습니다.")
    print(f" 📂 저장 위치: {out_file.absolute()}")
    print(f" 🗜 파일 크기: {out_file.stat().st_size / (1024*1024):.2f} MB")

if __name__ == "__main__":
    build_standalone()
