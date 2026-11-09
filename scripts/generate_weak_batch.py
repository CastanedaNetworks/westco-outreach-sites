"""Generate one-page preview sites for the top WEAK leads in an outreach sheet.

Usage:
    python scripts/generate_weak_batch.py "<path to sheet csv>" [--top 14]

Reads the sheet (columns: Search, Business Name, Phone, Website, Reviews,
Rating, Instagram, Flag, Notes), keeps Flag == WEAK, sorts by Reviews
descending, takes the top N and writes sites/<slug>/index.html for each.

Layout is picked from the Search column (taqueria / barber shop / auto
repair). Phone, review count and the map query all come straight from the
sheet. Hand-written hero and card copy lives in CONTENT below, keyed by
business name. Slugs listed in EXISTING already have a hand-built site and
are never overwritten.

Re-runnable: rewrites the same folders on each run.
"""
from __future__ import annotations

import csv
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote, quote_plus

ROOT = Path(__file__).resolve().parent.parent
SITES = ROOT / "sites"
PAGES_BASE = "https://castanedanetworks.github.io/westco-outreach-sites"
WESTCO_PHONE = "(213) 522-9136"
WESTCO_TEL = "+12135229136"
YEAR = "2026"

# Leads that already have a tailored site. Left untouched.
EXISTING = {"WRLDWIDEBARBERSHOP": "wrldwide-barbershop-pomona"}
EXISTING_DISPLAY = {"WRLDWIDEBARBERSHOP": "WRLDWIDE BARBERSHOP"}


def unsplash(photo_id: str, w: int = 1400) -> str:
    return f"https://images.unsplash.com/photo-{photo_id}?fm=jpg&q=72&w={w}&fit=crop"


# Stock stand-ins (Unsplash), each one opened and checked for subject.
# Swap for the owner's own photos before launch.
IMG = {
    "tacos_paper":   ("1504544750208-dc0358e63f7f", "Steak tacos with lime and cilantro on butcher paper"),
    "tacos_plate":   ("1551504734-5ee1c4a1479b", "Plate of loaded tacos on a blue table"),
    "tacos_radish":  ("1552332386-f8dd00dc2f85", "Tacos with cilantro, lime and radish"),
    "tacos_lime":    ("1565299585323-38d6b0865b47", "Lime squeezed over a row of tacos"),
    "tacos_jarrito": ("1582234372722-50d7ccc30ebd", "Tacos al pastor with salsa, limes and a soda"),
    "tacos_row":     ("1599974579688-8dbdd335c77f", "Row of beef tacos topped with onion and cilantro"),
    "tacos_tile":    ("1613514785940-daed07799d9b", "Tacos with salsa roja and lime on a tiled table"),
    "tacos_basket":  ("1624300629298-e9de39c13be5", "Basket of tacos held over a table"),
    "burrito":       ("1626700051175-6818013e1d4f", "Burrito cut in half on a wooden board"),
    "barber_shave":  ("1503951914875-452162b0f3f1", "Barber giving a straight razor shave"),
    "barber_shop":   ("1585747860715-2ba37e788b70", "Barbershop interior with a row of chairs and mirrors"),
    "barber_fade":   ("1599351431202-1e0f0137899a", "Barber finishing a fade with clippers"),
    "barber_tools":  ("1621605815971-fbc98d665033", "Clippers, shears and combs laid out on a mat"),
    "barber_cut":    ("1622286342621-4bd786c2447c", "Barber combing and cutting a client's hair"),
    "auto_engine":   ("1486262715619-67b85e0b08d3", "Close view of an engine and belts"),
    "auto_tires":    ("1578844251758-2f71da64c96f", "Stacks of tires at a tire shop"),
    "auto_hands":    ("1619642751034-765dfdf7c58e", "Mechanic's hands working on an engine with a wrench"),
    "auto_hood":     ("1625047509248-ec889cbff17f", "Technician leaning in under the open hood of a car"),
    "roof_ladder":   ("1632759145351-1d592919f522", "Roofer standing on a house roof with a ladder against the wall"),
    "roof_shingles": ("1635424710928-0544e8512eae", "Roofer in a safety vest walking a shingle roof"),
}

# Leads built in addition to the top N (exact Business Name from the sheet).
ALSO = [
    "HP Commercial Roofing Pro West Covina",
    "Energy Collision Center & Auto Body Shop",
    "Chad Da Barber\U0001F488 HeadSprung Barbershop",
    "Tacos Guerrero and Mexican Food",
]

# Top banner on every preview. Paste a Stripe payment link here and re-run.
# While it is empty the banner asks for Zelle to the WestCo number.
STRIPE_LINK = ""
RESERVE_PRICE = "$250"


def preview_banner(display_name: str) -> str:
    """Self-contained (inline styles), so it also drops into hand-built pages."""
    target = ' target="_blank" rel="noopener"' if STRIPE_LINK else ""
    if STRIPE_LINK:
        href, how = STRIPE_LINK, ""
    else:
        # No Stripe link yet: pay by Zelle to the WestCo number. The link opens
        # a text to that number so the owner can say which site they want.
        msg = quote(f"I want to reserve the {display_name} website for {RESERVE_PRICE}.")
        href, how = f"sms:{WESTCO_TEL}?&body={msg}", f" with Zelle to {WESTCO_PHONE}"
    return f"""<!-- PREVIEW BANNER START · delete through PREVIEW BANNER END to remove -->
<div id="preview-banner" style="background:#111;color:#fff;font:500 14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;display:flex;align-items:center;gap:8px;padding:8px 6px 8px 16px;position:relative;z-index:60;">
  <p style="margin:0;flex:1;min-width:0;">Preview built for {html.escape(display_name)}. <a href="{html.escape(href, quote=True)}"{target} style="color:#ffd84d;font-weight:700;text-decoration:underline;text-underline-offset:3px;">Want it live? Reserve it for {RESERVE_PRICE}{how} →</a></p>
  <button type="button" aria-label="Hide this banner" onclick="this.parentNode.remove()" style="flex:none;width:44px;height:44px;background:none;border:0;color:#fff;font-size:22px;line-height:1;cursor:pointer;">×</button>
</div>
<!-- PREVIEW BANNER END -->"""


