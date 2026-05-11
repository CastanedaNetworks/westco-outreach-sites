# WestCo outreach

Local outreach pipeline for **WestCo App Studio** (Castaneda Networks).
Goal: find SoCal businesses on Google Maps that **don't have a website**,
generate a personalized website preview for each on free GitHub Pages
hosting, and write a personalized cold email referencing their real
Google reviews.

**Service area:** Los Angeles County, San Bernardino + Riverside counties
(Inland Empire), Orange County.

**Cost:** $0 additional. Uses only Playwright (free), the Claude Code
subscription (no API key needed), and GitHub Pages (free).

---

## Repo layout

```
westco-outreach/
├── data/
│   ├── prospects.csv     # main lead database
│   ├── sent.csv          # what you've sent
│   └── replies.csv       # responses (logged manually)
├── templates/
│   └── landing.html      # ONE master template — Tailwind CDN, {{placeholders}}
├── sites/                # generated per-prospect sites (one folder per slug)
├── emails/               # one .md per prospect — the cold email draft
├── scripts/
│   ├── scrape_maps.py    # Playwright Google Maps scraper
│   ├── deploy.sh         # commit sites + push to gh-pages (bash)
│   ├── deploy.ps1        # same, native PowerShell
│   ├── new_day.sh        # pull + regenerate dashboard.md + open it (bash)
│   └── new_day.ps1       # same, native PowerShell
├── docs/
│   └── email_framework.md # tone + sentence-structure rules for cold emails
├── dashboard.md          # generated daily — current pipeline state
└── README.md             # you are here
```

---

## One-time setup

You only have to do this once.

### 1. Python + Playwright

```powershell
cd C:\Users\louis\westco-outreach
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install playwright
python -m playwright install chromium
```

Git Bash:
```bash
cd westco-outreach
python -m venv .venv
source .venv/Scripts/activate
pip install playwright
python -m playwright install chromium
```

You don't have to keep the venv "activated" — every command in this
README can also be run with the absolute path
`.\.venv\Scripts\python.exe ...` if that's easier.

The scraper uses Playwright in **headed mode** by default — a real
Chromium window opens so it looks like a human is browsing. Don't pass
`--headless` until you have a feel for how Maps responds to you.

### 2. Create the GitHub repo + Pages

1. Create a new public repo on GitHub, e.g. `westco-outreach-sites`.
   (Sites have to be public for free Pages hosting.)
2. **Don't** put anything sensitive in this repo — leads will be visible
   in git history. The CSV has phone numbers and addresses, all of which
   are already public on Google Maps, but be deliberate about it.
3. From inside `westco-outreach/`:

   ```bash
   git init
   git branch -M main
   git remote add origin git@github.com:<you>/westco-outreach-sites.git
   git checkout -b gh-pages
   git add .
   git commit -m "Initial scaffold"
   git push -u origin gh-pages
   ```

4. On GitHub, go to **Settings → Pages** and set:
   - **Source:** Deploy from a branch
   - **Branch:** `gh-pages` / `/ (root)`
   - Save. After a minute the site is live at
     `https://<you>.github.io/westco-outreach-sites/`.

Each generated site will then live at
`https://<you>.github.io/westco-outreach-sites/sites/<slug>/`.

### 3. Add a Google Analytics 4 property (optional but recommended)

1. analytics.google.com → create a property called "WestCo previews".
2. Add a Web data stream pointing at
   `https://<you>.github.io/westco-outreach-sites`.
3. Copy the **Measurement ID** (looks like `G-XXXXXXXXXX`).
4. When Claude Code generates each site it will substitute this into the
   `{{ga4_id}}` placeholder. Either:
   - keep the ID in your head and paste it when you ask Claude to
     generate the next batch, or
   - search-and-replace it once after generation in `sites/`.

This lets you see which previews actually get opened by the prospect.

### 4. Aged business inbox

Sending happens **manually** from your existing aged
`admin@castanedanetworks.com` inbox — no SMTP automation. This is on
purpose: a hand-sent email from an old domain has the best deliverability
and the lowest spam risk.

---

## Daily workflow

A clean run looks like this. You can do as few or as many steps as you
have time for in a day.

### 1. Scrape new prospects

PowerShell (the venv python works without activation):
```powershell
.\.venv\Scripts\python.exe scripts\scrape_maps.py --category "auto repair" --city "Covina" --max 25
.\.venv\Scripts\python.exe scripts\scrape_maps.py --category "barbershops" --city "Pomona" --max 25
.\.venv\Scripts\python.exe scripts\scrape_maps.py --category "pet groomers" --city "Riverside" --max 25
```

The scraper:
- skips listings that already have a Website button (the whole point)
- captures the top 5 Google reviews for each kept listing
- tags county automatically (LA / SB / RIV / OR)
- dedupes against the existing CSV by `place_id`
- adds delays so you don't look like a bot — expect ~3–5 min per 25 listings

**Categories to rotate through:** auto repair, salons, barbershops,
restaurants, dental offices, chiropractors, real estate offices,
landscaping, plumbing, HVAC, law offices, accountants, mechanics,
tattoo shops, gyms, pet groomers, cleaning services.

