"""
================================================================================
[Budget Data 통합 파이프라인 관리자 (Pipeline Manager)]
파일명: main_cli.py

이 스크립트는 예산서 PDF 원본 파일부터 최종 데이터베이스 적재용 JSON을 생성하기까지의 
모든 데이터 정제 및 추출 공정을 중앙에서 제어하고 자동화하는 '통합 관제탑'입니다.

💡 핵심 기능 (Smart Features)
  1. 스마트 폴더/파일 감지: 
     단일 파일뿐만 아니라 특정 폴더를 통째로 입력해도 내부의 처리 대상 파일을 모두 찾아냅니다.
  
  2. 스마트 점프 (진행 상태 추적 및 자동 재개): 
     동일한 이름(Base name)을 가진 파일들을 그룹화하여 "가장 진도가 많이 나간 파일"을 찾습니다.
     - PDF만 있는 경우: Step 1 (처음부터) 가동
     - xxx_raw.json이 있는 경우: 가장 오래 걸리는 Step 1(PDF 파싱)을 패스하고 Step 2부터 재개
     - xxx_structured.json이 있는 경우: Step 1, 2를 패스하고 Step 3(예산 파싱) 단독 가동

  3. 대화형 데이터 검증 (Human-in-the-loop):
     각 단계가 끝날 때마다 무결성 리포트(TOC, 페이지 합계 등)를 출력하고 
     사용자의 진행 승인(y/n)을 받습니다. (-y 옵션 사용 시 묻지 않고 논스톱 일괄 진행)

🚀 파이프라인 단계 (Pipeline Steps)
  - Step 1 [Raw 추출] : pdf_to_json.py 호출 -> PDF 텍스트/표 무손실 추출 (input/raw/ 경로 저장)
  - Step 2 [논리 분할]: json_structurer.py 호출 -> Front/Projects/Tail 구조로 쪼갬 (tmp/ 경로 저장)
  - Step 3 [예산 파싱]: budget_parser.py 호출 -> 37개 스키마 기반 데이터 최종 추출 (result/ 경로 저장)

⚙️ 사용법 (Usage)
  $ python main_cli.py -i <파일명 또는 폴더명> [-k <Tail키워드>] [-c <설정파일>] [-y]
  
  (예시)
  - 폴더 통째로 돌리기: python main_cli.py -i src/
  - 중간 정제파일만 돌리기: python main_cli.py -i tmp/sample_raw.json
  - 확인창 없이 논스톱 처리: python main_cli.py -i src/ -y
================================================================================
"""
import argparse
import sys
import json
from pathlib import Path

# 모듈 임포트
from pdf_to_json import PdfToJsonConverter
from json_structurer import JsonStructurer
from budget_parser import BudgetParser

