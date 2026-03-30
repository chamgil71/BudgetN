# budget_parser.py (v14 - 최종 무결성 및 데이터 전수 추출 결정판)

import re
import json
import os
import yaml
import sys
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

class BudgetParser:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            print(f"❌ 설정 파일({config_path})을 찾을 수 없습니다.")
            sys.exit(1)
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.base_year = self.config.get('years', {}).get('base_year', 2026)
        
        y2, y1, y0 = self.base_year - 2, self.base_year - 1, self.base_year
        self.BUDGET_KEYS = {
            f"{y2}_settlement":    [rf"{y2}.*결산", r'결산'],
            f"{y1}_original":      [rf"{y1}.*본예산(?!.*추경)", r'본예산(?!\(B\))'],
            f"{y1}_supplementary": [r'추경\(A\)', r'추경'],
            f"{y0}_budget":        [r'본예산\(B\)', rf"{y0}.*본예산", r'정부안']
        }

    # [데이터 세척] 숫자 중복(97239723) 및 하이픈 정제
    def _clean_num(self, val: Any) -> float:
        if val is None: return 0.0
        raw = str(val).replace(',', '').split('(')[0].strip()
        if len(raw) >= 4 and len(raw) % 2 == 0:
            half = len(raw) // 2
            if raw[:half] == raw[half:]: raw = raw[:half]
        num = re.sub(r'[^\d.-]', '', raw).rstrip('-')
        if not num or num in ['-', '.']: return 0.0
        try: return float(num)
        except: return 0.0

    # 1. 텍스트 블록 추출 (대제목 기준 풀스캔)
    def _extract_text_block(self, text: str, keywords: List[str]) -> Optional[str]:
        lines = text.split('\n')
        content, capturing = [], False
        for line in lines:
            clean = line.replace(' ', '')
            if not capturing:
                if any(kw in clean for kw in keywords) and len(clean) < 30: capturing = True
            else:
                if (line.strip().startswith('□') or bool(re.match(r'^\s*\d+\.\s', line))) and len(content) > 0: break
                content.append(line)
        return "\n".join(content).strip() if content else None

    # 2. 본문 내 기간, 사업비, 보조율 추출 (누락되었던 함수)
    def _extract_period_cost_rates(self, text: str) -> Dict[str, Any]:
        res = {
            "project_period": {"start_year": None, "end_year": None, "duration": None, "raw": None},
            "total_cost": {"total": None, "government": None, "raw": None},
            "subsidy_rate": None, "loan_rate": None
        }
        p_match = re.search(r'사업기간\s*[:|：]\s*([^\n]+)', text)
        if p_match:
            raw_p = p_match.group(1).strip()
            res["project_period"]["raw"] = raw_p
            years = re.findall(r'(20\d{2})', raw_p)
            if len(years) >= 2:
                res["project_period"]["start_year"], res["project_period"]["end_year"] = int(years[0]), int(years[-1])
            elif len(years) == 1:
                res["project_period"]["start_year"] = int(years[0])
                if '계속' in raw_p: res["project_period"]["end_year"] = 9999

        cost_match = re.search(r'총사업비\s*[:|：]\s*([^\n]+)', text)
        if cost_match:
            raw_c = cost_match.group(1).strip()
            res["total_cost"]["raw"] = raw_c
            nums = re.findall(r'([\d,]+)(?:백만원|억원)', raw_c.replace(' ', ''))
            if nums: res["total_cost"]["total"] = self._clean_num(nums[0])
            gov_m = re.search(r'국비\s*([\d,]+)', raw_c)
            if gov_m: res["total_cost"]["government"] = self._clean_num(gov_m.group(1))

        sub_m = re.search(r'(?:국고)?보조율\s*[:|：]\s*([^\n]+)', text)
        if sub_m: res["subsidy_rate"] = sub_m.group(1).strip()
        loan_m = re.search(r'융자율\s*[:|：]\s*([^\n]+)', text)
        if loan_m: res["loan_rate"] = loan_m.group(1).strip()
        return res

    # 3. 담당자 및 시행주체 병합 추출
    def _extract_managers(self, tables: List[Any], p_name: str) -> List[Dict]:
        mgr = {"sub_project": p_name.replace('\n', ' '), "managing_dept": [], "implementing_agency": [], "manager": None, "phone": None}
        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            t_str = "".join(str(c) for r in rows for c in r if c).replace(" ", "")
            if any(kw in t_str for kw in ['추진주체', '사업시행', '소관부처']):
                for r in rows:
                    r_str = "".join(str(c) for c in r if c).replace(" ", "")
                    if any(k in r_str for k in ['과기정통부', '혁신본부', '소관부처']):
                        m = re.search(r'([가-힣]+(?:부|국|과|본부))', r_str)
                        if m and m.group(1) not in mgr["managing_dept"]: mgr["managing_dept"].append(m.group(1))
                    if any(k in r_str for k in ['재단', '평가원', '진흥원', 'KISTEP', '시행기관']):
                        m = re.search(r'([가-힣]+(?:재단|원|소|회))', r_str)
                        if m and m.group(1) not in mgr["implementing_agency"]: mgr["implementing_agency"].append(m.group(1))
        f_dept = ", ".join(mgr["managing_dept"]) if mgr["managing_dept"] else None
        f_agency = ", ".join(mgr["implementing_agency"]) if mgr["implementing_agency"] else None
        return [{"sub_project": mgr["sub_project"], "managing_dept": f_dept, "implementing_agency": f_agency, "manager": None, "phone": None}] if f_dept or f_agency else []

    # 4. 내역사업 개별 추출
    def _extract_sub_projects(self, tables: List[Any]) -> List[Dict]:
        subs = []
        y2, y1, y0 = str(self.base_year-2), str(self.base_year-1), str(self.base_year)
        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            if not rows: continue
            header = [str(c).replace(' ', '').replace('\n', '') for c in rows[0]]
            if any(kw in "".join(header) for kw in ['내역사업', '항목', '분류']):
                n_idx = next((i for i, h in enumerate(header) if any(k in h for k in ['내역사업', '항목'])), 0)
                y_idx = [next((i for i, h in enumerate(header) if y in h), -1) for y in [y2, y1, y0]]
                for r in rows[1:]:
                    name = str(r[n_idx]).strip().replace('\n', ' ')
                    if not name or any(k in name for k in ['합계', '계', '총계']): continue
                    subs.append({"name": name, f"budget_{y2}": self._clean_num(r[y_idx[0]]), f"budget_{y1}": self._clean_num(r[y_idx[1]]), f"budget_{y0}": self._clean_num(r[y_idx[2]])})
                if subs: break
        return subs

    # 5. 메인 예산표 추출
    def _extract_budget(self, tables: List[Any]) -> Dict[str, float]:
        budget = {k: None for k in self.BUDGET_KEYS}
        target = None
        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            h_str = "".join(str(c) for r in rows[:3] for c in r if c).replace(" ", "")
            if '결산' in h_str and ('본예산' in h_str or '요구안' in h_str): target = rows; break
        if not target: return budget | {"change_amount": 0.0, "change_rate": 0.0}
        h_row = [str(target[0][i] or "") + str(target[1][i] or "") for i in range(len(target[0]))]
        d_row = next((r for r in target if any(kw in "".join(map(str, r)) for kw in ['합계', '계'])), 
                     max(target[1:], key=lambda r: sum(1 for c in r if re.search(r'\d', str(c))), default=None))
        if d_row:
            for k, patterns in self.BUDGET_KEYS.items():
                for p in patterns:
                    idx = next((i for i, h in enumerate(h_row) if re.search(p, h)), -1)
                    if idx != -1 and idx < len(d_row): budget[k] = self._clean_num(d_row[idx]); break
        v1, v2 = float(budget.get(f"{self.base_year-1}_original") or 0.0), float(budget.get(f"{self.base_year}_budget") or 0.0)
        budget["change_amount"] = round(v2 - v1, 2)
        budget["change_rate"] = round(((v2 - v1) / v1 * 100), 2) if v1 != 0.0 else 0.0
        return budget

    def _extract_yearly_budgets_list(self, tables: List[Any]) -> List[Dict]:
        res = []
        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            if not rows: continue
            header = [str(c) for c in rows[0]]
            y_cols = {i: re.search(r'(20\d{2})', h).group(1) for i, h in enumerate(header) if re.search(r'(20\d{2})', h)}
            if y_cols:
                d_row = next((r for r in rows if any(k in str(r[0]) for k in ['합계', '계'])), None)
                if d_row:
                    for i, y in y_cols.items(): res.append({"year": int(y), "amount": self._clean_num(d_row[i])})
                    return res
        return res

    def parse(self, input_path: str, output_path: str):
        with open(input_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
        chunks = list(raw_data["projects"].values()) if "projects" in raw_data else []
        results = []
        for chunk in chunks:
            text, tables = chunk.get('text', ''), chunk.get('tables', [])
            
            # 헤더 정보
            match = re.search(r'사\s*업\s*명\s*(.*?)(?=\n|$)', text)
            if not match: continue
            line = match.group(1).strip()
            code_m = re.search(r'(\d{4}-\d{3,4})', line)
            code = code_m.group(1) if code_m else "0000-000"
            p_name = line.replace(f"({code})", "").replace(code, "").strip()
            p_name = re.sub(r'^\(\d+\)\s*', '', p_name)

            p_rates = self._extract_period_cost_rates(text) # <--- 이제 에러 안 납니다!
            
            item = {
                "project_name": p_name, "code": code,
                "project_managers": self._extract_managers(tables, p_name),
                "budget": self._extract_budget(tables),
                "sub_projects": self._extract_sub_projects(tables),
                "purpose": self._extract_text_block(text, ["사업목적", "목적"]),
                "description": self._extract_text_block(text, ["사업내용", "내용"]),
                "legal_basis": self._extract_text_block(text, ["근거", "지원근거"]),
                "effectiveness": self._extract_text_block(text, ["기대효과"]),
                "yearly_budgets": self._extract_yearly_budgets_list(tables),
                "subsidy_rate": p_rates["subsidy_rate"],
                "project_period": p_rates["project_period"],
                "total_cost": p_rates["total_cost"]
            }
            results.append(item)
        
        out_file = Path(output_path) / "merged.json" if not Path(output_path).suffix else Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump({"projects": results}, f, ensure_ascii=False, indent=2)
        print(f"✅ 파싱 완료 ({len(results)}건): {out_file.name}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True); p.add_argument("-o", "--output", required=True); p.add_argument("-c", "--config", default="config/config.yaml")
    args = p.parse_args(); BudgetParser(args.config).parse(args.input, args.output)