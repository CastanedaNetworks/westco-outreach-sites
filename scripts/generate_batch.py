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
        "meta_description": "WRLDWIDE BARBERSHOP on Indian Hill Blvd, Pomona. 5.0 stars across 443 Google reviews. Alex, Erik, Chuy and Alvaro on the chairs, open every day.",
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
        "trust_badge": "5.0 · 443 Google reviews",
        # barbershop template — split hero, kickers, pull quote, marquee, barbers
        "eyebrow_kicker":      "@wrldwidebarbershop · 596 Indian Hill Blvd · Pomona, CA",
        "hero_headline_part_1": "SHARP FADES.",
        "hero_headline_part_2": "REAL FAMILY ENERGY.",
        "about_kicker":        "443 reviews. one stuck out.",
        "pull_quote_text":     "Fire cuts, real family energy in the shop, and a perfect spot right next to Tierra Mia. Easily the best barbershop in Pomona.",
        "pull_quote_author":   "Owen Brown",
        "marquee_text":        "WRLDWIDE BARBERSHOP · POMONA · @WRLDWIDEBARBERSHOP · OPEN 7 DAYS · WALK-INS + APPOINTMENTS · 596 INDIAN HILL BLVD · NEXT TO TIERRA MIA · 5.0 ★ ON GOOGLE",
        "barbers_lineup":      "ALEX · ERIK · CHUY · ALVARO",
        "visit_heading":       "On Indian Hill. Next to Tierra Mia.",
        "gallery_heading":     "On the chair this week.",
        "gallery_caption":     "Photos · from the shop's Instagram",
        "gallery_label_1":     "Fade",
        "gallery_label_2":     "Line-up",
        "gallery_label_3":     "Beard",
        "gallery_label_4":     "Kids' cut",
        "gallery_label_5":     "Hot towel",
        "gallery_label_6":     "Walk-in",
        # Kept for backwards-compat with default template — unused by barbershop template
        "hero_headline": "Pomona's chair. On Indian Hill since.",
        "hero_subhead": "Indian Hill Blvd, right next to Tierra Mia. Same chairs every day. Walk-ins welcome — call ahead for a specific barber.",
        "value_props": [
            ("Time on every cut",  "Reviewers keep saying the same thing — nobody gets rushed through that chair."),
            ("Sharp lines, clean fades", "From a quick taper to a full skin-fade with a beard line-up to match."),
            ("Real family energy",  "Owen's review nailed it: it's the kind of shop you bring your son to."),
        ],
        "about_heading": "Indian Hill. Same chairs.",
        "about_paragraph": "We're on Indian Hill Blvd, next to Tierra Mia. Alex has been on a chair here the longest — Chuy, Erik, and Alvaro round out the rotation. Most weeks one of them is cutting somebody's son for the first time.",
        "about_paragraph_2": "Five-star average across 443 reviews. The same four names — Alex, Erik, Chuy, Alvaro — show up in most of them. People book the same barber for years.",
        "services_heading": "Cuts.",
        "services_intro": "Open 7 days. Walk-ins fine most weekdays. Call ahead for a specific barber, especially Saturdays.",
        "services": [
            ("Signature fade",          "Skin, low, mid, or high. Tell us how you want it."),
            ("Beard work",              "Shape and line-up. Hot towel if you want it. Comes with most cuts."),
            ("Kids' cuts",              "Same chair, same time, less wiggle. First haircut or fifth — we're patient."),
            ("Hot-towel shave",         "Straight razor, hot towel, aftershave that actually stings."),
            ("Walk-ins",                "Weekday afternoons rarely have a wait. Saturday mornings, call first."),
        ],
        "reviews_heading": "443 reviews. Five stars.",
        "visit_paragraph": "596 Indian Hill Blvd, between Tierra Mia and the corner. Park out front. Walk in any day, or call to set a time.",
        "hours": {
            "mon": "10:00 AM – 7:00 PM",
            "tue": "10:00 AM – 7:00 PM",
            "wed": "10:00 AM – 7:00 PM",
            "thu": "10:00 AM – 7:00 PM",
            "fri": "10:00 AM – 8:00 PM",
            "sat": "9:00 AM – 7:00 PM",
            "sun": "10:00 AM – 4:00 PM",
        },
        "cta_heading": "Tap in.",
        "cta_body": "Walk in any day. Or call (909) 766-8039 and ask for Alex, Erik, Chuy, or Alvaro by name.",
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

    # ============ 4. Taperjes Barber Shop (El Monte) ============
    "taperjes-barber-shop-el-monte": {
        "template": "landing-barbershop.html",
        "meta_description": "Taperjes Barber Shop — Jes has been cutting hair on Valley Blvd in El Monte for years. 4.7 across 115 Google reviews. Walk-ins welcome.",
        "brand": {
            "50":  "#f1f2f5",
            "100": "#d8dade",
            "500": "#c0c5cc",
            "600": "#989aa3",
            "700": "#6e7077",
            "900": "#1a1b1e",
        },
        "trust_badge": "4.7 · 115 Google reviews",
        "eyebrow_kicker":      "12220 Valley Blvd · El Monte, CA · Jes since",
        "hero_headline_part_1": "JES.",
        "hero_headline_part_2": "EL MONTE'S BARBER.",
        "about_kicker":        "115 reviews. one says it best.",
        "pull_quote_text":     "Been going to Jes since I was in elementary school. Refuse to let anyone else cut my hair to this day.",
        "pull_quote_author":   "Jason Duran",
        "marquee_text":        "TAPERJES BARBER SHOP · EL MONTE · 12220 VALLEY BLVD · ONE CHAIR · IN AND OUT IN 20 · WALK-INS WELCOME · 4.7 ★ 115 GOOGLE REVIEWS",
        "barbers_lineup":      "JES",
        "visit_heading":       "On Valley Blvd. Park anywhere.",
        "gallery_heading":     "Recent cuts.",
        "gallery_caption":     "Photos · from the shop",
        "gallery_label_1":     "Fade",
        "gallery_label_2":     "Line-up",
        "gallery_label_3":     "Beard",
        "gallery_label_4":     "Kids' cut",
        "gallery_label_5":     "Trim",
        "gallery_label_6":     "Walk-in",
        "hero_headline":       "Jes on Valley Blvd.",
        "hero_subhead":        "One chair, one barber. Most regulars have been coming for years — some since elementary school.",
        "value_props": [
            ("One chair, no rotation",  "Jes cuts every head himself. Same hands every visit."),
            ("In and out in 20",        "Most cuts run twenty minutes. That's the formula."),
            ("Generational regulars",   "Some clients have been booking with Jes since they were kids."),
        ],
        "about_heading":       "On Valley Blvd. Years of regulars.",
        "about_paragraph":     "Jes has been cutting hair on Valley Blvd long enough that some of his regulars first sat in the chair as kids. Jason Duran's been coming since elementary school. David Alvarado started before Jes had his own shop. Most customers stay forever.",
        "about_paragraph_2":   "Jason now drives in from Ontario for his cuts. Sparta Chris calls it one of the best shops in SoCal. The reviews don't lead with the cut quality — they lead with the years.",
        "services_heading":    "Cuts.",
        "services_intro":      "One chair. Walk-ins fine most weekdays. Saturdays book up fast — call ahead.",
        "services": [
            ("Signature fade",  "Skin, low, mid, or high. Lined up clean."),
            ("Line-up",         "Tight edges, no fuss."),
            ("Kids' cuts",      "First haircut or fifth. Patient, no rush."),
            ("Beard",           "Shape and clean up. Quick."),
            ("Walk-in cut",     "In and out in 20 minutes most visits."),
        ],
        "reviews_heading":     "115 reviews. The years keep stacking.",
        "visit_paragraph":     "12220 Valley Blvd, El Monte. One chair, easy in and out. Park anywhere on the block.",
        "hours": {
            "mon": "Closed",
            "tue": "9:00 AM – 7:00 PM",
            "wed": "9:00 AM – 7:00 PM",
            "thu": "9:00 AM – 7:00 PM",
            "fri": "9:00 AM – 7:00 PM",
            "sat": "9:00 AM – 5:00 PM",
            "sun": "By appointment",
        },
        "cta_heading":         "Pull up.",
        "cta_body":            "Walk in any weekday. Or call (626) 582-8441 to lock a Saturday slot with Jes.",
        "email_subject":       "built Taperjes Barber Shop a website preview",
        "email_body": (
            "jason's review where he said he's been getting cuts from jes since elementary school stuck with me — and that he still drives back from ontario for them. that's the whole pitch.\n\n"
            "you're 4.7 stars across 115 Google reviews but anyone who searches Taperjes on their phone just hits a maps pin, no website.\n\n"
            "built you a preview using your real reviews — leaning into the years-with-regulars thing: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, 15 min from el monte if you'd rather meet."
        ),
    },

    # ============ 5. SN Barbershop (El Monte) ============
    "sn-barbershop-el-monte": {
        "template": "landing-barbershop.html",
        "meta_description": "SN Barbershop on Peck Rd, El Monte. Second-generation family shop with Jesse and Julian on the chairs. 4.7 across 101 Google reviews. Cash only.",
        "brand": {
            "50":  "#f1f2f5",
            "100": "#d8dade",
            "500": "#c0c5cc",
            "600": "#989aa3",
            "700": "#6e7077",
            "900": "#1a1b1e",
        },
        "trust_badge": "4.7 · 101 Google reviews",
        "eyebrow_kicker":      "4705 Peck Rd · El Monte · cash only (ATM inside)",
        "hero_headline_part_1": "JESSE. JULIAN.",
        "hero_headline_part_2": "PECK ROAD CHAIRS.",
        "about_kicker":        "101 reviews. one says it well.",
        "pull_quote_text":     "Julian made my hair look even better than imagined. I wasn't sure what cut to go with so he helped me decide. It came out looking amazing.",
        "pull_quote_author":   "Gordon Hebert",
        "marquee_text":        "SN BARBERSHOP · EL MONTE · 4705 PECK RD · JESSE & JULIAN · CASH ONLY · ATM INSIDE · WALK-INS + APPOINTMENTS · 4.7 ★ 101 GOOGLE REVIEWS",
        "barbers_lineup":      "JESSE · JULIAN",
        "visit_heading":       "On Peck Road. Cash only.",
        "gallery_heading":     "Recent cuts.",
        "gallery_caption":     "Photos · from the shop",
        "gallery_label_1":     "Fade",
        "gallery_label_2":     "Line-up",
        "gallery_label_3":     "Beard",
        "gallery_label_4":     "Kids' cut",
        "gallery_label_5":     "Style",
        "gallery_label_6":     "Walk-in",
        "hero_headline":       "SN Barbershop on Peck Rd.",
        "hero_subhead":        "Two chairs on Peck Road. Cash only — there's an ATM in the shop. Walk in most days, or call to set a weekend slot.",
        "value_props": [
            ("Family business, gen two", "Started by the founder, run by his son. Same chairs, same standards."),
            ("Two named barbers",        "Jesse and Julian both have regulars who book by name."),
            ("Cash only, no friction",   "ATM in the shop if you forgot. No app, no card fee."),
        ],
        "about_heading":       "Same chairs. New generation.",
        "about_paragraph":     "SN Barbershop's been on Peck Road for years. The founder started it, and after he passed his son kept the chairs running with the same standards. Jesse and Julian handle most of the walk-ins.",
        "about_paragraph_2":   "Art Mendoza summed it up in his review: the son cuts just as professionally as his late father did. New regulars walk in for Julian, longtime ones stay for the continuity.",
        "services_heading":    "Cuts.",
        "services_intro":      "Two chairs. Walk-ins welcome most days. Weekend appointments fill fast — call Friday for Saturday.",
        "services": [
            ("Fade",            "Skin, low, mid, or high. Clean lines."),
            ("Line-up",         "Hair or beard, dialed in."),
            ("Kids' cuts",      "Patient with first timers."),
            ("Style cut",       "Tell us what you want or ask — Julian's good with suggestions."),
            ("Walk-in",         "Most days, no wait. Cash only — ATM in the shop."),
        ],
        "reviews_heading":     "101 reviews. Five stars from regulars.",
        "visit_paragraph":     "4705 Peck Rd, El Monte. Cash only — there's an ATM inside if you forgot. Walk in most days, or call to set a weekend slot.",
        "hours": {
            "mon": "Closed",
            "tue": "10:00 AM – 7:00 PM",
            "wed": "10:00 AM – 7:00 PM",
            "thu": "10:00 AM – 7:00 PM",
            "fri": "10:00 AM – 7:00 PM",
            "sat": "9:00 AM – 6:00 PM",
            "sun": "10:00 AM – 3:00 PM",
        },
        "cta_heading":         "Stop by.",
        "cta_body":            "Walk in most days. Or call (626) 454-2393 and ask for Jesse or Julian by name.",
        "email_subject":       "built SN Barbershop a website preview",
        "email_body": (
            "gordon's review where he said julian made his hair look better than he imagined stuck with me — that's exactly what every guy who doesn't know what to ask for is searching for.\n\n"
            "you're 4.7 stars across 101 Google reviews but anyone who searches SN Barbershop on their phone just hits a maps pin, no website.\n\n"
            "built you a preview using your real reviews — kept the family-shop story front and center: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, 15 min from el monte if you'd rather meet."
        ),
    },

    # ============ 6. Oscar Barber shop (El Monte) ============
    "oscar-barber-shop-el-monte": {
        "template": "landing-barbershop.html",
        "meta_description": "Oscar Barber shop on Peck Rd, El Monte. Oscar and Gloria on the chairs — fast fades, 20-minute walk-ins. 4.7 across 79 Google reviews.",
        "brand": {
            "50":  "#f1f2f5",
            "100": "#d8dade",
            "500": "#c0c5cc",
            "600": "#989aa3",
            "700": "#6e7077",
            "900": "#1a1b1e",
        },
        "trust_badge": "4.7 · 79 Google reviews",
        "eyebrow_kicker":      "4356 Peck Rd · El Monte, CA · fast walk-ins",
        "hero_headline_part_1": "FADES IN 20.",
        "hero_headline_part_2": "OSCAR ON PECK ROAD.",
        "about_kicker":        "79 reviews. one was specific.",
        "pull_quote_text":     "Im in and out within 20 minutes, ready for another 10,000 miles. No time wasted. Thank you Oscar.",
        "pull_quote_author":   "BL UE",
        "marquee_text":        "OSCAR BARBER SHOP · EL MONTE · 4356 PECK RD · OSCAR + GLORIA · FAST WALK-INS · FADES IN 20 · 4.7 ★ 79 GOOGLE REVIEWS",
        "barbers_lineup":      "OSCAR · GLORIA",
        "visit_heading":       "On Peck Road. Walk in.",
        "gallery_heading":     "Recent cuts.",
        "gallery_caption":     "Photos · from the shop",
        "gallery_label_1":     "Fade",
        "gallery_label_2":     "Line-up",
        "gallery_label_3":     "Beard",
        "gallery_label_4":     "Kids' cut",
        "gallery_label_5":     "Quick cut",
        "gallery_label_6":     "Walk-in",
        "hero_headline":       "Fades in 20 — Oscar on Peck Road.",
        "hero_subhead":        "Two chairs on Peck Road. Walk in any weekday, in and out in twenty minutes, ready for the rest of your week.",
        "value_props": [
            ("In and out in 20",        "Most cuts run twenty minutes. No appointment usually needed."),
            ("Oscar and Gloria",        "Two barbers, both regulars favorites. Mister Felix drives back from out of the area for his cuts."),
            ("Rock-bottom prices",      "Reviews mention it more than the cuts themselves."),
        ],
        "about_heading":       "Two chairs. Twenty minutes.",
        "about_paragraph":     "Oscar runs the shop on Peck Road. Gloria's there most days too, on the second chair. Most cuts wrap in twenty minutes start to finish.",
        "about_paragraph_2":   "Mister Felix moved out of the area years ago and still drives back for his cuts. The reviews mention the speed as often as the quality — that's the brand.",
        "services_heading":    "Cuts.",
        "services_intro":      "Two chairs, fast turnover. Walk in any weekday. Call to check weekend hours.",
        "services": [
            ("Fade",            "Skin to high. Quick clean work."),
            ("Line-up",         "Sharp edges, no waiting."),
            ("Kids' cuts",      "In and out. Easy for first-timers."),
            ("Beard",           "Shape, line up, done."),
            ("Walk-in cut",     "Twenty minutes start to finish, most visits."),
        ],
        "reviews_heading":     "79 reviews. Most say one thing — fast.",
        "visit_paragraph":     "4356 Peck Rd, El Monte. Two chairs, walk in any weekday. Parking out front, in and out in twenty.",
        "hours": {
            "mon": "Closed",
            "tue": "9:00 AM – 6:00 PM",
            "wed": "9:00 AM – 6:00 PM",
            "thu": "9:00 AM – 6:00 PM",
            "fri": "9:00 AM – 6:00 PM",
            "sat": "9:00 AM – 5:00 PM",
            "sun": "Closed",
        },
        "cta_heading":         "Walk in.",
        "cta_body":            "Pull up any weekday. Or call (626) 221-2140 to confirm weekend hours.",
        "email_subject":       "built Oscar Barber shop a website preview",
        "email_body": (
            "the review from bl ue where they said they're 'in and out in 20 minutes, ready for another 10,000 miles' — that's such a specific way to describe the shop, it made me want to drive over.\n\n"
            "you're 4.7 stars across 79 Google reviews but anyone who searches Oscar Barber shop on their phone just hits a maps pin, no website.\n\n"
            "built you a preview using your real reviews — leaned into the fast-cuts thing: {preview_url}\n\n"
            "if you want it live this week, i can have it up for $1,497 — text or call me at (213) 522-9136.\n\n"
            "i'm in west covina, 15 min from el monte if you'd rather meet."
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
