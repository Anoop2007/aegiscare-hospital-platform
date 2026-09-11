import re

html = open("frontend/index.html", "r", encoding="utf-8").read()
lines = html.split("\n")

for i, line in enumerate(lines):
    if '<section class="view-section' in line:
        m = re.search(r'id="([^"]+)"', line)
        vid = m.group(1) if m else "unknown"
        print(f"Line {i+1}: {vid}")
