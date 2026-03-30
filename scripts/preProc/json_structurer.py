# json_structurer.py (v2 - 사업 경계 오탐 수정 + multi 저장 직렬화 수정)
#
# [v2 변경사항]
# BUG-S1: 사업 경계 오탐 수정
#   - 기존: "사업명" in text_content (부분 문자열) → 내역사업명/표 헤더에 오탐
#   - 수정: _is_project_start() 전용 메서드
#           "사 업 명\n(N) 사업명 (NNNN-NNN)" 제목 패턴만 허용
# BUG-S2: _get_project_id() 코드 오인식 보완
#   - 괄호 내 패턴 우선 매칭으로 예산금액 오인식 감소
# BUG-S3: save() multi 모드 직렬화 누락
#   - projects: Dict[str, ProjectData] → 각 ProjectData.model_dump() 처리

import json
import re
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel

# -------------------------
# Pydantic Models for Schema
# -------------------------
class ProjectData(BaseModel):
    pages: List[int] = []
    text: str = ""
    tables: List[Any] = []

class StructuredDocument(BaseModel):
    front: Dict[str, Any] = {"pages": [], "text": ""}
    projects: Dict[str, ProjectData] = {}
    tail: Dict[str, Any] = {"pages": [], "text": ""}

# -------------------------
# Main Processor
# -------------------------
class JsonStructurer:
    def __init__(self, input_path: Path):
        self.input_path = input_path
        if not input_path.exists():
            raise FileNotFoundError(f"❌ 파일을 찾을 수 없습니다: {input_path}")
            
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        self.pages = raw_data.get('pages', [])
        self.total_pages_in_raw = len(self.pages)

    def _get_project_id(self, text: str) -> Optional[str]:
        """보조용: 본문 어딘가의 NNNN-NNN 패턴 반환 (괄호 내 우선)."""
        m = re.search(r'\((\d{4}-\d{3,4})\)', text)
        if m:
            return m.group(1)
        m = re.search(r'(\d{4}-\d{3})', text)
        return m.group(1) if m else None

    def _is_project_start(self, text: str) -> Optional[str]:
        """
        사업 시작 페이지 정밀 판정.
        '사 업 명' 단독 줄 바로 다음에 '(N) 사업명 (NNNN-NNN)' 패턴이 있을 때만 코드 반환.
        단순 '사업명' 부분 문자열(가. 예산 총괄표 헤더, 내역사업명 등) 오탐 방지.
        """
        m = re.search(
            r'사\s*업\s*명\s*\n\s*(?:\(\d+\))?\s*.+?\((\d{4}-\d{3,4})\)',
            text
        )
        return m.group(1) if m else None

    # [수정 1] tail_start_keyword를 Optional로 변경
    def process(self, tail_start_keyword: Optional[str] = None, dry_run: bool = False) -> Optional[StructuredDocument]:
        doc = StructuredDocument()
        current_section = "front"
        current_project_id = None
        
        duplicate_ids = []
        project_toc = [] # [수정 2] 경계 검증용 목차 (ID, 시작페이지)

        clean_keyword = tail_start_keyword.replace(" ", "") if tail_start_keyword else None

        for page in self.pages:
            p_num = page.get('page_number', 0)
            text = page.get('text', '') or ""
            text_content = text.replace(" ", "")

            raw_tables = page.get('tables', [])
            normalized_tables = []
            for t in raw_tables:
                rows = t.get('rows', t) if isinstance(t, dict) else t
                normalized_tables.append(rows)

            # [수정 1] clean_keyword가 존재할 때만 Tail 판정 수행 (없으면 평생 Tail 진입 불가)
            if clean_keyword and current_section != "tail" and clean_keyword in text_content:
                current_section = "tail"
            
            # Project 판정 (BUG-S1 수정: 정밀 패턴으로 오탐 방지)
            elif current_section != "tail":
                p_id = self._is_project_start(text)   # 사업명+코드 제목 줄 패턴만 허용
                if p_id:
                    current_section = "projects"
                    current_project_id = p_id
                    if p_id in doc.projects:
                        duplicate_ids.append(f"Page {p_num}: {p_id}")
                    else:
                        doc.projects[p_id] = ProjectData()
                        project_toc.append((p_id, p_num)) # 새 사업 시작 페이지 기록

            # 데이터 분배
            if current_section == "front":
                doc.front["pages"].append(p_num)
                doc.front["text"] += text
            elif current_section == "projects":
                target = doc.projects[current_project_id]
                target.pages.append(p_num)
                target.text += text
                target.tables.extend(normalized_tables)
            elif current_section == "tail":
                doc.tail["pages"].append(p_num)
                doc.tail["text"] += text

        # 통계 산출 (목차 데이터 포함)
        metrics = self._calculate_metrics(doc, duplicate_ids, project_toc)
        self._print_report(metrics, is_dryrun=dry_run)

        return None if dry_run else doc

    def _calculate_metrics(self, doc: StructuredDocument, duplicates: List[str], toc: List[Tuple[str, int]]) -> Dict:
        f_pages = doc.front["pages"]
        t_pages = doc.tail["pages"]
        all_p_pages = [p for proj in doc.projects.values() for p in proj.pages]
        
        return {
            "original_total": self.total_pages_in_raw,
            "front_info": (len(f_pages), f"{f_pages[0]}~{f_pages[-1]}" if f_pages else "N/A"),
            "projects_info": (len(doc.projects), len(all_p_pages), f"{all_p_pages[0]}~{all_p_pages[-1]}" if all_p_pages else "N/A"),
            "tail_info": (len(t_pages), f"{t_pages[0]}~{t_pages[-1]}" if t_pages else "N/A"),
            "sum_check": len(f_pages) + len(all_p_pages) + len(t_pages),
            "duplicates": duplicates,
            "toc": toc
        }

    # [수정 2] Dryrun 시 목차 출력 기능 강화
    def _print_report(self, m: Dict, is_dryrun: bool = False):
        print("\n" + "═"*60)
        print(" 🔍 [경계 검증 및 무결성 리포트]")
        print("═"*60)
        print(f" 1. Front 영역 : {m['front_info'][0]:3}p (페이지: {m['front_info'][1]})")
        print(f" 2. Projects   : {m['projects_info'][0]:3}개 (페이지: {m['projects_info'][2]})")
        print(f" 3. Tail 영역  : {m['tail_info'][0]:3}p (페이지: {m['tail_info'][1]})")
        print("─"*60)
        print(f" ✅ 원본 페이지 합계 : {m['original_total']}p")
        print(f" ✅ 분류 페이지 합계 : {m['sum_check']}p")
        
        status = "정상" if m['original_total'] == m['sum_check'] else "⚠️ 불일치 (누락 발생)"
        print(f" ✅ 무결성 검증 : {status}")
        
        if m['duplicates']:
            print(f" ⚠️ 중복 사업코드 발견: {m['duplicates']}")

        # Dryrun일 경우 감지된 사업 시작 페이지 목록 출력 (처음과 끝 위주)
        if is_dryrun and m['toc']:
            print("─"*60)
            print(" 📋 [감지된 사업 시작점 검증 (TOC)]")
            toc = m['toc']
            # 너무 길면 앞뒤 5개씩만 출력
            display_toc = toc if len(toc) <= 10 else toc[:5] + [("...", "...")] + toc[-5:]
            for idx, item in enumerate(display_toc):
                if item[0] == "...":
                    print("    ... (중략) ...")
                else:
                    real_idx = idx + 1 if item[0] != "..." and idx < 5 else len(toc) - (len(display_toc) - idx - 1)
                    print(f"    {real_idx:02d}. 사업코드: {item[0]} (시작: {item[1]}p)")
            print(f"    * 총 {len(toc)}개 사업 감지 완료")

        print("═"*60 + "\n")

    def save(self, doc: StructuredDocument, mode: str):
        base_path = self.input_path.parent / self.input_path.stem
        
        if mode == "single":
            output_file = base_path.with_name(f"{base_path.name}_structured.json")
            content = doc.dict() if hasattr(doc, 'dict') else doc.model_dump()
            output_file.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding='utf-8')
            print(f"💾 단일 파일 저장: {output_file}")
            
        elif mode == "multi":
            for part in ["front", "projects", "tail"]:
                output_file = base_path.with_name(f"{base_path.name}_{part}_structured.json")
                part_data = getattr(doc, part)
                # BUG-S3 수정: projects는 Dict[str, ProjectData] → 각 값을 개별 직렬화
                if part == "projects":
                    serialized = {
                        k: (v.model_dump() if hasattr(v, "model_dump") else
                            v.dict()       if hasattr(v, "dict")       else v)
                        for k, v in part_data.items()
                    }
                else:
                    serialized = (part_data.model_dump() if hasattr(part_data, "model_dump") else
                                  part_data.dict()       if hasattr(part_data, "dict")       else
                                  part_data)
                output_file.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f"💾 분할 파일 저장: {output_file}")

# -------------------------
# CLI 실행부
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="PDF 추출 데이터를 논리적 구조로 재편성 및 검증")
    parser.add_argument("-i", "--input", required=True, help="입력 raw.json 파일")
    # [수정 1] required=False 로 변경하여 옵션화
    parser.add_argument("-k", "--keyword", required=False, default=None, help="Tail 영역 시작 키워드 (없으면 생략)")
    parser.add_argument("-m", "--mode", choices=["single", "multi"], default="single", help="저장 모드")
    parser.add_argument("--dryrun", action="store_true", help="파일 생성 없이 구역 경계 검증 리포트만 출력")
    
    args = parser.parse_args()
    input_path = Path(args.input)
    
    structurer = JsonStructurer(input_path)
    result = structurer.process(args.keyword, dry_run=args.dryrun)
    
    if result and not args.dryrun:
        structurer.save(result, args.mode)

if __name__ == "__main__":
    main()