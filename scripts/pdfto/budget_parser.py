import re
import json
import os
import yaml
import sys
import argparse
from typing import Dict, Any, List

class BudgetParser:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            print(f"❌ 설정 파일({config_path})을 찾을 수 없습니다.")
            sys.exit(1)
            
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 1. 하드코딩 완전 제거
        self.base_year = self.config.get('base_year', 2026)
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
        """페이지 배열을 '사 업 명' 단위로 묶는 필수 전처리"""
        chunks = []
        current_chunk = {"text": "", "tables": [], "page_numbers": []}
        split_pattern = r'사\s*업\s*명'

        for page in pages:
            text = page.get('text', '')
            if re.search(split_pattern, text) and current_chunk["text"].strip():
                chunks.append(current_chunk)
                current_chunk = {"text": "", "tables": [], "page_numbers": []}
            
            current_chunk["text"] += "\n" + text
            current_chunk["tables"].extend(page.get('tables', []))
            current_chunk["page_numbers"].append(page.get('page_number', 0))
            
        if current_chunk["text"].strip():
            chunks.append(current_chunk)
        return chunks

    def _parse_header(self, text: str) -> Dict[str, Any]:
        """[사 업 명] 라인에서 이름, 코드, 시작페이지 추출"""
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
        """[sample.pdf 대응] 최상단 요약 표 2개에서 소관, 실국, 프로그램 등을 기계적으로 추출"""
        result = {
            "account_type": None, "department": None, "division": None, 
            "field": None, "sector": None,
            "program": {"code": None, "name": None},
            "unit_project": {"code": None, "name": None},
            "detail_project": {"code": None, "name": None}
        }
        
        for table in tables:
            if not table or len(table) < 2: continue
            
            header_row = [str(c).replace('\n', '').replace(' ', '') for c in table[0]]
            
            # 1. 회계/소관/실국 표
            if "소관" in header_row and "실국(기관)" in header_row:
                idx_acc = header_row.index("회계") if "회계" in header_row else -1
                idx_dept = header_row.index("소관") if "소관" in header_row else -1
                idx_div = header_row.index("실국(기관)") if "실국(기관)" in header_row else -1
                idx_field = header_row.index("분야") if "분야" in header_row else -1
                idx_sector = header_row.index("부문") if "부문" in header_row else -1
                
                for row in table[1:]:
                    row_str = "".join(str(c) for c in row if c)
                    # 코드가 아닌 실제 텍스트가 들어있는 행 스캔
                    if "회계" in row_str or "기금" in row_str or "명칭" in row_str or "부" in row_str:
                        if idx_acc != -1 and len(row) > idx_acc and str(row[idx_acc]).strip():
                            result["account_type"] = str(row[idx_acc]).replace('\n', ' ').strip()
                        if idx_dept != -1 and len(row) > idx_dept and str(row[idx_dept]).strip():
                            result["department"] = str(row[idx_dept]).replace('\n', ' ').strip()
                        if idx_div != -1 and len(row) > idx_div and str(row[idx_div]).strip():
                            result["division"] = str(row[idx_div]).replace('\n', ' ').strip()
                        if idx_field != -1 and len(row) > idx_field and str(row[idx_field]).strip():
                            result["field"] = str(row[idx_field]).replace('\n', ' ').strip()
                        if idx_sector != -1 and len(row) > idx_sector and str(row[idx_sector]).strip():
                            result["sector"] = str(row[idx_sector]).replace('\n', ' ').strip()
                            
            # 2. 프로그램/단위사업 표
            elif "프로그램" in header_row and "단위사업" in header_row:
                idx_prog = header_row.index("프로그램")
                idx_unit = header_row.index("단위사업")
                idx_detail = header_row.index("세부사업") if "세부사업" in header_row else -1
                
                for row in table[1:]:
                    row_type = str(row[0]).replace(' ', '') if row else ""
                    if "코드" in row_type:
                        result["program"]["code"] = str(row[idx_prog]).strip()
                        result["unit_project"]["code"] = str(row[idx_unit]).strip()
                        if idx_detail != -1: result["detail_project"]["code"] = str(row[idx_detail]).strip()
                    elif "명칭" in row_type:
                        result["program"]["name"] = str(row[idx_prog]).replace('\n', ' ').strip()
                        result["unit_project"]["name"] = str(row[idx_unit]).replace('\n', ' ').strip()
                        if idx_detail != -1: result["detail_project"]["name"] = str(row[idx_detail]).replace('\n', ' ').strip()
                        
        return result

    def _extract_budget(self, tables: List[List]) -> Dict[str, float]:
        """연도별 예산 (합계 행 추출)"""
        budget_map = {col: None for col in self.project_columns if '_' in col}
        target_table = None
        
        for table in tables:
            if not table or len(table) < 2: continue
            header_str = "".join(str(c) for h in table[:2] for c in h if h)
            if any(kw in header_str for kw in ['결산', '본예산', '정부안', '요구']):
                target_table = table
                break
        if not target_table: return budget_map

        header_row = [str(c).replace(' ', '').replace('\n', '') for c in target_table[0]]
        data_row = next((row for row in target_table if any(kw in "".join(map(str, row)) for kw in ['합계', '계'])), [])
        if not data_row: return budget_map

        for col, offset in self.year_offsets.items():
            target_year = self.base_year + offset
            for idx, h_text in enumerate(header_row):
                if str(target_year) in h_text:
                    val = str(data_row[idx]).split('(')[0]
                    num = re.sub(r'[^\d.-]', '', val)
                    if num: budget_map[col] = float(num)
        return budget_map

    def _extract_text_block(self, text: str, keyword: str) -> str:
        """키워드가 포함된 섹션 전체를 가져옴"""
        lines = text.split('\n')
        content = []
        found = False
        for l in lines:
            if keyword in l.replace(' ', ''): 
                found = True
                continue
            if found:
                if re.match(r'^\s*(\d+\.|□|ㅇ|가\.)', l) and content: 
                    break
                content.append(l)
        return "\n".join(content).strip() if content else None

    def _extract_overview(self, text: str) -> Dict[str, str]:
        """Dict 구조 반환 (실데이터 기준)"""
        overview = {"사업규모": None, "사업수혜자": None, "사업시행방법": None}
        block = self._extract_text_block(text, "사업개요")
        if not block: return overview
        for line in block.split('\n'):
            if "규모" in line: overview["사업규모"] = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
            elif "수혜자" in line or "대상" in line: overview["사업수혜자"] = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
            elif "시행방법" in line or "방식" in line: overview["사업시행방법"] = line.split(':', 1)[-1].strip() if ':' in line else line.strip()
        return overview

    def _extract_history(self, text: str) -> List[Dict[str, Any]]:
        """List[Dict] 구조 반환 (실데이터 기준)"""
        history = []
        block = self._extract_text_block(text, "추진경과")
        if not block: return history
        
        current_year = None
        current_desc = []
        for line in block.split('\n'):
            line = line.strip()
            year_match = re.search(r'(20\d{2})', line)
            if year_match and line.startswith(year_match.group(1)):
                if current_year: history.append({"year": current_year, "description": " ".join(current_desc).strip()})
                current_year = int(year_match.group(1))
                current_desc = [line.replace(str(current_year), "", 1).replace('년', '').replace('.', '').strip()]
            elif current_year and line:
                current_desc.append(line)
        if current_year: history.append({"year": current_year, "description": " ".join(current_desc).strip()})
        return history

    def _extract_ai_domains(self, text: str, project_name: str) -> List[str]:
        """config에 ai_keyword_dict가 정의되어 있으면 매핑, 없으면 [] 반환"""
        ai_dictionary = self.config.get('ai_keyword_dict', {})
        if not ai_dictionary: return []
        
        detected = set()
        target_text = (project_name + "\n" + text).replace(" ", "").upper()
        for domain, keywords in ai_dictionary.items():
            for kw in keywords:
                if kw.replace(" ", "").upper() in target_text:
                    detected.add(domain)
                    break 
        return list(detected)

    def parse(self, input_path: str, output_dir: str):
        if not os.path.exists(input_path):
            print(f"❌ 입력 파일 없음: {input_path}"); sys.exit(1)

        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        
        pages = raw_data.get('pages', [])
        chunks = self._split_into_chunks(pages) if pages else raw_data
        
        merged_results = []
        os.makedirs(os.path.join(output_dir, "residual"), exist_ok=True)

        for chunk in chunks:
            text = chunk.get('text', '')
            tables = chunk.get('tables', [])
            
            header = self._parse_header(text)
            p_id = header["code"]
            if p_id == "0000-000": continue
            
            # [1] 상단 표에서 기본 메타데이터 추출 (sample.pdf 기준)
            summary_info = self._extract_top_summary_tables(tables)
            dept_name = summary_info["department"] if summary_info["department"] else "미상"
            
            # [2] 종료 페이지 찾기
            all_pages = re.findall(r'-\s*(\d+)\s*-', text)
            page_end = int(all_pages[-1]) if all_pages else header["page_start"]
            
            # [3] 텍스트 블록
            purpose_text = self._extract_text_block(text, "사업목적")
            desc_text = self._extract_text_block(text, "사업내용")
            if not desc_text: desc_text = purpose_text # 합쳐진 경우 보완

            # ==========================================================
            # [4] 스키마 매핑 (budget_db.json 38개 필드와 100% 동일 구조)
            # ==========================================================
            project_item = {
                "id": None, # 임의 인덱스 생성 금지
                "name": f"{dept_name}_{header['name']}",
                "project_name": header["name"],
                "code": p_id,
                
                # 상단 표에서 읽어온 값 매핑
                "department": summary_info["department"],
                "division": summary_info["division"],
                "account_type": summary_info["account_type"],
                "field": summary_info["field"],
                "sector": summary_info["sector"],
                "program": summary_info["program"],
                "unit_project": summary_info["unit_project"],
                "detail_project": summary_info["detail_project"],
                
                "status": "신규" if "신규" in text[:500] else "계속",
                "support_type": None,
                "implementing_agency": None,
                "subsidy_rate": None,
                "loan_rate": None,
                "project_managers": [],
                
                "budget": self._extract_budget(tables),
                
                "project_period": {
                    "start_year": None, "end_year": None, "duration": None, "raw": None
                },
                "total_cost": {"total": None, "government": None, "raw": None},
                "sub_projects": [],
                
                "purpose": purpose_text,
                "description": desc_text,
                "legal_basis": self._extract_text_block(text, "근거"),
                
                "is_rnd": "R&D" in header["name"] or "연구개발" in text,
                "is_informatization": "정보화" in header["name"] or "정보화" in text,
                "keywords": [w for w in header["name"].split() if len(w) > 1],
                
                "page_start": header["page_start"],
                "page_end": page_end,
                
                "kpi": [],
                "overview": self._extract_overview(text),
                "budget_calculation": [],
                "effectiveness": self._extract_text_block(text, "기대효과"),
                
                "execution_detail": {"method": None, "recipients": None, "subsidy_rate_detail": None},
                "yearly_budgets": {},
                "history": self._extract_history(text),
                "ai_domains": self._extract_ai_domains(text, header["name"])
            }
            
            merged_results.append(project_item)
            
            # 원본 비교를 위한 잔여 데이터 저장
            res_path = os.path.join(output_dir, "residual", f"{p_id}_residual.json")
            with open(res_path, 'w', encoding='utf-8') as f:
                json.dump(chunk, f, ensure_ascii=False, indent=2)

        output_data = {
            "metadata": {"total_count": len(merged_results), "base_year": self.base_year},
            "project": merged_results,
            "analysis": {}
        }

        out_file = os.path.join(output_dir, "merged.json")
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 파싱 완료! (추출: {len(merged_results)}건)")
        print(f"   - 정형 데이터: {out_file}")
        print(f"   - 잔여 데이터: {output_dir}/residual/")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("-i", "--input", required=True)
    p.add_argument("-o", "--output", default="./result")
    p.add_argument("-c", "--config", default="config.yaml")
    args = p.parse_args()
    
    BudgetParser(args.config).parse(args.input, args.output)