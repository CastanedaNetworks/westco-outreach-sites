"""One-shot cleanup: drop rows with 0 captured reviews OR junk name.

Keeps the Covina Complete Auto Repair row (3 reviews, good) and any other
genuinely complete row. After this runs, the next scrape will re-fetch
the dropped place_ids since dedupe is by place_id and they're gone.
"""
import csv, json
from pathlib import Path

CSV = Path("data/prospects.csv")
COLS = ['place_id','name','slug','address','city','county','phone','rating','review_count','category','reviews_json','status','generated_url','created_at','sent_at','replied_at','notes']

rows = list(csv.DictReader(CSV.open("r", encoding="utf-8", newline="")))
kept, dropped = [], []
for r in rows:
    name = (r.get("name") or "").strip().lower()
    try:
        revs = json.loads(r.get("reviews_json") or "[]")
    except Exception:
        revs = []
    if name in ("results", "sponsored", "") or len(revs) == 0:
        dropped.append(r)
    else:
        kept.append(r)

with CSV.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    for r in kept:
        w.writerow({k: r.get(k, "") for k in COLS})

print(f"kept {len(kept)} rows, dropped {len(dropped)} rows")
for r in dropped:
    print(f"  dropped: {r.get('name','?')} ({r.get('city','?')})")
