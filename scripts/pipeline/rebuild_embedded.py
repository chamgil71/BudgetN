import json
import os
from pathlib import Path

def rebuild_embedded():
    mapping = [
        ('web/data/budget_db.json', 'web/js/embedded-data.js', 'window.EMBEDDED_DATA'),
        ('web/data/similarity_analysis.json', 'web/js/embedded-sim-v10-data.js', 'const EMBEDDED_SIM_V10_DATA'),
        ('web/data/collaboration_analysis.json', 'web/js/embedded-collab-data.js', 'const EMBEDDED_COLLAB_DATA'),
        ('web/data/hybrid_similarity.json', 'web/js/embedded-hybrid-data.js', 'const EMBEDDED_HYBRID_DATA')
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
