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
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.base_year = self.config.get('years', {}).get('base_year', 2026)

    def parse(self, input_path: str, output_path: str):
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
        text = project_data.get("text", "")
        tables = project_data.get("tables", [])
        pages = project_data.get("pages", [])
        
        res = self._init_result()
        if pages:
            res["page_start"], res["page_end"] = pages[0], pages[-1]

        # -------------------------------------------------------------
        # 1. 메타데이터: 사업명 및 코드 (오탐 방지)
        # -------------------------------------------------------------
        title_match = re.search(r'(?:^|\n)\s*사\s*업\s*명\s*[:：]?\s*[\r\n]*\s*(?:\(\d+\)|\[\d+\]|\d+\.)?\s*([^\n]+?)\s*\((\d{4}-\d{3,4})\)', text)
        if title_match:
            res["project_name"] = title_match.group(1).strip()
            res["code"] = title_match.group(2).strip()
            res["id"] = f"{self.base_year}_{res['code']}"

        if res["project_name"]:
            if "R&D" in res["project_name"].upper(): res["is_rnd"] = True
            if "정보화" in res["project_name"]: res["is_informatization"] = True
       
        # -------------------------------------------------------------
        # 2. 2D 표(Table) 전수 파싱 (독립 파싱 로직 적용)
        # -------------------------------------------------------------
        sub_dept_map = {}
        sub_budget_map = {}
        # 동그라미, 체크 기호를 모두 포함하는 강력한 정규식 (소문자o 오탐지 방지 적용 완료)
        chk_pattern = re.compile(r'[OΟV☑■o○●〇v✔]')

        for t in tables:
            rows = t.get('rows', []) if isinstance(t, dict) else t
            if not rows or len(rows) < 2: continue
            
            clean_row0 = [str(c).replace(" ", "").replace("\n", "").strip() if c else "" for c in rows[0]]
            h_str = "".join(clean_row0)
            
            # 💡 [핵심] 헤더가 1행과 2행에 쪼개져 있는 경우를 대비한 확장 검색 문자열
            h_str_extended = "".join([str(c).replace(" ", "").replace("\n", "") for r in rows[:2] for c in r if c])

            # [1] 기본 메타데이터 (이 두 개는 보통 표가 명확히 나뉘어 있으므로 if-elif 체인 유지)
            if "회계" in h_str and "소관" in h_str:
                res["account_type"] = self._get_vertical_val(rows, clean_row0, "회계", 1, 2)
                res["department"] = self._get_vertical_val(rows, clean_row0, "소관", 1, 2)
                res["division"] = self._get_vertical_val(rows, clean_row0, "실국(기관)", 1, 2)
                res["field"] = self._get_vertical_val(rows, clean_row0, "분야", 1, 1)
                res["sector"] = self._get_vertical_val(rows, clean_row0, "부문", 1, 1)
                
            elif "프로그램" in h_str and "단위사업" in h_str:
                res["program"]["code"] = self._get_vertical_val(rows, clean_row0, "프로그램", 1, 1)
                res["program"]["name"] = self._get_vertical_val(rows, clean_row0, "프로그램", 2, 2)
                res["unit_project"]["code"] = self._get_vertical_val(rows, clean_row0, "단위사업", 1, 1)
                res["unit_project"]["name"] = self._get_vertical_val(rows, clean_row0, "단위사업", 2, 2)
                res["detail_project"]["code"] = self._get_vertical_val(rows, clean_row0, "세부사업", 1, 1)
                res["detail_project"]["name"] = self._get_vertical_val(rows, clean_row0, "세부사업", 2, 2)

            # 💡 [2] 상태값 (여기서부터 모두 독립된 if문으로 사슬을 끊음)
            if "신규" in h_str_extended and "계속" in h_str_extended:
                header_combined = [str(rows[0][i] or "") + str(rows[1][i] if len(rows)>1 else "") for i in range(len(rows[0]))]
                for key in ["신규", "계속", "완료"]:
                    idx = self._find_idx(header_combined, key)
                    if idx != -1:
                        for r_idx in range(1, min(4, len(rows))):
                            # None이 "None" 문자열이 되어 소문자 'o'로 오탐지되는 버그 방지
                            val = str(rows[r_idx][idx] or "")
                            if val and chk_pattern.search(val):
                                res["status"] = key
                                break
                    if res["status"]: break

            # 💡 [3] 지원 형태 (독립된 if문, "율" 제외 로직 적용)
            if "출연" in h_str and "보조" in h_str:
                for key in ["직접", "출자", "출연", "보조", "융자"]:
                    idx = self._find_idx(clean_row0, key, exclude="율")
                    if idx != -1:
                        for r_idx in range(1, min(4, len(rows))):
                            val = str(rows[r_idx][idx] or "")
                            if val and chk_pattern.search(val):
                                if key not in res["support_type"]:
                                    res["support_type"].append(key)
                                break
                res["subsidy_rate"] = self._clean_num(self._get_vertical_val(rows, clean_row0, "국고보조율(%)", 1, 1))
                res["loan_rate"] = self._clean_num(self._get_vertical_val(rows, clean_row0, "융자율(%)", 1, 1))

            # 💡 [4] 소관부처 및 시행주체 (독립된 if문)
            # BUG-P4: h_str_extended 사용 → 헤더가 병합셀로 2열에 나뉜 경우도 감지
            if "소관부처" in h_str_extended or "사업시행주체" in h_str_extended:
                current_sub_name = ""
                for r in rows[1:]:
                    col0 = str(r[0]).replace('\n', ' ').strip() if r[0] else ""
                    col1 = str(r[1]).replace(' ', '').strip() if len(r) > 1 and r[1] else ""
                    col2 = str(r[2]).replace('\n', ' ').strip() if len(r) > 2 and r[2] else ""
                    
                    # col0에 사업명이 있으면 현재 내역사업 갱신 (병합셀 이전값 승계)
                    if col0 and col0 not in ["사업명", "구분"]:
                        # \n 포함 병합 사업명 → 첫 줄만 사업명으로 사용
                        current_sub_name = col0.split('\n')[0].strip()
                        if current_sub_name not in sub_dept_map:
                            sub_dept_map[current_sub_name] = {"managing_dept": "", "implementing_agency": ""}
                    if current_sub_name:
                        if "소관부처" in col1:
                            sub_dept_map[current_sub_name]["managing_dept"] = col2
                        elif "사업시행주체" in col1 or "시행기관" in col1:
                            sub_dept_map[current_sub_name]["implementing_agency"] = col2

                # 본사업 implementing_agency = 첫 번째 내역사업의 시행주체
                if sub_dept_map and not res["implementing_agency"]:
                    first_sub = list(sub_dept_map.keys())[0]
                    res["implementing_agency"] = sub_dept_map[first_sub].get("implementing_agency", "")

            # 💡 [5] 지출계획 총괄표 (독립된 if문)
            # BUG-P5: "결산"+"예산"+"증감" 조건이 "사업 성격" 표의 "예산사업" 문자에 오탐됨
            # → "요구안" 또는 "본예산(B)"를 추가 필수 조건으로 강화 (총괄표에만 존재하는 고유 키워드)
            h_str_ext_full = "".join(str(c).replace(" ","").replace("\n","") for r in rows[:2] for c in r if c)
            if ("결산" in h_str_ext_full and "요구안" in h_str_ext_full and
                    (f"{self.base_year}" in h_str_ext_full or "본예산(B)" in h_str_ext_full)):
                # combined: row[0] + row[1] 열별 결합
                n_cols = len(rows[0])
                header_combined = [
                    (str(rows[0][i] or "") + str(rows[1][i] if len(rows) > 1 and i < len(rows[1]) else ""))
                    .replace('\n', '').replace(' ', '')
                    for i in range(n_cols)
                ]
                y2, y1, y0 = self.base_year - 2, self.base_year - 1, self.base_year
                idx_map = {
                    f"{y2}_settlement": self._find_idx(header_combined, [f"{y2}년결산", "결산"]),
                    f"{y1}_original":   self._find_idx(header_combined, "본예산", exclude="B"),
                    f"{y1}_supplementary": self._find_idx(header_combined, ["추경*(A)", "추경(A)", "추경"]),
                    f"{y0}_request":    self._find_idx(header_combined, "요구안"),
                    f"{y0}_budget":     self._find_idx(header_combined, ["본예산(B)", "본예산B", "정부안"]),
                }
                # 데이터 행: 숫자가 3개 이상이고 사업명/헤더 행이 아닌 첫 번째 행
                for r in rows[1:]:
                    if sum(1 for c in r if re.search(r'\d', str(c or ""))) >= 3 \
                            and not any(k in str(r[0] or "") for k in ["사업명", "결산", "예산", "구분"]):
                        for k, idx in idx_map.items():
                            if idx != -1 and idx < len(r):
                                res["budget"][k] = self._clean_num(r[idx])
                        break

            # 💡 [6] 기능별(내역사업별) 계획 내역 (독립된 if문)
            # BUG-P6: 병합 셀로 내역사업명·금액이 \n 구분 한 셀에 묶임 → 행 단위 순회 불가
            # → 연도 anchor 기반 컬럼 탐색 + col[0] \n 분해로 내역사업명·금액 동시 추출
            # 결산표(표15)와 구분: "다음연도이월액"이 있으면 결산표이므로 skip
            is_func_table = (
                "예산액" in h_str_ext_full and
                "집행액" in h_str_ext_full and
                "이월액" in h_str_ext_full and
                "다음연도" not in h_str_ext_full and   # 결산표 제외
                "집행률" not in h_str_ext_full          # 결산표 제외
            )
            if is_func_table:
                n_cols = len(rows[0])
                combined = [
                    (str(rows[0][i] or "") + str(rows[1][i] if len(rows) > 1 and i < len(rows[1]) else ""))
                    .replace('\n', '').replace(' ', '')
                    for i in range(n_cols)
                ]
                y2, y1, y0 = self.base_year - 2, self.base_year - 1, self.base_year

                # 연도 anchor: 헤더에서 연도 숫자가 처음 등장하는 열 인덱스
                anchors: Dict[int, int] = {}
                for i, h in enumerate(combined):
                    for yr in [y2, y1, y0]:
                        if str(yr) in h and yr not in anchors:
                            anchors[yr] = i

                # 컬럼 인덱스 결정
                # y2: anchor+2(집행액), y1: anchor+1(예산현액), y0: 마지막 컬럼(예산)
                idx_y2 = anchors.get(y2, -1) + 2 if y2 in anchors else -1
                idx_y1 = anchors.get(y1, -1) + 1 if y1 in anchors else -1
                idx_y0 = anchors.get(y0, n_cols - 1) if y0 in anchors else n_cols - 1

                BULLETS = set('·․・\u00b7\uff65·')

                def _split_sub_names(raw: str) -> List[str]:
                    """병합 셀 col[0]에서 내역사업명 목록 추출 (가운뎃점·기호 기준 분리)"""
                    names, buf = [], ""
                    for line in raw.split('\n'):
                        line = line.strip()
                        if not line:
                            continue
                        first = line[0] if line else ""
                        # 합계/소계 행 skip
                        if first in ('○', 'ο', 'O') and any(k in line for k in ['합계', '소계', '총계']):
                            continue
                        if first in BULLETS or line.startswith('·') or line.startswith('·'):
                            if buf:
                                names.append(buf.strip())
                            buf = re.sub(r'^[·\-\s\.]+', '', line).strip()
                        else:
                            buf += (" " + line) if buf else line
                    if buf:
                        names.append(buf.strip())
                    return [re.sub(r'^[·\-\s\.]+', '', n) for n in names if n]

                def _split_amounts(raw: str, skip_first: bool = True) -> List[str]:
                    """병합 셀 금액 컬럼 분해 (첫 줄=합계이므로 기본 제외)"""
                    vals = [v.strip() for v in str(raw or "").split('\n') if v.strip()]
                    return vals[1:] if skip_first and len(vals) > 1 else vals

                # 데이터 행(병합 셀)은 rows[2] (row[0]=헤더1, row[1]=헤더2, row[2]=데이터)
                for r in rows[2:]:
                    col0 = str(r[0] or "")
                    # 합계 행만 있거나 내역사업명이 없으면 skip
                    if not col0.strip():
                        continue

                    names = _split_sub_names(col0)
                    if not names:
                        continue

                    y2_amts = _split_amounts(r[idx_y2]) if idx_y2 != -1 and idx_y2 < len(r) else []
                    y1_amts = _split_amounts(r[idx_y1]) if idx_y1 != -1 and idx_y1 < len(r) else []
                    y0_amts = _split_amounts(r[idx_y0]) if idx_y0 < len(r) else []

                    for i, name in enumerate(names):
                        clean_name = re.sub(r'^[·\-\s\.]+', '', name).strip()
                        if not clean_name or any(k in clean_name for k in ["합계", "소계", "총계"]):
                            continue
                        if clean_name not in sub_budget_map:
                            sub_budget_map[clean_name] = {}
                        val_y2 = self._clean_num(y2_amts[i]) if i < len(y2_amts) else 0.0
                        val_y1 = self._clean_num(y1_amts[i]) if i < len(y1_amts) else 0.0
                        val_y0 = self._clean_num(y0_amts[i]) if i < len(y0_amts) else 0.0
                        # 모든 금액이 0이면 내역사업이 아닌 잡음 행 → skip
                        if val_y2 == 0.0 and val_y1 == 0.0 and val_y0 == 0.0:
                            continue
                        if val_y2 > 0: sub_budget_map[clean_name][f"budget_{y2}"] = val_y2
                        if val_y1 > 0: sub_budget_map[clean_name][f"budget_{y1}"] = val_y1
                        if val_y0 > 0: sub_budget_map[clean_name][f"budget_{y0}"] = val_y0

            # 💡 [7] 성과지표 KPI (독립된 if문)
            if "지표명" in h_str and "목표" in h_str:
                idx_name = self._find_idx(clean_row0, "지표명")
                idx_target = self._find_idx(clean_row0, ["목표", f"{self.base_year}"])
                for r in rows[1:]:
                    if idx_name != -1 and idx_name < len(r) and r[idx_name]:
                        res["kpi"].append({
                            "parent_code": res.get("code", ""),
                            "indicator_name": str(r[idx_name]).replace('\n', ' ').strip(),
                            "target_value": str(r[idx_target]).replace('\n', ' ').strip() if idx_target != -1 and idx_target < len(r) else ""
                        })

            # 💡 [8] 연도별 사업추진 경과 History (독립된 if문)
            if "연도" in h_str and ("경과" in h_str or "내용" in h_str):
                idx_year = self._find_idx(clean_row0, "연도")
                idx_desc = self._find_idx(clean_row0, ["경과", "내용"])
                for r in rows[1:]:
                    if idx_year != -1 and idx_year < len(r) and r[idx_year]:
                        y_val = self._clean_num(r[idx_year])
                        if y_val > 0:
                            res["history"].append({
                                "parent_code": res.get("code", ""),
                                "year": int(y_val),
                                "description": str(r[idx_desc]).replace('\n', ' ').strip() if idx_desc != -1 and idx_desc < len(r) else ""
                            })

            # 💡 [9] 결산액 Yearly Budgets (독립된 if문)
            if "결산액" in h_str or "집행액" in h_str:
                idx_year = self._find_idx(clean_row0, ["연도", "구분"])
                idx_amt = self._find_idx(clean_row0, ["결산액", "집행액"])
                for r in rows[1:]:
                    if idx_year != -1 and idx_year < len(r) and str(r[idx_year]).strip().isdigit():
                        res["yearly_budgets"].append({
                            "parent_code": res.get("code", ""),
                            "year": int(str(r[idx_year]).strip()),
                            "settlement_amount": self._clean_num(r[idx_amt]) if idx_amt != -1 and idx_amt < len(r) else 0.0
                        })

        self._assemble_sub_data(res, sub_dept_map, sub_budget_map)

        # -------------------------------------------------------------
        # 3. 텍스트 목차 슬라이싱
        # -------------------------------------------------------------
        res["purpose"] = self._slice_block(text, ["사업목적", "사업개요", "목적및내용"], ["법령상근거", "사업근거", "추진경위", "주요내용", "사업규모"])
        res["legal_basis"] = self._slice_block(text, ["법령상근거", "사업근거", "추진경위"], ["주요내용", "사업규모", "산출근거", "산출내역"])
        
        main_content = self._slice_block(text, ["주요내용", "사업내용", "사업규모"], ["산출근거", "산출내역", "사업효과", "기대효과"])
        res["description"] = main_content
        
        res["budget_calculation"] = self._slice_block(text, ["산출근거", "산출내역"], ["사업효과", "기대효과", "타당성조사", "각종평가", "집행절차"])
        res["effectiveness"] = self._slice_block(text, ["사업효과", "기대효과"], ["타당성조사", "집행절차", "각종평가", "결산내역"])
        res["evaluations"] = self._slice_block(text, ["각종평가", "타당성조사", "국회지적"], ["결산내역", "결산표"])
        
        self._extract_inline_meta(main_content or text, res)
        
        rec_text = self._slice_block(main_content or text, ["사업수혜자", "정책수혜자"], ["보조율", "지원비율", "법적근거", "산출근거", "산출내역"])
        res["execution_detail"]["recipients"] = rec_text.replace('\n', ' ').strip()
        
        method_text = self._slice_block(text, ["사업집행절차", "집행절차"], ["각종평가", "결산내역"])
        if method_text:
            res["execution_detail"]["method"] = method_text.replace('\n', ' ').strip()[:50]

        res["ai_tech_types"] = self._match_keywords(text, ["머신러닝", "딥러닝", "자연어", "비전", "생성형"])
        rnd_match = self._match_keywords(text, ["기초연구", "응용연구", "개발연구"])
        res["rnd_stage"] = rnd_match[0] if rnd_match else ""
        res["ai_domains"] = self._match_keywords(text, ["국방", "의료", "제조", "교육", "금융", "행정"])

        return res

    # =================================================================
    # 내부 유틸리티 및 헬퍼 메서드
    # =================================================================
    def _is_heading(self, text: str, match_start: int, match_end: int) -> bool:
        nl_start = text.rfind('\n', 0, match_start)
        line_start = nl_start + 1 if nl_start != -1 else 0
        nl_end = text.find('\n', match_end)
        line_end = nl_end if nl_end != -1 else len(text)
        
        line = text[line_start:line_end].strip()
        line = re.sub(r'^-\s*\d+\s*-\s*', '', line).strip()
        
        if len(line) > 60: return False
        if line.endswith(('다.', '다', '며,', '고,')): return False
        if len(line) < 40: return True
        if re.match(r'^(?:□|ㅇ|■|○|●|①|②|③|④|⑤|\d+\)|\d+\.|가\.|나\.|다\.|-)', line): return True
        
        return False

    def _slice_block(self, text: str, start_keys: List[str], end_keys: List[str]) -> str:
        if not text: return ""
        start_idx = -1
        for sk in start_keys:
            sk_pattern = r'\s*'.join(list(sk.replace(" ", "")))
            for m in re.finditer(sk_pattern, text):
                if self._is_heading(text, m.start(), m.end()):
                    idx = m.end()
                    if start_idx == -1 or idx < start_idx:
                        start_idx = idx
                    break
        if start_idx == -1: return ""
        
        end_idx = len(text)
        for ek in end_keys:
            ek_pattern = r'\s*'.join(list(ek.replace(" ", "")))
            for m in re.finditer(ek_pattern, text[start_idx:]):
                abs_start = start_idx + m.start()
                abs_end = start_idx + m.end()
                if self._is_heading(text, abs_start, abs_end):
                    nl_pos = text.rfind('\n', start_idx, abs_start)
                    split_pos = nl_pos if nl_pos != -1 else abs_start
                    if split_pos < end_idx:
                        end_idx = split_pos
                    break
        return text[start_idx:end_idx].strip()

    def _assemble_sub_data(self, res, dept_map, budget_map):
        all_keys = set(dept_map.keys()) | set(budget_map.keys())
        y2, y1, y0 = self.base_year-2, self.base_year-1, self.base_year
        for name in all_keys:
            clean_name = re.sub(r'^[·\-\s]*', '', name)
            if not clean_name:
                continue
            d = dept_map.get(name, {"managing_dept": "", "implementing_agency": ""})
            b = budget_map.get(name, {})
            val_y2 = b.get(f"budget_{y2}", 0.0)
            val_y1 = b.get(f"budget_{y1}", 0.0)
            val_y0 = b.get(f"budget_{y0}", 0.0)

            # 예산이 하나라도 있는 경우에만 sub_projects에 추가
            # (dept_map에만 있고 기능별 내역표에 없는 본사업명 잡음 제거)
            if val_y2 > 0 or val_y1 > 0 or val_y0 > 0:
                res["sub_projects"].append({
                    "parent_id": res.get("code", ""),
                    "name": clean_name,
                    f"budget_{y2}": val_y2,
                    f"budget_{y1}": val_y1,
                    f"budget_{y0}": val_y0,
                })

            # project_managers는 예산 유무와 무관하게 항상 추가 (관리자 정보 보존)
            res["project_managers"].append({
                "parent_code": res.get("code", ""),
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

    def _extract_inline_meta(self, text: str, res: dict):
        # 1. 총사업비 추출
        cost_m = re.search(r'총사업비\s*[:：]?\s*([^\n]+)', text)
        if cost_m:
            nums = re.findall(r'([\d,]+)(?:백만원|억원)', cost_m.group(1).replace(' ', ''))
            if nums: res["total_cost"]["total"] = self._clean_num(nums[0])
        
        # 2. 사업기간 추출
        y_match = re.search(r'(?:사업기간|기간).*?(\d{2,4})년?\s*~\s*([^ \n]+)', text)
        if y_match:
            sy_str = y_match.group(1)
            if len(sy_str) == 2:
                sy_int = int(sy_str)
                sy = 2000 + sy_int if sy_int < 50 else 1900 + sy_int
            else:
                sy = int(sy_str)
            res["project_period"]["start_year"] = sy
            res["project_period"]["end_year"] = y_match.group(2).replace('년', '').strip()

        # 💡 [핵심 패치] 3. 텍스트 본문에서 시행주체 직접 추출 (표에서 못 찾았을 경우 완벽 방어)
        if not res.get("implementing_agency"):
            agency_match = re.search(r'사업시행주체\s*[:：]?\s*([^\n]+)', text)
            if agency_match:
                # 불필요한 특수문자 제거 후 깔끔하게 저장
                res["implementing_agency"] = re.sub(r'^[^\w가-힣]+', '', agency_match.group(1)).strip()

    def _match_keywords(self, text: str, keywords: List[str]) -> List[str]:
        return [k for k in keywords if k in text]

    def _init_result(self) -> Dict[str, Any]:
        y2, y1, y0 = self.base_year-2, self.base_year-1, self.base_year
        return {
            "id": None, "project_name": "", "code": "", "department": "", "division": "",
            "implementing_agency": "", "account_type": "", "field": None, "sector": None,
            "program": {"code": "", "name": ""},
            "unit_project": {"code": "", "name": ""},
            "detail_project": {"code": "", "name": ""},
            "status": "", "support_type": [],
            "is_rnd": False, "is_informatization": False,
            "project_period": {"start_year": None, "end_year": None, "duration": None, "raw": None},
            "total_cost": {"total": 0.0, "government": 0.0, "raw": None},
            "budget": {
                f"{y2}_settlement": 0.0, f"{y1}_original": 0.0,
                f"{y1}_supplementary": 0.0, f"{y0}_request": 0.0, f"{y0}_budget": 0.0
            },
            "purpose": "", "description": "", "legal_basis": "",
            "ai_tech_types": [], "rnd_stage": "", "ai_domains": [],
            "page_start": None, "page_end": None, "subsidy_rate": 0.0, "loan_rate": 0.0,
            "execution_detail": {"method": "", "recipients": ""},
            "budget_calculation": "", "effectiveness": "", "evaluations": "",
            "sub_projects": [], "project_managers": [], "kpi": [], "history": [], "yearly_budgets": []
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)
    parser.add_argument("-c", "--config", default="config.yaml")
    args = parser.parse_args()
    BudgetParser(args.config).parse(args.input, args.output)