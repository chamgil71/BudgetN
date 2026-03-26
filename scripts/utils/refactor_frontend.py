import os, re
from pathlib import Path

ROOT = Path(__file__).parent.parent
WEB_JS = ROOT / "web" / "js"
HTML_FILE = ROOT / "web" / "index.html"

def refactor_js():
    for root, dirs, files in os.walk(WEB_JS):
        for f in files:
            if not f.endswith(".js"): continue
            if f == "common.js": continue # Already manually fixed
            path = Path(root) / f
            with open(path, "r", encoding="utf-8") as file:
                content = file.read()
            
            orig = content
            content = content.replace("getBudget2026", "getBudgetBase")
            content = content.replace("budget_2026", "budget_base")
            content = content.replace("getBudget2025", "getBudgetPrev")
            content = content.replace("budget_2025", "budget_prev")
            
            # 따옴표로 감싸진 경우
            content = content.replace("'2026 예산'", "`${window.BASE_YEAR} 예산`")
            content = content.replace('"2026 예산"', "`${window.BASE_YEAR} 예산`")
            content = content.replace("'2026년'", "`${window.BASE_YEAR}년`")
            content = content.replace('"2026년"', "`${window.BASE_YEAR}년`")
            
            # 백틱 내부인 경우 (따옴표 변환이 안 먹힌 곳)
            content = content.replace("2026 예산", "${window.BASE_YEAR} 예산")
            content = content.replace("2026년", "${window.BASE_YEAR}년")
            
            if orig != content:
                with open(path, "w", encoding="utf-8") as file:
                    file.write(content)
                print(f"Refactored JS: {path.relative_to(ROOT)}")

def refactor_html():
    with open(HTML_FILE, "r", encoding="utf-8") as file:
        content = file.read()
    
    orig = content
    content = content.replace("2026 AI 재정사업 분석 플랫폼", '<span class="dyn-year">2026</span> AI 재정사업 분석 플랫폼')
    content = content.replace('<a href="#" class="header-link">문서</a>', '<a href="docs/guide.html" class="header-link" target="_blank">문서</a>')

    if orig != content:
        with open(HTML_FILE, "w", encoding="utf-8") as file:
            file.write(content)
        print(f"Refactored HTML: {HTML_FILE.name}")

if __name__ == "__main__":
    refactor_js()
    refactor_html()
    print("Done frontend refactoring.")
