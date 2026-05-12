"""End-of-session status report — diagnostic, not part of the pipeline."""
import csv, json
from collections import Counter
from pathlib import Path

rows = list(csv.DictReader(Path("data/prospects.csv").open("r", encoding="utf-8", newline="")))

# Reviews captured per row
def cap(r):
    try:
        return len(json.loads(r.get("reviews_json") or "[]"))
    except Exception:
        return 0

useable  = [r for r in rows if cap(r) >= 1]
broken   = [r for r in rows if cap(r) == 0]
by_county = Counter(r.get("county", "UNK") for r in rows)

def f_rating(r):
    try: return float(r["rating"])
    except: return 0.0
def f_count(r):
    try: return int(r["review_count"])
    except: return 0

ranked = sorted(useable, key=lambda r: (-f_rating(r), -f_count(r)))

print(f"Total prospects: {len(rows)}")
print(f"  - useable (>=1 review captured): {len(useable)}")
print(f"  - broken (0 reviews captured):   {len(broken)}")
print()
print("By county:")
for c in ("LA", "SB", "RIV", "OR", "UNK"):
    print(f"  {c}: {by_county.get(c, 0)}")
print()
print("Top 5 useable prospects (rating desc, review_count desc):")
print(f"{'rating':<7}{'rc':<6}{'city':<14}{'county':<8}name")
print("-" * 78)
for r in ranked[:5]:
    print(f"{r['rating']:<7}{r['review_count']:<6}{r['city']:<14}{r['county']:<8}{r['name']}")
print()
if broken:
    print("Rows missing reviews (need re-scrape or skip):")
    for r in broken:
        print(f"  - {r['name']} ({r['city']}, {r['county']}) — {r['review_count']} real reviews on Google")
