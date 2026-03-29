#!/usr/bin/env python3
"""
JSON → 정적 사이트 생성 스크립트
- app.html : 전체 목록 페이지 (검색/정렬/페이지네이션)
- html/*.html : 개별 상세 페이지

사용법: python generate_html.py merged.json [output_dir]
  output_dir 기본값: 현재 디렉토리 (.)
  결과:
    {output_dir}/app.html
    {output_dir}/html/{code}_{project_name}.html
"""
import json, sys, os, html as h


# ─────────────────────────── 유틸 ───────────────────────────
def fmt(v):
    if v is None: return "-"
    if isinstance(v, (int, float)): return f"{v:,.0f}"
    return str(v)

def row(label, value, full=False):
    cs = ' style="grid-column:1/-1"' if full else ''
    return f'''<div class="info-row"{cs}>
  <div class="label">{h.escape(label)}</div>
  <div class="value">{h.escape(str(value)) if value else "-"}</div>
</div>'''

def safe_filename(code, name):
    code = code.replace("/", "_")
    name = name.replace("/", "_").replace(" ", "_")
    return f"{code}_{name}.html"


# ─────────────────────────── 상세 페이지 ───────────────────────────
def generate_detail(p):
    title = f'{h.escape(p["project_name"])} ({h.escape(p["code"])})'
    b = p.get("budget", {})
    pp = p.get("project_period", {})
    tc = p.get("total_cost", {})

    sub_rows = ""
    for sp in p.get("sub_projects", []):
        sub_rows += f'<tr><td>{h.escape(sp["name"])}</td><td class="r">{fmt(sp.get("budget_2024"))}</td><td class="r">{fmt(sp.get("budget_2025"))}</td><td class="r">{fmt(sp.get("budget_2026"))}</td></tr>\n'

    pm_rows = ""
    for pm in p.get("project_managers", []):
        pm_rows += row("세부사업", pm.get("sub_project"), True)
        pm_rows += row("관리부서", pm.get("managing_dept"))
        pm_rows += row("시행기관", pm.get("implementing_agency"))
        pm_rows += row("담당자", pm.get("manager"))
        pm_rows += row("연락처", pm.get("phone"))

    overview_rows = ""
    for k, v in p.get("overview", {}).items():
        overview_rows += row(k, v, True)

    kw_badges = " ".join(f'<span class="badge">{h.escape(k)}</span>' for k in p.get("keywords", []))
    ai_badges = " ".join(f'<span class="badge">{h.escape(d)}</span>' for d in p.get("ai_domains", []))

    yearly_rows = ""
    for yr, amt in p.get("yearly_budgets", {}).items():
        yearly_rows += row(f"{yr}년", fmt(amt))

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Pretendard','Apple SD Gothic Neo',sans-serif;font-size:13px;color:#1a1a2e;background:#fff;padding:20px;max-width:800px;margin:0 auto}}
.back{{display:inline-block;margin-bottom:12px;color:#2563eb;text-decoration:none;font-size:13px}}
.back:hover{{text-decoration:underline}}
h1{{font-size:18px;margin-bottom:8px;color:#1a1a2e}}
.badges{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px}}
.badge{{background:#f0f0f5;color:#555;padding:2px 8px;border-radius:4px;font-size:11px}}
.section{{border:1px solid #ddd;border-radius:6px;overflow:hidden;margin-bottom:14px}}
.section-title{{background:#1a1a2e;color:#fff;padding:6px 12px;font-size:13px;font-weight:600}}
.grid{{display:grid;grid-template-columns:1fr 1fr}}
.info-row{{display:flex;border-bottom:1px solid #eee}}
.info-row .label{{width:130px;min-width:130px;background:#f7f7fa;padding:6px 10px;font-weight:500;color:#666;border-right:1px solid #eee;flex-shrink:0}}
.info-row .value{{flex:1;padding:6px 10px;white-space:pre-wrap;word-break:break-word}}
table{{width:100%;border-collapse:collapse}}
th,td{{padding:6px 10px;text-align:left;border-bottom:1px solid #eee;font-size:12px}}
th{{background:#f7f7fa;font-weight:500;color:#666}}
.r{{text-align:right}}
.meta{{text-align:right;font-size:11px;color:#999;margin-top:10px}}
@media print{{body{{padding:0;max-width:none}} @page{{size:A4;margin:12mm}} .section{{break-inside:avoid}} .back{{display:none}}}}
@media(max-width:600px){{.grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<a class="back" href="../app.html">← 목록으로</a>
<h1>{title}</h1>
<div class="badges">
  <span class="badge">{h.escape(p.get("department",""))}</span>
  <span class="badge">{h.escape(p.get("status",""))}</span>
  {kw_badges}
</div>

<div class="section">
  <div class="section-title">기본 정보</div>
  <div class="grid">
    {row("사업코드", p.get("code"))}
    {row("사업상태", p.get("status"))}
    {row("부처", p.get("department"))}
    {row("과", p.get("division"))}
    {row("회계유형", p.get("account_type"))}
    {row("지원유형", p.get("support_type"))}
    {row("분야", p.get("field"))}
    {row("부문", p.get("sector"))}
    {row("시행기관", p.get("implementing_agency"), True)}
  </div>
</div>

<div class="section">
  <div class="section-title">프로그램 구조</div>
  <div class="grid">
    {row("프로그램", f'{p["program"]["name"]} ({p["program"]["code"]})', True)}
    {row("단위사업", f'{p["unit_project"]["name"]} ({p["unit_project"]["code"]})', True)}
    {row("세부사업", f'{p["detail_project"]["name"]} ({p["detail_project"]["code"]})', True)}
  </div>
</div>

<div class="section">
  <div class="section-title">사업 기간 및 총사업비</div>
  <div class="grid">
    {row("사업기간", f'{pp.get("start_year","")}~{pp.get("end_year","")} ({pp.get("duration","")})')}
    {row("원문", pp.get("raw"))}
    {row("총사업비", f'{fmt(tc.get("total"))}백만원' if tc.get("total") else "-")}
    {row("국비", f'{fmt(tc.get("government"))}백만원' if tc.get("government") else "-")}
  </div>
</div>

<div class="section">
  <div class="section-title">예산 (백만원)</div>
  <div class="grid">
    {row("'25 결산", fmt(b.get("2025_settlement")))}
    {row("'26 본예산", fmt(b.get("2026_original")))}
    {row("'26 추경", fmt(b.get("2026_supplementary")))}
    {row("'27 요구", fmt(b.get("2027_request")))}
    {row("'27 편성", fmt(b.get("2027_budget")))}
    {row("증감", fmt(b.get("change_amount")))}
  </div>
</div>

{"<div class='section'><div class='section-title'>연도별 예산 (백만원)</div><div class='grid'>" + yearly_rows + "</div></div>" if yearly_rows else ""}

{"<div class='section'><div class='section-title'>하위 사업</div><table><thead><tr><th>사업명</th><th class=r>2024</th><th class=r>2025</th><th class=r>2026</th></tr></thead><tbody>" + sub_rows + "</tbody></table></div>" if sub_rows else ""}

{"<div class='section'><div class='section-title'>담당자 정보</div><div class='grid'>" + pm_rows + "</div></div>" if pm_rows else ""}

{"<div class='section'><div class='section-title'>사업 개요</div><div class='grid'>" + overview_rows + "</div></div>" if overview_rows else ""}

<div class="section">
  <div class="section-title">사업 목적 및 내용</div>
  <div class="grid">
    {row("사업목적", p.get("purpose"), True)}
  </div>
</div>

{"<div class='section'><div class='section-title'>법적 근거</div><div style='padding:8px 10px;white-space:pre-wrap;font-size:12px'>" + h.escape(p.get("legal_basis","")) + "</div></div>" if p.get("legal_basis") else ""}

{"<div class='section'><div class='section-title'>성과 및 기대효과</div><div style='padding:8px 10px;white-space:pre-wrap;font-size:12px'>" + h.escape(p.get("effectiveness","")) + "</div></div>" if p.get("effectiveness") else ""}

{"<div class='section'><div class='section-title'>AI 관련 분야</div><div style='padding:8px 10px;display:flex;gap:6px;flex-wrap:wrap'>" + ai_badges + "</div></div>" if ai_badges else ""}

<div class="meta">원문 페이지: {p.get("page_start","")}~{p.get("page_end","")}p</div>
</body>
</html>'''


# ─────────────────────────── 목록 페이지 ───────────────────────────
def generate_app(projects):
    js_data = json.dumps([{
        "code": p.get("code",""),
        "project_name": p.get("project_name",""),
        "department": p.get("department",""),
        "account_type": p.get("account_type",""),
        "file": "html/" + safe_filename(p["code"], p["project_name"]),
    } for p in projects], ensure_ascii=False)

    total = len(projects)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>정부 R&D 사업 목록</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f6fa;color:#222;line-height:1.6}}
.container{{max-width:1100px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.6rem;margin-bottom:4px}}
.sub{{color:#666;font-size:.9rem;margin-bottom:16px}}
.search-box{{position:relative;margin-bottom:16px}}
.search-box input{{width:100%;padding:10px 12px 10px 36px;border:1px solid #ddd;border-radius:8px;font-size:.95rem;outline:none}}
.search-box input:focus{{border-color:#3b82f6}}
.search-box svg{{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:#999}}
table{{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08)}}
th{{background:#f8f9fb;padding:10px 12px;text-align:left;font-size:.85rem;color:#666;cursor:pointer;user-select:none;white-space:nowrap}}
th:hover{{background:#eef1f6}}
th .arrow{{font-size:.7rem;margin-left:4px}}
td{{padding:10px 12px;border-top:1px solid #f0f0f0;font-size:.9rem}}
tr:hover td{{background:#f8faff}}
a{{color:#2563eb;text-decoration:none;font-weight:500}}
a:hover{{text-decoration:underline}}
.pager{{display:flex;justify-content:center;gap:4px;margin-top:16px;flex-wrap:wrap}}
.pager button{{min-width:34px;height:34px;border:1px solid #ddd;background:#fff;border-radius:6px;cursor:pointer;font-size:.85rem}}
.pager button.active{{background:#2563eb;color:#fff;border-color:#2563eb}}
.pager button:disabled{{opacity:.4;cursor:default}}
.mono{{font-family:"SF Mono",Monaco,Consolas,monospace;font-size:.85rem}}
@media(max-width:640px){{th,td{{padding:8px 6px;font-size:.8rem}} h1{{font-size:1.3rem}}}}
</style>
</head>
<body>
<div class="container">
  <h1>정부 R&amp;D 사업 목록</h1>
  <p class="sub" id="stats">총 {total}개 사업</p>
  <div class="search-box">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
    <input id="search" placeholder="사업코드, 사업명, 부처, 회계 검색..." />
  </div>
  <table>
    <thead><tr>
      <th data-col="code" style="width:110px">사업코드 <span class="arrow">⇅</span></th>
      <th data-col="project_name">사업명 <span class="arrow">⇅</span></th>
      <th data-col="department" style="width:150px">부처 <span class="arrow">⇅</span></th>
      <th data-col="account_type" style="width:100px">회계 <span class="arrow">⇅</span></th>
    </tr></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="pager" id="pager"></div>
</div>
<script>
const DATA={js_data};
const PAGE=20;
let sortKey="code",sortDir=1,page=1,filtered=DATA.slice();
const $=id=>document.getElementById(id);
const tbody=$("tbody"),pager=$("pager"),stats=$("stats"),sinput=$("search");
function render(){{
  const start=(page-1)*PAGE,items=filtered.slice(start,start+PAGE);
  tbody.innerHTML=items.map(p=>`<tr>
    <td class="mono">${{p.code}}</td>
    <td><a href="${{p.file}}">${{p.project_name}}</a></td>
    <td>${{p.department}}</td>
    <td>${{p.account_type}}</td></tr>`).join("")||`<tr><td colspan="4" style="text-align:center;padding:40px;color:#999">검색 결과가 없습니다</td></tr>`;
  const tp=Math.ceil(filtered.length/PAGE)||1;
  let h=`<button ${{page<=1?"disabled":""}} onclick="go(${{page-1}})">‹</button>`;
  for(let i=1;i<=tp;i++)h+=`<button class="${{i===page?"active":""}}" onclick="go(${{i}})">${{i}}</button>`;
  h+=`<button ${{page>=tp?"disabled":""}} onclick="go(${{page+1}})">›</button>`;
  pager.innerHTML=h;
  stats.textContent=`총 ${{DATA.length}}개 사업 | 검색결과 ${{filtered.length}}개`;
}}
function go(p){{page=p;render()}}
function doSearch(){{
  const q=sinput.value.toLowerCase();
  filtered=DATA.filter(p=>p.code.toLowerCase().includes(q)||p.project_name.toLowerCase().includes(q)||p.department.toLowerCase().includes(q)||p.account_type.toLowerCase().includes(q));
  doSort();
}}
function doSort(){{
  filtered.sort((a,b)=>{{const va=a[sortKey]||"",vb=b[sortKey]||"";return va.localeCompare(vb,"ko")*sortDir}});
  page=1;render();
}}
sinput.addEventListener("input",doSearch);
document.querySelectorAll("th[data-col]").forEach(th=>th.addEventListener("click",()=>{{
  const col=th.dataset.col;
  if(sortKey===col)sortDir*=-1;else{{sortKey=col;sortDir=1}}
  doSort();
}}));
doSort();
</script>
</body>
</html>'''


# ─────────────────────────── 메인 ───────────────────────────
def main():
    if len(sys.argv) < 2:
        print("사용법: python generate_html.py <json파일> [출력디렉토리]")
        print("예시:   python generate_html.py merged.json ./docs")
        sys.exit(1)

    json_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    html_dir = os.path.join(out_dir, "html")
    os.makedirs(html_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    projects = data["projects"]

    # 1) app.html 생성
    app_path = os.path.join(out_dir, "app.html")
    with open(app_path, "w", encoding="utf-8") as f:
        f.write(generate_app(projects))
    print(f"✓ app.html ({len(projects)}개 사업 목록)")

    # 2) 개별 상세 HTML 생성
    for p in projects:
        filename = safe_filename(p["code"], p["project_name"])
        filepath = os.path.join(html_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(generate_detail(p))
        print(f"  ✓ html/{filename}")

    print(f"\n완료! 총 {len(projects)+1}개 파일 생성 → {out_dir}/")
    print(f"  app.html         ← 브라우저에서 열기")
    print(f"  html/*.html      ← 상세 페이지 ({len(projects)}개)")

if __name__ == "__main__":
    main()
