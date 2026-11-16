
import os

html_path = r'c:\ai\KAIB2026\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 3383 (0-indexed: 3382) is EMBEDDED_SIM_V10_DATA
# Line 3385 (0-indexed: 3384) is EMBEDDED_COLLAB_DATA
sim_data = lines[3382].strip()
collab_data = lines[3384].strip()

# Utility functions and others (approx 3209 to 11200)
# We want to keep the HTML structure but replace the massive <script> block.
# Actually, let's just create the data files first.

with open(r'c:\ai\KAIB2026\js\data-sim.js', 'w', encoding='utf-8') as f:
    f.write(sim_data)

with open(r'c:\ai\KAIB2026\js\data-collab.js', 'w', encoding='utf-8') as f:
    f.write(collab_data)

print(f"Extracted SIM data: {len(sim_data)} bytes")
print(f"Extracted Collab data: {len(collab_data)} bytes")
