# WestCo cold email framework

This is the rulebook for every cold email generated from a row in
`data/prospects.csv`. The file in `emails/<slug>.md` should follow it
exactly — short, plain text, lowercase tone, no fluff.

Each generated email file should be Markdown with:

```
Subject: <subject line>

<email body>
```

---

## Email structure (4–5 sentences max, plain text, lowercase tone)

### Subject patterns

Rotate per email, all lowercase. Pick whichever fits the row best:

- `built {business_name} a website preview`
- `{owner_first_name}, quick thing for {business_name}`
- `saw your reviews — made you something`
- `{business_name} without a website?? here`
- `for {business_name}`

If `owner_first_name` is unknown, fall back to a non-name pattern.

### Sentence 1 — HOOK

Reference ONE specific review by the reviewer's first name. Quote a
concrete detail. Never "I noticed you have great reviews."

> _good example:_ "carlos's review where he said you got him in same-day
> for a brake job stuck with me — that kind of turnaround is rare."

> _bad example:_ "I noticed you have wonderful reviews on Google Maps!"

### Sentence 2 — GAP

One sentence stating the obvious gap, casually.

> _example:_ "you're crushing it on reviews but anyone who googles you on
> their phone hits a dead end."

### Sentence 3 — PITCH

What I built. Include the preview link.

> _example:_ "built you a preview using your actual reviews and services:
> {preview_url}"

### Sentence 4 — CTA

Low-friction offer.

> _example:_ "takes 30 seconds to look. if you want it live this week, i
> can have it up for $1,497 — text or call me at (XXX) XXX-XXXX."

### Sentence 5 — OPTIONAL local note

> _example:_ "i'm in west covina if you'd rather meet in person."

---

## Tone rules

- **Lowercase everything** except business names and proper nouns
  (the business owner's name, the city, brand names like Google).
- **No emojis.** Max one exclamation point in the whole email — and
  usually zero.
- **Banned phrases** (never use these): "I hope this email finds you
  well", "passionate", "synergy", "I'd love to", "quick 15-minute
  call", "circle back", "touch base", "leverage", "as per", "kindly".
- Write like texting a friend who runs a business.
- Never apologize for cold outreach.
- **The preview link IS the meeting.** Don't ask for a call to "explore
  fit" or "see if it makes sense" — the work is already done.

---

## Mechanics for the generator (me, tomorrow)

When asked to generate emails for status=new rows:

1. Parse `reviews_json` for each prospect. Pick the most specific
   review — the one with a concrete detail (a service, a price, a
   turnaround time, a staff name) — for Sentence 1. Skip generic
   five-star "great service!" reviews.
2. The reviewer's first name goes into Sentence 1 directly. If only a
   last initial is available ("Carlos M."), use the first name.
3. Sentence 3's `{preview_url}` is the `generated_url` column — built
   as `https://<gh_user>.github.io/<gh_repo>/sites/<slug>/`.
4. Sentence 4's phone number is the WestCo phone (placeholder until
   Louis fills it in). Use Louis's mobile or business line.
5. Sentence 5 — include only when the prospect is in or adjacent to a
   city WestCo operates from (default: West Covina). For prospects in
   Riverside/Orange County, drop sentence 5 or rewrite to "happy to
   drive out if you'd rather meet."
6. After writing the email, update the prospect row:
   - `status` → `ready`
   - `generated_url` → the live URL
   - leave `sent_at` empty (Louis fills it after sending by hand)

---

## Worked example

CSV row:
```
name: Joe's Auto Repair
slug: joes-auto-repair-covina
city: Covina
rating: 4.8
review_count: 73
reviews_json: [{"author":"Carlos M.","text":"Got my brakes done same day, fair price, Joe explained everything."}, ...]
```

`emails/joes-auto-repair-covina.md`:
```
Subject: built Joe's Auto Repair a website preview

carlos's review where he said you did his brakes same-day and walked him
through the work stuck with me — that kind of trust is the whole
business in 2026.

you're crushing it on reviews but anyone who googles you on their phone
hits a dead end.

built you a preview using your real reviews and services:
https://castaneda-networks.github.io/westco-outreach-sites/sites/joes-auto-repair-covina/

takes 30 seconds to look. if you want it live this week, i can have it
up for $1,497 — text or call me at (XXX) XXX-XXXX.

i'm in west covina if you'd rather meet in person.
```
