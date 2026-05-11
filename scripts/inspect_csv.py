"""Quick CSV inspector — diagnostic only, not part of the pipeline."""
import csv, json
from pathlib import Path

rows = list(csv.DictReader(Path("data/prospects.csv").open("r", encoding="utf-8", newline="")))
print(f"{len(rows)} rows")
print()
print(f"{'city':<16} {'rc':>5} {'rt':>4} {'cap':>4}  name")
print("-" * 78)
for r in rows:
    try:
        revs = json.loads(r.get("reviews_json") or "[]")
    except Exception:
        revs = []
    print(f"{r['city']:<16} {r['review_count']:>5} {r['rating']:>4} {len(revs):>4}  {r['name']}")
