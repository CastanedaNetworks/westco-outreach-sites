"""Print full data for a single prospect by slug. Diagnostic-only."""
import csv, json, sys
from pathlib import Path

slug = sys.argv[1] if len(sys.argv) > 1 else None
rows = list(csv.DictReader(Path("data/prospects.csv").open("r", encoding="utf-8", newline="")))
for r in rows:
    if slug and r["slug"] != slug:
        continue
    print("=" * 78)
    for k, v in r.items():
        if k == "reviews_json":
            try:
                revs = json.loads(v or "[]")
                print(f"reviews ({len(revs)}):")
                for rev in revs:
                    print(f"  - {rev.get('author','?')}: {rev.get('text','')}")
            except Exception as e:
                print(f"reviews: ERR {e}")
        else:
            print(f"{k:14} {v}")