def rating_line(rating: str, reviews: int) -> tuple[str, str]:
    """(html, plain). Below 4.0 the stars are dropped and only the count shows."""
    count = f"{reviews:,} Google reviews"
    r = float(rating)
    if r < 4.0:
        return count, count
    return (f'<span class="whitespace-nowrap">{r:.1f} <span class="text-accent">★</span></span> · {count}',
            f"{r:.1f} ★ · {count}")

# --------------------------------------------------------------------------- #
# Themes. Colors are "r g b" triples so Tailwind opacity modifiers work.
# --------------------------------------------------------------------------- #
THEMES = {
    "taqueria": {
        "fonts": "family=Bowlby+One&family=Work+Sans:wght@400;500;600;700",
        "display": "'Bowlby One', Impact, sans-serif",
        "sans": "'Work Sans', ui-sans-serif, system-ui, sans-serif",
        "mono": "'Work Sans', ui-sans-serif, system-ui, sans-serif",
        "bg": "251 244 230", "panel": "244 232 208", "ink": "36 24 16",
        "display_css": "font-weight:400; letter-spacing:0.005em; line-height:1.02;",
        "radius": "0.75rem",
    },
    "barber": {
        "fonts": "family=Big+Shoulders+Display:wght@700;800;900&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700",
        "display": "'Big Shoulders Display', Impact, 'Arial Narrow', sans-serif",
        "sans": "Inter, ui-sans-serif, system-ui, sans-serif",
        "mono": "'JetBrains Mono', ui-monospace, monospace",
        "bg": "10 10 10", "panel": "22 22 22", "ink": "244 241 234",
        "display_css": "font-weight:800; text-transform:uppercase; letter-spacing:0.01em; line-height:0.92;",
        "radius": "0.125rem",
    },
    "auto": {
        "fonts": "family=Anton&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500",
        "display": "Anton, Impact, 'Arial Black', sans-serif",
        "sans": "'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif",
        "mono": "'IBM Plex Mono', ui-monospace, monospace",
        "bg": "19 21 26", "panel": "26 29 36", "ink": "240 236 227",
        "display_css": "font-weight:400; text-transform:uppercase; letter-spacing:0; line-height:0.95;",
        "radius": "0",
    },
    "contractor": {
        "fonts": "family=Archivo:wght@800;900&family=Source+Sans+3:wght@400;500;600;700",
        "display": "Archivo, 'Arial Black', sans-serif",
        "sans": "'Source Sans 3', ui-sans-serif, system-ui, sans-serif",
        "mono": "'Source Sans 3', ui-sans-serif, system-ui, sans-serif",
        "bg": "247 245 240", "panel": "235 231 222", "ink": "24 28 32",
        "display_css": "font-weight:900; letter-spacing:-0.015em; line-height:1.02;",
        "radius": "0.25rem",
    },
}

# --------------------------------------------------------------------------- #
# Per-business copy. accent / on_accent are "r g b" triples.
# cards: exactly three (title, body).
# --------------------------------------------------------------------------- #
TACO_CARDS_DEFAULT = None  # every taqueria writes its own

