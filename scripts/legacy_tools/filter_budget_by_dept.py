import json
import os
import sys
from pathlib import Path

# 프로젝트 루트(scripts/legacy_tools 에서 두 단계 위)를 import 경로에 넣고 경로 SSOT(config/path_config) 사용
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from config.path_config import WEB_DATA_DIR  # noqa: E402

def filter_by_department(dept_name: str):
    # 예전 c:\ai\KAIB2026\data (없는 경로) 대신 현재 budget_db.json 위치인 web/data
    input_file = str(WEB_DATA_DIR / "budget_db.json")
    output_file = str(WEB_DATA_DIR / f"budget_db_{dept_name}.json")
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get("projects", [])
    filtered_projects = [p for p in projects if p.get("department") == dept_name]
    
    print(f"Found {len(filtered_projects)} projects for department: {dept_name}")
    
    # Create output data structure
    output_data = {
        "metadata": data.get("metadata", {}).copy(),
        "projects": filtered_projects
    }
    
    # Update some metadata for the filtered subset
    output_data["metadata"]["filtered_department"] = dept_name
    output_data["metadata"]["project_count"] = len(filtered_projects)
    
    print(f"Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python filter_budget_by_dept.py <department_name>")
        sys.exit(1)
    
    target_dept = sys.argv[1]
    filter_by_department(target_dept)
