"""Generate sites + emails for a hand-picked batch of 3 prospects.

Reads templates/landing.html, fills per-prospect content, writes:
  - sites/<slug>/index.html
  - emails/<slug>.md
Then updates data/prospects.csv (status -> ready, generated_url filled).

Re-runnable: rewrites files for the same slugs on each run.
"""
from __future__ import annotations
import csv, json, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "templates"
DEFAULT_TEMPLATE = "landing.html"
CSV_PATH = ROOT / "data" / "prospects.csv"

# Cache templates so we don't re-read them per prospect.
_template_cache: dict[str, str] = {}
def load_template(name: str) -> str:
    if name not in _template_cache:
        _template_cache[name] = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    return _template_cache[name]
PAGES_BASE = "https://castanedanetworks.github.io/westco-outreach-sites"
WESTCO_PHONE = "(213) 522-9136"
WESTCO_TEL = "+12135229136"
YEAR = "2026"
BUILT_ON = "May 2026"

# CSV column order — must match scrape_maps.py
COLS = ['place_id','name','slug','address','city','county','phone','rating','review_count','category','reviews_json','status','generated_url','created_at','sent_at','replied_at','notes']


# --------------------------------------------------------------------------- #
# Per-prospect content. Hand-crafted per business — references real reviews.
# --------------------------------------------------------------------------- #

