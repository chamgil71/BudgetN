#!/usr/bin/env python3
"""
JSON → 개별 HTML 생성 스크립트
사용법: python generate_html.py merged.json [output_dir]
"""
import json, sys, os, html as h

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

def generate_html(p):
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
@media print{{
  body{{padding:0;max-width:none}}
  @page{{size:A4;margin:12mm}}
  .section{{break-inside:avoid}}
}}
@media(max-width:600px){{
  .grid{{grid-template-columns:1fr}}
}}
</style>
</head>
<body>
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

def main():
    if len(sys.argv) < 2:
        print("사용법: python generate_html.py merged.json [output_dir]")
        sys.exit(1)

    json_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "./html"
    os.makedirs(out_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for p in data["projects"]:
        code = p["code"].replace("/", "_")
        name = p["project_name"].replace("/", "_").replace(" ", "_")
        filename = f"{code}_{name}.html"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(generate_html(p))
        print(f"✓ {filename}")

    print(f"\n총 {len(data['projects'])}개 HTML 생성 → {out_dir}/")

if __name__ == "__main__":
    main()
