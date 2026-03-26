import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
COMMON_JS = ROOT / "web" / "js" / "common.js"
INDEX_HTML = ROOT / "web" / "index.html"
STYLE_CSS = ROOT / "web" / "css" / "style.css"

def fix_common():
    with open(COMMON_JS, "r", encoding="utf-8") as file:
        content = file.read()
    
    # 먼저 기본 이름 치환
    content = content.replace("getBudget2026", "getBudgetBase")
    content = content.replace("budget_2026", "budget_base")
    content = content.replace("getBudget2025", "getBudgetPrev")
    content = content.replace("budget_2025", "budget_prev")

    # window.getBudgetBase = ... 라인 재정의
    old_base_func = "window.getBudgetBase = p => p ? (p.budget?.budget_base ?? p.budget?.['2026_budget'] ?? p.budget_base ?? 0) : 0;"
    new_base_func = """window.getBudgetBase = p => {
    if (!p) return 0;
    const by = window.BASE_YEAR || 2026;
    return p.budget?.[`budget_${by}`] ?? p.budget?.[`${by}_budget`] ?? p[`budget_${by}`] ?? p.budget_base ?? 0;
};"""
    content = content.replace(old_base_func, new_base_func)

    old_prev_func = "window.getBudgetPrev = p => p ? (p.budget?.budget_prev ?? p.budget?.['2025_original'] ?? p.budget_prev ?? 0) : 0;"
    new_prev_func = """window.getBudgetPrev = p => {
    if (!p) return 0;
    const py = (window.BASE_YEAR || 2026) - 1;
    return p.budget?.[`budget_${py}`] ?? p.budget?.[`${py}_original`] ?? p[`budget_${py}`] ?? p.budget_prev ?? 0;
};"""
    content = content.replace(old_prev_func, new_prev_func)

    with open(COMMON_JS, "w", encoding="utf-8") as file:
        file.write(content)
    print("Fixed common.js")

def add_pure_db_tab_colors():
    # 1. index.html에서 대상 탭 버튼에 pure-db 캘래스 추가
    pure_tabs = ["'overview'", "'dept'", "'field'", "'list'", "'compare'", "'sim'", "'tech'"]
    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    
    for tab in pure_tabs:
        # 매칭: onclick="switchTab('overview')"
        # 변경: class에 pure-db 추가. 
        # html에 <button class="tab-btn" onclick="switchTab('dept')"> 가 있음
        # active가 붙은 경우: <button class="tab-btn active" onclick="switchTab('overview')">
        
        pattern = r'(<button class="tab-btn[^"]*")\s+onclick="switchTab\(' + tab + r'\)"'
        replacement = r'\1 data-type="pure" onclick="switchTab(' + tab + ')"'
        html = re.sub(pattern, replacement, html)
        
    with open(INDEX_HTML, "w", encoding="utf-8") as f:
        f.write(html)
        
    # 2. css 추가
    css_rule = "\n/* DB 의존 탭 강조 스타일 추가 */\n.nav-tabs .tab-btn[data-type=\"pure\"].active {\n    color: #1d4ed8;\n    border-bottom: 2px solid #1d4ed8;\n    background: rgba(29, 78, 216, 0.05);\n}\n"
    with open(STYLE_CSS, "a", encoding="utf-8") as f:
        f.write(css_rule)
    print("HTML and CSS updated with data-type='pure' and colors.")

if __name__ == "__main__":
    fix_common()
    add_pure_db_tab_colors()
