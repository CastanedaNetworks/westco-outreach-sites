"""Print the top 3 status='new' prospects with reviews, sorted by rating desc, review_count desc."""
import csv, json
from pathlib import Path

rows = list(csv.DictReader(Path("data/prospects.csv").open("r", encoding="utf-8", newline="")))

def cap(r):
    try: return len(json.loads(r.get("reviews_json") or "[]"))
    except: return 0
def f_rating(r):
    try: return float(r["rating"])
    except: return 0.0
def f_count(r):
    try: return int(r["review_count"])
    except: return 0

def has_text(r):
    try: revs = json.loads(r.get("reviews_json") or "[]")
    except: return False
    return any((rev.get("text") or "").strip() for rev in revs)

candidates = [r for r in rows if r.get("status") == "new" and has_text(r)]
candidates.sort(key=lambda r: (-f_rating(r), -f_count(r)))

for r in candidates[:3]:
    print("=" * 78)
    print(f"slug:         {r['slug']}")
    print(f"name:         {r['name']}")
    print(f"address:      {r['address']}")
    print(f"city/county:  {r['city']} / {r['county']}")
    print(f"phone:        {r['phone']}")
    print(f"category:     {r['category']}")
    print(f"rating:       {r['rating']} ({r['review_count']} reviews)")
    print(f"place_id:     {r['place_id']}")
    print(f"captured:     {cap(r)} reviews")
    print("reviews:")
    for rev in json.loads(r["reviews_json"]):
        text = rev["text"][:160].replace("\n", " ")
        print(f"  - {rev['author']}: {text}{'...' if len(rev['text'])>160 else ''}")
