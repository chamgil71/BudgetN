
import os

html_path = r'c:\ai\KAIB2026\index.html'
clean_html_path = r'c:\ai\KAIB2026\index_clean.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if '<script>' in line and i > 3000: # Target the big block
        new_lines.append('  <!-- Externalized Data Blocks -->\n')
        new_lines.append('  <script src="js/embedded-sim-v10-data.js"></script>\n')
        new_lines.append('  <script src="js/embedded-collab-data.js"></script>\n')
        new_lines.append('  <script src="js/embedded-hybrid-data.js"></script>\n')
        new_lines.append('  <script src="js/embedded-data.js"></script>\n')
        new_lines.append('\n')
        new_lines.append('  <!-- Core Framework & Utilities -->\n')
        new_lines.append('  <script src="js/common.js"></script>\n')
        new_lines.append('  <script src="js/charts.js"></script>\n')
        new_lines.append('  <script src="js/tab-handler.js"></script>\n')
        new_lines.append('\n')
        new_lines.append('  <!-- Feature Modules -->\n')
        new_lines.append('  <script src="js/budget-advanced.js"></script>\n')
        new_lines.append('  <script src="js/network-viz.js"></script>\n')
        new_lines.append('  <script src="js/cross-compare.js"></script>\n')
        new_lines.append('  <script src="js/report-logic.js"></script>\n')
        new_lines.append('  <script src="js/policy-cluster.js"></script>\n')
        new_lines.append('  <script src="js/future-sim.js"></script>\n')
        new_lines.append('  <script src="js/notes-pdf.js"></script>\n')
        new_lines.append('  <script src="js/budget-insight.js"></script>\n')
        new_lines.append('  <script src="js/ai-tech.js"></script>\n')
        new_lines.append('\n')
        new_lines.append('  <!-- Main Application Logic -->\n')
        new_lines.append('  <script src="js/app.js"></script>\n')
        skip = True
        continue
    if '</script>' in line and skip:
        skip = False
        continue
    if not skip:
        # Also skip existing script tags that we already added above
        if any(x in line for x in ['src="js/policy-cluster.js"', 'src="js/cross-compare.js"', 'src="js/future-sim.js"', 'src="js/budget-advanced.js"', 'src="js/network-viz.js"', 'src="js/notes-pdf.js"', 'src="js/budget-insight.js"', 'src="js/ai-tech.js"']):
            continue
        new_lines.append(line)

with open(clean_html_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Cleaned HTML saved to {clean_html_path}")
