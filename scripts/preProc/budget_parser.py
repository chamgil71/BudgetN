# budget_parser.py (v5 - 파이프라인 연동 하이브리드 버전)

import re
import json
import os
import yaml
import sys
import argparse
from typing import Dict, Any, List
from pathlib import Path

class BudgetParser:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            print(f"❌ 설정 파일({config_path})을 찾을 수 없습니다.")
            sys.exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # [설정 동적 로딩]
        self.base_year = self.config.get('years', {}).get('base_year', 2026)
        self.project_columns = self.config.get('schema', {}).get('project_columns', [])
        self.year_offsets = self._calculate_offsets()

    def _calculate_offsets(self) -> Dict[str, int]:
        offsets = {}
        for col in self.project_columns:
            match = re.match(r'(\d{4})_', col)
            if match:
                offsets[col] = int(match.group(1)) - self.base_year
        return offsets

    def _split_into_chunks(self, pages: List[Dict]) -> List[Dict]:
        """[기존 Raw 방식 전용] 페이지 번호와 사업코드를 조합한 정밀한 사업 경계 분리"""
        chunks = []
        current_chunk = {"text": "", "tables": [], "page_numbers": []}
        
        for page in pages:
            text = page.get('text', '')
            is_new_project = re.search(r'-\s*\d+\s*-', text) and re.search(r'\d{4}-\d{3}', text)
            
            if is_new_project and current_chunk["text"].strip():
                chunks.append(current_chunk)
                current_chunk = {"text": "", "tables": [], "page_numbers": []}
            
            current_chunk["text"] += "\n" + text
            
            for t in page.get('tables', []):
                rows = t.get('rows', t) if isinstance(t, dict) else t
                current_chunk["tables"].append(rows)
                
            current_chunk["page_numbers"].append(page.get('page_number', 0))
            
        if current_chunk["text"].strip():
            chunks.append(current_chunk)
        return chunks

    def _parse_header(self, text: str) -> Dict[str, Any]:
        res = {"name": "", "code": "0000-000", "page_start": 0}
        match = re.search(r'사\s*업\s*명\s*(.*?)(?=\n|$)', text)
        if match:
            line = match.group(1).strip()
            p_match = re.search(r'-\s*(\d+)\s*-', line)
            if p_match:
                res["page_start"] = int(p_match.group(1))
                line = line[:p_match.start()].strip()
            
            c_match = re.search(r'(\d{4}-\d{3})', line)
            if c_match:
                res["code"] = c_match.group(1)
                res["name"] = line.replace(f"({res['code']})", "").replace(res['code'], "").strip()
        return res

    def _extract_top_summary_tables(self, tables: List[List]) -> Dict[str, Any]:
        """[방어 코드 적용] 헤더 매칭 및 요약표 기계적 추출"""
        result = {
            "account_type": None, "department": None, "division": None, 
            "field": None, "sector": None,
            "program": {"code": None, "name": None},
            "unit_project": {"code": None, "name": None},
            "detail_project": {"code": None, "name": None}
        }
        
        def find_col(header, keyword):
            return next((i for i, h in enumerate(header) if keyword in str(h).replace(' ', '')), -1)

        for table in tables:
            # TableModel dict 구조 방어
            if isinstance(table, dict) and 'rows' in table:
                table = table['rows']
                
            if not table or len(table) < 2: continue
            header_row = [str(c).replace('\n', '').replace(' ', '') for c in table[0]]
            
            idx_dept = find_col(header_row, "소관")
            idx_div = find_col(header_row, "실국(기관)")
            if idx_dept != -1 and idx_div != -1:
                idx_map = {
                    "회계": "account_type", "소관": "department", "실국(기관)": "division", 
                    "분야": "field", "부문": "sector"
                }
                for row in table[1:]:
                    row_str = "".join(str(c) for c in row if c)
                    if any(kw in row_str for kw in ["회계", "기금", "부", "청"]):
                        for k, target in idx_map.items():
                            c_idx = find_col(header_row, k)
                            if c_idx != -1 and len(row) > c_idx:
                                val = str(row[c_idx]).strip().replace('\n', ' ')
                                if val and val not in ["코드", "명칭"]:
                                    result[target] = val
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

    def _extract_budget(self, tables: List[List]) -> Dict[str, float]:
        """[Fallback 적용] 예산 추출"""
        budget_map = {col: None for col in self.project_columns if '_' in col}
        target_table = None
        for table in tables:
            if isinstance(table, dict) and 'rows' in table:
                table = table['rows']
                
            if not table or len(table) < 2: continue
            header_str = "".join(str(c) for h in table[:2] for c in h if h)
            if any(kw in header_str for kw in ['결산', '본예산', '정부안', '요구']):
                target_table = table; break
        if not target_table: return budget_map

        header_row = [str(c).replace(' ', '').replace('\n', '') for c in target_table[0]]
        data_row = next((row for row in target_table if any(kw in "".join(map(str, row)) for kw in ['합계', '계'])), None)
        
        # Fallback 로직 (숫자가 가장 많은 행)
        if not data_row:
            data_row = max(
                (r for r in target_table[1:] if any(r)),
                key=lambda r: sum(1 for c in r if re.search(r'\d', str(c))),
                default=[]
            )
        
        if not data_row: return budget_map

        for col, offset in self.year_offsets.items():
            target_year = self.base_year + offset
            for idx, h_text in enumerate(header_row):
                if str(target_year) in h_text:
                    num = re.sub(r'[^\d.-]', '', str(data_row[idx]).split('(')[0])
                    if num: budget_map[col] = float(num)
        return budget_map

    def _extract_text_block(self, text: str, keyword: str) -> str:
        lines = text.split('\n')
        content = []
        found = False
        for l in lines:
            if keyword in l.replace(' ', ''): found = True; continue
            if found:
                if re.match(r'^\s*(\d+\.|□|ㅇ|가\.)', l) and content: break
                content.append(l)
        return "\n".join(content).strip() if content else None

    # ==========================================
    # 🔴 수정의 핵심: parse 함수 (입력 데이터 분기)
    # ==========================================
    def parse(self, input_path: str, output_path: str):
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        chunks = []
        
        # [신규 흐름] json_structurer.py를 거친 경우 (projects 딕셔너리 구조)
        if "projects" in raw_data:
            # 이미 사업별로 쪼개져 있으므로 values()만 가져옴
            chunks = list(raw_data["projects"].values())
        
        # [기존 흐름] pdf_to_json.py 직후의 원본인 경우 (pages 리스트 구조)
        elif "pages" in raw_data:
            pages = raw_data.get('pages', [])
            chunks = self._split_into_chunks(pages) if pages else raw_data
        
        else:
            chunks = raw_data

        merged_results = []
        # 💡 [수정 3] 전달받은 output_path에서 부모 폴더 경로를 추출하여 output_dir로 사용합니다!
        output_dir = Path(output_path).parent
        os.makedirs(os.path.join(output_dir, "residual"), exist_ok=True)

        for chunk in chunks:
            text = chunk.get('text', '')
            tables = chunk.get('tables', [])
            
            header = self._parse_header(text)
            if header["code"] == "0000-000": continue
            
            summary = self._extract_top_summary_tables(tables)
            budget = self._extract_budget(tables)
            
            budget_key = f"{self.base_year}_budget"
            yearly_budgets = {str(self.base_year): budget.get(budget_key)} if budget.get(budget_key) else {}

            # [무결성 유지] 37개 스키마 필드 완전 보존
            project_item = {
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
                "status": "신규" if "신규" in text[:500] else "계속",
                "support_type": None,
                "implementing_agency": None,
                "subsidy_rate": None,
                "loan_rate": None,
                "project_managers": [],
                "budget": budget,
                "project_period": {"start_year":None, "end_year":None, "duration":None, "raw":None},
                "total_cost": {"total":None, "government":None, "raw":None},
                "sub_projects": [],
                "purpose": self._extract_text_block(text, "사업목적"),
                "description": self._extract_text_block(text, "사업내용"),
                "legal_basis": self._extract_text_block(text, "근거"),
                "is_rnd": "(R&D)" in header["name"],
                "is_informatization": "(정보화)" in header["name"],
                "keywords": [],
                "page_start": header["page_start"],
                "page_end": int(re.findall(r'-\s*(\d+)\s*-', text)[-1]) if re.findall(r'-\s*(\d+)\s*-', text) else header["page_start"],
                "kpi": [],
                "overview": {"사업규모":None, "사업수혜자":None, "사업시행방법":None},
                "budget_calculation": [],
                "effectiveness": self._extract_text_block(text, "기대효과"),
                "execution_detail": {"method":None, "recipients":None, "subsidy_rate_detail":None},
                "yearly_budgets": yearly_budgets,
                "history": [],
                "ai_domains": []
            }
            merged_results.append(project_item)
            
        output_data = {
            "metadata": {
                "total_count": len(merged_results), 
                "base_year": self.base_year,
                "source": "Budget Parser v5.0 (Pipeline Integrated)"
            },
            "projects": merged_results,
            "analysis": {}
        }

        # out_file = os.path.join(output_dir, "merged.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✅ Budget Parser: 필드 추출 완료 ({len(merged_results)}건) -> {Path(output_path).name}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True)
    p.add_argument("-o", "--output", default="./result")
    p.add_argument("-c", "--config", default="config.yaml")
    args = p.parse_args()
    BudgetParser(args.config).parse(args.input, args.output)