CONTENT = {

    # ============ 1. WRLDWIDE BARBERSHOP (Pomona) ============
    "wrldwide-barbershop-pomona": {
        "template": "landing-barbershop.html",
        "meta_description": "WRLDWIDE BARBERSHOP — Pomona's most-booked chair. 5.0 stars across 443 reviews. Open 7 days. Walk-ins + appointments on Indian Hill Blvd.",
        # Black + silver luxury palette. Their brand identity is monochrome —
        # we use a cool silver for kickers/accents (clearly distinct from the
        # warm-white body chalk) and a darker graphite for radial glows and
        # hover states. The hero's second-line headline uses a separate chrome
        # gradient class — these vars don't drive that.
        "brand": {
            "50":  "#f1f2f5",
            "100": "#d8dade",
            "500": "#c0c5cc",
            "600": "#989aa3",
            "700": "#6e7077",
            "900": "#1a1b1e",
        },
        "trust_badge": "5.0 stars on Google — 443 reviews",
        # barbershop template — split hero, kickers, pull quote, marquee, barbers
        "eyebrow_kicker":      "@wrldwidebarbershop · Indian Hill Blvd · Pomona, CA",
        "hero_headline_part_1": "SHARP FADES.",
        "hero_headline_part_2": "REAL FAMILY ENERGY.",
        "about_kicker":        "What people say",
        "pull_quote_text":     "Fire cuts, real family energy in the shop, and a perfect spot right next to Tierra Mia. Easily the best barbershop in Pomona.",
        "pull_quote_author":   "Owen Brown",
        "marquee_text":        "WRLDWIDE BARBERSHOP · POMONA · @WRLDWIDEBARBERSHOP · OPEN 7 DAYS · WALK-INS + APPOINTMENTS · SHARP FADES · LINE-UPS · BEARDS · KIDS' CUTS · 5.0 ★ ON GOOGLE",
        "barbers_lineup":      "ALEX · ERIK · CHUY",
        "visit_heading":       "On Indian Hill. Next to Tierra Mia.",
        "gallery_heading":     "Fresh work.",
        "gallery_caption":     "Photos · from the shop's Instagram",
        "gallery_label_1":     "Fade",
        "gallery_label_2":     "Line-up",
        "gallery_label_3":     "Beard",
        "gallery_label_4":     "Kids' cut",
        "gallery_label_5":     "Hot towel",
        "gallery_label_6":     "Walk-in",
        # Kept for backwards-compat with default template — unused by barbershop template
        "hero_headline": "Pomona's most-booked chair.",
        "hero_subhead": "Sharp fades, line-ups that hold, and real family energy in the shop. Walk in, sit down, walk out feeling brand new.",
        "value_props": [
            ("Time on every cut",  "Reviewers keep saying the same thing — nobody gets rushed through that chair."),
            ("Sharp lines, clean fades", "From a quick taper to a full skin-fade with a beard line-up to match."),
            ("Real family energy",  "Owen's review nailed it: it's the kind of shop you bring your son to."),
        ],
        "about_heading": "Built for Pomona, by people from Pomona.",
        "about_paragraph": "WRLDWIDE BARBERSHOP sits on Indian Hill Blvd, right next door to Tierra Mia Coffee. Five chairs, a deep bench of barbers — Alex, Erik, Chuy — and a regular flow of dads bringing their kids in for their first cut.",
        "about_paragraph_2": "Five stars across 443 Google reviews isn't an accident. People come back because the cuts hold, the conversation is good, and nobody walks out unhappy.",
        "services_heading": "What we do.",
        "services_intro": "Open 7 days, walk-ins welcome. Saturdays book up early — call ahead if you want a specific barber.",
        "services": [
            ("Signature fade",          "Skin, low, mid, or high — whatever the cut calls for, lined up clean."),
            ("Beard work",              "Shape, line-up, hot-towel detail. Comes with most cuts or solo."),
            ("Kids' cuts",              "Younger clients get the same time and care — easy first-haircut energy."),
            ("Hot-towel shave",         "Old-school straight razor finish with hot towels and aftershave."),
            ("Walk-ins welcome",        "Weekday afternoons rarely have a wait. Saturday mornings, call first."),
        ],
        "reviews_heading": "Pomona on WRLDWIDE.",
        "visit_paragraph": "Indian Hill Blvd in Pomona, right next to Tierra Mia. Open 7 days — walk-ins and appointments both welcome.",
        "hours": {
            "mon": "10:00 AM – 7:00 PM",
            "tue": "10:00 AM – 7:00 PM",
            "wed": "10:00 AM – 7:00 PM",
            "thu": "10:00 AM – 7:00 PM",
            "fri": "10:00 AM – 8:00 PM",
            "sat": "9:00 AM – 7:00 PM",
            "sun": "10:00 AM – 4:00 PM",
        },
        "cta_heading": "Ready for a fresh cut?",
        "cta_body": "Walk in, or call to lock in a chair with the barber you want. We'll handle the rest.",
        # email content (hook + sentences)
        "email_subject": "built WRLDWIDE BARBERSHOP a website preview",
        "email_body": (
            "owen's review called out the 'real family energy' in your shop and said alex never misses — 443 five-star reviews say he's not the only one.\n\n"
            "you're crushing it on Google but anyone who searches WRLDWIDE BARBERSHOP on their phone just hits a maps pin, no website.\n\n"
            "built you a preview using your actual reviews and the way people talk about the shop: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, easy drive to pomona if you'd rather meet in person."
        ),
    },

    # ============ 2. My BarberShop (El Monte) ============
    "my-barbershop-el-monte": {
        "meta_description": "My BarberShop — Ruben's one-man crew in El Monte. 4.9 stars on Google. 7-year regulars, sharp cuts, appointments fill up early on Tyler Ave.",
        "brand": {
            "50":  "#eff6ff",
            "100": "#dbeafe",
            "500": "#1d4ed8",
            "600": "#1e40af",
            "700": "#1e3a8a",
            "900": "#172554",
        },
        "trust_badge": "4.9 stars — 7-year regulars",
        "hero_headline": "El Monte's one-man crew. Always has been.",
        "hero_subhead": "Ruben books 30–40 cuts a day in the SGV. No rotating chairs, no shortcuts — just your barber, every time. Call the day before if you want in.",
        "value_props": [
            ("One barber, one chair",    "Ruben handles every cut himself. Same hands every visit."),
            ("Takes the time",           "Daniel said it: 'tell him how you want it' and he doesn't cut corners. Most cuts run 30–45 min."),
            ("7-year regulars",          "Manuel's been coming for seven years without a single off-day. That kind of consistency is rare."),
        ],
        "about_heading": "Same chair, same hands, 30–40 fresh cuts a day.",
        "about_paragraph": "My BarberShop on Tyler Ave is exactly what it sounds like — one barber, Ruben, who's been keeping the SGV looking sharp for years. No second chair, no extra hands, no rushing through to clear a queue.",
        "about_paragraph_2": "It's the spot regulars send their kids and their dads. Edgar called it 'a one man crew, but holds it down for the SGV' — that's the whole pitch right there.",
        "services_heading": "What's on the menu.",
        "services_intro": "Appointments fill up fast — call the day before. Walk-ins work mid-week if Ruben has a gap.",
        "services": [
            ("Signature cut",       "Whatever shape and length you want, dialed in over a real conversation."),
            ("Fade + line-up",      "Skin, low, mid, high. Crisp lines, sharp temples."),
            ("Beard work",          "Shape, edge-up, hot towel detail."),
            ("Kids' cuts",          "Younger clients welcome. Ruben's patient with first haircuts."),
            ("Standing appointments", "Weekly or bi-weekly slots — locked in so you never have to chase."),
        ],
        "reviews_heading": "What the SGV says.",
        "visit_paragraph": "Tyler Ave in El Monte, easy parking. Call the day before if you have a specific time in mind — Saturdays especially.",
        "hours": {
            "mon": "Closed",
            "tue": "9:00 AM – 6:00 PM",
            "wed": "9:00 AM – 6:00 PM",
            "thu": "9:00 AM – 6:00 PM",
            "fri": "9:00 AM – 7:00 PM",
            "sat": "8:00 AM – 5:00 PM",
            "sun": "10:00 AM – 3:00 PM",
        },
        "cta_heading": "Book your standing slot.",
        "cta_body": "Tell Ruben what you want, when you want it. That's the whole formula — and the reason regulars don't leave.",
        "email_subject": "built My BarberShop a website preview",
        "email_body": (
            "manuel said ruben has been his barber for 7 years without disappointing once — that's the whole pitch right there.\n\n"
            "you're 4.9 stars across 29 Google reviews but if someone searches for the spot on their phone they don't find you, just the maps pin.\n\n"
            "built you a preview using your actual reviews and the one-man-crew thing edgar called out: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, 15 minutes from el monte if you'd rather meet."
        ),
    },

    # ============ 3. serenity pet grooming (Pomona) ============
    "serenity-pet-grooming-pomona": {
        "template": "landing-petgroomer.html",
        "meta_description": "serenity pet grooming — Pomona dog and pet grooming on Phillips Blvd. 4.8 stars on Google, gentle with anxious dogs, next-day appointments available.",
        "brand": {
            # warm sage palette — feels nothing like a SaaS landing page
            "50":  "#eef3ed",
            "100": "#dbe7d9",
            "500": "#6b8f6b",
            "600": "#557455",
            "700": "#3f5a3f",
            "900": "#1f2e1f",
        },
        "trust_badge": "small + friendly · pomona, ca",
        "hero_headline_part_1": "Anxious pup?",
        "hero_headline_part_2": "They walk out happy.",
        "hero_polaroid_caption": "first visit · no stress",
        "visit_heading": "Phillips Blvd. Easy parking. Friendly door.",
        # Kept for backwards-compat with default template — unused by petgroomer template
        "hero_headline": "Anxious pup? They come out happy.",
        "hero_subhead": "Patient grooming for dogs who don't love it. Next-day bookings, friendly staff, and the kind of care that gets dogs walking back in willingly.",
        "value_props": [
            ("Calm with anxious dogs",  "Dany's usually-nervous dog came out happy. That's the whole reason people drive across town to come here."),
            ("Ready for the photos",    "Roxanna books trims around Christmas pictures — they know what 'photo-ready' actually means."),
            ("Next-day bookings",       "No need to plan three weeks out — call and check, openings happen fast."),
        ],
        "about_heading": "A grooming salon dogs actually like.",
        "about_paragraph": "serenity pet grooming sits on Phillips Blvd in Pomona. Small, friendly staff, easy parking, and a real talent for handling nervous dogs.",
        "about_paragraph_2": "Most reviews say the same thing in different words — the staff is gentle, the prices are fair, and your dog comes out looking great without the stress signals you'd see at a bigger chain.",
        "services_heading": "What we offer.",
        "services_intro": "Full grooming, trims, nail care, and bath services. Call ahead to talk about your dog — coat type, temperament, and any specific notes.",
        "services": [
            ("Full grooming",           "Bath, brush-out, haircut, nails, ears. Everything your dog needs in one visit."),
            ("Trims & bath",            "Lighter package — bath, blow-dry, trim around face and feet."),
            ("Nail care",               "Quick nail clipping or grinding, in and out."),
            ("Anxious-pet care",        "We take extra time with dogs who don't love grooming. No shortcuts, no force."),
            ("Holiday-photo grooming",  "Books up around Christmas and Easter — get on the schedule early."),
        ],
        "reviews_heading": "What pet parents say.",
        "visit_paragraph": "Phillips Blvd in Pomona. Friendly staff, easy parking, and they'll work with your dog's pace.",
        "hours": {
            "mon": "By appointment",
            "tue": "9:00 AM – 5:00 PM",
            "wed": "9:00 AM – 5:00 PM",
            "thu": "9:00 AM – 5:00 PM",
            "fri": "9:00 AM – 5:00 PM",
            "sat": "9:00 AM – 4:00 PM",
            "sun": "Closed",
        },
        "cta_heading": "Book your dog's next visit.",
        "cta_body": "Call to set up — next-day bookings are often available. Tell us about your dog and we'll plan around them.",
        "email_subject": "built serenity pet grooming a website preview",
        "email_body": (
            "dany's review where she said her usually-anxious dog came out happy stuck with me — that's exactly what every nervous-dog owner is searching for.\n\n"
            "you're 4.8 stars on Google but anyone who looks you up on their phone just hits a maps pin, no website.\n\n"
            "built you a preview using your real reviews — including the one about being ready for Christmas photos: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, easy drive to pomona if you'd rather meet in person."
        ),
    },
}


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def initial_of(name: str) -> str:
    return (name.strip()[:1] or "G").upper()

