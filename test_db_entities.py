from backend.app.database import query_all

res = query_all('SELECT u.avatar_url, count(*) as cnt FROM users u JOIN doctors d ON u.id = d.user_id GROUP BY u.avatar_url')
total_docs = sum(r['cnt'] for r in res)
print(f"Total doctors: {total_docs}, Unique avatars: {len(res)}")

h_res = query_all('SELECT city, count(*) as cnt FROM hospitals GROUP BY city')
print(f"Hospitals per city: {[(r['city'], r['cnt']) for r in h_res]}")

doc_cities = query_all('SELECT city, count(*) as cnt FROM doctors GROUP BY city')
print(f"Doctors per city: {[(r['city'], r['cnt']) for r in doc_cities]}")
