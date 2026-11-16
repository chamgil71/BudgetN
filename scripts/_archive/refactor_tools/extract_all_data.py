
import os
import re

html_path = r'c:\ai\KAIB2026\index.html'
js_dir = r'c:\ai\KAIB2026\js'

if not os.path.exists(js_dir):
    os.makedirs(js_dir)

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('const EMBEDDED_'):
        # Extract constant name
        match = re.search(r'const (EMBEDDED_\w+)', stripped)
        if match:
            const_name = match.group(1)
            file_name = const_name.lower().replace('_', '-') + '.js'
            file_path = os.path.join(js_dir, file_name)
            
            with open(file_path, 'w', encoding='utf-8') as f_out:
                f_out.write(stripped)
            print(f"Extracted {const_name} to {file_name} ({len(stripped)} bytes)")

# Also extract loadData logic and others if they are still there