CONTENT = {
    "El Picoso Restaurant": {
        "slug": "el-picoso-restaurant-azusa", "short": "El Picoso",
        "accent": "200 40 28", "on_accent": "255 248 235",
        "hero": "tacos_tile", "side": "burrito",
        "kicker": "Mexican restaurant · Azusa, CA",
        "h1": "If you like it with some heat, you found the right place.",
        "sub": "El Picoso serves tacos, burritos and full plates in Azusa, with salsa that means it. Call your order in and it will be ready when you pull up.",
        "cards_heading": "What people order",
        "cards": [
            ("Tacos", "Your choice of meat on warm tortillas with onion, cilantro and salsa on the side. Order two or order ten."),
            ("Burritos", "Rolled big and wrapped tight. Rice, beans, your meat and whatever else you want in there."),
            ("Plates", "A full plate with rice, beans and tortillas for when a couple of tacos is not going to cut it."),
        ],
    },
    "Taqueria La Fogata": {
        "slug": "taqueria-la-fogata-azusa", "short": "La Fogata",
        "accent": "214 92 20", "on_accent": "30 18 8",
        "hero": "tacos_row", "side": "tacos_lime",
        "kicker": "Taqueria · Azusa, CA",
        "h1": "Tacos hot off the grill, right here in Azusa.",
        "sub": "Taqueria La Fogata keeps it simple. Good meat, fresh tortillas and salsa that does its job. Call ahead or come by and eat.",
        "cards_heading": "Off the grill",
        "cards": [
            ("Tacos", "Street style on corn tortillas with onion and cilantro. Tell us the meat and how many."),
            ("Burritos", "A full meal you can hold in one hand, filled with rice, beans and your choice of meat."),
            ("Combination plates", "Pick your favorite and we add the rice, beans and tortillas."),
        ],
    },
    "Tacos El Superior": {
        "slug": "tacos-el-superior-azusa", "short": "Tacos El Superior",
        "accent": "20 110 70", "on_accent": "250 246 232",
        "hero": "tacos_lime", "side": "tacos_radish",
        "kicker": "Taqueria · Azusa, CA",
        "h1": "Order ahead and your tacos are waiting when you get here.",
        "sub": "Tacos El Superior takes orders online and over the phone. Pick what you want, tell us when, and skip the line.",
        "cards_heading": "On the menu",
        "cards": [
            ("Tacos", "The reason our name starts with tacos. Corn tortillas, your meat, onion, cilantro and salsa."),
            ("Burritos", "Big, filling and easy to take with you. Add what you like and leave out what you don't."),
            ("Quesadillas and plates", "Melted cheese, your choice of meat, or a full plate with rice and beans."),
        ],
    },
    "Taco Tapatio": {
        "slug": "taco-tapatio-azusa", "short": "Taco Tapatio",
        "accent": "176 28 46", "on_accent": "255 246 230",
        "hero": "tacos_jarrito", "side": "tacos_basket",
        "kicker": "Taqueria · Azusa, CA",
        "h1": "Come hungry. We will take care of the rest.",
        "sub": "Taco Tapatio is the neighborhood spot for tacos, burritos and plates in Azusa. Call in your order or come see us.",
        "cards_heading": "Menu favorites",
        "cards": [
            ("Tacos", "Made to order with onion, cilantro, lime and salsa. Mix and match your meats."),
            ("Burritos", "Stuffed and wrapped to go. Good for lunch, better for dinner."),
            ("Plates", "Rice, beans, tortillas and your pick of meat when you want to sit down and eat."),
        ],
    },
    "Lalo's Family Restaurant Comida Mexicana": {
        "slug": "lalos-family-restaurant-azusa", "short": "Lalo's Family Restaurant",
        "accent": "24 96 120", "on_accent": "250 246 232",
        "hero": "tacos_plate", "side": "tacos_paper",
        "kicker": "Comida mexicana · Azusa, CA",
        "h1": "Bring the whole family. There is room at the table.",
        "sub": "Lalo's Family Restaurant cooks comida mexicana the way you grew up eating it. Come in, sit down, or call your order in to go.",
        "cards_heading": "From our kitchen",
        "cards": [
            ("Plates", "Full plates with rice, beans and warm tortillas. The kind of meal that sends you home happy."),
            ("Tacos and burritos", "For a quick lunch or a to go order on the way home."),
            ("Family orders", "Feeding a group? Call ahead and we will have everything packed and ready."),
        ],
    },
    "El Bukanas Azusa": {
        "slug": "el-bukanas-azusa", "short": "El Bukanas",
        "accent": "232 176 32", "on_accent": "32 22 8",
        "hero": "tacos_radish", "side": "tacos_tile",
        "kicker": "Mexican food · Azusa, CA",
        "h1": "When the craving hits, pull up to El Bukanas.",
        "sub": "Tacos, burritos and plates made fresh in Azusa. Give us a call and we will have your order going before you park.",
        "cards_heading": "What to order",
        "cards": [
            ("Tacos", "Warm tortillas, your choice of meat, onion, cilantro and salsa."),
            ("Burritos", "Loaded up and wrapped tight so you can eat here or take it with you."),
            ("Plates", "Your favorite with rice, beans and tortillas on the side."),
        ],
    },
    "Sandy’s Cocina": {
        "slug": "sandys-cocina-azusa", "short": "Sandy’s Cocina",
        "accent": "196 60 96", "on_accent": "255 246 236",
        "hero": "tacos_basket", "side": "tacos_jarrito",
        "kicker": "Mexican kitchen · Azusa, CA",
        "h1": "Sandy’s Cocina cooks like you are eating at home.",
        "sub": "Home style Mexican food in Azusa. Order online for pickup, call it in, or stop by and see what is cooking today.",
        "cards_heading": "From the cocina",
        "cards": [
            ("Tacos", "Simple and done right, with fresh toppings and salsa."),
            ("Burritos", "Made to order and big enough to share. You probably won't."),
            ("Plates", "A proper plate with rice and beans, like dinner at somebody's house."),
        ],
    },
    "Main St Barbershop": {
        "slug": "main-st-barbershop-pomona", "short": "Main St Barbershop",
        "accent": "198 162 92", "on_accent": "10 10 10",
        "hero": "barber_shop", "side": "barber_tools",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Your next cut is one booking away.",
        "sub": "Main St Barbershop keeps Pomona looking sharp. Pick your barber and your time online, or call the shop and we will get you in.",
        "cards_heading": "In the chair",
        "cards": [
            ("Cuts", "Classic cuts, scissor work and everything in between. Tell your barber what you want or show a photo."),
            ("Fades", "Low, mid, high or a taper. Blended clean with a sharp lineup to finish."),
            ("Beard", "Trim, shape and edge so the beard matches the cut."),
        ],
    },
    "El Punto Barbershop Pomona": {
        "slug": "el-punto-barbershop-pomona", "short": "El Punto Barbershop",
        "accent": "214 60 48", "on_accent": "250 246 240",
        "hero": "barber_fade", "side": "barber_tools",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Clean fades and sharp lineups at El Punto.",
        "sub": "Book your chair online in a minute or call the shop. Either way you leave El Punto looking right.",
        "cards_heading": "What we do",
        "cards": [
            ("Cuts", "From a quick clean up to a full restyle. Your barber takes the time to get it right."),
            ("Fades", "Skin fades, tapers and blends with a crisp lineup."),
            ("Beard", "Shaped, trimmed and lined up so it all comes together."),
        ],
    },
    "Christian & Roberto's Barber": {
        "slug": "christian-and-robertos-barber-pomona", "short": "Christian & Roberto's",
        "accent": "70 130 190", "on_accent": "250 248 244",
        "hero": "barber_cut", "side": "barber_shave",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Two names on the sign and a cut you can count on.",
        "sub": "At Christian & Roberto's we know what you mean by a little off the top. Call the shop to get in the chair.",
        "cards_heading": "At the shop",
        "cards": [
            ("Cuts", "Classic barbershop cuts for men and kids, done the way you ask for them."),
            ("Fades", "Tapers and fades blended clean, finished with a lineup."),
            ("Beard", "Beard trims and shape ups to go with your cut."),
        ],
    },
    "The Bambino Barbershop Pomona": {
        "slug": "the-bambino-barbershop-pomona", "short": "The Bambino Barbershop",
        "accent": "224 190 70", "on_accent": "12 12 12",
        "hero": "barber_shave", "side": "barber_cut",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Walk out of The Bambino looking sharp.",
        "sub": "Cuts, fades and beard work in Pomona. Call the shop and we will tell you when a chair is open.",
        "cards_heading": "In the chair",
        "cards": [
            ("Cuts", "Whatever you wear, your barber will keep it fresh. Kids are welcome too."),
            ("Fades", "Low to high and everything between, blended smooth."),
            ("Beard", "Trimmed and edged up so the whole look is clean."),
        ],
    },
    "Erik's Tires": {
        "slug": "eriks-tires-baldwin-park", "short": "Erik's Tires",
        "accent": "255 196 20", "on_accent": "19 21 26",
        "hero": "auto_tires", "side": "auto_hands",
        "kicker": "Tire shop · Baldwin Park, CA",
        "h1": "Need tires today? Call Erik's.",
        "sub": "Tell us your tire size over the phone and we will tell you what we have and what it costs. Then come by and we will get you back on the road.",
        "cards_heading": "What we do",
        "cards": [
            ("Tires", "Call with your size or read it to us off the sidewall. We will quote you before you drive over."),
            ("Flat repair", "Picked up a nail? Bring it in and we will see if it can be patched before you buy anything."),
            ("Mount and balance", "Tires mounted and balanced so the ride is smooth and the wear is even."),
        ],
    },
    "Purrfect Auto Service": {
        "slug": "purrfect-auto-service-baldwin-park", "short": "Purrfect Auto Service",
        "accent": "255 107 53", "on_accent": "19 21 26",
        "hero": "auto_hands", "side": "auto_engine",
        "kicker": "Auto repair · Baldwin Park, CA",
        "h1": "Something feel off with your car? Call the shop first.",
        "sub": "Tell us what it is doing and we will tell you when to bring it in. Purrfect Auto Service handles repairs and maintenance in Baldwin Park.",
        "cards_heading": "Services",
        "cards": [
            ("Brakes", "Squealing, grinding or a soft pedal. We check it and show you what it needs."),
            ("Oil change", "Oil and filter with a look over the basics while your car is in the bay."),
            ("Check engine light", "We pull the code, find the cause and explain it in plain English."),
        ],
    },
    "HP Commercial Roofing Pro West Covina": {
        "slug": "hp-commercial-roofing-pro-west-covina", "short": "HP Roofing Pro",
        "display": "HP Commercial Roofing Pro",
        "accent": "178 58 34", "on_accent": "255 250 244",
        "hero": "roof_shingles", "side": "roof_ladder",
        "kicker": "Roofing contractor · West Covina, CA",
        "h1": "Tell us about your roof and get a free estimate.",
        "sub": "HP Commercial Roofing Pro works on roofs in and around West Covina. Send us the details below or call, and we will come out and take a look.",
        "cards_heading": "Roofing services",
        "cards": [
            ("Commercial roofing", "Flat and low slope roofs for shops, offices and warehouses, done with as little downtime as we can manage."),
            ("Leak repair", "Water coming in? We track down where it starts and fix that, so you are not patching the same spot every winter."),
            ("Roof replacement", "When repairs stop making sense we tear off the old roof and put on a new one, with the price agreed before we start."),
        ],
        "form_field": "Property address",
        "form_placeholder": "Leak over the back office, flat roof, about 20 years old",
    },
    "Energy Collision Center & Auto Body Shop": {
        "slug": "energy-collision-center-baldwin-park", "short": "Energy Collision Center",
        "display": "Energy Collision Center",
        "accent": "132 214 64", "on_accent": "19 21 26",
        "hero": "auto_hood", "side": "auto_engine",
        "kicker": "Collision and auto body · Baldwin Park, CA",
        "h1": "Got hit? Get a free estimate before you decide anything.",
        "sub": "Energy Collision Center fixes collision damage, dents and paint in Baldwin Park. Tell us what happened below or call the shop.",
        "cards_heading": "Body shop services",
        "cards": [
            ("Collision repair", "From a parking lot bump to a real accident. We look it over and tell you what it takes to make it right."),
            ("Dents and body work", "Dented doors, bent fenders and cracked bumpers straightened or replaced."),
            ("Paint", "Color matched to your car so the repair does not stand out."),
        ],
        "form": True,
        "form_field": "Vehicle (year, make, model)",
        "form_placeholder": "Rear ended on the driver side, bumper and tail light",
    },
    "Chad Da Barber\U0001F488 HeadSprung Barbershop": {
        "slug": "headsprung-barbershop-pomona", "short": "HeadSprung Barbershop",
        "display": "HeadSprung Barbershop", "q": "HeadSprung Barbershop",
        "accent": "40 190 170", "on_accent": "8 12 12",
        "hero": "barber_cut", "side": "barber_tools",
        "kicker": "Chad Da Barber · Pomona, CA",
        "h1": "Get your head right at HeadSprung.",
        "sub": "Chad Da Barber is cutting in Pomona. Call the shop to book your chair.",
        "cards_heading": "In the chair",
        "cards": [
            ("Cuts", "Tell Chad what you are going for or show him a photo. He takes it from there."),
            ("Fades", "Tapers, skin fades and blends finished with a clean lineup."),
            ("Beard", "Trimmed, shaped and edged to match the cut."),
        ],
    },
    "Tacos Guerrero and Mexican Food": {
        "slug": "tacos-guerrero-azusa", "short": "Tacos Guerrero",
        "accent": "150 30 90", "on_accent": "255 246 236",
        "hero": "tacos_paper", "side": "tacos_row",
        "kicker": "Tacos and Mexican food · Azusa, CA",
        "h1": "Tacos Guerrero is cooking. Come get a plate.",
        "sub": "Tacos and Mexican food made fresh in Azusa. Call your order in or stop by and eat.",
        "cards_heading": "On the menu",
        "cards": [
            ("Tacos", "On warm tortillas with onion, cilantro and salsa. Pick your meat and how many."),
            ("Burritos", "Filled up, wrapped tight and ready to go."),
            ("Plates", "Your choice of meat with rice, beans and tortillas."),
        ],
    },
}