def split_address(addr: str) -> tuple[str, str]:
    """E.g. '596 Indian Hill Blvd, Pomona, CA 91766' -> ('596 Indian Hill Blvd', 'Pomona, CA 91766')."""
    parts = [p.strip() for p in addr.split(",")]
    if len(parts) >= 3:
        return parts[0], ", ".join(parts[1:])
    if len(parts) == 2:
        return parts[0], parts[1]
    return addr.strip(), ""

def tel_form(display: str) -> str:
    digits = re.sub(r"\D", "", display)
    if len(digits) == 10:
        digits = "1" + digits
    return "+" + digits

def google_maps_url(name: str, address: str) -> str:
    from urllib.parse import quote_plus
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(name + ' ' + address)}"


def render_one(row: dict, content: dict) -> str:
    slug = row["slug"]
    addr_1, addr_2 = split_address(row["address"])
    template = load_template(content.get("template", DEFAULT_TEMPLATE))

    # Reviews from CSV
    try:
        captured = json.loads(row["reviews_json"] or "[]")
    except Exception:
        captured = []
    # Keep only entries with actual text
    captured = [r for r in captured if (r.get("text") or "").strip()]

    canonical = f"{PAGES_BASE}/sites/{slug}/"

    sub: dict[str, str] = {
        "business_name":       row["name"],
        "city":                row["city"],
        "meta_description":    content["meta_description"],
        "canonical_url":       canonical,
        "ga4_id":              "{{ga4_id}}",   # leave placeholder for Louis
        "brand_50":            content["brand"]["50"],
        "brand_100":           content["brand"]["100"],
        "brand_500":           content["brand"]["500"],
        "brand_600":           content["brand"]["600"],
        "brand_700":           content["brand"]["700"],
        "brand_900":           content["brand"]["900"],
        "phone_tel":           tel_form(row["phone"]),
        "phone_display":       row["phone"],
        "trust_badge":         content["trust_badge"],
        "hero_headline":       content.get("hero_headline", ""),
        "hero_subhead":        content["hero_subhead"],
        # pet-groomer template only (default template ignores these via no-op substitution)
        "hero_headline_part_1": content.get("hero_headline_part_1", ""),
        "hero_headline_part_2": content.get("hero_headline_part_2", ""),
        "hero_polaroid_caption": content.get("hero_polaroid_caption", ""),
        "visit_heading":       content.get("visit_heading", f"Come see us in {row['city']}"),
        # barbershop template only
        "eyebrow_kicker":      content.get("eyebrow_kicker", ""),
        "about_kicker":        content.get("about_kicker", "What people say"),
        "pull_quote_text":     content.get("pull_quote_text", ""),
        "pull_quote_author":   content.get("pull_quote_author", ""),
        "marquee_text":        content.get("marquee_text", ""),
        "barbers_lineup":      content.get("barbers_lineup", ""),
        "gallery_heading":     content.get("gallery_heading", "Fresh work."),
        "gallery_caption":     content.get("gallery_caption", "Photos · from the shop's Instagram"),
        "gallery_label_1":     content.get("gallery_label_1", "Fade"),
        "gallery_label_2":     content.get("gallery_label_2", "Line-up"),
        "gallery_label_3":     content.get("gallery_label_3", "Beard"),
        "gallery_label_4":     content.get("gallery_label_4", "Kids' cut"),
        "gallery_label_5":     content.get("gallery_label_5", "Hot towel"),
        "gallery_label_6":     content.get("gallery_label_6", "Walk-in"),
        "rating":              row["rating"],
        "review_count":        row["review_count"],
        "value_prop_1_title":  content["value_props"][0][0],
        "value_prop_1_body":   content["value_props"][0][1],
        "value_prop_2_title":  content["value_props"][1][0],
        "value_prop_2_body":   content["value_props"][1][1],
        "value_prop_3_title":  content["value_props"][2][0],
        "value_prop_3_body":   content["value_props"][2][1],
        "about_heading":       content["about_heading"],
        "about_paragraph":     content["about_paragraph"],
        "about_paragraph_2":   content["about_paragraph_2"],
        "services_heading":    content["services_heading"],
        "services_intro":      content["services_intro"],
        "service_1_title":     content["services"][0][0],
        "service_1_body":      content["services"][0][1],
        "service_2_title":     content["services"][1][0],
        "service_2_body":      content["services"][1][1],
        "service_3_title":     content["services"][2][0],
        "service_3_body":      content["services"][2][1],
        "service_4_title":     content["services"][3][0],
        "service_4_body":      content["services"][3][1],
        "service_5_title":     content["services"][4][0],
        "service_5_body":      content["services"][4][1],
        "reviews_heading":     content["reviews_heading"],
        "google_maps_url":     google_maps_url(row["name"], row["address"]),
        "visit_paragraph":     content["visit_paragraph"],
        "address_line_1":      addr_1,
        "address_line_2":      addr_2,
        "hours_mon":           content["hours"]["mon"],
        "hours_tue":           content["hours"]["tue"],
        "hours_wed":           content["hours"]["wed"],
        "hours_thu":           content["hours"]["thu"],
        "hours_fri":           content["hours"]["fri"],
        "hours_sat":           content["hours"]["sat"],
        "hours_sun":           content["hours"]["sun"],
        "cta_heading":         content["cta_heading"],
        "cta_body":            content["cta_body"],
        "westco_phone_tel":    WESTCO_TEL,
        "westco_phone_display": WESTCO_PHONE,
        "year":                YEAR,
        "built_on":            BUILT_ON,
    }

    # Reviews — fill up to 5, blank the rest so the post-process pass can drop them
    for i in range(1, 6):
        if i <= len(captured):
            rev = captured[i - 1]
            sub[f"review_{i}_text"]    = rev.get("text", "").replace('"', "“")
            sub[f"review_{i}_author"]  = rev.get("author", "Google reviewer")
            sub[f"review_{i}_initial"] = initial_of(rev.get("author", "G"))
        else:
            sub[f"review_{i}_text"]    = "__BLANK_REVIEW__"
            sub[f"review_{i}_author"]  = ""
            sub[f"review_{i}_initial"] = ""

    # Apply substitutions
    rendered = template
    for k, v in sub.items():
        rendered = rendered.replace("{{" + k + "}}", str(v))

    # Strip any review figure whose blockquote contains the blank sentinel.
    # The tempered token `(?:(?!</figure>).)*?` keeps the match from crossing
    # figure boundaries (a plain `.*?` would eat earlier good figures to
    # reach the first sentinel). Class-agnostic so it works across templates.
    rendered = re.sub(
        r'\s*<figure\b[^>]*>'
        r'(?:(?!</figure>).)*?"__BLANK_REVIEW__"(?:(?!</figure>).)*?</figure>',
        '',
        rendered,
        flags=re.DOTALL,
    )

    return rendered