class PipelineManager:
    def __init__(self, args):
        self.args = args
        
        # 💡 [핵심] 프로젝트 루트 동적 추적
        # Path(__file__).resolve() = 현재 이 스크립트의 절대 경로 (.../scripts/preProc/main_cli.py)
        # .parent.parent.parent = scripts -> project_root 로 이동
        self.script_dir = Path(__file__).resolve().parent
        self.project_root = self.script_dir.parent.parent
        
        # 💡 [핵심] 새로운 data 폴더 구조에 맞춘 절대 경로 맵핑
        self.data_dir = self.project_root / "database"
        self.src_dir = self.data_dir / "src"
        self.raw_dir = self.data_dir / "raw"
        self.structure_dir = self.data_dir / "structure"
        self.parse_result_dir = self.data_dir / "parse_result"
        
        # 기본 config 경로 (루트의 config 폴더)
        self.default_config_path = self.project_root / "config" / "config.yaml"

        # 작업에 필요한 폴더들이 없으면 자동 생성
        for d in [self.src_dir, self.raw_dir, self.structure_dir, self.parse_result_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def ask_proceed(self, step_name: str) -> bool:
        """사용자에게 y/n 승인을 받습니다. (-y 옵션 시 자동 패스)"""
        if self.args.yes:
            return True
        res = input(f"\n▶ [{step_name}] 단계를 진행하시겠습니까? (y/n): ").lower()
        return res in ['y', 'yes']

    def run(self):
        target_path = Path(self.args.input)
        if not target_path.exists():
            print(f"❌ 입력 경로를 찾을 수 없습니다: {target_path}")
            sys.exit(1)

        files_to_process = []

        if target_path.is_file():
            files_to_process.append(target_path)
        elif target_path.is_dir():
            print(f"📂 폴더 모드 가동: {target_path}")
            for ext in ['*.pdf', '*_raw.json', '*_structured.json']:
                files_to_process.extend(target_path.rglob(ext))

        if not files_to_process:
            print("❌ 처리할 수 있는 문서가 없습니다.")
            sys.exit(1)

        # 파일 그룹화 (동일 사업명으로 묶음)
        projects = {}
        for f in files_to_process:
            base_name = f.stem.replace('_raw', '').replace('_structured', '')
            if base_name not in projects:
                projects[base_name] = []
            projects[base_name].append(f)

        print(f"🔍 총 {len(projects)}개의 독립된 문서를 감지했습니다.\n")

        for idx, (base_name, flist) in enumerate(projects.items(), start=1):
            print("═"*60)
            print(f"📄 [문서 {idx}/{len(projects)}] {base_name} 파이프라인 가동")
            
            # 우선순위: structured > raw > pdf (가장 진도 나간 것 기준)
            best_file = None
            structured_file = next((f for f in flist if "_structured.json" in f.name), None)
            raw_file = next((f for f in flist if "_raw.json" in f.name), None)
            pdf_file = next((f for f in flist if f.suffix.lower() == ".pdf"), None)

            if structured_file:   best_file = structured_file
            elif raw_file:        best_file = raw_file
            elif pdf_file:        best_file = pdf_file
            else: continue

            # 단일 문서 처리
            self._process_single(best_file, base_name)

        print("\n🎉 전체 파이프라인 작업이 완료되었습니다.")

    def _process_single(self, input_path: Path, base_name: str):
        ext = input_path.suffix.lower()
        
        # 각 단계별 목표 파일 경로 (고정)
        raw_json_path = self.raw_dir / f"{base_name}_raw.json"
        structured_json_path = self.structure_dir / f"{base_name}_structured.json"
        final_out_path = self.parse_result_dir / f"{base_name}_parsed.json"

        # 입력 파일에 따른 상태 세팅
        current_raw = None
        current_struct = None

        if ext == '.pdf':
            pass # 처음부터 시작
        elif ext == '.json':
            if "_structured" in input_path.name:
                current_struct = input_path
            else:
                current_raw = input_path

        # ==========================================
        # ⚙️ Step 1: PDF to Raw JSON
        # ==========================================
        if ext == '.pdf':
            if raw_json_path.exists():
                print(f"ℹ️ Step 1 패스: 이미 추출된 Raw 파일이 존재합니다. ({raw_json_path.name})")
                current_raw = raw_json_path
            else:
                # [수정됨] Step 1에도 반드시 묻고 진행하도록 수정
                if self.ask_proceed(f"Step 1: PDF 원본 추출 ({base_name}.pdf)"):
                    print(f"⏳ 추출 중... ({raw_json_path.name})")
                    doc = PdfToJsonConverter.extract_data(input_path)
                    if doc:
                        content = doc.dict() if hasattr(doc, 'dict') else doc.model_dump()
                        raw_json_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding='utf-8')
                        current_raw = raw_json_path
                else:
                    print("사용자 취소로 해당 문서 처리를 중단합니다.")
                    return

        # ==========================================
        # ⚙️ Step 2: Structuring (구조화)
        # ==========================================
        if current_raw and not current_struct:
            if structured_json_path.exists():
                print(f"ℹ️ Step 2 패스: 이미 구조화된 파일이 존재합니다. ({structured_json_path.name})")
                current_struct = structured_json_path
            else:
                if self.ask_proceed(f"Step 2: 논리 구조화 및 목차 검증 ({current_raw.name})"):
                    structurer = JsonStructurer(current_raw)
                    keyword = self.args.keyword if self.args.keyword else None
                    
                    doc_struct = structurer.process(keyword, dry_run=False)
                    if doc_struct:
                        content = doc_struct.dict() if hasattr(doc_struct, 'dict') else doc_struct.model_dump()
                        structured_json_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding='utf-8')
                        current_struct = structured_json_path
                        print(f"✅ Step 2 완료: {structured_json_path.name}")
                else:
                    print("사용자 취소로 해당 문서 처리를 중단합니다.")
                    return

        # ==========================================
        # ⚙️ Step 3: Budget Parsing (최종 추출)
        # ==========================================
        if current_struct:
            if final_out_path.exists():
                print(f"ℹ️ Step 3 패스: 최종 파싱 결과물이 이미 존재합니다. ({final_out_path.name})")
            else:
                if self.ask_proceed(f"Step 3: 37개 스키마 예산 데이터 추출 ({current_struct.name})"):
                    print(f"⏳ 파싱 엔진 가동 중... ({current_struct.name})")
                    parser = BudgetParser(self.args.config)
                    parser.parse(str(current_struct), str(self.parse_result_dir))
                    
                    temp_merged = self.parse_result_dir / "merged.json"
                    if temp_merged.exists():
                        temp_merged.rename(final_out_path)
                        print(f"✅ Step 3 완료: {final_out_path.name}")

def main():
    parser = argparse.ArgumentParser(description="Budget Data 통합 파이프라인 CLI")
    
    # 💡 [수정] 입력(-i)을 생략하면 기본값으로 data/src/ 폴더를 바라보도록 설정
    # (매번 -i .\data\src\ 안 쳐도 됨!)
    pipeline_dummy = PipelineManager(argparse.Namespace()) # 경로만 빌려오기 위한 더미
    parser.add_argument("-i", "--input", default=str(pipeline_dummy.src_dir), help="입력 파일/폴더 (기본: data/src)")
    parser.add_argument("-k", "--keyword", required=False, default=None, help="Tail 영역 시작 키워드 (선택)")
    parser.add_argument("-c", "--config", default=str(pipeline_dummy.default_config_path), help="설정 파일 경로")
    parser.add_argument("-y", "--yes", action="store_true", help="승인 없이 일괄 진행")
    
    args = parser.parse_args()
    PipelineManager(args).run()

if __name__ == "__main__":
    main()