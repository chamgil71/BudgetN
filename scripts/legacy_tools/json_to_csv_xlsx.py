import json
import csv
import argparse
import os
import yaml
from pathlib import Path

def get_config():
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def json_to_csv_xlsx():
    parser = argparse.ArgumentParser(description='Export KAIB2026 JSON data to CSV/XLSX')
    parser.add_argument('--input', type=str, help='Input JSON file path')
    parser.add_argument('--output_dir', type=str, default='output', help='Output directory')
    parser.add_argument('--format', type=str, choices=['csv', 'xlsx', 'all'], default='all', help='Output format')
    
    args = parser.parse_args()
    config = get_config()
    
    input_file = args.input or config.get('paths', {}).get('db_data', 'data/budget_db.json')
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    projects = data.get('projects', [])
    if not projects:
        print("No projects found in data.")
        return

    # Prepare project data for CSV/XLSX
    flat_projects = []
    sub_projects = []
    
    for p in projects:
        # Flatten main project info
        p_info = {
            'id': p.get('id'),
            'project_name': p.get('project_name'),
            'code': p.get('code'),
            'department': p.get('department'),
            'division': p.get('division'),
            'implementing_agency': p.get('implementing_agency'),
            'account_type': p.get('account_type'),
            'field': p.get('field'),
            'sector': p.get('sector'),
            'program_code': p.get('program', {}).get('code'),
            'program_name': p.get('program', {}).get('name'),
            'status': p.get('status'),
            'support_type': p.get('support_type'),
            'is_rnd': p.get('is_rnd'),
            'is_informatization': p.get('is_informatization'),
            'start_year': p.get('project_period', {}).get('start'),
            'end_year': p.get('project_period', {}).get('end'),
            'budget_2026': p.get('budget', {}).get('2026_budget'),
            'ai_domains': ', '.join(p.get('ai_classification', {}).get('ai_domains', [])),
            'ai_tech_types': ', '.join(p.get('ai_classification', {}).get('ai_tech_types', [])),
            'rnd_stage': p.get('ai_classification', {}).get('rnd_stage', '')
        }
        flat_projects.append(p_info)
        
        # Collect sub-projects
        for s in p.get('sub_projects', []):
            sub_projects.append({
                'parent_id': p.get('id'),
                'sub_project_name': s.get('name'),
                'budget_2026': s.get('budget_2026')
            })

    # Export to CSV
    if args.format in ['csv', 'all']:
        projects_csv = output_dir / 'projects_export.csv'
        with open(projects_csv, 'w', encoding='utf-8-sig', newline='') as f:
            if flat_projects:
                writer = csv.DictWriter(f, fieldnames=flat_projects[0].keys())
                writer.writeheader()
                writer.writerows(flat_projects)
        
        subs_csv = output_dir / 'sub_projects_export.csv'
        with open(subs_csv, 'w', encoding='utf-8-sig', newline='') as f:
            if sub_projects:
                writer = csv.DictWriter(f, fieldnames=sub_projects[0].keys())
                writer.writeheader()
                writer.writerows(sub_projects)
        print(f"CSV files exported to {output_dir}")

    # Export to XLSX (requires pandas and openpyxl)
    if args.format in ['xlsx', 'all']:
        try:
            import pandas as pd
            projects_xlsx = output_dir / 'budget_data_export.xlsx'
            with pd.ExcelWriter(projects_xlsx) as writer:
                pd.DataFrame(flat_projects).to_sheet(writer, sheet_name='Projects', index=False)
                pd.DataFrame(sub_projects).to_sheet(writer, sheet_name='SubProjects', index=False)
            print(f"Excel file exported to {projects_xlsx}")
        except ImportError:
            print("Warning: pandas or openpyxl not found. Skipping Excel export.")

if __name__ == "__main__":
    json_to_csv_xlsx()
