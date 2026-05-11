# new_day.ps1 — start-of-day convenience: pull latest, regenerate dashboard, open it.
#
# Usage:
#   .\scripts\new_day.ps1

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

Write-Output "[new_day] pulling latest..."
try {
    & git pull --rebase --autostash 2>&1 | Out-Host
} catch {
    Write-Output "[new_day] (skipping pull - no upstream yet)"
}

$csvPath = "data/prospects.csv"
$outPath = "dashboard.md"

if (-not (Test-Path $csvPath)) {
    Write-Output "[new_day] no prospects.csv yet - run the scraper first."
    exit 0
}

# Prefer the venv python so the user doesn't have to activate it first
$venvPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $python = $venvPython
} else {
    $python = "python"
}

# Inline Python: rebuild dashboard.md from the CSV
$dashScript = @'
import csv, collections, datetime
from pathlib import Path

csv_path = Path("data/prospects.csv")
rows = list(csv.DictReader(csv_path.open("r", encoding="utf-8", newline="")))

by_status = collections.Counter(r.get("status", "new") for r in rows)
by_county = collections.Counter(r.get("county", "UNK") for r in rows)
by_city   = collections.Counter(r.get("city", "?") for r in rows)

def fmt_row(r):
    return (
        f"- **{r.get('name','?')}** ({r.get('city','?')}, {r.get('county','?')}) - "
        f"{r.get('category','?')} - {r.get('rating','?')} stars ({r.get('review_count','?')} reviews) - "
        f"`{r.get('place_id','?')}`"
    )

new_rows   = [r for r in rows if r.get("status") == "new"]
ready_rows = [r for r in rows if r.get("status") == "ready"]
sent_rows  = [r for r in rows if r.get("status") == "sent"]

lines = []
lines.append("# WestCo outreach - daily dashboard\n")
lines.append(f"_Generated: {datetime.datetime.now().isoformat(timespec='seconds')}_\n")
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
lines.append(f"## NEW - ready to generate ({len(new_rows)})\n")
lines += [fmt_row(r) for r in new_rows] or ["_(none)_"]
lines.append("")
lines.append(f"## READY - site built, email drafted ({len(ready_rows)})\n")
lines += [fmt_row(r) + f" - site: `{r.get('generated_url','')}`" for r in ready_rows] or ["_(none)_"]
lines.append("")
lines.append(f"## SENT ({len(sent_rows)})\n")
lines += [fmt_row(r) + f" - sent {r.get('sent_at','')}" for r in sent_rows] or ["_(none)_"]
lines.append("")

Path("dashboard.md").write_text("\n".join(lines), encoding="utf-8")
print("[new_day] wrote dashboard.md")
'@

# Pipe the inline script to python on stdin
$dashScript | & $python -

# Open dashboard.md in the default Windows app
Invoke-Item $outPath
