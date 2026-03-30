# budget_parser.py (v12 - 본문 텍스트 증발 버그 완벽 수정본)

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
        
        y_minus_2 = self.base_year - 2
        y_minus_1 = self.base_year - 1
        y_current = self.base_year
        
        self.BUDGET_KEYS = {
            f"{y_minus_2}_settlement":    [rf"{y_minus_2}.*결산", r'결산'],
            f"{y_minus_1}_original":      [rf"{y_minus_1}.*본예산(?!.*추경)", r'본예산(?!\(B\))'],
            f"{y_minus_1}_supplementary": [r'추경\(A\)', r'추경'],
            f"{y_current}_request":       [r'요구안', rf"{y_current}.*요구"],
            f"{y_current}_budget":        [r'본예산\(B\)', rf"{y_current}.*본예산", r'정부안']
        }

    # ==========================================
    # 1. 텍스트 추출 모듈 (대대적 수정)
    # ==========================================
    def _parse_header(self, text: str) -> Dict[str, Any]:
        res: Dict[str, Any] = {"name": "", "code": "0000-000", "page_start": 0}
        match = re.search(r'사\s*업\s*명\s*(.*?)(?=\n|$)', text)
        if match:
            line = match.group(1).strip()
            p_match = re.search(r'-\s*(\d+)\s*-', line)
            if p_match:
                res["page_start"] = int(p_match.group(1))
                line = line[:p_match.start()].strip()
            
            c_match = re.search(r'(\d{4}-\d{3,4})', line)
            if c_match:
                res["code"] = c_match.group(1)
                res["name"] = line.replace(f"({res['code']})", "").replace(res['code'], "").strip()
                res["name"] = re.sub(r'^\(\d+\)\s*', '', res["name"])
        return res

    def _extract_main_agency(self, text: str) -> Optional[str]:
        match = re.search(r'(?:사업시행주체|시행주체|시행기관)\s*[:|：]\s*([^\n]+)', text)
        return match.group(1).strip() if match else None

    def _extract_text_block(self, text: str, keywords: List[str]) -> Optional[str]:
        """[핵심 수정] 'ㅇ'에서 멈추지 않고, 다음 대제목(□)이 나올 때까지 본문을 꽉꽉 채워 긁어옴"""
        lines = text.split('\n')
        content = []
        capturing = False
        
        for line in lines:
            clean_line = line.replace(' ', '')
            
            if not capturing:
                # 시작 조건: 제시된 키워드(예: 사업내용)가 포함되어 있고, 제목처럼 짧은 줄일 때
                if any(kw in clean_line for kw in keywords) and len(clean_line) < 30:
                    capturing = True
            else:
                # 종료 조건: 다음 대분류 목차(□ 또는 1., 2. 등)를 만나면 스톱!
                # 절대 'ㅇ' 이나 '-' 기호에서 멈추지 않음.
                is_major_header = line.strip().startswith('□') or bool(re.match(r'^\s*\d+\.\s', line))
                
                # 다른 주요 목차 단어가 튀어나와도 스톱
                other_keywords = ['사업목적', '사업내용', '지원근거', '기대효과', '예산현황', '산출근거', '추진계획']
                is_other_header = any(okw in clean_line for okw in other_keywords if okw not in "".join(keywords)) and len(clean_line) < 20
                
                if (is_major_header or is_other_header) and len(content) > 0:
                    break
                    
                content.append(line)
                
        res = "\n".join(content).strip()
        return res if res else None

    def _extract_overview(self, text: str) -> Dict[str, Optional[str]]:
        overview = {"사업규모": None, "사업수혜자": None, "사업시행방법": None}
        lines = text.split('\n')
        for i, line in enumerate(lines):
            clean_line = line.replace(' ', '')
            if '사업규모' in clean_line or '규모:' in clean_line or '규모：' in clean_line:
                val = line.split(':')[-1].split('：')[-1].strip()
                if len(val) > 2: overview["사업규모"] = val
            elif '수혜자' in clean_line or '지원대상' in clean_line:
                val = line.split(':')[-1].split('：')[-1].strip()
                if len(val) > 2: overview["사업수혜자"] = val
            elif '시행방법' in clean_line or '추진방법' in clean_line or '지원형태' in clean_line:
                val = line.split(':')[-1].split('：')[-1].strip()
                if len(val) > 2: overview["사업시행방법"] = val
        return overview

    def _extract_period_cost_rates(self, text: str) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "project_period": {"start_year": None, "end_year": None, "duration": None, "raw": None},
            "total_cost": {"total": None, "government": None, "raw": None},
            "subsidy_rate": None,
            "loan_rate": None
        }
        period_match = re.search(r'사업기간\s*[:|：]\s*([^\n]+)', text)
        if period_match:
            raw_period = period_match.group(1).strip()
            res["project_period"]["raw"] = raw_period
            years = re.findall(r'(20\d{2})', raw_period)
            if len(years) >= 2:
                res["project_period"]["start_year"], res["project_period"]["end_year"] = int(years[0]), int(years[-1])
            elif len(years) == 1:
                res["project_period"]["start_year"] = int(years[0])
                if '계속' in raw_period: res["project_period"]["end_year"] = 9999

        cost_match = re.search(r'총사업비\s*[:|：]\s*([^\n]+)', text)
        if cost_match:
            raw_cost = cost_match.group(1).strip()
            res["total_cost"]["raw"] = raw_cost
            nums = re.findall(r'([\d,]+)(?:백만원|억원)', raw_cost.replace(' ', ''))
            if nums: res["total_cost"]["total"] = float(nums[0].replace(',', ''))
            gov_match = re.search(r'국비\s*([\d,]+)', raw_cost)
            if gov_match: res["total_cost"]["government"] = float(gov_match.group(1).replace(',', ''))

        sub_match = re.search(r'(?:국고)?보조율\s*[:|：]\s*([^\n]+)', text)
        if sub_match: res["subsidy_rate"] = sub_match.group(1).strip()

        loan_match = re.search(r'융자율\s*[:|：]\s*([^\n]+)', text)
        if loan_match: res["loan_rate"] = loan_match.group(1).strip()

        return res

    # ==========================================
    # 2. 표(Table) 추출 모듈 (이전 완벽 버전 유지)
    # ==========================================
    def _extract_top_summary_tables(self, tables: List[Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "account_type": None, "department": None, "division": None, 
            "field": None, "sector": None,
            "program": {"code": None, "name": None},
            "unit_project": {"code": None, "name": None},
            "detail_project": {"code": None, "name": None}
        }
        def find_col(header, keyword):
            return next((i for i, h in enumerate(header) if keyword in str(h).replace(' ', '')), -1)

        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue
            header_row = [str(c).replace('\n', '').replace(' ', '') for c in table[0]]
            
            idx_dept = find_col(header_row, "소관")
            idx_div = find_col(header_row, "실국(기관)")
            if idx_dept != -1 and idx_div != -1:
                idx_map = {"회계": "account_type", "소관": "department", "실국(기관)": "division", "분야": "field", "부문": "sector"}
                for row in table[1:]:
                    row_str = "".join(str(c) for c in row if c)
                    if any(kw in row_str for kw in ["회계", "기금", "부", "청"]):
                        for k, target in idx_map.items():
                            c_idx = find_col(header_row, k)
                            if c_idx != -1 and len(row) > c_idx:
                                val = str(row[c_idx]).strip().replace('\n', ' ')
                                if val and val not in ["코드", "명칭"]: result[target] = val
                        break

            elif find_col(header_row, "프로그램") != -1 and find_col(header_row, "단위사업") != -1:
                idx_p, idx_u, idx_d = find_col(header_row, "프로그램"), find_col(header_row, "단위사업"), find_col(header_row, "세부사업")
                for row in table[1:]:
                    row_type = str(row[0]).replace(' ', '')
                    if "코드" in row_type:
                        result["program"]["code"] = str(row[idx_p]).strip()
                        result["unit_project"]["code"] = str(row[idx_u]).strip()
                        if idx_d != -1: result["detail_project"]["code"] = str(row[idx_d]).strip()
                    elif "명칭" in row_type:
                        result["program"]["name"] = str(row[idx_p]).strip().replace('\n', ' ')
                        result["unit_project"]["name"] = str(row[idx_u]).strip().replace('\n', ' ')
                        if idx_d != -1: result["detail_project"]["name"] = str(row[idx_d]).strip().replace('\n', ' ')
        return result

    def _extract_status_and_support(self, tables: List[Any]) -> Dict[str, Any]:
        result: Dict[str, Any] = {"status": "계속", "support_type": None, "subsidy_rate": None, "loan_rate": None}
        check_marks = ['ㅇ', 'O', 'o', '○', '0', '◎', 'v', 'V']

        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue

            for row_idx, row in enumerate(table):
                row_str = "".join(str(c).replace(" ", "") for c in row)
                
                if "신규" in row_str and "계속" in row_str:
                    if row_idx + 1 < len(table):
                        data_row = table[row_idx + 1]
                        for kw in ["신규", "계속", "완료"]:
                            idx = next((i for i, c in enumerate(row) if kw in str(c).replace(" ", "")), -1)
                            if idx != -1 and idx < len(data_row) and any(m in str(data_row[idx]) for m in check_marks):
                                result["status"] = kw

                if "직접" in row_str and ("보조" in row_str or "출연" in row_str):
                    if row_idx + 1 < len(table):
                        data_row = table[row_idx + 1]
                        types = []
                        for kw in ["직접", "출자", "출연", "보조", "융자"]:
                            idx = next((i for i, c in enumerate(row) if kw in str(c).replace(" ", "")), -1)
                            if idx != -1 and idx < len(data_row) and any(m in str(data_row[idx]) for m in check_marks):
                                types.append(kw)
                        if types: result["support_type"] = ", ".join(types)

                        idx_sub = next((i for i, c in enumerate(row) if '보조율' in str(c).replace(" ", "")), -1)
                        idx_loan = next((i for i, c in enumerate(row) if '융자율' in str(c).replace(" ", "")), -1)
                        
                        if idx_sub != -1 and idx_sub < len(data_row):
                            val = re.sub(r'[^\d.-]', '', str(data_row[idx_sub]).split('(')[0])
                            if val and val not in ['-', '.']: result["subsidy_rate"] = val
                            
                        if idx_loan != -1 and idx_loan < len(data_row):
                            val = re.sub(r'[^\d.-]', '', str(data_row[idx_loan]).split('(')[0])
                            if val and val not in ['-', '.']: result["loan_rate"] = val
        return result

    def _extract_budget(self, tables: List[Any]) -> Dict[str, float]:
        budget: Dict[str, Any] = {k: None for k in self.BUDGET_KEYS}
        target_table = None
        
        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue
            
            header_str = "".join(str(c) for h in table[:3] for c in h if h).replace(" ", "")
            if '결산' in header_str and ('본예산' in header_str or '요구안' in header_str or '정부안' in header_str):
                target_table = table
                break
                
        if not target_table: 
            budget["change_amount"] = 0.0
            budget["change_rate"] = 0.0
            return budget

        header_row = []
        for col_idx in range(len(target_table[0])):
            h1 = str(target_table[0][col_idx] if col_idx < len(target_table[0]) else "").replace(' ', '').replace('\n', '')
            h2 = str(target_table[1][col_idx] if len(target_table) > 1 and col_idx < len(target_table[1]) else "").replace(' ', '').replace('\n', '')
            header_row.append(h1 + h2)

        data_row = next((row for row in target_table if any(kw in "".join(map(str, row)) for kw in ['합계', '계'])), None)
        if not data_row and len(target_table) > 1:
            data_rows = target_table[2:] if len(target_table) > 2 else target_table[1:]
            data_row = max(data_rows, key=lambda r: sum(1 for c in r if re.search(r'\d', str(c))), default=None)

        if data_row:
            for key, patterns in self.BUDGET_KEYS.items():
                for p in patterns:
                    matched_idx = next((i for i, h in enumerate(header_row) if re.search(p, h)), -1)
                    if matched_idx != -1 and matched_idx < len(data_row):
                        try:
                            val_str = re.sub(r'[^\d.-]', '', str(data_row[matched_idx]).split('(')[0])
                            if val_str and val_str not in ['-', '.']:
                                budget[key] = float(val_str)
                                break
                        except ValueError: pass

        prev_key = f"{self.base_year - 1}_original"
        curr_key = f"{self.base_year}_budget"
        v1 = float(budget.get(prev_key) or 0.0)
        v2 = float(budget.get(curr_key) or 0.0)
        budget["change_amount"] = round(v2 - v1, 2)
        budget["change_rate"] = round(((v2 - v1) / v1 * 100), 2) if v1 != 0.0 else 0.0

        return budget

    def _extract_yearly_budgets(self, tables: List[Any]) -> List[Dict[str, Any]]:
        yearly = []
        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue
            
            header = [str(c).replace(' ', '').replace('\n', '') for c in table[0]]
            year_cols = {}
            for i, h in enumerate(header):
                y_match = re.search(r'(20[1-3]\d)', h)
                if y_match: year_cols[i] = y_match.group(1)
            
            if year_cols:
                for row in table[1:]:
                    row_title = str(row[0]).replace(' ', '')
                    if '합계' in row_title or row_title == '계':
                        for col_idx, year in year_cols.items():
                            if col_idx < len(row):
                                raw_val = str(row[col_idx]).split('(')[0]
                                val_str = re.sub(r'[^\d.-]', '', raw_val).rstrip('-')
                                if not val_str or val_str in ['-', '.']:
                                    yearly.append({"year": int(year), "amount": 0.0})
                                else:
                                    try: yearly.append({"year": int(year), "amount": float(val_str)})
                                    except ValueError: yearly.append({"year": int(year), "amount": 0.0})
                        return yearly
        return yearly

    def _extract_sub_projects(self, tables: List[Any]) -> List[Dict]:
        sub_projects = []
        y_minus_2, y_minus_1, y_current = str(self.base_year - 2), str(self.base_year - 1), str(self.base_year)
        
        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue
            
            header = [str(c).replace(' ', '').replace('\n', '') for c in table[0]]
            if any(kw in h for h in header for kw in ['기능별', '내역사업', '세부사업', '사업명']):
                name_idx = next((i for i, h in enumerate(header) if '분류' in h or '사업' in h or '항목' in h), 0)
                y2_idx = next((i for i, h in enumerate(header) if y_minus_2 in h), -1)
                y1_idx = next((i for i, h in enumerate(header) if y_minus_1 in h), -1)
                y0_idx = next((i for i, h in enumerate(header) if y_current in h), -1)
                
                if y2_idx != -1 or y1_idx != -1 or y0_idx != -1:
                    for row in table[1:]:
                        if not any(row): continue
                        sub_name = str(row[name_idx]).strip().replace('\n', ' ')
                        if not sub_name or '합계' in sub_name or '총계' in sub_name: continue
                        
                        def get_val(idx):
                            if idx == -1 or idx >= len(row): return None
                            num = re.sub(r'[^\d.-]', '', str(row[idx]).split('(')[0])
                            if not num or num == '-' or num == '.': return 0.0
                            try: return float(num)
                            except ValueError: return 0.0

                        sub_projects.append({
                            "name": sub_name,
                            f"budget_{y_minus_2}": get_val(y2_idx),
                            f"budget_{y_minus_1}": get_val(y1_idx),
                            f"budget_{y_current}": get_val(y0_idx)
                        })
                    break
        return sub_projects

    def _extract_managers(self, tables: List[Any]) -> List[Dict]:
        managers = []
        for table in tables:
            if isinstance(table, dict) and 'rows' in table: table = table['rows']
            if not table or len(table) < 2: continue
            
            table_str = "".join(str(c) for row in table for c in row if c).replace(" ", "")
            
            if '담당자' in table_str or '전화번호' in table_str:
                header_idx = next((i for i, r in enumerate(table) if any('담당자' in str(c) for c in r)), -1)
                if header_idx != -1:
                    header = [str(c).replace(' ', '').replace('\n', '') for c in table[header_idx]]
                    sub_idx = next((i for i, h in enumerate(header) if '내역사업' in h), -1)
                    dept_idx = next((i for i, h in enumerate(header) if '소관' in h or '부서' in h), -1)
                    agency_idx = next((i for i, h in enumerate(header) if '시행기관' in h), -1)
                    man_idx = next((i for i, h in enumerate(header) if '담당자' in h or '성명' in h), -1)
                    phone_idx = next((i for i, h in enumerate(header) if '전화' in h or '연락처' in h), -1)
                    
                    for row in table[header_idx+1:]:
                        if not any(row): continue
                        managers.append({
                            "sub_project": str(row[sub_idx]).strip() if sub_idx != -1 and sub_idx < len(row) else None,
                            "managing_dept": str(row[dept_idx]).strip() if dept_idx != -1 and dept_idx < len(row) else None,
                            "implementing_agency": str(row[agency_idx]).strip() if agency_idx != -1 and agency_idx < len(row) else None,
                            "manager": str(row[man_idx]).strip() if man_idx != -1 and man_idx < len(row) else None,
                            "phone": str(row[phone_idx]).strip() if phone_idx != -1 and phone_idx < len(row) else None
                        })
                    break
                    
            elif '사업시행주체' in table_str:
                for row in table:
                    row_str = "".join(str(c) for c in row)
                    if '사업시행주체' in row_str or '소관부처' in row_str:
                        agency = None
                        for cell in reversed(row):
                            val = str(cell).strip()
                            if val and val not in ['사업시행주체', '소관부처', '구분', '사업명']:
                                agency = val
                                break
                        
                        if agency and not any(m.get("implementing_agency") == agency for m in managers):
                            managers.append({
                                "sub_project": str(row[0]).strip() if len(row) > 0 and str(row[0]).strip() not in ['사업명', '구분'] else None,
                                "managing_dept": agency if '소관부처' in row_str else None,
                                "implementing_agency": agency if '사업시행주체' in row_str else None,
                                "manager": None,
                                "phone": None
                            })
        return managers

    # ==========================================
    # 3. 메인 조립부
    # ==========================================
    def parse(self, input_path: str, output_path: str):
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        chunks = list(raw_data["projects"].values()) if "projects" in raw_data else []
        merged_results = []

        for chunk in chunks:
            text = chunk.get('text', '')
            tables = chunk.get('tables', [])
            
            header = self._parse_header(text)
            if header["code"] == "0000-000": continue
            
            summary = self._extract_top_summary_tables(tables)
            budget = self._extract_budget(tables)
            main_agency = self._extract_main_agency(text)
            status_support = self._extract_status_and_support(tables)
            sub_projects = self._extract_sub_projects(tables)
            period_cost_rates = self._extract_period_cost_rates(text)
            managers = self._extract_managers(tables)
            yearly_budgets = self._extract_yearly_budgets(tables)
            overview = self._extract_overview(text)
            
            project_item: Dict[str, Any] = {
                "id": None,
                "name": f"{summary['department'] or '미상'}_{header['name']}",
                "project_name": header["name"],
                "code": header["code"],
                "department": summary["department"],
                "division": summary["division"],
                "account_type": summary["account_type"],
                "field": summary["field"],
                "sector": summary["sector"],
                "program": summary["program"],
                "unit_project": summary["unit_project"],
                "detail_project": summary["detail_project"],
                "status": status_support["status"],
                "support_type": status_support["support_type"],
                "implementing_agency": main_agency or summary["department"],
                
                "subsidy_rate": status_support.get("subsidy_rate") or period_cost_rates.get("subsidy_rate"),
                "loan_rate": status_support.get("loan_rate") or period_cost_rates.get("loan_rate"),
                
                "project_managers": managers,
                "budget": budget,       
                "project_period": period_cost_rates["project_period"],
                "total_cost": period_cost_rates["total_cost"],
                "sub_projects": sub_projects, 
                
                # [적용 완료] 여러 키워드를 포괄하여 본문을 싹 다 긁어옴
                "purpose": self._extract_text_block(text, ["사업목적", "목적"]),
                "description": self._extract_text_block(text, ["사업내용", "주요내용", "내용"]),
                "legal_basis": self._extract_text_block(text, ["지원근거", "법적근거", "설치근거", "근거"]),
                "effectiveness": self._extract_text_block(text, ["기대효과", "효과"]),
                
                "is_rnd": "(R&D)" in header["name"],
                "is_informatization": "(정보화)" in header["name"],
                "keywords": [],
                "page_start": header["page_start"],
                "page_end": int(re.findall(r'-\s*(\d+)\s*-', text)[-1]) if re.findall(r'-\s*(\d+)\s*-', text) else header["page_start"],
                "kpi": [], 
                "overview": overview,
                "budget_calculation": [],
                "execution_detail": {"method": None, "recipients": None, "subsidy_rate_detail": None},
                "yearly_budgets": yearly_budgets, 
                "history": [],
                "ai_domains": []
            }
            merged_results.append(project_item)
            
        output_data = {
            "metadata": {
                "total_count": len(merged_results), 
                "base_year": self.base_year,
                "source": "Budget Parser v12.0 (Text Block Master)"
            },
            "projects": merged_results,
            "analysis": {}
        }

        out_path_obj = Path(output_path)
        if not out_path_obj.suffix:  
            out_path_obj.mkdir(parents=True, exist_ok=True)
            final_out_file = out_path_obj / "merged.json"
        else:
            out_path_obj.parent.mkdir(parents=True, exist_ok=True)
            final_out_file = out_path_obj

        with open(final_out_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Budget Parser: 추출 완료 ({len(merged_results)}건) -> {final_out_file.name}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True)
    p.add_argument("-o", "--output", required=True)
    p.add_argument("-c", "--config", default="config/config.yaml")
    args = p.parse_args()
    BudgetParser(args.config).parse(args.input, args.output)