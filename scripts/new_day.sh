#!/usr/bin/env bash
# new_day.sh — start-of-day convenience: pull latest, regenerate dashboard, open it.
#
# Usage:
#   ./scripts/new_day.sh
#
# What this does:
#   1. git pull (so multiple machines stay in sync)
#   2. Rebuilds dashboard.md from data/prospects.csv
#   3. Opens dashboard.md in the default viewer

set -euo pipefail

cd "$(dirname "$0")/.."

echo "[new_day] pulling latest…"
git pull --rebase --autostash || echo "[new_day] (skipping pull — no upstream yet)"

CSV="data/prospects.csv"
OUT="dashboard.md"

if [[ ! -f "$CSV" ]]; then
  echo "[new_day] no prospects.csv yet — run the scraper first."
  exit 0
fi

TODAY="$(date '+%Y-%m-%d %H:%M')"

# Build dashboard.md from the CSV using python (already required for scraper).
python - <<'PY'
import csv, os, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent if "__file__" in dir() else Path(".")
csv_path = Path("data/prospects.csv")
rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8", newline="")))

by_status = collections.Counter(r.get("status", "new") for r in rows)
by_county = collections.Counter(r.get("county", "UNK") for r in rows)
by_city   = collections.Counter(r.get("city", "?") for r in rows)

def fmt_row(r):
    return (
        f"- **{r.get('name','?')}** ({r.get('city','?')}, {r.get('county','?')}) — "
        f"{r.get('category','?')} — {r.get('rating','?')}★ ({r.get('review_count','?')} reviews) — "
        f"`{r.get('place_id','?')}`"
    )

new_rows   = [r for r in rows if r.get("status") == "new"]
ready_rows = [r for r in rows if r.get("status") == "ready"]
sent_rows  = [r for r in rows if r.get("status") == "sent"]

lines = []
lines.append("# WestCo outreach — daily dashboard\n")
lines.append(f"_Generated: {os.popen('date').read().strip()}_\n")
lines.append("## Pipeline\n")
lines.append(f"- Total prospects: **{len(rows)}**")
for s in ("new", "ready", "sent", "opened", "replied", "closed", "dead"):
    lines.append(f"- {s}: {by_status.get(s, 0)}")
lines.append("")
lines.append("## By county\n")
for c, n in sorted(by_county.items(), key=lambda kv: -kv[1]):
    lines.append(f"- {c}: {n}")
lines.append("")
lines.append("## By city\n")
for c, n in sorted(by_city.items(), key=lambda kv: -kv[1])[:15]:
    lines.append(f"- {c}: {n}")
lines.append("")
lines.append(f"## NEW — ready to generate ({len(new_rows)})\n")
lines += [fmt_row(r) for r in new_rows] or ["_(none)_"]
lines.append("")
lines.append(f"## READY — site built, email drafted ({len(ready_rows)})\n")
lines += [fmt_row(r) + f" — site: `{r.get('generated_url','')}`" for r in ready_rows] or ["_(none)_"]
lines.append("")
lines.append(f"## SENT ({len(sent_rows)})\n")
lines += [fmt_row(r) + f" — sent {r.get('sent_at','')}" for r in sent_rows] or ["_(none)_"]
lines.append("")

Path("dashboard.md").write_text("\n".join(lines), encoding="utf-8")
print("[new_day] wrote dashboard.md")
PY

# Open dashboard.md in the default viewer (cross-platform best effort).
if command -v wslview >/dev/null 2>&1; then
  wslview "$OUT" || true
elif [[ "$(uname -s)" == "Darwin" ]]; then
  open "$OUT" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$OUT" || true
elif command -v cmd.exe >/dev/null 2>&1; then
  cmd.exe /c start "" "$OUT" || true
else
  echo "[new_day] open dashboard.md manually."
fi
