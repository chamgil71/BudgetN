import argparse
import sys
import logging
import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class BudgetParser:
    def __init__(self):
        self.project_split_pattern = re.compile(r'\(\d+\)\s*([^\(]+?)\s*\((\d{4}-\d{3})\)')
        self.current_id = 1

    def parse_file(self, raw_json_path: Path) -> List[Dict[str, Any]]:
        logger.info(f"🔍 파싱 시작: {raw_json_path.name}")
        
        try:
            with open(raw_json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            logger.error(f"❌ Raw JSON 읽기 실패: {e}")
            return []

        # ==========================================
        # [사용자 설계] 파일명 기반 config.yaml 매핑
        # ==========================================
        file_name = raw_json_path.stem
        prefix = file_name.split('_')[0] if '_' in file_name else file_name
        department_name = prefix  
        
        # 프로젝트 루트의 config.yaml 탐색
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = yaml.safe_load(f)
                    aliases = cfg.get("search_aliases", {})
                    if prefix in aliases:
                        department_name = aliases[prefix][0]
            except Exception as e:
                logger.warning(f"⚠️ config.yaml 파싱 실패, 파일명을 그대로 사용합니다: {e}")
                
        logger.info(f"🏢 확정 부처명: {department_name}")
        # ==========================================

        full_text = ""
        all_tables = []
        for page in raw_data.get("pages", []):
            full_text += page.get("text", "") + "\n"
            for table in page.get("tables", []):
                all_tables.append(table.get("rows", []))

        matches = list(self.project_split_pattern.finditer(full_text))
        if not matches:
            logger.warning("문서에서 사업명 패턴을 찾을 수 없습니다.")
            return []

        logger.info(f"✅ 총 {len(matches)}개의 사업 단위(Chunk)를 발견했습니다.")
        projects = []

        for i, match in enumerate(matches):
            project_name = match.group(1).strip()
            project_code = match.group(2).strip()
            
            start_idx = match.end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
            chunk_text = full_text[start_idx:end_idx]
            
            project_data = self._extract_project_data(department_name, project_name, project_code, chunk_text, all_tables)
            projects.append(project_data)
            self.current_id += 1

        return projects

    def _extract_project_data(self, department_name: str, project_name: str, project_code: str, chunk_text: str, all_tables: list) -> Dict[str, Any]:
        budget_data = self._extract_budget_row(all_tables)
        start_yr, end_yr = self._extract_period(chunk_text)
        
        budget_25 = budget_data.get("2025", 0.0)
        budget_26 = budget_data.get("2026", 0.0)

        duration_val = f"{end_yr - start_yr + 1}년" if (start_yr and end_yr) else None
        
        change_amt = None
        change_rt = None
        if budget_26 is not None and budget_25 is not None:
            change_amt = budget_26 - budget_25
            if budget_25 != 0:
                change_rt = round((change_amt / budget_25) * 100, 2)

        managers = self._parse_managers_table(all_tables)
        agency_set = set(m["implementing_agency"] for m in managers if m.get("implementing_agency"))
        root_agency = ", ".join(agency_set) if agency_set else None

        project = {
            "id": self.current_id,
            "name": f"{department_name}_{project_name}",
            "project_name": project_name,
            "code": project_code,
            
            "department": department_name, 
            "division": self._extract_kv_from_table(all_tables, "실국(기관)"),
            "account_type": self._extract_kv_from_table(all_tables, "회계", is_vertical=True) or self._extract_kv_from_table(all_tables, "회계"),
            "field": self._extract_kv_from_table(all_tables, "분야", is_vertical=True) or "통신",
            "sector": self._extract_kv_from_table(all_tables, "부문", is_vertical=True) or "정보통신",
            
            "program": {
                "code": self._extract_kv_from_table(all_tables, "프로그램", is_vertical=True),
                "name": self._extract_kv_from_table(all_tables, "프로그램", is_vertical=True)
            },
            "unit_project": {
                "code": self._extract_kv_from_table(all_tables, "단위사업", is_vertical=True),
                "name": self._extract_kv_from_table(all_tables, "단위사업", is_vertical=True)
            },
            "detail_project": {
                "code": project_code,
                "name": project_name
            },
            
            "status": self._extract_kv_from_table(all_tables, "신규") or "계속",
            "support_type": self._extract_kv_from_table(all_tables, "지원형태") or "직접",
            "implementing_agency": root_agency or self._extract_kv_from_table(all_tables, "시행주체") or "미상",
            "subsidy_rate": self._extract_kv_from_table(all_tables, "보조율"),
            "loan_rate": self._extract_kv_from_table(all_tables, "융자율"),
            
            "project_managers": managers,
            
            "budget": {
                "2024_settlement": budget_data.get("2024"),
                "2025_original": budget_25,
                "2025_supplementary": None,
                "2026_request": budget_26,
                "2026_budget": budget_26,
                "change_amount": change_amt,
                "change_rate": change_rt
            },
            
            "project_period": {
                "start_year": start_yr,
                "end_year": end_yr,
                "duration": duration_val,
                "raw": self._extract_kv_from_table(all_tables, "사업기간")
            },
            
            "total_cost": {
                "total": self._extract_kv_from_table(all_tables, "총사업비"),
                "government": self._extract_kv_from_table(all_tables, "국비"),
                "raw": None
            },
            
            "sub_projects": [],
            "purpose": self._extract_text_block(chunk_text, "사업목적"),
            "description": self._extract_text_block(chunk_text, "사업내용"),
            "legal_basis": self._extract_text_block(chunk_text, "법적근거"),
            
            "is_rnd": "(R&D)" in project_name,
            "is_informatization": "(정보화)" in project_name,
            "keywords": [],
            "page_start": None,
            "page_end": None,
            "kpi": [],
            "overview": {
                "사업규모": self._extract_kv_from_table(all_tables, "사업규모"),
                "사업수혜자": self._extract_kv_from_table(all_tables, "수혜자"),
                "사업시행방법": self._extract_kv_from_table(all_tables, "시행방법")
            },
            "budget_calculation": [],
            "effectiveness": self._extract_text_block(chunk_text, "기대효과"),
            "execution_detail": {
                "method": self._extract_text_block(chunk_text, "추진체계"),
                "recipients": self._extract_kv_from_table(all_tables, "지원대상"),
                "subsidy_rate_detail": None
            },
            "yearly_budgets": {
                "2026": budget_26
            },
            "history": [],
            "ai_domains": ["디지털전환(AX)"]
        }

        return project

    def _extract_kv_from_table(self, tables, keyword: str, is_vertical=False) -> Optional[str]:
        for table in tables:
            if not table: continue
            if is_vertical and len(table) > 1:
                header = table[0]
                for c_idx, cell in enumerate(header):
                    if cell and keyword in str(cell):
                        for row in table[1:]:
                            if len(row) > c_idx and row[c_idx]:
                                val = str(row[c_idx]).replace('\n', ' ').strip()
                                if val and val != "None": return val
            else:
                for row in table:
                    for c_idx, cell in enumerate(row):
                        if cell and keyword in str(cell):
                            if c_idx + 1 < len(row) and row[c_idx + 1]:
                                val = str(row[c_idx + 1]).replace('\n', ' ').strip()
                                if val and val != "None": return val
        return None

    def _extract_text_block(self, text: str, keyword: str) -> Optional[str]:
        pattern = re.compile(rf"{keyword}.*?(?=\n\s*\d+\)|\Z)", re.DOTALL)
        match = pattern.search(text)
        if match:
            clean_text = match.group(0).replace('\n', ' ').strip()
            return clean_text[:500] 
        return None

    def _extract_period(self, text: str) -> tuple:
        match = re.search(r'(20\d{2})\s*(?:~|-|부터)\s*(20\d{2}|\s*계속)', text)
        if match:
            start = int(match.group(1))
            end_str = match.group(2).replace(' ', '')
            end = 2099 if '계속' in end_str else int(end_str)
            return start, end
        return None, None

    def _extract_budget_row(self, tables) -> Dict[str, float]:
        budget = {}
        for table in tables:
            if not table or not table[0]: continue
            
            header_str = "".join(str(c).replace('\n', '').replace(' ', '') for c in table[0] if c)
            if any(y in header_str for y in ['2024', '2025', '2026', '24년', '25년', '26년', '결산', '요구']):
                
                best_row_vals = []
                for row in table[1:]:
                    if not any(row): continue
                    row_str = "".join(str(c).replace(' ', '').replace('\n', '') for c in row if c)
                    
                    if any(kw in row_str for kw in ['합계', '계', '총계', '사업비', '국비', '예산']):
                        vals = [self._clean_budget(c) for c in row if c and re.search(r'\d', str(c))]
                        if len(vals) >= 1:
                            best_row_vals = vals
                            break 
                
                if not best_row_vals:
                    max_nums = 0
                    for row in table[1:]:
                        vals = [self._clean_budget(c) for c in row if c and re.search(r'\d', str(c))]
                        if len(vals) > max_nums:
                            max_nums = len(vals)
                            best_row_vals = vals
                
                if len(best_row_vals) >= 3:
                    budget["2024"] = best_row_vals[-3]
                    budget["2025"] = best_row_vals[-2]
                    budget["2026"] = best_row_vals[-1]
                elif len(best_row_vals) == 2:
                    budget["2025"] = best_row_vals[-2]
                    budget["2026"] = best_row_vals[-1]
                elif len(best_row_vals) == 1:
                    budget["2026"] = best_row_vals[-1]
                    
                if budget: 
                    return budget 
        return budget

    def _clean_budget(self, val) -> float:
        if not val: return 0.0
        v = str(val).replace(',', '').replace('\n', '').strip()
        if v in ['-', '', '.', '해당없음']: return 0.0
        
        v = re.sub(r'[^\d\.\-]', '', v)
        try: 
            return float(v) if v else 0.0
        except ValueError: 
            return 0.0

    def _parse_managers_table(self, tables) -> List[Dict]:
        managers = []
        for table in tables:
            if not table or not table[0]: continue
            header = str(table[0]).replace('\n', '').replace(' ', '')
            if '내역사업' in header or '담당자' in header:
                for row in table[1:]:
                    if len(row) >= 4:
                        managers.append({
                            "sub_project": str(row[0]).strip() if row[0] else None,
                            "managing_dept": str(row[1]).strip() if row[1] else None,
                            "implementing_agency": str(row[2]).strip() if row[2] else None,
                            "manager": str(row[3]).strip() if row[3] else None,
                            "phone": str(row[4]).strip() if len(row) > 4 and row[4] else None
                        })
        return managers

def main():
    parser = argparse.ArgumentParser(description="Raw JSON -> 개별 Parsed JSON 파서")
    parser.add_argument("--input", "-i", default="./input", help="Raw JSON 파일 또는 폴더 경로")
    parser.add_argument("--output", "-o", default="./output/individual", help="개별 파싱 결과 저장 폴더")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_files = []

    # 입력 경로가 파일인지 폴더인지 정확히 구분하여 처리합니다.
    if input_path.is_file():
        raw_files.append(input_path)
    elif input_path.is_dir():
        raw_files = list(input_path.glob("*_raw.json"))
    else:
        logger.error(f"❌ 입력 경로를 찾을 수 없습니다: {input_path}")
        sys.exit(1)

    if not raw_files:
        logger.error(f"❌ '{input_path}' 경로에 변환할 파일이 없습니다.")
        sys.exit(1)

    parser_obj = BudgetParser()
    total_projects = 0

    for file_path in raw_files:
        projects = parser_obj.parse_file(file_path)
        if projects:
            out_file = output_dir / f"{file_path.stem.replace('_raw', '')}_parsed.json"
            with open(out_file, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
            logger.info(f"💾 파싱 완료: {out_file.name} (사업 {len(projects)}개 추출)")
            total_projects += len(projects)

    logger.info(f"🎉 모든 파싱 완료! 총 {total_projects}개 사업이 추출되었습니다.")

if __name__ == "__main__":
    main()