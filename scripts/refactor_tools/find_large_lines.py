
import os

html_path = r'c:\ai\KAIB2026\index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if len(line) > 100000:
            print(f"Line {i+1}: {len(line)} bytes")
