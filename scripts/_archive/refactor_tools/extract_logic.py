
import os
import re

html_path = r'c:\ai\KAIB2026\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Script block starts at line ~3193 and ends at ~11200
script_lines = []
in_script = False
for line in lines:
    if '<script>' in line:
        in_script = True
        continue
    if '</script>' in line:
        in_script = False
        continue
    if in_script:
        # Skip the massive data lines we already extracted
        if 'const EMBEDDED_' in line:
            continue
        script_lines.append(line)

with open(r'c:\ai\KAIB2026\js\all-logic-extracted.js', 'w', encoding='utf-8') as f:
    f.writelines(script_lines)

print(f"Extracted {len(script_lines)} lines of logic.")
