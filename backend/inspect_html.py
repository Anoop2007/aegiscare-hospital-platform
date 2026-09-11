import re

html = open("frontend/index.html", "r", encoding="utf-8").read()

print("--- View IDs ---")
for m in re.finditer(r'id="(view-[^"]+)"', html):
    print(m.group(1))

print("\n--- Dollar signs count ---")
dollars = re.findall(r'\$[0-9]+|\$\{[^}]+\}|\$', html)
print(f"Total $ found: {len(dollars)}")
for d in re.findall(r'(\$[0-9]+(?:\.[0-9]+)?)', html):
    print(f"Sample price: {d}")

print("\n--- Nav links ---")
for m in re.finditer(r'data-view="([^"]+)"', html):
    print(m.group(1))
