import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import query_all

deps = query_all("""
    SELECT dep.id, dep.code, dep.name, count(d.id) as doc_count 
    FROM departments dep 
    LEFT JOIN doctors d ON dep.id = d.department_id 
    GROUP BY dep.id
""")
print(f"Total departments: {len(deps)}")
zero_docs = []
single_docs = []
for d in deps:
    cnt = d['doc_count']
    if cnt == 0:
        zero_docs.append(d['code'])
    elif cnt == 1:
        single_docs.append(d['code'])
    print(f"{d['code']:<8} {d['name']:<24}: {cnt} doctor(s)")

print("Zero doctor departments:", zero_docs)
print("Single doctor departments:", single_docs)
