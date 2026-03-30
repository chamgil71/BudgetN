"""
excel_manager.py
통합 Excel 변환(Export/Import) 매니저
사용법:
  # 내보내기 (JSON -> Excel)
  python scripts/pipeline/excel_manager.py export --type both
  python scripts/pipeline/excel_manager.py export --type summary
  python scripts/pipeline/excel_manager.py export --type a4 --dept 과학기술정보통신부

  # 가져오기 (Excel -> JSON)
  python scripts/pipeline/excel_manager.py import --type both
  python scripts/pipeline/excel_manager.py import --type a4 --file input/abc.xlsx
"""
import sys
import argparse
from pathlib import Path

# 파이프라인 모듈(원본 export/convert 계열 스크립트)과 경로 셋업
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from config import path_config
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))

import export_xlsx
import export_a4
import convert
import convert_a4

def run_export(args, unknown_args):
    """ 내보내기 로직 분기 """
    # 입력 파일이 명시되지 않았다면 웹 폴더의 원본 budget_db.json을 기본값으로 사용
    has_input = any(arg for arg in unknown_args if not arg.startswith('-'))
    if not has_input:
        unknown_args.insert(0, str(path_config.WEB_DATA_DIR / "budget_db.json"))

    if args.type in ('summary', 'both'):
        print("=== [Export: Summary Excel] ===")
        sys.argv = [sys.argv[0]] + unknown_args
        export_xlsx.main()
    if args.type in ('a4', 'both'):
        print("=== [Export: A4 Excel] ===")
        sys.argv = [sys.argv[0]] + unknown_args
        export_a4.main()

def run_import(args, unknown_args):
    """ 변환 로직 분기 (merged.json 업데이트) """
    if args.file:
        unknown_args = [args.file] + unknown_args
    sys.argv = [sys.argv[0]] + unknown_args

    if args.type in ('summary', 'both'):
        print("=== [Import: Summary Excel] ===")
        convert.main()
    if args.type in ('a4', 'both'):
        print("=== [Import: A4 Excel] ===")
        convert_a4.main()

def main():
    parser = argparse.ArgumentParser(description="통합 Excel 매니저 (KAIB2026)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # export 명령어
    export_parser = subparsers.add_parser("export", help="JSON → Excel 생성")
    export_parser.add_argument("--type", choices=['summary', 'a4', 'both'], required=True,
                               help="summary(총괄표), a4(A4요약), both(동시 추출)")

    # import 명령어
    import_parser = subparsers.add_parser("import", help="Excel → JSON 갱신")
    import_parser.add_argument("--type", choices=['summary', 'a4', 'both'], required=True,
                               help="읽어들일 원본 엑셀 형식")
    import_parser.add_argument("--file", default=None, help="단일 파일 경로 (지정 안 하면 폴더 스캔)")

    args, unknown = parser.parse_known_args()

    if args.command == "export":
        run_export(args, unknown)
    elif args.command == "import":
        run_import(args, unknown)

if __name__ == "__main__":
    main()
