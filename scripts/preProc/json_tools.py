import json
import os
import argparse
from typing import Any, Dict, List

class JsonProcessor:
    def __init__(self, input_path: str):
        if not os.path.exists(input_path):
            print(f"❌ 원본 파일을 찾을 수 없습니다: {input_path}")
            return
            
        with open(input_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        self.input_path = input_path

    # ==========================================
    # 1. 경로 기반 항목별 데이터 집계 (Full Path 방식)
    # ==========================================
    def print_stats(self):
        stats = {}

        def traverse(node: Any, current_path: str):
            if isinstance(node, dict):
                for key, value in node.items():
                    # 부모 경로를 포함한 전체 경로 생성 (예: project_managers.implementing_agency)
                    path = f"{current_path}.{key}" if current_path else key
                    
                    if path not in stats:
                        stats[path] = {"count": 0, "total_chars": 0}
                    
                    # 데이터가 유의미한 경우만 집계 (None, "", [], {} 제외)
                    if value not in (None, "", [], {}):
                        stats[path]["count"] += 1
                        stats[path]["total_chars"] += len(str(value))
                    
                    # 재귀 탐색
                    traverse(value, path)
                    
            elif isinstance(node, list):
                for item in node:
                    traverse(item, current_path)

        # 'project' 배열 내부를 기준으로 집계 시작
        projects = self.data.get("projects", [])
        traverse(projects, "")
        
        print(f"\n📊 [트리 경로별 집계 결과 - {self.input_path}]")
        print("-" * 60)
        # 경로 순으로 정렬하여 출력
        for path in sorted(stats.keys()):
            s = stats[path]
            if s['count'] > 0:
                print(f"{path} : {s['count']}건 ({s['total_chars']}글자)")

    # ==========================================
    # 2. 정확한 경로 지정 일괄 초기화 (새 파일 생성)
    # ==========================================
    def clear_by_path_and_save(self, target_paths: List[str], output_path: str):
        """지정된 Full Path와 정확히 일치하는 항목만 찾아 빈값 처리"""
        
        def get_empty_value(val):
            if isinstance(val, list): return []
            if isinstance(val, dict): return {}
            if isinstance(val, (int, float)): return None
            return ""

        def traverse_and_clear(node: Any, current_path: str):
            if isinstance(node, dict):
                for key in list(node.keys()):
                    full_path = f"{current_path}.{key}" if current_path else key
                    
                    # 입력받은 경로와 정확히 일치하는 경우만 초기화
                    if full_path in target_paths:
                        node[key] = get_empty_value(node[key])
                    else:
                        # 일치하지 않으면 하위 노드 탐색
                        traverse_and_clear(node[key], full_path)
            elif isinstance(node, list):
                for item in node:
                    traverse_and_clear(item, current_path)

        # 데이터 수정 (project 내부 타겟팅)
        traverse_and_clear(self.data.get("projects", []), "")
        
        # 새로운 파일로 저장 (원본 보호)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            
        print(f"\n🧹 지정 경로 초기화 완료: {target_paths}")
        print(f"💾 새 파일이 생성되었습니다: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JSON 트리 구조 대응 집계 및 초기화 도구")
    parser.add_argument("-i", "--input", required=True, help="분석할 merged.json 경로")
    parser.add_argument("-o", "--output", default="cleared_merged.json", help="저장할 새 파일명")
    parser.add_argument("--stats", action="store_true", help="경로별 데이터 건수/글자수 집계")
    parser.add_argument("--clear", nargs="+", help="초기화할 전체 경로 (예: department project_managers.implementing_agency)")

    args = parser.parse_args()
    processor = JsonProcessor(args.input)

    if args.stats:
        processor.print_stats()

    if args.clear:
        processor.clear_by_path_and_save(args.clear, args.output)