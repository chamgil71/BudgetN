import json
import os
import sys

def filter_by_department(dept_name: str):
    base_dir = r"c:\ai\KAIB2026"
    input_file = os.path.join(base_dir, "data", "budget_db.json")
    output_file = os.path.join(base_dir, "data", f"budget_db_{dept_name}.json")
    
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
