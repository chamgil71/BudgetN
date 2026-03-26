import csv
import json
import argparse
import os
import yaml
from pathlib import Path
from datetime import datetime

def get_config():
    config_path = Path(__file__).parent.parent.parent / 'config' / 'config.yaml'
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

def convert_csv_to_json():
    parser = argparse.ArgumentParser(description='Convert KAIB2026 CSV templates to JSON (Raw and DB)')
    parser.add_argument('--projects', type=str, help='Projects CSV file')
    parser.add_argument('--subs', type=str, help='Sub-projects CSV file')
    parser.add_argument('--config', type=str, help='Config YAML file')
    
    args = parser.parse_args()
    config = get_config()
    
    projects_file = args.projects or config.get('paths', {}).get('template_dir', 'template') + '/projects_template.csv'
    sub_projects_file = args.subs or config.get('paths', {}).get('template_dir', 'template') + '/sub_projects_template.csv'
    raw_output = config.get('paths', {}).get('raw_data', 'data/budget_raw.json')
    db_output = config.get('paths', {}).get('db_data', 'data/budget_db.json')

    if not os.path.exists(projects_file) or not os.path.exists(sub_projects_file):
        print(f"Error: Template files missing ({projects_file}, {sub_projects_file}).")
        return

    # Load sub-projects
    subs_by_parent = {}
    with open(sub_projects_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['parent_id']
            if pid not in subs_by_parent:
                subs_by_parent[pid] = []
            subs_by_parent[pid].append({
                "name": row['sub_project_name'],
                "budget_2024": float(row['budget_2024']) if row['budget_2024'] else 0,
                "budget_2025": float(row['budget_2025']) if row['budget_2025'] else 0,
                "budget_2026": float(row['budget_2026']) if row['budget_2026'] else 0,
                # Project managers mapping (basic)
                "managing_dept": row.get('managing_dept', ''),
                "implementing_agency": row.get('implementing_agency', '')
            })

    # Load projects and merge
    projects = []
    with open(projects_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row['id']
            b25 = float(row['2025_original']) if row['2025_original'] else 0
            b26 = float(row['2026_budget']) if row['2026_budget'] else 0
            diff = b26 - b25
            rate = (diff / b25 * 100) if b25 != 0 else 0

            project = {
                "id": int(pid),
                "name": f"{row['department']}_{row['project_name']}",
                "project_name": row['project_name'],
                "code": row['code'],
                "department": row['department'],
                "division": row['division'],
                "implementing_agency": row['implementing_agency'],
                "account_type": row['account_type'],
                "field": row['field'],
                "sector": row['sector'],
                "program": {"code": row.get('program_code',''), "name": row.get('program_name','')},
                "unit_project": {"code": row.get('unit_project_code',''), "name": row.get('unit_project_name','')},
                "detail_project": {"code": row.get('detail_project_code',''), "name": row.get('detail_project_name','')},
                "status": row['status'],
                "support_type": row['support_type'],
                "is_rnd": row['is_rnd'].upper() == 'TRUE',
                "is_informatization": row['is_informatization'].upper() == 'TRUE',
                "project_period": {
                    "start": int(row['start_year']) if row['start_year'] else None,
                    "end": int(row['end_year']) if row['end_year'] else None,
                    "duration": int(row['duration']) if row['duration'] else 0
                },
                "total_cost": {
                    "total": float(row['total_cost']) if row['total_cost'] else 0,
                    "government": float(row['total_gov_cost']) if row['total_gov_cost'] else 0
                },
                "budget": {
                    "2024_settlement": float(row['2024_settlement']) if row['2024_settlement'] else 0,
                    "2025_original": b25,
                    "2025_supplementary": float(row['2025_supplementary']) if row['2025_supplementary'] else b25,
                    "2026_request": float(row['2026_request']) if row['2026_request'] else 0,
                    "2026_budget": b26,
                    "change_amount": diff,
                    "change_rate": round(rate, 1)
                },
                "sub_projects": subs_by_parent.get(pid, []),
                "project_managers": [
                    {"sub_project": s['name'], "managing_dept": s['managing_dept'], "implementing_agency": s['implementing_agency']}
                    for s in subs_by_parent.get(pid, [])
                ],
                "purpose": row['purpose'],
                "description": row['description'],
                "legal_basis": row['legal_basis'],
                "keywords": [], # Placeholder or simple splitting of name/description
                "ai_classification": {
                    "ai_tech_types": [x.strip() for x in row.get('ai_tech_types', '').split(',') if x.strip()],
                    "rnd_stage": row.get('rnd_stage', ''),
                    "ai_domains": [x.strip() for x in row.get('ai_domains', '').split(',') if x.strip()]
                },
                "page_range": {"start": int(row['page_start']) if row['page_start'] else 0, "end": int(row['page_end']) if row['page_end'] else 0}
            }
            projects.append(project)

    # Save budget_raw.json
    Path(raw_output).parent.mkdir(parents=True, exist_ok=True)
    with open(raw_output, 'w', encoding='utf-8') as f:
        json.dump(projects, f, ensure_ascii=False, indent=2)

    # Generate budget_db.json with analysis
    db_data = {
        "metadata": {
            "source": "KAIB2026 CSV Import",
            "generated_at": datetime.now().isoformat(),
            "version": config.get('project', {}).get('version', '1.0.0'),
            "project_count": len(projects),
            "total_budget_2026": sum(p['budget']['2026_budget'] for p in projects),
            "departments_count": len(set(p['department'] for p in projects))
        },
        "projects": projects,
        "analysis": generate_analysis(projects)
    }
    
    with open(db_output, 'w', encoding='utf-8') as f:
        json.dump(db_data, f, ensure_ascii=False, indent=2)

    print(f"Successfully converted CSV to {raw_output} and {db_output}")

def generate_analysis(projects):
    depts = {}
    domains = {}
    for p in projects:
        d = p['department']
        b = p['budget']['2026_budget']
        if d not in depts: depts[d] = {"name": d, "count": 0, "budget_2026": 0}
        depts[d]['count'] += 1
        depts[d]['budget_2026'] += b
        
        for dom in p['ai_classification']['ai_domains']:
            if dom not in domains: domains[dom] = {"name": dom, "count": 0, "budget_2026": 0}
            domains[dom]['count'] += 1
            domains[dom]['budget_2026'] += b

    total = sum(p['budget']['2026_budget'] for p in projects)
    dept_analysis = sorted(depts.values(), key=lambda x: x['budget_2026'], reverse=True)
    for d in dept_analysis: d['share'] = round(d['budget_2026'] / total * 100, 1) if total > 0 else 0

    domain_analysis = sorted(domains.values(), key=lambda x: x['budget_2026'], reverse=True)
    for d in domain_analysis: d['share'] = round(d['budget_2026'] / total * 100, 1) if total > 0 else 0

    return {
        "by_department": dept_analysis,
        "by_domain": domain_analysis,
        "by_type": {
            "rnd": {"count": len([p for p in projects if p['is_rnd']]), "budget": sum(p['budget']['2026_budget'] for p in projects if p['is_rnd'])},
            "informatization": {"count": len([p for p in projects if p['is_informatization']]), "budget": sum(p['budget']['2026_budget'] for p in projects if p['is_informatization'])},
            "new": {"count": len([p for p in projects if p['status'] == '신규']), "budget": sum(p['budget']['2026_budget'] for p in projects if p['status'] == '신규')}
        },
        "top_increases": sorted(projects, key=lambda x: x['budget']['change_rate'], reverse=True)[:10],
        "top_decreases": sorted(projects, key=lambda x: x['budget']['change_rate'])[:10],
        "duplicates": [] # Simplified for script
    }

if __name__ == "__main__":
    convert_csv_to_json()
