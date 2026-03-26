import yaml
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
OLD_CFG = ROOT / 'config.yaml'
NEW_CFG = ROOT / 'config' / 'config.yaml'

def merge_configs():
    if not OLD_CFG.exists():
        print("Root config.yaml already missing.")
        return

    with open(OLD_CFG, 'r', encoding='utf-8') as f:
        old_data = yaml.safe_load(f) or {}
    with open(NEW_CFG, 'r', encoding='utf-8') as f:
        new_data = yaml.safe_load(f) or {}

    # Merge project
    if 'project' in old_data:
        new_data['project'] = old_data['project']
    
    # Merge unique paths
    if 'paths' in old_data:
        if 'paths' not in new_data:
            new_data['paths'] = {}
        for k, v in old_data['paths'].items():
            if k not in new_data['paths']:
                new_data['paths'][k] = v

    # Merge schema
    if 'schema' in old_data:
        new_data['schema'] = old_data['schema']

    with open(NEW_CFG, 'w', encoding='utf-8') as f:
        yaml.dump(new_data, f, allow_unicode=True, sort_keys=False)
    
    OLD_CFG.unlink()
    print("Merged and deleted root config.yaml")

def fix_legacy_tools():
    legacy_dir = ROOT / 'scripts' / 'legacy_tools'
    if not legacy_dir.exists(): return
    for f in legacy_dir.iterdir():
        if f.suffix == '.py':
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
            # If they had .parent.parent / 'config.yaml'
            # change to .parent.parent.parent / 'config' / 'config.yaml'
            orig = content
            content = content.replace("Path(__file__).parent.parent / 'config.yaml'", 
                                     "Path(__file__).parent.parent.parent / 'config' / 'config.yaml'")
            if orig != content:
                with open(f, 'w', encoding='utf-8') as file:
                    file.write(content)
                print(f"Fixed {f.name} config path")

if __name__ == '__main__':
    merge_configs()
    fix_legacy_tools()
