with open('frontend/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'id="view-patient-hospitals"' in line or 'id="view-profile"' in line:
        print(f"Line {idx+1}: {line.strip()}")
        for j in range(idx, min(len(lines), idx + 45)):
            print(f"  {j+1}: {lines[j].strip()}")
