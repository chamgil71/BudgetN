import re
import json
import logging
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class BudgetParser:
    def __init__(self, config_path: str):
        """설정 로드 및 전역 변수 초기화"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.base_year = self.config.get('years', {}).get('base_year', 2026)

    def parse(self, input_path: str, output_path: str):
        """파일 단위 파싱 오케스트레이션"""
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
        chunks = list(raw_data.get("projects", {}).values()) if isinstance(raw_data.get("projects"), dict) else raw_data.get("projects", [])
        results = []
        
        for chunk in chunks:
            try:
                parsed_item = self._parse_single_project(chunk)
                if parsed_item.get("code"):
                    results.append(parsed_item)
            except Exception as e:
                logger.error(f"프로젝트 파싱 중 오류 발생: {e}")
                
        out_file = Path(output_path) / "merged.json" if not Path(output_path).suffix else Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump({"projects": results}, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 파싱 완료 ({len(results)}건): {out_file.name}")

    def _parse_single_project(self, project_data: dict) -> Dict[str, Any]:
        """단일 사업 데이터(Chunk)에서 54개 키 전수 추출"""
        text = project_data.get("text", "")
        tables = project_data.get("tables", [])
        pages = project_data.get("pages", [])
        
        # 1. 빈 그릇(초기값) 생성 (template.json 계층 구조 반영)
        res = self._init_result()
        if pages:
            res["page_start"] = pages[0]
            res["page_end"] = pages[-1]

        # -------------------------------------------------------------
        # 2. 메타데이터 (최상단 '사 업 명' 앵커 기준 추출)
        # -------------------------------------------------------------
        title_anchor = re.search(r'사\s*업\s*명\s*[\r\n]+([^\n□]+)', text)
        if title_anchor:
            raw_title_line = title_anchor.group(1).strip() 
            # 고객 규칙: 숫자 4자리-3자리 규격만 코드로 인정
            code_match = re.search(r'\((\d{4}-\d{3})\)', raw_title_line)
            if code_match:
                res["code"] = code_match.group(1)
                # 앞의 순번과 뒤의 코드 제거하여 순수 사업명 확보
                name_clean = raw_title_line.replace(code_match.group(0), '')
                name_clean = re.sub(r'^\s*(?:\(\d+\)|\[\d+\]|\d+\.)\s*', '', name_clean)
                res["project_name"] = name_clean.strip()
                # id 생성 (Validation 필수 항목)
                res["id"] = f"{self.base_year}_{res['code']}"

        # R&D, 정보화 판별
        if res["project_name"]:
            if "R&D" in res["project_name"].upper(): res["is_rnd"] = True
            if "정보화" in res["project_name"]: res["is_informatization"] = True
       
        # -------------------------------------------------------------
        # 3. 2D 표(Table) 시그니처 및 인덱스 기반 추출 (원본 로직 보존)
        # -------------------------------------------------------------
        sub_dept_map = {}
        sub_budget_map = {}

        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            if not rows or len(rows) < 2: continue
            
            clean_row0 = [str(c).replace(" ", "").replace("\n", "").strip() if c else "" for c in rows[0]]
            h_str = "".join(clean_row0)

            # [표 1] 사업 코드 정보 (회계, 소관, 분야 등)
            if "회계" in h_str and "소관" in h_str:
                res["account_type"] = self._get_vertical_val(rows, clean_row0, "회계", 1, 2)
                res["department"] = self._get_vertical_val(rows, clean_row0, "소관", 1, 2)
                res["division"] = self._get_vertical_val(rows, clean_row0, "실국(기관)", 1, 2)
                res["field"] = self._get_vertical_val(rows, clean_row0, "분야", 1, 1)
                res["sector"] = self._get_vertical_val(rows, clean_row0, "부문", 1, 1)
                res["name"] = f"{res['department']}_{res['project_name']}"

            # [표 2] 사업 코드 정보 (프로그램 등 - 계층 구조 반영)
            elif "프로그램" in h_str and "단위사업" in h_str:
                res["program"]["code"] = self._get_vertical_val(rows, clean_row0, "프로그램", 1, 1)
                res["program"]["name"] = self._get_vertical_val(rows, clean_row0, "프로그램", 2, 2)
                res["unit_project"]["code"] = self._get_vertical_val(rows, clean_row0, "단위사업", 1, 1)
                res["unit_project"]["name"] = self._get_vertical_val(rows, clean_row0, "단위사업", 2, 2)
                res["detail_project"]["code"] = self._get_vertical_val(rows, clean_row0, "세부사업", 1, 1)
                res["detail_project"]["name"] = self._get_vertical_val(rows, clean_row0, "세부사업", 2, 2)

            # [표 3] 사업 성격 (신규/계속/완료)
            elif "신규" in h_str and "계속" in h_str:
                chk_pattern = re.compile(r'[OΟV☑■o]')
                for key in ["신규", "계속", "완료"]:
                    if key in clean_row0:
                        idx = clean_row0.index(key)
                        if idx < len(rows[1]) and rows[1][idx] and chk_pattern.search(str(rows[1][idx])):
                            res["status"] = key
                            break

            # [표 4] 사업 지원 형태 및 지원율
            elif "출연" in h_str and "보조" in h_str:
                chk_pattern = re.compile(r'[OΟV☑■o]')
                for key in ["직접", "출자", "출연", "보조", "융자"]:
                    if key in clean_row0:
                        idx = clean_row0.index(key)
                        if idx < len(rows[1]) and rows[1][idx] and chk_pattern.search(str(rows[1][idx])):
                            res["support_type"] = key # 단일 String 규격
                            break
                res["subsidy_rate"] = self._get_vertical_val(rows, clean_row0, "국고보조율(%)", 1, 1)
                res["loan_rate"] = self._get_vertical_val(rows, clean_row0, "융자율(%)", 1, 1)

            # [표 5] 사업 소관부처 및 시행주체 (내역사업 데이터)
            elif "소관부처" in h_str or "사업시행주체" in h_str:
                current_sub_name = ""
                for r in rows[1:]:
                    col0 = str(r[0]).replace('\n', ' ').strip() if r[0] else ""
                    col1 = str(r[1]).replace(' ', '').strip() if len(r) > 1 and r[1] else ""
                    col2 = str(r[2]).replace('\n', ' ').strip() if len(r) > 2 and r[2] else ""
                    
                    if col0 and col0 not in ["사업명", "구분"]:
                        current_sub_name = col0
                        if current_sub_name not in sub_dept_map:
                            sub_dept_map[current_sub_name] = {"managing_dept": "", "implementing_agency": ""}
                    
                    if current_sub_name:
                        if "소관부처" in col1:
                            sub_dept_map[current_sub_name]["managing_dept"] = col2
                        elif "사업시행주체" in col1 or "시행기관" in col1:
                            sub_dept_map[current_sub_name]["implementing_agency"] = col2

                if sub_dept_map and not res["implementing_agency"]:
                    first_sub = list(sub_dept_map.keys())[0]
                    res["implementing_agency"] = sub_dept_map[first_sub].get("implementing_agency", "")

            # [표 6] 지출계획 총괄표 (budget 객체 내 매핑)
            elif "결산" in h_str and ("본예산" in h_str or "요구안" in h_str):
                idx_map = {
                    "2024_settlement": self._find_idx(clean_row0, "결산"),
                    "2025_original": self._find_idx(clean_row0, "본예산", exclude="B"),
                    "2026_request": self._find_idx(clean_row0, "요구안"),
                    "2026_budget": self._find_idx(clean_row0, ["본예산(B)", "정부안"])
                }
                for r in rows[1:]:
                    if sum(1 for c in r if re.search(r'\d', str(c))) >= 3:
                        for k, idx in idx_map.items():
                            if idx != -1 and idx < len(r):
                                res["budget"][k] = self._clean_num(r[idx])
                        break
            
            # [표 7] 기능별(내역사업별) 계획 내역
            elif "합계" in h_str or "기능별" in h_str or "내역사업" in h_str:
                header_combined = [str(rows[0][i] or "") + str(rows[1][i] if len(rows)>1 else "") for i in range(len(rows[0]))]
                idx_y2 = self._find_idx(header_combined, [f"{self.base_year-2}", "결산", "집행액"])
                idx_y1 = self._find_idx(header_combined, [f"{self.base_year-1}", "본예산", "현액"])
                idx_y0 = self._find_idx(header_combined, [f"{self.base_year}", "예산", "정부안"])

                for r in rows[1:]:
                    name = str(r[0]).strip().replace('\n', ' ')
                    if not name or any(k in name for k in ["합계", "소계", "총계"]): continue
                    clean_name = re.sub(r'^[·\-\s]*', '', name)
                    
                    sub_budget_map[clean_name] = {
                        "budget_2024": self._clean_num(r[idx_y2]) if idx_y2 != -1 and idx_y2 < len(r) else 0.0,
                        "budget_2025": self._clean_num(r[idx_y1]) if idx_y1 != -1 and idx_y1 < len(r) else 0.0,
                        "budget_2026": self._clean_num(r[idx_y0]) if idx_y0 != -1 and idx_y0 < len(r) else 0.0,
                    }

            # [표 8] 성과지표 (KPI)
            elif "지표명" in h_str and "목표" in h_str:
                idx_name = self._find_idx(clean_row0, "지표명")
                idx_target = self._find_idx(clean_row0, ["목표", f"{self.base_year}"])
                for r in rows[1:]:
                    if idx_name != -1 and idx_name < len(r) and r[idx_name]:
                        res["kpi"].append({
                            "indicator_name": str(r[idx_name]).replace('\n', ' ').strip(),
                            "target_value": str(r[idx_target]).replace('\n', ' ').strip() if idx_target != -1 and idx_target < len(r) else ""
                        })

            # [표 9] 연도별 사업추진 경과 (History)
            elif "연도" in h_str and ("경과" in h_str or "내용" in h_str):
                idx_year = self._find_idx(clean_row0, "연도")
                idx_desc = self._find_idx(clean_row0, ["경과", "내용"])
                for r in rows[1:]:
                    if idx_year != -1 and idx_year < len(r) and r[idx_year]:
                        y_val = self._clean_num(r[idx_year])
                        if y_val > 0:
                            res["history"].append({
                                "year": int(y_val),
                                "description": str(r[idx_desc]).replace('\n', ' ').strip() if idx_desc != -1 and idx_desc < len(r) else ""
                            })

            # [표 10] 최근 4년간 결산내역 (Yearly Budgets)
            elif "결산액" in h_str or "집행액" in h_str:
                idx_year = self._find_idx(clean_row0, ["연도", "구분"])
                idx_amt = self._find_idx(clean_row0, ["결산액", "집행액"])
                for r in rows[1:]:
                    if idx_year != -1 and idx_year < len(r) and str(r[idx_year]).strip().isdigit():
                        res["yearly_budgets"].append({
                            "year": int(str(r[idx_year]).strip()),
                            "amount": self._clean_num(r[idx_amt]) if idx_amt != -1 and idx_amt < len(r) else 0.0
                        })

        # 내역사업 조립 (1:N 데이터 병합)
        self._assemble_sub_data(res, sub_dept_map, sub_budget_map)

        # -------------------------------------------------------------
        # 4. 텍스트 목차 슬라이싱 (서술형 데이터 블록 추출)
        # -------------------------------------------------------------
        res["purpose"] = self._slice_block(text, ["사업목적·내용", "사업개요"], ["사업근거", "주요내용"])
        res["description"] = res["purpose"]
        res["legal_basis"] = self._slice_block(text, ["사업근거", "지원근거", "사업개요"], ["주요내용"])
        res["effectiveness"] = self._slice_block(text, ["기대효과", "사업효과"], ["타당성조사", "각종 평가"])
        res["evaluations"] = self._slice_block(text, ["타당성조사", "각종 평가"], ["최근 4년간 결산내역", "결산표"])
        
        main_content = self._slice_block(text, ["주요내용"], ["산출 근거", "기대효과"])
        self._extract_inline_meta(main_content or text, res)
        
        # 수혜자 및 집행방법 (20자 룰)
        res["execution_detail"]["recipients"] = self._slice_block(main_content or text, ["사업수혜자", "정책수혜자"], ["2026년도", "산출근거", "기대효과"])
        method_text = self._slice_block(text, ["사업 집행절차", "집행절차"], ["각종 평가", "결산내역"])
        if method_text:
            res["execution_detail"]["method"] = method_text.replace('\n', ' ').strip()[:20]

        # -------------------------------------------------------------
        # 5. NLP 키워드 검사 (AI기술, R&D단계, 도메인)
        # -------------------------------------------------------------
        res["ai_tech_types"] = self._match_keywords(text, ["머신러닝", "딥러닝", "자연어", "비전", "생성형"])
        rnd_match = self._match_keywords(text, ["기초연구", "응용연구", "개발연구"])
        res["rnd_stage"] = rnd_match[0] if rnd_match else ""
        res["ai_domains"] = self._match_keywords(text, ["국방", "의료", "제조", "교육", "금융", "행정"])

        # -------------------------------------------------------------
        # 6. 교차 검증 (Cross-Validation)
        # -------------------------------------------------------------
        self._cross_validate(res, main_content or "", sub_dept_map, sub_budget_map)

        return res

    # =================================================================
    # 내부 유틸리티 및 헬퍼 메서드
    # =================================================================
    def _assemble_sub_data(self, res, dept_map, budget_map):
        all_keys = set(dept_map.keys()) | set(budget_map.keys())
        for name in all_keys:
            clean_name = re.sub(r'^[·\-\s]*', '', name)
            d = dept_map.get(name, {"managing_dept": "", "implementing_agency": ""})
            b = budget_map.get(name, {"budget_2024": 0.0, "budget_2025": 0.0, "budget_2026": 0.0})
            
            res["sub_projects"].append({
                "parent_id": res["code"], # 내역사업 내부로 parent_id 이동
                "name": clean_name,
                "budget_2024": b["budget_2024"],
                "budget_2025": b["budget_2025"],
                "budget_2026": b["budget_2026"]
            })
            res["project_managers"].append({
                "sub_project": clean_name,
                "managing_dept": d["managing_dept"],
                "implementing_agency": d["implementing_agency"],
                "manager": None, "phone": None
            })

    def _get_vertical_val(self, rows: list, headers: list, key: str, start_row: int, end_row: int) -> str:
        if key not in headers: return ""
        idx = headers.index(key)
        val = ""
        for i in range(start_row, min(end_row + 1, len(rows))):
            if idx < len(rows[i]) and rows[i][idx]:
                val += str(rows[i][idx]).strip() + " "
        return val.strip().replace('\n', ' ')

    def _find_idx(self, headers: list, keywords, exclude: str = None) -> int:
        if isinstance(keywords, str): keywords = [keywords]
        for i, h in enumerate(headers):
            if any(k in h for k in keywords):
                if exclude and exclude in h: continue
                return i
        return -1

    def _clean_num(self, val) -> float:
        if not val: return 0.0
        clean = re.sub(r'[^\d.-]', '', str(val).split('\n')[0])
        return float(clean) if clean and clean not in ['-', '.'] else 0.0

    def _slice_block(self, text: str, start_keys: List[str], end_keys: List[str]) -> str:
        if not text: return ""
        start_idx = -1
        for sk in start_keys:
            match = re.search(rf'^\s*[□ㅇ\-\d\.]*\s*{sk}', text, re.MULTILINE)
            if match:
                start_idx = match.end()
                break
        if start_idx == -1: return ""
        end_idx = len(text)
        for ek in end_keys:
            match = re.search(rf'^\s*[□ㅇ\-\d\.]*\s*{ek}', text[start_idx:], re.MULTILINE)
            if match:
                temp_end = start_idx + match.start()
                if temp_end < end_idx: end_idx = temp_end
        return text[start_idx:end_idx].strip()

    def _extract_inline_meta(self, text: str, res: dict):
        cost_m = re.search(r'총사업비\s*[:：]?\s*([^\n]+)', text)
        if cost_m:
            nums = re.findall(r'([\d,]+)(?:백만원|억원)', cost_m.group(1).replace(' ', ''))
            if nums: res["total_cost"]["total"] = self._clean_num(nums[0])
        
        y_match = re.search(r'(?:사업기간|기간).*?(\d{4})년?\s*~\s*([^ \n]+)', text)
        if y_match:
            res["project_period"]["start_year"] = y_match.group(1)
            res["project_period"]["end_year"] = y_match.group(2).replace('년', '').strip()

    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        return [k for k in keywords if k in text]

    def _cross_validate(self, res: dict, main_text: str, dept_map: dict, budget_map: dict):
        errors = []
        code_id = res.get("code", "Unknown")
        if res["unit_project"]["code"] and res["detail_project"]["code"]:
            expected = f"{res['unit_project']['code']}-{res['detail_project']['code']}"
            if code_id != expected: errors.append(f"코드불일치 ({code_id} vs {expected})")
        if errors: logger.warning(f"⚠️ 검증 실패 [{code_id}]: {', '.join(errors)}")

    def _init_result(self) -> Dict[str, Any]:
        """template.json 규격에 맞춘 54개 키의 계층적 초기 구조"""
        return {
            "id": None, "name": "", "project_name": "", "code": "", "department": "", "division": "",
            "account_type": "", "field": None, "sector": None,
            "program": {"code": "", "name": ""},
            "unit_project": {"code": "", "name": ""},
            "detail_project": {"code": "", "name": ""},
            "status": "계속", "support_type": "출연", "implementing_agency": "",
            "subsidy_rate": "0%", "loan_rate": "0%", "is_rnd": False, "is_informatization": False,
            "project_managers": [],
            "budget": {"2024_settlement": 0.0, "2025_original": 0.0, "2026_request": 0.0, "2026_budget": 0.0},
            "project_period": {"start_year": None, "end_year": None, "duration": None, "raw": None},
            "total_cost": {"total": None, "government": None, "raw": None},
            "sub_projects": [], "purpose": "", "description": "", "legal_basis": "",
            "keywords": [], "page_start": None, "page_end": None, "kpi": [], "history": [], "yearly_budgets": [],
            "ai_domains": ["디지털전환(AX)"], "effectiveness": "", "evaluations": "",
            "budget_calculation": [], "execution_detail": {"method": "", "recipients": ""}
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-c", "--config", default="config.yaml")
    args = parser.parse_args()
    BudgetParser(args.config).parse(args.input, args.output)