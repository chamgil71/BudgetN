'''
python scripts/utils/replace_json.py data.json`
'''
import json
import yaml
import argparse
import re
import sys
from pathlib import Path

def load_config(yaml_path: Path):
    if not yaml_path.exists():
        print(f"❌ 설정 파일 없음: {yaml_path}")
        sys.exit(1)
        
    with open(yaml_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    field_rules = {}
    if not config: return field_rules

    for field, rules in config.items():
        compiled_rules = []
        for final_val, targets in rules.items():
            # 리스트 형식이 아니면 리스트로 변환
            target_list = targets if isinstance(targets, list) else [targets]
            for t in target_list:
                try:
                    # 정규식 컴파일
                    pattern = re.compile(str(t).strip())
                    compiled_rules.append((pattern, str(final_val)))
                except re.error as e:
                    print(f"⚠️ 정규식 오류 ({t}): {e}")
        field_rules[field] = compiled_rules
    return field_rules

def process_node(node, field_rules):
    if isinstance(node, dict):
        new_dict = {}
        for k, v in node.items():
            # 1. 규칙이 있는 키(Field)인가? 2. 값이 문자열인가?
            if k in field_rules and isinstance(v, str):
                temp_v = v
                matched = False
                for pattern, final in field_rules[k]:
                    # pattern.search로 해당 패턴이 존재하는지 확인
                    if pattern.search(temp_v):
                        # 패턴에 매칭되면 '필드 전체'를 final값으로 교체
                        temp_v = final
                        matched = True
                        break # 한 필드에 하나의 규칙만 적용하고 다음 필드로
                new_dict[k] = temp_v.strip()
            else:
                new_dict[k] = process_node(v, field_rules)
        return new_dict
    elif isinstance(node, list):
        return [process_node(elem, field_rules) for elem in node]
    return node

def main():
    # 경로 자동 설정 (스크립트 위치 기준 프로젝트 루트 탐색)
    current_script = Path(__file__).resolve()
    project_root = current_script.parent.parent.parent
    default_yaml = project_root / "config" / "pattern.yaml"

    parser = argparse.ArgumentParser(description="JSON 특정 필드 정규식 기반 일괄 치환")
    parser.add_argument("input", type=str, help="대상 JSON 파일 경로")
    parser.add_argument("--pattern", "-p", type=str, default=str(default_yaml), help="패턴 YAML 경로")
    parser.add_argument("--output", "-o", type=str, help="출력 파일 경로")

    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    pattern_path = Path(args.pattern).resolve()

    if not input_path.exists():
        print(f"❌ 인풋 파일 없음: {input_path}")
        return

    # 설정 및 데이터 로드
    field_rules = load_config(pattern_path)
    with open(input_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 변환 작업
    updated_data = process_node(json_data, field_rules)
    
    # 출력 경로 결정
    output_path = Path(args.output).resolve() if args.output else \
                  input_path.with_name(f"{input_path.stem}_fixed{input_path.suffix}")

    # 결과 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, ensure_ascii=False, indent=4)
        
    print(f"✅ 완료! 필드별 치환이 적용되었습니다.")
    print(f"💾 결과 저장: {output_path}")

if __name__ == "__main__":
    main()