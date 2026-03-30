import json
import os
from pathlib import Path
import sys
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from config import path_config

def rebuild_embedded():
    # Use path_config locations
    mapping = [
        (path_config.WEB_DATA_DIR / 'budget_db.json', path_config.WEB_DIR / 'js' / 'embedded-data.js', 'window.EMBEDDED_DATA'),
        (path_config.WEB_DATA_DIR / 'similarity_analysis.json', path_config.WEB_DIR / 'js' / 'embedded-sim-v10-data.js', 'const EMBEDDED_SIM_V10_DATA'),
        (path_config.WEB_DATA_DIR / 'collaboration_analysis.json', path_config.WEB_DIR / 'js' / 'embedded-collab-data.js', 'const EMBEDDED_COLLAB_DATA'),
        (path_config.WEB_DATA_DIR / 'hybrid_similarity.json', path_config.WEB_DIR / 'js' / 'embedded-hybrid-data.js', 'const EMBEDDED_HYBRID_DATA')
    ]

    for src, dst, var_name in mapping:
        src_path = Path(src)
        dst_path = Path(dst)

        if not src_path.exists():
            print(f"Skipping {src}: File not found.")
            continue

        print(f"Rebuilding {dst} from {src}...")
        try:
            with open(src_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            with open(dst_path, 'w', encoding='utf-8') as f:
                f.write(f"{var_name} = {json.dumps(data, ensure_ascii=False)};")
            print(f"Successfully rebuilt {dst}")
        except Exception as e:
            print(f"Error rebuilding {dst}: {e}")

if __name__ == "__main__":
    rebuild_embedded()
