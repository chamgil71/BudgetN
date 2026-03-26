import json
import os
from datetime import datetime
from pathlib import Path

def sync_budget_data():
    db_path = Path('web/data/budget_db.json')
    sim_path = Path('web/data/similarity_analysis.json')

    if not db_path.exists():
        print(f"Error: {db_path} not found.")
        return

    # 1. Load budget_db.json
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {db_path}: {e}")
        return

    projects = data.get('projects', [])
    if not isinstance(projects, list) or not projects:
        print("Warning: No valid projects list found in budget_db.json.")
        return

    print(f"Syncing {len(projects)} projects...")

    # 2. Helper functions with more safety
    def get_budget_2026(p):
        if not isinstance(p, dict): return 0
        b = p.get('budget', {})
        if isinstance(b, dict):
            val = b.get('2026_budget', b.get('budget_ request', b.get('2026_request', 0))) # Handle variations
            if val is None: val = 0
            try: return float(val)
            except: return 0
        return 0

    def get_budget_2025(p):
        if not isinstance(p, dict): return 0
        b = p.get('budget', {})
        if isinstance(b, dict):
            val = b.get('2025_original', b.get('2025_budget', 0))
            if val is None: val = 0
            try: return float(val)
            except: return 0
        return 0

    # 3. Recalculate Metadata
    valid_projects = [p for p in projects if isinstance(p, dict)]
    total_budget = sum(get_budget_2026(p) for p in valid_projects)
    depts = set(p.get('department', '기타') for p in valid_projects)

    if 'metadata' not in data: data['metadata'] = {}
    data['metadata']['project_count'] = len(valid_projects)
    data['metadata']['total_budget_2026'] = total_budget
    data['metadata']['departments_count'] = len(depts)
    data['metadata']['updated_at'] = datetime.now().isoformat()

    # 4. Recalculate Basic Analysis
    if 'analysis' not in data:
        data['analysis'] = {}

    # By Department
    dept_map = {}
    for p in valid_projects:
        d = p.get('department', '기타')
        b = get_budget_2026(p)
        if d not in dept_map:
            dept_map[d] = {"name": d, "count": 0, "budget_2026": 0}
        dept_map[d]['count'] += 1
        dept_map[d]['budget_2026'] += b

    dept_analysis = sorted(dept_map.values(), key=lambda x: x['budget_2026'], reverse=True)
    for d in dept_analysis:
        d['share'] = round(d['budget_2026'] / total_budget * 100, 1) if total_budget > 0 else 0
    data['analysis']['by_department'] = dept_analysis

    # Top Increases / Decreases
    def get_rate(p):
        b25 = get_budget_2025(p)
        b26 = get_budget_2026(p)
        if b25 > 0:
            return round((b26 - b25) / b25 * 100, 1)
        return 0

    projects_with_rate = []
    for p in valid_projects:
        p_copy = p.copy()
        p_copy['temp_rate'] = get_rate(p)
        projects_with_rate.append(p_copy)

    data['analysis']['top_increases'] = sorted(projects_with_rate, key=lambda x: x.get('temp_rate', 0), reverse=True)[:10]
    data['analysis']['top_decreases'] = sorted(projects_with_rate, key=lambda x: x.get('temp_rate', 0))[:10]

    for p in data['analysis']['top_increases']: p.pop('temp_rate', None)
    for p in data['analysis']['top_decreases']: p.pop('temp_rate', None)

    # 5. Save budget_db.json
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully updated {db_path}")

    # 6. Sync similarity_analysis.json if exists
    if sim_path.exists():
        print(f"Found {sim_path}. Syncing project info...")
        try:
            with open(sim_path, 'r', encoding='utf-8') as f:
                sim_data = json.load(f)
            
            project_lookup = {p['id']: p for p in valid_projects if 'id' in p}
            updated_count = 0
            
            for pair in sim_data.get('pairs', []):
                for key in ['project_a', 'project_b']:
                    p_ref = pair.get(key)
                    if p_ref and p_ref.get('id') in project_lookup:
                        new_p = project_lookup[p_ref['id']]
                        # Update basic fields without breaking similarity logic
                        p_ref['project_name'] = new_p.get('project_name', p_ref.get('project_name'))
                        p_ref['department'] = new_p.get('department', p_ref.get('department'))
                        p_ref['budget_2026'] = get_budget_2026(new_p)
                        updated_count += 1
            
            if 'metadata' not in sim_data: sim_data['metadata'] = {}
            sim_data['metadata']['sync_at'] = datetime.now().isoformat()
            
            with open(sim_path, 'w', encoding='utf-8') as f:
                json.dump(sim_data, f, ensure_ascii=False, indent=2)
            print(f"Successfully updated {sim_path} ({updated_count} references updated)")
        except Exception as sim_e:
            print(f"Error syncing {sim_path}: {sim_e}")

if __name__ == "__main__":
    sync_budget_data()
