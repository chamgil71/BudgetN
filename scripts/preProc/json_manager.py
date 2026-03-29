import argparse
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ... (compare_keys 함수는 기존과 동일하게 유지) ...
def compare_keys(template: Dict, target: Dict, path: str = "") -> List[str]:
    errors = []
    for key in template.keys():
        current_path = f"{path}.{key}" if path else key
        if key not in target:
            errors.append(f"누락된 키: {current_path}")
        elif isinstance(template[key], dict) and isinstance(target[key], dict):
            errors.extend(compare_keys(template[key], target[key], current_path))
    for key in target.keys():
        current_path = f"{path}.{key}" if path else key
        if key not in template:
            errors.append(f"초과된 키: {current_path}")
    return errors

def cmd_validate(args):
    """[기능 1] 개별 JSON 파일들이 템플릿 스키마와 일치하는지 검증합니다."""
    input_dir = Path(args.input)
    template_path = Path(args.template)
    
    if not template_path.exists():
        logger.error(f"❌ 템플릿 파일이 존재하지 않습니다: {template_path}")
        sys.exit(1)
        
    with open(template_path, 'r', encoding='utf-8') as f:
        full_template = json.load(f)
        
    project_schema = full_template.get("projects", [{}])[0]

    parsed_files = list(input_dir.glob("*_parsed.json"))
    if not parsed_files:
        logger.error(f"❌ 검증할 JSON 파일이 없습니다: {input_dir}")
        sys.exit(1)

    logger.info(f"=== 구조 검증(Validation) 시작 (대상: {len(parsed_files)}개 파일) ===")
    
    total_errors = 0
    for file_path in parsed_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            projects = json.load(f).get("projects", []) # 💡 data 래핑 호환성 처리
            
        for idx, project in enumerate(projects):
            errors = compare_keys(project_schema, project)
            if errors:
                logger.error(f"[{file_path.name}] 사업 #{idx+1} 구조 오류:")
                for err in errors:
                    logger.error(f"  - {err}")
                total_errors += 1

    if total_errors == 0:
        logger.info("✅ 모든 파일이 템플릿 스키마와 100% 일치합니다.")
    else:
        logger.warning(f"⚠️ 총 {total_errors}개의 구조 불일치가 발견되었습니다. 수정이 필요합니다.")
        sys.exit(1)

def cmd_merge(args):
    """[기능 2] 개별 JSON 파일들을 모아 순차적 ID를 부여하고 하나의 파일로 병합합니다."""
    input_dir = Path(args.input)
    output_file = Path(args.output)
    template_path = Path(args.template)
    
    if not template_path.exists():
        logger.error(f"❌ 템플릿 파일이 존재하지 않습니다: {template_path}")
        sys.exit(1)

    parsed_files = list(input_dir.glob("*_parsed.json"))
    if not parsed_files:
        logger.error(f"❌ 병합할 JSON 파일이 없습니다: {input_dir}")
        sys.exit(1)

    logger.info(f"=== 데이터 병합(Merge) 시작 ===")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        final_db = json.load(f)
    
    final_db["projects"] = [] 
    global_id = 1

    for file_path in parsed_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # budget_parser 출력물에서 projects 배열만 추출
            projects = data.get("projects", data) if isinstance(data, dict) else data
            
        for project in projects:
            project["id"] = global_id
            final_db["projects"].append(project)
            global_id += 1

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_db, f, ensure_ascii=False, indent=2)
        logger.info(f"🎉 병합 성공! 총 {len(final_db['projects'])}개 사업이 저장됨: {output_file.name}")
    except Exception as e:
        logger.error(f"❌ 병합 파일 저장 실패: {e}")
        sys.exit(1)

def main():
    # 💡 [핵심] 절대 경로 자동 추적 (scripts/pipeline 기준)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    # 새 구조에 맞춘 기본 경로 설정
    default_input = project_root / "database" / "parse_result"
    default_output = project_root / "database" / "output" / "merged.json"
    default_template = project_root / "config" / "template.json"

    parser = argparse.ArgumentParser(description="JSON 검증 및 병합 매니저")
    subparsers = parser.add_subparsers(dest="command", required=True, help="실행할 명령어 (validate 또는 merge)")

    # 1. validate 명령어 하위 파서
    val_parser = subparsers.add_parser("validate", help="JSON 구조가 템플릿과 일치하는지 검증합니다.")
    val_parser.add_argument("-i", "--input", default=str(default_input), help="입력 폴더 (기본: data/parse_result)")
    val_parser.add_argument("-t", "--template", default=str(default_template), help="템플릿 경로")

    # 2. merge 명령어 하위 파서
    merge_parser = subparsers.add_parser("merge", help="개별 JSON 파일들을 하나로 병합합니다.")
    merge_parser.add_argument("-i", "--input", default=str(default_input), help="입력 폴더 (기본: data/parse_result)")
    merge_parser.add_argument("-o", "--output", default=str(default_output), help="출력 파일 (기본: data/output/merged.json)")
    merge_parser.add_argument("-t", "--template", default=str(default_template), help="템플릿 경로")

    args = parser.parse_args()

    if args.command == "validate":
        cmd_validate(args)
    elif args.command == "merge":
        cmd_merge(args)

if __name__ == "__main__":
    main()