def render_email(row: dict, content: dict) -> str:
    slug = row["slug"]
    preview_url = f"{PAGES_BASE}/sites/{slug}/"
    body = content["email_body"].replace("{preview_url}", preview_url)
    return f"Subject: {content['email_subject']}\n\n{body}\n"


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open("r", encoding="utf-8", newline="")))
    by_slug = {r["slug"]: r for r in rows}

    updated = []
    for slug, content in CONTENT.items():
        if slug not in by_slug:
            print(f"!! no CSV row for slug={slug}")
            continue
        row = by_slug[slug]
        html = render_one(row, content)
        email = render_email(row, content)

        site_dir = ROOT / "sites" / slug
        site_dir.mkdir(parents=True, exist_ok=True)
        (site_dir / "index.html").write_text(html, encoding="utf-8")

        email_path = ROOT / "emails" / f"{slug}.md"
        email_path.parent.mkdir(parents=True, exist_ok=True)
        email_path.write_text(email, encoding="utf-8")

        row["status"] = "ready"
        row["generated_url"] = f"{PAGES_BASE}/sites/{slug}/"
        updated.append(slug)
        print(f"  generated  {slug}  ->  {row['generated_url']}")

    # Rewrite CSV in place
    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in COLS})

    print(f"\nDone. {len(updated)} prospects marked ready.")


if __name__ == "__main__":
    main()
