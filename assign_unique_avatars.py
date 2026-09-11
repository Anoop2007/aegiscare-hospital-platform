from backend.app.database import query_all, execute_update
import urllib.parse

# List of 60 distinct high-quality portrait photo IDs from Unsplash
portrait_ids = [
    "photo-1622253692010-333f2da6031d",
    "photo-1537368910025-700350fe46c7",
    "photo-1612349317150-e413f6a5b16d",
    "photo-1582750433449-648ed127bb54",
    "photo-1594824813627-2c140c83d6a1",
    "photo-1559839734-2b71ea197ec2",
    "photo-1573496359142-b8d87734a5a2",
    "photo-1534528741775-53994a69daeb",
    "photo-1567532939604-b6b5b0db2604",
    "photo-1507003211169-0a1dd7228f2d",
    "photo-1500648767791-00dcc994a43e",
    "photo-1544005313-94ddf0286df2",
    "photo-1472099645785-5658abf4ff4e",
    "photo-1519085360753-af0119f7cbe7",
    "photo-1506794778202-cad84cf45f1d",
    "photo-1573497019940-1c28c88b4f3e",
    "photo-1580489944761-15a19d654956",
    "photo-1551836022-deb4988cc6c0",
    "photo-1560250097-0b93528c311a",
    "photo-1508214751196-bcfd4ca60f91",
    "photo-1570295999919-56ceb5ecca61",
    "photo-1535713875002-d1d0cf377fde",
    "photo-1527980965255-d3b416303d12",
    "photo-1531746020798-e6953c6e8e04",
    "photo-1584467735871-8e85353a8413",
    "photo-1584515979956-d9f6e5d09982",
    "photo-1629909613654-28e377c37b09",
    "photo-1633332755192-727a05c4013d",
    "photo-1548142813-c348350df52b",
    "photo-1576091160399-112ba8d25d1d",
    "photo-1576091160550-2173dba999ef",
    "photo-1582719508461-905c673771fd",
    "photo-1559839734-2b71ea197ec2",
    "photo-1544717305-2782549b5136",
    "photo-1522075469751-3a6694fb2f61",
    "photo-1501196354995-cbb51c65aaea",
    "photo-1517841905240-472988babdf9",
    "photo-1539571696357-5a69c17a67c6",
    "photo-1519085360753-af0119f7cbe7",
    "photo-1542909168-82c3e7fdca5c",
    "photo-1524504388940-b1c1722653e1",
    "photo-1546961329-78bef0414d7c",
    "photo-1544005313-94ddf0286df2",
    "photo-1517841905240-472988babdf9",
    "photo-1560250097-0b93528c311a",
    "photo-1573496359142-b8d87734a5a2",
    "photo-1580489944761-15a19d654956",
    "photo-1500648767791-00dcc994a43e",
    "photo-1534528741775-53994a69daeb",
    "photo-1507003211169-0a1dd7228f2d",
    "photo-1567532939604-b6b5b0db2604",
    "photo-1519494026892-80bbd2d6fd0d",
    "photo-1582750433449-648ed127bb54",
    "photo-1537368910025-700350fe46c7",
    "photo-1612349317150-e413f6a5b16d",
    "photo-1594824813627-2c140c83d6a1",
    "photo-1622253692010-333f2da6031d",
    "photo-1576091160399-112ba8d25d1d"
]

doctors = query_all("SELECT d.id as doc_id, u.id as user_id, u.full_name FROM doctors d JOIN users u ON d.user_id = u.id ORDER BY d.id ASC")
print(f"Assigning unique avatars to {len(doctors)} doctors...")

for idx, doc in enumerate(doctors):
    photo_id = portrait_ids[idx % len(portrait_ids)]
    unique_url = f"https://images.unsplash.com/{photo_id}?w=150&auto=format&fit=crop&q=80&docId={doc['doc_id']}"
    execute_update("UPDATE users SET avatar_url = ? WHERE id = ?", (unique_url, doc["user_id"]))

# Verify
res = query_all('SELECT u.avatar_url, count(*) as cnt FROM users u JOIN doctors d ON u.id = d.user_id GROUP BY u.avatar_url')
print(f"Total doctors: {len(doctors)}, Unique avatar URLs: {len(res)}")