# Real ordering / booking pages from the sheet's Website column.
ACTION_URL_HINTS = ("toasttab.com", "clover.com", "getsquire.com")


def category(search: str) -> str:
    s = search.lower()
    if "taqueria" in s:
        return "taqueria"
    if "barber" in s:
        return "barber"
    if "auto repair" in s or "tire" in s:
        return "auto"
    if "roofing" in s or "contractor" in s:
        return "contractor"
    return "other"


def city_of(search: str) -> str:
    """'taqueria Azusa' -> 'Azusa'; 'auto repair Baldwin Park' -> 'Baldwin Park'."""
    s = re.sub(r"\s+CA$", "", search.strip())
    for prefix in ("general contractor", "auto repair", "barber shop", "mobile detailing",
                   "taqueria", "roofing", "landscaping"):
        if s.lower().startswith(prefix):
            return s[len(prefix):].strip()
    return s


def tel(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return "+1" + digits[-10:]


def e(s: str) -> str:
    return html.escape(s, quote=True)


def img_tag(key: str, cls: str, w: int = 1400, eager: bool = False) -> str:
    pid, alt = IMG[key]
    load = "eager" if eager else "lazy"
    return f'<img src="{unsplash(pid, w)}" alt="{e(alt)}" class="{cls}" loading="{load}" />'


def render(row: dict) -> tuple[str, str]:
    name = row["Business Name"].strip()
    c = CONTENT[name]
    cat = category(row["Search"])
    t = THEMES[cat]
    city = city_of(row["Search"])
    phone = row["Phone"].strip()
    phone_tel = tel(phone)
    reviews = int(row["Reviews"])
    slug = c["slug"]
    url = f"{PAGES_BASE}/sites/{slug}/"
    display = c.get("display", name)
    has_form = cat == "contractor" or c.get("form", False)
    stars_html, stars_plain = rating_line(row["Rating"], reviews)
    q = quote_plus(f'{c.get("q", name)} {city} CA')
    maps_link = f"https://www.google.com/maps/search/?api=1&query={q}"
    maps_embed = f"https://www.google.com/maps?q={q}&output=embed"
    site = row["Website"].strip()
    action_url = site if any(h in site for h in ACTION_URL_HINTS) else ""

    btn = "inline-flex items-center justify-center font-semibold text-sm px-6 py-3.5 transition btn"
    primary = f"{btn} bg-accent text-onaccent hover:brightness-110"
    ghost = f"{btn} ring-1 ring-ink/25 hover:bg-ink/5"
    call_btn = f'<a href="tel:{phone_tel}" class="{primary}">Call {e(phone)}</a>'
    dir_btn = f'<a href="{maps_link}" target="_blank" rel="noopener" class="{ghost}">Get directions</a>'

    if cat == "taqueria":
        if action_url:
            cta = (f'<a href="{e(action_url)}" target="_blank" rel="noopener" class="{primary}">Order online</a>'
                   f'<a href="tel:{phone_tel}" class="{ghost}">Call {e(phone)}</a>{dir_btn}')
        else:
            cta = (f'<a href="tel:{phone_tel}" class="{primary}">Call to order · {e(phone)}</a>{dir_btn}')
        nav_label, closing_h, closing_p = "Order", "Hungry yet?", "Call your order in and it will be ready when you get here."
        visit_h = "Come eat with us"
    elif cat == "barber":
        if action_url:
            cta = (f'<a href="{e(action_url)}" target="_blank" rel="noopener" class="{primary}">Book now</a>'
                   f'<a href="tel:{phone_tel}" class="{ghost}">Call {e(phone)}</a>')
        else:
            cta = f'<a href="tel:{phone_tel}" class="{primary}">Book now · {e(phone)}</a>{dir_btn}'
        nav_label, closing_h, closing_p = "Book", "Get in the chair", "Call the shop and we will find you a time that works."
        visit_h = "Find the shop"
    elif cat == "contractor":
        cta = (f'<a href="#estimate" class="{primary}">Free estimate</a>'
               f'<a href="tel:{phone_tel}" class="{ghost}">Call {e(phone)}</a>')
        nav_label, closing_h, closing_p = "Estimate", "Rather talk it through?", "Call and tell us what is going on with the roof. The estimate is free either way."
        visit_h = "Where we work"
    else:
        second = (f'<a href="#estimate" class="{ghost}">Free estimate</a>' if has_form
                  else f'<a href="#hours" class="{ghost}">Hours</a>')
        cta = f'<a href="tel:{phone_tel}" class="{primary}">Call now · {e(phone)}</a>{second}{dir_btn}'
        nav_label, closing_h, closing_p = "Call", "Call before you come in", "A two minute call saves you a trip. We will tell you what we can do and when."
        visit_h = "Where to find us"

    # ---- hero variants -----------------------------------------------------
    kicker = f'<p class="kicker text-accent">{e(c["kicker"])}</p>'
    h1 = f'<h1 class="display mt-4 text-[clamp(2.1rem,8.6vw,5.25rem)] max-w-[18ch]">{e(c["h1"])}</h1>'
    sub = f'<p class="mt-6 text-ink/75 text-[17px] sm:text-lg leading-relaxed max-w-[52ch]">{e(c["sub"])}</p>'
    ctas = f'<div class="mt-8 flex flex-col min-[480px]:flex-row min-[480px]:flex-wrap gap-3">{cta}</div>'

    if cat == "taqueria":
        hero = f"""
<section id="top" class="max-w-6xl mx-auto px-4 sm:px-8 pt-10 sm:pt-16 pb-12 sm:pb-20">
  {kicker}
  {h1}
  <div class="mt-8 sm:mt-10 grid lg:grid-cols-12 gap-8 lg:gap-12 items-start">
    <figure class="lg:col-span-8 relative">
      {img_tag(c["hero"], "w-full h-[240px] sm:h-[420px] object-cover photo", eager=True)}
      <figcaption class="sticker absolute -bottom-4 right-3 sm:right-6 bg-accent text-onaccent display text-sm sm:text-lg px-4 py-2.5">{e(city)}, CA</figcaption>
    </figure>
    <div class="lg:col-span-4 lg:pt-2">
      {sub.replace('mt-6 ', '')}
      {ctas}
    </div>
  </div>
</section>"""
    elif cat == "barber":
        hero = f"""
<section id="top" class="relative overflow-hidden">
  {img_tag(c["hero"], "absolute inset-0 w-full h-full object-cover opacity-45", eager=True)}
  <div class="absolute inset-0 bg-gradient-to-t from-bg via-bg/70 to-bg/30"></div>
  <div class="relative max-w-6xl mx-auto px-4 sm:px-8 pt-28 sm:pt-44 pb-12 sm:pb-20">
    {kicker}
    {h1}
    {sub}
    {ctas}
  </div>
</section>"""
    elif cat == "contractor":
        hero = f"""
<section id="top" class="max-w-6xl mx-auto px-4 sm:px-8 pt-10 sm:pt-16 pb-12 sm:pb-20 grid lg:grid-cols-12 gap-8 lg:gap-12 items-center">
  <div class="lg:col-span-6 lg:order-2">
    {kicker}
    {h1}
    {sub}
    {ctas}
  </div>
  <div class="lg:col-span-6 lg:order-1">
    {img_tag(c["hero"], "w-full h-[230px] sm:h-[460px] object-cover photo", eager=True)}
  </div>
</section>"""
    else:
        hero = f"""
<section id="top" class="max-w-7xl mx-auto grid lg:grid-cols-12">
  <div class="lg:col-span-7 px-4 sm:px-8 pt-10 pb-12 sm:pt-20 sm:pb-20">
    {kicker}
    {h1}
    {sub}
    {ctas}
  </div>
  <div class="lg:col-span-5 relative min-h-[15rem] sm:min-h-[24rem]">
    {img_tag(c["hero"], "absolute inset-0 w-full h-full object-cover", eager=True)}
  </div>
</section>"""

    # ---- three service cards ----------------------------------------------
    cards = "\n".join(
        f"""      <article class="card bg-panel p-6 sm:p-7{' md:mt-8' if i == 1 else ''}">
        <h3 class="display text-2xl sm:text-3xl">{e(title)}</h3>
        <p class="mt-3 text-ink/70 leading-relaxed">{e(body)}</p>
      </article>"""
        for i, (title, body) in enumerate(c["cards"])
    )
    services = f"""
<section id="services" class="border-t border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-14 sm:py-24">
    <div class="grid lg:grid-cols-12 gap-8 items-end">
      <h2 class="lg:col-span-7 display text-[clamp(1.9rem,6.5vw,3.75rem)]">{e(c["cards_heading"])}</h2>
      <div class="lg:col-span-5">
        {img_tag(c["side"], "w-full h-40 sm:h-52 object-cover photo", w=900)}
      </div>
    </div>
    <div class="mt-8 sm:mt-12 grid md:grid-cols-3 gap-4 sm:gap-6 items-start">
{cards}
    </div>
  </div>
</section>"""

    # ---- reviews -----------------------------------------------------------
    reviews_sec = f"""
<section id="reviews" class="bg-panel border-y border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-14 sm:py-20 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
    <p class="display text-[clamp(1.5rem,6vw,3.25rem)]" aria-label="{e(stars_plain)}">{stars_html}</p>
    <a href="{maps_link}" target="_blank" rel="noopener" class="{ghost} self-start md:self-auto shrink-0">Read them on Google</a>
  </div>
</section>"""

    # ---- visit (map, phone, hours for auto) --------------------------------
    hours = ""
    if cat == "auto":
        hours = f"""
      <div id="hours" class="card mt-8 border border-ink/15 p-6">
        <p class="kicker text-ink/55">Hours</p>
        <dl class="mt-4 font-mono text-[15px]">
          <div class="flex justify-between gap-4 py-2 border-b border-ink/10"><dt class="text-ink/60">Mon to Fri</dt><dd>Call to confirm</dd></div>
          <div class="flex justify-between gap-4 py-2 border-b border-ink/10"><dt class="text-ink/60">Saturday</dt><dd>Call to confirm</dd></div>
          <div class="flex justify-between gap-4 py-2"><dt class="text-ink/60">Sunday</dt><dd>Call to confirm</dd></div>
        </dl>
        <p class="mt-4 text-sm text-ink/55">The shop's posted hours go here on the live site.</p>
      </div>"""
    visit = f"""
<section id="visit">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-14 sm:py-24 grid lg:grid-cols-12 gap-8 lg:gap-12">
    <div class="lg:col-span-5">
      <p class="kicker text-accent">{e(city)}, CA</p>
      <h2 class="display mt-3 text-[clamp(1.9rem,6.5vw,3.75rem)]">{e(visit_h)}</h2>
      <p class="mt-6 kicker text-ink/55">Phone</p>
      <a href="tel:{phone_tel}" class="display block mt-1 text-3xl sm:text-4xl hover:text-accent transition">{e(phone)}</a>
      <div class="mt-6 flex flex-col min-[480px]:flex-row gap-3">
        {call_btn}
        {dir_btn}
      </div>{hours}
    </div>
    <div class="lg:col-span-7">
      <iframe title="Map to {e(display)} in {e(city)}, CA" src="{maps_embed}"
              class="card w-full h-[320px] sm:h-[440px] border border-ink/15" loading="lazy"
              referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
  </div>
</section>"""

    closing = f"""
<section class="bg-accent text-onaccent">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-14 sm:py-20">
    <h2 class="display text-[clamp(2rem,8vw,4.5rem)]">{e(closing_h)}</h2>
    <p class="mt-4 text-lg max-w-[46ch] opacity-90">{e(closing_p)}</p>
    <a href="tel:{phone_tel}" class="display inline-block mt-6 text-[clamp(2rem,10vw,5rem)] underline decoration-2 underline-offset-8 hover:no-underline">{e(phone)}</a>
  </div>
</section>"""

    # ---- free estimate form (opens the visitor's mail app, fields filled in) --
    estimate = ""
    if has_form:
        field = c.get("form_field", "Address")
        inp = "mt-1.5 w-full bg-bg border border-ink/25 px-3 py-3 text-base card focus:outline-none focus:border-accent"
        estimate = f"""
<section id="estimate" class="bg-panel border-t border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-14 sm:py-24 grid lg:grid-cols-12 gap-8 lg:gap-14">
    <div class="lg:col-span-5">
      <p class="kicker text-accent">No charge, no pressure</p>
      <h2 class="display mt-3 text-[clamp(1.9rem,6.5vw,3.75rem)]">Get a free estimate</h2>
      <p class="mt-5 text-ink/70 text-[17px] leading-relaxed max-w-[44ch]">Fill this out and hit the button. It opens an email to us with everything already typed in, so all you do is press send.</p>
      <p class="mt-5 text-ink/70">In a hurry? <a class="font-semibold underline underline-offset-4 hover:text-accent transition" href="tel:{phone_tel}">Call {e(phone)}</a></p>
    </div>
    <form id="estimate-form" class="lg:col-span-7 grid sm:grid-cols-2 gap-4" data-to="{e(c.get('email', ''))}" data-business="{e(display)}" data-field="{e(field)}">
      <label class="block text-sm font-semibold">Your name
        <input class="{inp}" name="name" autocomplete="name" required />
      </label>
      <label class="block text-sm font-semibold">Phone
        <input class="{inp}" name="phone" type="tel" autocomplete="tel" inputmode="tel" required />
      </label>
      <label class="block text-sm font-semibold sm:col-span-2">{e(field)}
        <input class="{inp}" name="extra" />
      </label>
      <label class="block text-sm font-semibold sm:col-span-2">What is going on?
        <textarea class="{inp}" name="details" rows="4" placeholder="{e(c.get('form_placeholder', ''))}" required></textarea>
      </label>
      <div class="sm:col-span-2">
        <button type="submit" class="{primary} w-full sm:w-auto">Free Estimate</button>
      </div>
    </form>
  </div>
</section>
<script>
  document.getElementById('estimate-form').addEventListener('submit', function (ev) {{
    ev.preventDefault();
    var f = ev.target, d = f.dataset, v = function (n) {{ return f.elements[n].value.trim(); }};
    var body = [
      'Name: ' + v('name'),
      'Phone: ' + v('phone'),
      d.field + ': ' + v('extra'),
      '',
      v('details')
    ].join('\\n');
    location.href = 'mailto:' + encodeURIComponent(d.to) +
      '?subject=' + encodeURIComponent('Free estimate request for ' + d.business) +
      '&body=' + encodeURIComponent(body);
  }});
</script>"""

    top_band = '<div class="hazard h-1.5"></div>' if cat == "auto" else ""
    banner = preview_banner(display)
    desc = f'{display} in {city}, CA. {c["sub"]}'

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover" />
<title>{e(display)} · {e(city)}, CA</title>
<meta name="description" content="{e(desc)}" />
<meta name="robots" content="noindex,nofollow" />
<link rel="canonical" href="{url}" />

<meta property="og:title" content="{e(display)}" />
<meta property="og:description" content="{e(c["h1"])}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{unsplash(IMG[c["hero"]][0], 1200)}" />

<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?{t["fonts"]}&display=swap" rel="stylesheet" />

<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {{
    theme: {{
      extend: {{
        fontFamily: {{ sans: [{t["sans"]!r}], mono: [{t["mono"]!r}] }},
        colors: {{
          bg:       'rgb(var(--bg) / <alpha-value>)',
          panel:    'rgb(var(--panel) / <alpha-value>)',
          ink:      'rgb(var(--ink) / <alpha-value>)',
          accent:   'rgb(var(--accent) / <alpha-value>)',
          onaccent: 'rgb(var(--on-accent) / <alpha-value>)',
        }},
      }},
    }},
  }};
</script>
<style>
  :root {{
    --bg: {t["bg"]}; --panel: {t["panel"]}; --ink: {t["ink"]};
    --accent: {c["accent"]}; --on-accent: {c["on_accent"]};
    --radius: {t["radius"]};
  }}
  html {{ scroll-behavior: smooth; background: rgb(var(--bg)); }}
  body {{ background: rgb(var(--bg)); color: rgb(var(--ink)); overflow-x: hidden; -webkit-font-smoothing: antialiased; }}
  .display {{ font-family: {t["display"]}; {t["display_css"]} overflow-wrap: break-word; }}
  .kicker {{ font-family: {t["mono"]}; font-size: 12px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; }}
  .btn, .card, .photo {{ border-radius: var(--radius); }}
  .btn {{ min-height: 48px; text-align: center; }}
  .sticker {{ border-radius: var(--radius); transform: rotate(-3deg); }}
  .hazard {{ background-image: repeating-linear-gradient(45deg, rgb(var(--accent)) 0 14px, rgb(var(--bg)) 14px 28px); }}
</style>
</head>

<body class="font-sans">
{banner}
{top_band}
<header class="sticky top-0 z-40 bg-bg/95 backdrop-blur border-b border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 h-14 sm:h-16 flex items-center justify-between gap-3">
    <a href="#top" class="display text-base sm:text-xl truncate min-w-0">{e(c["short"])}</a>
    <nav class="hidden md:flex items-center gap-7 text-sm font-medium text-ink/65">
      <a class="hover:text-ink transition" href="#services">{e(c["cards_heading"])}</a>
      <a class="hover:text-ink transition" href="#reviews">Reviews</a>
      <a class="hover:text-ink transition" href="#visit">Map</a>
    </nav>
    <a href="tel:{phone_tel}" class="inline-flex items-center bg-accent text-onaccent font-semibold text-sm px-4 py-2.5 shrink-0 whitespace-nowrap btn hover:brightness-110 transition" style="min-height:40px">
      <span class="sm:hidden">Call</span><span class="hidden sm:inline">{e(phone)}</span>
    </a>
  </div>
</header>
{hero}
{services}
{estimate}
{reviews_sec}
{visit}
{closing}

<footer class="border-t border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-10 flex flex-col sm:flex-row sm:items-start justify-between gap-6 text-sm">
    <div>
      <p class="display text-xl">{e(display)}</p>
      <p class="mt-1 text-ink/60">{e(city)}, CA</p>
      <p class="mt-1"><a class="inline-block py-1.5 hover:text-accent transition" href="tel:{phone_tel}">{e(phone)}</a></p>
    </div>
    <div class="text-ink/60 sm:text-right">
      <p>Website preview by <span class="text-ink font-semibold">WestCo App Studio</span></p>
      <p class="mt-1">
        <a class="inline-block py-1.5 underline underline-offset-2 hover:text-accent transition" href="https://castanedanetworks.com" target="_blank" rel="noopener">castanedanetworks.com</a>
        · <a class="inline-block py-1.5 underline underline-offset-2 hover:text-accent transition" href="tel:{WESTCO_TEL}">{WESTCO_PHONE}</a>
      </p>
    </div>
  </div>
  <div class="border-t border-ink/10">
    <div class="max-w-6xl mx-auto px-4 sm:px-8 py-4 flex flex-wrap items-center justify-between gap-2 text-[11px] uppercase tracking-[0.18em] text-ink/45">
      <span>© {YEAR} {e(display)}</span>
      <span>Website preview · not the official site</span>
    </div>
  </div>
</footer>

<!-- Photos are stock stand-ins from Unsplash. Swap for the owner's own photos before launch. -->
</body>
</html>
"""
    assert "—" not in page and "–" not in page, f"dash crept into {slug}"
    return slug, page


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    top = 14
    if "--top" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1])
        args = [a for a in args if a != str(top)]
    with open(args[0], newline="", encoding="utf-8-sig") as f:
        sheet = list(csv.DictReader(f))
    rows = [r for r in sheet if r["Flag"].strip().upper() == "WEAK"]
    rows.sort(key=lambda r: int(r["Reviews"]), reverse=True)
    rows = rows[:top]
    picked = {r["Business Name"].strip() for r in rows}
    for wanted in ALSO:
        match = [r for r in sheet if r["Business Name"].strip() == wanted]
        if not match:
            sys.exit(f"ALSO entry not found in sheet: {wanted!r}")
        if wanted not in picked:
            rows.append(match[0])

    for r in rows:
        name = r["Business Name"].strip()
        if name in EXISTING:
            slug = EXISTING[name]
            # Hand-built page: only keep its preview banner in sync.
            path = SITES / slug / "index.html"
            src = path.read_text(encoding="utf-8")
            block = preview_banner(EXISTING_DISPLAY.get(name, name))
            if "PREVIEW BANNER START" in src:
                src = re.sub(r"<!-- PREVIEW BANNER START.*?PREVIEW BANNER END -->", lambda m: block, src, flags=re.S)
            else:
                src = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + block, src, count=1)
            path.write_text(src, encoding="utf-8", newline="\n")
            print(f"KEPT\t{name}\t{PAGES_BASE}/sites/{slug}/")
            continue
        if name not in CONTENT:
            sys.exit(f"No copy written for {name!r} ({r['Search']}). Add it to CONTENT.")
        slug, page = render(r)
        out = SITES / slug
        out.mkdir(parents=True, exist_ok=True)
        (out / "index.html").write_text(page, encoding="utf-8", newline="\n")
        print(f"BUILT\t{name}\t{PAGES_BASE}/sites/{slug}/")


if __name__ == "__main__":
    main()