**Cities seeded in the county map:** West Covina, Covina, Baldwin Park,
Pomona, Ontario, Rancho Cucamonga, Riverside, San Bernardino, Anaheim,
Orange, Santa Ana, Fullerton, Garden Grove, Long Beach, Whittier,
Pasadena, El Monte, Downey, Norwalk, Fontana. Plus their neighbors —
see `CITY_COUNTY` in `scripts/scrape_maps.py`.

### 2. Generate sites + emails (Claude Code does this)

Open Claude Code in the project root and say something like:

> "Generate sites and email drafts for the next 5 NEW prospects in
> `data/prospects.csv`. Use `templates/landing.html`. Put each site at
> `sites/<slug>/index.html`. Put each email at `emails/<slug>.md`. Set
> their status to `ready` and fill in `generated_url`. The GA4 ID is
> `G-XXXXXXXXXX`."

Claude will:
- read each prospect's category, rating, reviews, etc.
- pick a sensible accent color
- write hero copy, services, value props, and hours based on category
- fill in the 5 review quotes with the real reviews from `reviews_json`
- write a cold email in `emails/<slug>.md` that references something
  specific from a real review (proving you actually read them)

Spot-check a few before deploying. Edit any that feel off.

### 3. Deploy

PowerShell (Windows-native):
```powershell
.\scripts\deploy.ps1
# or .\scripts\deploy.ps1 -Branch gh-pages
```

Git Bash / WSL / macOS:
```bash
./scripts/deploy.sh
```

Both stage `sites/`, `data/prospects.csv`, and `dashboard.md`, commit
with a timestamp, push to `gh-pages`, and print the live URLs of any
newly added site folders. GitHub Pages takes 30–90 seconds to publish.

### 4. Send the emails by hand

Open `emails/<slug>.md`, copy the subject + body into your inbox, paste
the live URL, send. Then update the row in `prospects.csv`:

- `status` → `sent`
- `sent_at` → today's ISO date
- `notes` → whatever you want

You can edit `prospects.csv` directly in a spreadsheet, just save as CSV.

### 5. Log replies

When someone responds, add a row to `data/replies.csv` with the
sentiment and what you plan to do next, and bump that prospect's
`status` to `replied` (or `closed` / `dead`).

### 6. Refresh the dashboard

PowerShell:
```powershell
.\scripts\new_day.ps1
```

Git Bash / WSL / macOS:
```bash
./scripts/new_day.sh
```

Pulls latest, rebuilds `dashboard.md` from the CSV, opens it.

---

## prospects.csv schema

| column          | notes |
|-----------------|-------|
| place_id        | `wco_<sha1[:16]>` of name+address — stable, dedupe key |
| name            | business name from the listing header |
| slug            | url-safe, used for `sites/<slug>/` |
| address         | full address string from Maps |
| city            | from your scraper input |
| county          | LA / SB / RIV / OR / UNK |
| phone           | E.164-ish or display format, as Maps gave it |
| rating          | e.g. `4.7` |
| review_count    | integer (no commas) |
| category        | from Maps' category button |
| reviews_json    | JSON array of `{author, text}` — the top 5 |
| status          | new → ready → sent → opened → replied → closed / dead |
| generated_url   | full URL on GitHub Pages once deployed |
| created_at      | ISO timestamp of scrape |
| sent_at         | ISO date — fill in when you send |
| replied_at      | ISO date — fill in on reply |
| notes           | freeform |

---

## Troubleshooting

**The scraper opens Maps but no results appear.**
You probably hit a CAPTCHA or a region prompt. Solve it manually in the
window — the scraper waits for the results feed. After you solve it,
the next run usually goes through clean.

**Most rows have empty rating / review_count.**
Google A/B tests their detail panel. Open `scripts/scrape_maps.py`,
find `get_rating_and_count()` and adjust the selectors. The function
already has a regex fallback that catches most variants.

**`has_website()` is missing sites that clearly have a website.**
Same fix — add the new selector to the list in `has_website()`. Better
to over-skip (false positives = you waste no time on already-online
businesses) than to under-skip.

**Reviews come back empty.**
The reviews tab sometimes lazy-loads. Increase the wait in
`get_reviews()` or run with `--debug` and inspect the screenshot.

**GitHub Pages 404.**
Pages takes up to 90 seconds after a push. Also confirm Settings →
Pages is pointed at `gh-pages` / root and that the repo is public.

**Deliverability — my emails are landing in spam.**
This pipeline is built for hand-sending from an aged inbox; that's the
biggest deliverability lever. Beyond that: don't include the preview
link as the very first thing in the message, vary subject lines, and
never send more than ~20–30/day from a single mailbox.

**Don't I need permission to put their business on a webpage?**
The preview pages are unindexed (`<meta name="robots">` is the easy
addition if you want to be strict — see template), they clearly say
"Website preview created by WestCo App Studio — not the official site"
in the footer, and they only use information already public on Google
Maps. If a prospect asks you to take their preview down, do it
immediately: `rm -rf sites/<slug>` and push.

---

## What's intentionally not here

- No paid APIs (Places, SerpAPI, Outscraper, Apollo).
- No Anthropic API key — generation runs through your Claude Code
  subscription via this exact repo.
- No SMTP / send automation — manual send from your aged inbox.
- No CRM. The CSV + the `emails/` folder + the dashboard *is* the CRM.

If any of those constraints loosen later, the schema is designed to
absorb it (e.g. add an `apollo_email` column and a sender script that
reads `status=ready,sent_at=""`).
