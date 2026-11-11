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
    if photo_id.startswith("pexels:"):
        n = photo_id.split(":", 1)[1]
        return f"https://images.pexels.com/photos/{n}/pexels-photo-{n}.jpeg?auto=compress&cs=tinysrgb&w={w}"
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
    "detail_buckets":  ("1607860108855-64acf2078ed9", "Detailer hand washing a dark sports car beside wash buckets"),
    "detail_wheel":    ("1552930294-6b595f4c2974", "Man pressure washing the wheel of a black convertible"),
    "detail_headlight": ("1632823469850-2f77dd9c7f93", "Detailer working on the headlight of a silver car"),
    "detail_foam":     ("1608506375591-b90e1f955e4b", "Soapy wheel and fender of a car mid wash"),
    "detail_rinse":    ("1520340356584-f9917d1eea6f", "Soap being rinsed off the back of a sports car"),
    "detail_polish":   ("pexels:5233262", "Hands running a polisher over a red car door"),
    "detail_sponge":   ("pexels:4870705", "Hand scrubbing a car wheel with a soapy sponge"),
    "remodel_kitchen": ("1556911220-bff31c812dba", "Remodeled kitchen with white cabinets and a stone counter"),
    "remodel_plans":   ("1503387762-592deb58ef4e", "Contractor marking up a set of building plans"),
    "margarita":       ("1556855810-ac404aa91e85", "Strawberry margarita with a salted rim on the bar"),
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
        "fonts": "family=Big+Shoulders+Display:wght@700;800;900&family=Archivo:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700",
        "display": "'Big Shoulders Display', Impact, 'Arial Narrow', sans-serif",
        "sans": "Archivo, ui-sans-serif, system-ui, sans-serif",
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
    "detail": {
        "fonts": "family=Barlow+Condensed:wght@600;700&family=Barlow:wght@400;500;600;700",
        "display": "'Barlow Condensed', 'Arial Narrow', sans-serif",
        "sans": "Barlow, ui-sans-serif, system-ui, sans-serif",
        "mono": "Barlow, ui-sans-serif, system-ui, sans-serif",
        "bg": "11 16 24", "panel": "20 28 40", "ink": "238 242 246",
        "display_css": "font-weight:700; text-transform:uppercase; letter-spacing:0.005em; line-height:0.98;",
        "radius": "0.5rem",
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
    "Mr. Lai's Mobile Detailing Services": {
        "slug": "mr-lais-mobile-detailing-el-monte", "short": "Mr. Lai's Mobile Detailing",
        "display": "Mr. Lai's Mobile Detailing", "mobile": True,
        # Red and blue badge on white, bold serif wordmark (their Instagram logo).
        "logo": True,
        "theme": {
            "fonts": "family=Zilla+Slab:wght@600;700&family=Public+Sans:wght@400;500;600;700",
            "display": "'Zilla Slab', Georgia, serif",
            "sans": "'Public Sans', ui-sans-serif, system-ui, sans-serif",
            "mono": "'Public Sans', ui-sans-serif, system-ui, sans-serif",
            "bg": "255 255 255", "panel": "240 244 251", "ink": "24 38 92",
            "display_css": "font-weight:700; letter-spacing:-0.01em; line-height:1.04;",
            "radius": "0.375rem", "h1": "clamp(2.1rem,8.2vw,4.5rem)",
        },
        "accent": "200 32 44", "on_accent": "255 255 255",
        "hero": "detail_buckets", "side": "detail_foam",
        "kicker": "Mobile detailing · El Monte, CA",
        "h1": "Your car detailed right where it is parked.",
        "sub": "Mr. Lai's Mobile Detailing comes to your home or your work around El Monte. Call, tell us what you drive, and we will set a time.",
        "cards_heading": "What we do",
        "cards": [
            ("Wash", "A proper hand wash with the wheels and tires done, then dried so it does not spot."),
            ("Interior", "Vacuumed, wiped down and cleaned out, from the dash to the floor mats."),
            ("Full detail", "Inside and outside in one visit. Ask what is included for your car and we will quote it on the call."),
        ],
        "closing": ("Ready when you are", "Call and tell us what you drive and where it is parked. We will give you a price and a time."),
    },
    "Ride & Shine Auto Detail Supplies": {
        "slug": "ride-and-shine-auto-detail-supplies-el-monte", "short": "Ride & Shine",
        # Green and white on black, heavy italic lettering (their Instagram logo).
        "address": "2229 Durfee Ave, El Monte, CA",
        "logo": True,
        "theme": {
            "fonts": "family=Kanit:ital,wght@1,700;1,800&family=Mukta:wght@400;500;600;700",
            "display": "Kanit, 'Arial Black', sans-serif",
            "sans": "Mukta, ui-sans-serif, system-ui, sans-serif",
            "mono": "Mukta, ui-sans-serif, system-ui, sans-serif",
            "bg": "12 12 12", "panel": "26 26 26", "ink": "246 246 242",
            "display_css": "font-weight:800; font-style:italic; letter-spacing:-0.005em; line-height:1.02;",
            "radius": "999px", "h1": "clamp(2rem,8vw,4.5rem)",
        },
        "accent": "40 180 90", "on_accent": "6 18 10",
        "hero": "detail_polish", "side": "detail_sponge",
        "kicker": "Auto detail supplies · El Monte, CA",
        "h1": "Detail supplies for people who take care of their own car.",
        "sub": "Ride & Shine sells auto detail supplies at 2229 Durfee Ave in El Monte. Call to ask if we carry what you are looking for, then come by.",
        "cards_heading": "On the shelf",
        "cards": [
            ("Wash", "Soaps, mitts and buckets for washing by hand."),
            ("Protect", "Waxes, sealants and sprays that keep the shine after the wash."),
            ("Interior", "Cleaners, brushes and towels for the inside of the car."),
        ],
        "closing": ("Looking for something specific?", "Call and ask. We will tell you if it is on the shelf before you make the drive."),
    },
    "Reservedparkingdetail": {
        "slug": "reserved-parking-detail-el-monte", "short": "Reserved Parking",
        "display": "Reserved Parking Car Detailing",
        # Their Instagram says they serve the SGV and lists no shop address.
        "mobile": True, "visit_h": "Serving the SGV",
        # Ice blue and white on black, stencil wordmark (their Instagram logo).
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": {
            "fonts": "family=Saira+Stencil+One&family=Saira:wght@400;500;600;700",
            "display": "'Saira Stencil One', Impact, sans-serif",
            "sans": "Saira, ui-sans-serif, system-ui, sans-serif",
            "mono": "Saira, ui-sans-serif, system-ui, sans-serif",
            "bg": "0 0 0", "panel": "14 20 28", "ink": "236 244 250",
            "display_css": "font-weight:400; text-transform:uppercase; letter-spacing:0.01em; line-height:1.02;",
            "radius": "0.25rem", "h1": "clamp(1.8rem,7.4vw,4.25rem)",
        },
        "accent": "104 196 244", "on_accent": "0 10 18",
        "hero": "detail_wheel", "side": "detail_headlight",
        "kicker": "Auto detailing · El Monte, CA",
        "h1": "Your car should look good wherever you park it.",
        "sub": "Reserved Parking details cars inside and out around the San Gabriel Valley. Call to get a price for yours and pick a day.",
        "cards_heading": "Services",
        "cards": [
            ("Exterior", "Hand washed and dried, with the wheels, tires and glass done right."),
            ("Interior", "Seats, carpets, dash and door panels vacuumed and wiped clean."),
            ("Inside and out", "Get both done in one appointment. Call with your make and model for a quote."),
        ],
        "closing": ("Get a price for your car", "Call with the make and model and tell us what it needs. We will quote it and find you a day."),
    },
    "The Hair Lab Pomona": {
        "slug": "the-hair-lab-pomona", "short": "The Hair Lab",
        "display": "The Hair Lab",
        # Neon green and hot pink on black (their Instagram logo).
        "logo": True, "logo_shape": "rounded-[14px]",
        "theme": {
            "fonts": "family=Rubik:ital,wght@1,800;1,900&family=Rubik:wght@400;500;600",
            "display": "Rubik, 'Arial Black', sans-serif",
            "sans": "Rubik, ui-sans-serif, system-ui, sans-serif",
            "mono": "Rubik, ui-sans-serif, system-ui, sans-serif",
            "bg": "7 5 12", "panel": "22 16 32", "ink": "248 244 252",
            "display_css": "font-weight:900; font-style:italic; text-transform:uppercase; letter-spacing:-0.01em; line-height:1;",
            "radius": "0.875rem", "h1": "clamp(1.9rem,7.6vw,4.5rem)",
        },
        "accent": "150 255 40", "on_accent": "7 5 12",
        "hero": "barber_cut", "side": "barber_tools",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Tell us the cut you want and we will dial it in.",
        "sub": "The Hair Lab is in Pomona. Call the shop to grab a time, then come see us.",
        "cards_heading": "What we do",
        "cards": [
            ("Cuts", "Bring a photo or just describe it. Your barber will talk it through before the clippers come out."),
            ("Fades", "Tapers and fades blended smooth and finished with a sharp lineup."),
            ("Beard", "Trimmed, shaped and edged so it matches the cut."),
        ],
    },
    "Pomona Barbers": {
        "slug": "pomona-barbers-pomona", "short": "Pomona Barbers",
        # Black slab lettering in a red ring on white (their sign, from Instagram).
        "logo": True, "address": "430 W. Holt Ave. #D, Pomona, CA 91766",
        "theme": {
            "fonts": "family=Arvo:wght@700&family=Libre+Franklin:wght@400;500;600;700",
            "display": "Arvo, Rockwell, Georgia, serif",
            "sans": "'Libre Franklin', ui-sans-serif, system-ui, sans-serif",
            "mono": "'Libre Franklin', ui-sans-serif, system-ui, sans-serif",
            "bg": "248 244 236", "panel": "237 230 216", "ink": "22 19 16",
            "display_css": "font-weight:700; letter-spacing:-0.01em; line-height:1.06;",
            "radius": "0.125rem", "h1": "clamp(1.9rem,7.6vw,4.25rem)",
        },
        "accent": "176 32 36", "on_accent": "255 252 246",
        "hero": "barber_shop", "side": "barber_fade",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "A good haircut close to home in Pomona.",
        "sub": "Pomona Barbers does cuts, fades and beard work. Call ahead and we will have a chair ready for you.",
        "cards_heading": "In the chair",
        "cards": [
            ("Cuts", "Regular cuts and clean ups done the way you ask for them."),
            ("Fades", "Low, mid or high, blended clean with a lineup to finish."),
            ("Beard", "Beard trims and shape ups to go with the cut."),
        ],
    },
    "SERGE BARBERSHOP": {
        "slug": "serge-barbershop-pomona", "short": "Serge Barbershop",
        "display": "Serge Barbershop",
        "action_url": "https://bookedin.com/book/sergio-3",  # from the @serge_fades bio
        # No logo on their Instagram; the profile photo is Serge cutting in the shop.
        "address": "929 W Mission Blvd, Pomona, CA",
        "logo": True, "logo_alt": "Serge cutting hair in the shop",
        "accent": "200 36 52", "on_accent": "250 246 240",
        "hero": "barber_fade", "side": "barber_shave",
        "kicker": "Barbershop · Pomona, CA",
        "h1": "Book with Serge and leave with a clean fade.",
        "sub": "Pick your time online in a minute, or call. Serge Barbershop is at 929 W Mission Blvd in Pomona.",
        "cards_heading": "At the shop",
        "cards": [
            ("Cuts", "Tell Serge what you are going for and he will get you there."),
            ("Fades", "Skin fades, tapers and blends with a crisp lineup."),
            ("Beard", "Lined up and trimmed so the whole look comes together."),
        ],
    },
}

def _theme(fonts, display, sans, bg, panel, ink, css, radius, h1="clamp(2rem,8vw,4.5rem)"):
    return {"fonts": fonts, "display": display, "sans": sans, "mono": sans, "bg": bg, "panel": panel,
            "ink": ink, "display_css": css, "radius": radius, "h1": h1}


# Nov 9 batch, reworked around each shop's own logo and colors (Instagram or
# Facebook profile picture, saved as sites/<slug>/logo.jpg) and the dishes and
# services their Google reviewers mention most (the sheet's Hook column).
REFRESH = {
    "El Picoso Restaurant": {
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": _theme("family=Rozha+One&family=Karla:wght@400;500;600;700", "'Rozha One', Georgia, serif",
                        "Karla, ui-sans-serif, system-ui, sans-serif", "164 20 30", "140 14 24", "255 244 220",
                        "font-weight:400; line-height:1.04;", "0.5rem"),
        "accent": "252 208 40", "on_accent": "60 16 10",
        "cards": [
            ("Asada", "The one people keep coming back for. Get it in tacos, in a burrito or on a plate."),
            ("Huaraches", "Thick masa off the griddle, topped with beans, your choice of meat and everything that goes with it."),
            ("Pozole", "A big bowl with the fixings on the side. Call ahead to make sure it is on today."),
        ],
    },
    "Taqueria La Fogata": {
        "slug": "taqueria-la-fogata-west-covina", "city": "West Covina",
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": _theme("family=Rokkitt:wght@700;800&family=Nunito+Sans:wght@400;600;700", "Rokkitt, Rockwell, Georgia, serif",
                        "'Nunito Sans', ui-sans-serif, system-ui, sans-serif", "245 237 222", "234 222 200", "74 24 36",
                        "font-weight:800; line-height:1;", "0.375rem", "clamp(2.2rem,9vw,5rem)"),
        "accent": "224 98 28", "on_accent": "40 14 6",
        "kicker": "Taqueria · West Covina, CA",
        "address": "314 N Azusa Ave, West Covina, CA",
        "h1": "Handmade tortillas and birria worth the drive.",
        "sub": "Taqueria La Fogata makes authentic Mexican food in West Covina. Call ahead or come by and eat.",
        "cards_heading": "What people come for",
        "cards": [
            ("Handmade tortillas", "Pressed and cooked here. You can taste the difference in every taco."),
            ("Birria", "Slow cooked and rich. Ask how we are serving it today."),
            ("Catering", "Feeding a party or the office? We cater any occasion. Call and we will set it up."),
        ],
    },
    "Tacos El Superior": {
        "logo": True, "logo_shape": "rounded-[10px]", "tagline": "Hecho con amor y calidad",
        "theme": _theme("family=Patua+One&family=Work+Sans:wght@400;500;600;700", "'Patua One', Georgia, serif",
                        "'Work Sans', ui-sans-serif, system-ui, sans-serif", "247 246 244", "236 233 228", "44 30 30",
                        "font-weight:400; line-height:1.04;", "0.5rem"),
        "accent": "212 38 46", "on_accent": "255 255 255",
        "cards": [
            ("Quesabirria", "Crisp, cheesy and made for dipping. It is what most people walk in asking for."),
            ("Tacos", "Corn tortillas, your meat, onion, cilantro and salsa."),
            ("Burritos", "Big, filling and easy to take with you. Add what you like and leave out what you don't."),
        ],
    },
    "Taco Tapatio": {
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": _theme("family=Bowlby+One&family=Work+Sans:wght@400;500;600;700", "'Bowlby One', Impact, sans-serif",
                        "'Work Sans', ui-sans-serif, system-ui, sans-serif", "255 248 230", "248 234 204", "64 16 16",
                        "font-weight:400; line-height:1.03;", "0.5rem", "clamp(1.9rem,7.6vw,4.25rem)"),
        "accent": "198 28 36", "on_accent": "255 244 214",
        "cards": [
            ("Carne asada", "Grilled and chopped to order. Have it in tacos, a burrito or on a plate."),
            ("Fish tacos", "Done right, with lime and salsa on the side."),
            ("Burritos and plates", "Rice, beans and your pick of meat when a couple of tacos is not enough."),
        ],
    },
    "Lalo's Family Restaurant Comida Mexicana": {
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": _theme("family=Berkshire+Swash&family=Mulish:wght@400;500;600;700", "'Berkshire Swash', Georgia, serif",
                        "Mulish, ui-sans-serif, system-ui, sans-serif", "255 247 228", "250 232 196", "56 30 10",
                        "font-weight:400; line-height:1.08;", "0.75rem"),
        "accent": "204 84 16", "on_accent": "255 248 232",
        "sub": "Lalo's is a family-owned restaurant cooking comida mexicana in Azusa. Come in and sit down, or call your order in to go.",
        "address": "530 S Citrus Ave, Azusa, CA",
        "cards": [
            ("Chilaquiles", "Done the way they should be, and good at any time of day."),
            ("Wet burritos", "Covered in sauce and melted cheese. You will want a fork."),
            ("Family orders", "Feeding a group? Call ahead and we will have everything packed and ready."),
        ],
    },
    "El Bukanas Azusa": {
        "display": "El Bukanas", "q": "El Bukanas",
        "logo": True,
        "theme": _theme("family=Lobster+Two:ital,wght@1,700&family=Cabin:wght@400;500;600;700", "'Lobster Two', Georgia, serif",
                        "Cabin, ui-sans-serif, system-ui, sans-serif", "253 246 238", "246 230 214", "78 32 16",
                        "font-weight:700; font-style:italic; line-height:1.04;", "0.75rem", "clamp(2.3rem,9.4vw,5rem)"),
        "accent": "184 76 38", "on_accent": "255 246 236",
        "cards": [
            ("Tacos gobernador", "Shrimp and melted cheese folded into a crisp tortilla."),
            ("Tacos al vapor", "Soft steamed tacos, the kind that are hard to find done right."),
            ("Burritos and brunch", "Burritos big enough for two meals, plus our new brunch menu. Ask what is on it."),
        ],
    },
    "Sandy’s Cocina": {
        "logo": True, "logo_alt": "Tacos from Sandy’s Cocina",
        "cards": [
            ("Taco Tuesday", "Tuesday is taco day here. Call to ask what the deal is this week."),
            ("Chilaquiles", "A plate that fills you up, made the way you would get it at home."),
            ("Burritos and plates", "Made to order, with rice and beans on the side when you want the full meal."),
        ],
    },
    "Main St Barbershop": {
        "logo": True, "logo_shape": "rounded-none",
        "theme": _theme("family=Zilla+Slab:wght@700&family=Archivo:wght@400;500;600;700", "'Zilla Slab', Rockwell, serif",
                        "Archivo, ui-sans-serif, system-ui, sans-serif", "255 255 255", "242 242 240", "14 14 14",
                        "font-weight:700; text-transform:uppercase; letter-spacing:0.005em; line-height:1;", "0", "clamp(2rem,8.2vw,4.5rem)"),
        "accent": "196 30 44", "on_accent": "255 255 255",
        "sub": "Main St Barbershop is in downtown Pomona. Pick your barber and your time online, or call the shop and we will get you in.",
        "cards": [
            ("Cuts", "Classic cuts, scissor work and everything in between. Tell your barber what you want or show a photo."),
            ("Fades", "Low, mid, high or a taper. Blended clean with a sharp lineup to finish."),
            ("Beard trims", "Shaped, lined up and finished clean. Plenty of our regulars come in just for this."),
        ],
    },
    "El Punto Barbershop Pomona": {
        "display": "El Punto Barbershop",
        "logo": True,
        "theme": _theme("family=Roboto+Slab:wght@800&family=Archivo:wght@400;500;600;700", "'Roboto Slab', Rockwell, serif",
                        "Archivo, ui-sans-serif, system-ui, sans-serif", "20 17 28", "32 28 44", "238 230 212",
                        "font-weight:800; text-transform:uppercase; letter-spacing:0.01em; line-height:1.02;", "0.125rem", "clamp(1.8rem,7.4vw,4.25rem)"),
        "accent": "232 222 198", "on_accent": "20 17 28",
        "cards": [
            ("Cuts", "From a quick clean up to a full restyle. Your barber takes the time to get it right."),
            ("Fades", "Skin fades, tapers and blends with a crisp lineup."),
            ("Kids' cuts", "Kids are welcome here. Our barbers are patient and know how to keep them still."),
        ],
    },
    "The Bambino Barbershop Pomona": {
        "display": "The Bambino Barbershop",
        "logo": True,
        "theme": _theme("family=Lilita+One&family=Nunito:wght@400;600;700", "'Lilita One', Impact, sans-serif",
                        "Nunito, ui-sans-serif, system-ui, sans-serif", "5 10 22", "14 26 52", "244 248 255",
                        "font-weight:400; line-height:1.02;", "0.875rem"),
        "accent": "255 168 20", "on_accent": "20 10 0",
        "cards": [
            ("Cuts", "Whatever you wear, your barber will keep it fresh."),
            ("Fades", "Low to high and everything between, blended smooth."),
            ("Kids' cuts", "Parents bring their kids here for a reason. We take our time and keep it fun."),
        ],
    },
    "Christian & Roberto's Barber": {
        "sub": "Good cuts at a fair price in Pomona. It gets busy, so call the shop before you head over.",
        "address": "1183 W Holt Ave, Pomona, CA",
    },
    "Erik's Tires": {
        "address": "13900 Ramona Blvd, Baldwin Park, CA",
        "cards": [
            ("New and used tires", "Call with your size or read it to us off the sidewall. We will tell you what we have and what it costs."),
            # Their Facebook page says they do not use plugs.
            ("Flat repair", "Picked up a nail? We patch it properly. We do not use plugs."),
            ("Alignment and smog", "Pulling to one side or due for a smog check? We do both here."),
        ],
    },
    "Purrfect Auto Service": {
        "cards": [
            ("Oil change", "Oil and filter with a look over the basics while your car is in the bay."),
            ("Smog check", "Due for smog? Bring it in and we will get it done."),
            ("Brakes", "Squealing, grinding or a soft pedal. We check it and show you what it needs."),
        ],
    },
    "HP Commercial Roofing Pro West Covina": {
        "logo": True,
        "theme": _theme("family=Montserrat:wght@700;800&family=Source+Sans+3:wght@400;500;600;700", "Montserrat, 'Arial Black', sans-serif",
                        "'Source Sans 3', ui-sans-serif, system-ui, sans-serif", "255 255 255", "238 242 246", "44 52 62",
                        "font-weight:800; letter-spacing:-0.02em; line-height:1.04;", "0.25rem", "clamp(1.9rem,7.6vw,4.25rem)"),
        "accent": "18 108 178", "on_accent": "255 255 255",
    },
    "Chad Da Barber\U0001F488 HeadSprung Barbershop": {
        "logo": True, "logo_shape": "rounded-[10px]", "logo_alt": "The HeadSprung Barbershop storefront",
        "accent": "236 48 60", "on_accent": "255 248 248",
    },
}
for _name, _over in REFRESH.items():
    CONTENT[_name].update(_over)

# Nov 10: WEAK leads with an Instagram account that had no page yet.
CONTENT.update({
    "CSWF Construction": {
        "slug": "cswf-construction-covina", "short": "CSWF Construction",
        # Gold lettering on black (their Instagram logo).
        "logo": True, "logo_shape": "rounded-[10px]",
        "theme": _theme("family=Bebas+Neue&family=Barlow:wght@400;500;600;700", "'Bebas Neue', Impact, sans-serif",
                        "Barlow, ui-sans-serif, system-ui, sans-serif", "10 10 10", "26 23 16", "246 241 228",
                        "font-weight:400; letter-spacing:0.01em; line-height:0.98;", "0.25rem", "clamp(2.4rem,10vw,5.5rem)"),
        "accent": "214 168 60", "on_accent": "18 13 2",
        "hero": "roof_ladder", "side": "roof_shingles",
        "kicker": "General contractor · Covina, CA",
        "h1": "Tell us what you want built and get a free estimate.",
        "sub": "CSWF Construction builds ADUs, custom homes and apartment complexes. Send the details below or call, and we will come take a look.",
        "cards_heading": "What we build",
        "cards": [
            ("ADUs", "A backyard unit for family or rental income, built from the plans to the final inspection."),
            ("Custom homes", "Your house built the way you want it, with one contractor responsible for all of it."),
            ("Apartment complexes", "Multi-unit projects built for owners and investors."),
        ],
        "form_field": "Property address",
        "form_placeholder": "Detached ADU in the backyard, about 600 square feet, hoping to start in spring",
        "closing": ("Rather talk it through?", "Call and tell us about the job. The estimate is free either way."),
    },
    "Avila Auto Repair": {
        "slug": "avila-auto-repair-baldwin-park", "short": "Avila Auto Repair",
        # No Instagram: @avilas.inc is a different Avila's Auto Repair in Tracy, CA.
        "accent": "72 152 255", "on_accent": "8 14 24",
        "hero": "auto_hood", "side": "auto_hands",
        "kicker": "Auto repair · Baldwin Park, CA",
        "h1": "Bring it to Avila and find out what it really needs.",
        "sub": "Avila Auto Repair works on cars and trucks in Baldwin Park. Call and tell us what it is doing, and we will tell you when to bring it in.",
        "cards_heading": "In the bay",
        "cards": [
            ("Diagnostics", "Warning light, strange noise or a car that just feels wrong. We find the cause first."),
            ("Brakes", "Pads, rotors and everything that stops you, checked and replaced when it is time."),
            ("Maintenance", "Oil, fluids, belts and the regular work that keeps you out of the shop."),
        ],
    },
    "Engine Dynamics": {
        "slug": "engine-dynamics-baldwin-park", "short": "Engine Dynamics",
        "accent": "255 96 32", "on_accent": "19 21 26",
        "hero": "auto_engine", "side": "auto_hands",
        "kicker": "Auto repair · Baldwin Park, CA",
        "h1": "Engine trouble? Call before it gets worse.",
        "sub": "Engine Dynamics works on old and new vehicles in Baldwin Park. Tell us what you are hearing or feeling and we will tell you when to bring it in.",
        "cards_heading": "What we do",
        "cards": [
            ("Engine repair", "Rough idle, misfires, leaks or loss of power. We find the cause before we replace anything."),
            ("Mufflers and exhaust", "Mufflerville is part of the shop. Bring us anything loud, leaking or rusted through."),
            ("U-Haul rentals", "We are a U-Haul dealer too. Call to ask what trucks and trailers are on the lot."),
        ],
    },
    "Magik Touch Mobile Detailing": {
        "slug": "magik-touch-mobile-detailing-el-monte", "short": "Magik Touch", "mobile": True,
        # Gold ring and lettering on black with a red car outline (their Instagram logo).
        "logo": True,
        "theme": _theme("family=Rajdhani:wght@600;700&family=Barlow:wght@400;500;600;700", "Rajdhani, 'Arial Narrow', sans-serif",
                        "Barlow, ui-sans-serif, system-ui, sans-serif", "8 8 8", "24 21 15", "246 242 232",
                        "font-weight:700; text-transform:uppercase; letter-spacing:0.02em; line-height:1;", "0.375rem", "clamp(2.1rem,8.8vw,4.75rem)"),
        "accent": "214 168 64", "on_accent": "16 12 2",
        "hero": "detail_rinse", "side": "detail_foam",
        "kicker": "Mobile detailing · El Monte, CA",
        "h1": "A full detail without leaving your driveway.",
        "sub": "Magik Touch Mobile Detailing comes to you across LA, the Inland Empire and Orange County. Call, tell us what you drive, and we will set a time.",
        "cards_heading": "What we do",
        "cards": [
            ("Exterior", "Hand wash, wheels, tires and glass, finished so the paint shines."),
            ("Interior", "Vacuumed, wiped and cleaned out, seats and carpets included."),
            ("Full detail", "Inside and out in one visit. Call with your make and model for a price."),
        ],
        "closing": ("Book your detail", "Call and tell us what you drive and where it is parked. We will give you a price and a time."),
    },
})

CONTENT.update({
    "Santa Maria’s Punta Roja": {
        "slug": "santa-marias-punta-roja-azusa", "short": "Santa Maria’s",
        "display": "Santa Maria’s Punta Roja",
        # Anchor mark, dark red blackletter and small caps on cream (their Facebook profile picture).
        "logo": True, "logo_shape": "rounded-[6px]", "logo_box": "w-[168px] h-auto sm:w-[220px]",
        "theme": _theme("family=Marcellus+SC&family=Lora:wght@400;500;600;700", "'Marcellus SC', Georgia, serif",
                        "Lora, Georgia, serif", "246 242 232", "235 228 212", "34 32 40",
                        "font-weight:400; letter-spacing:0.01em; line-height:1.08;", "0.25rem", "clamp(2rem,8.4vw,4.5rem)"),
        "accent": "150 24 34", "on_accent": "255 248 240",
        "hero": "tacos_plate", "side": "tacos_tile",
        "kicker": "Mexican kitchen · Azusa, CA",
        "h1": "Authentic Mexican food from our kitchen in Azusa.",
        "sub": "Santa Maria’s Punta Roja is a Mexican kitchen in Azusa. Call your order in, or come by and eat with us.",
        "cards_heading": "From the kitchen",
        "cards": [
            ("Tacos", "On warm tortillas with onion, cilantro and salsa. Tell us the meat and how many."),
            ("Burritos", "Rolled to order and filling enough to be the whole meal."),
            ("Plates", "Your choice with rice, beans and tortillas when you want to sit down and eat."),
        ],
    },
})

CONTENT.update({
    "Prestige Mercedes Imports": {
        "slug": "prestige-mercedes-imports-baldwin-park", "short": "Prestige Mercedes Imports",
        # Profile photo on their Instagram is a white AMG fender badge; no logo.
        "logo": True, "logo_shape": "rounded-[10px]", "logo_alt": "V8 Biturbo badge on a white Mercedes-AMG",
        "no_band": True,
        "theme": _theme("family=Sora:wght@600;700&family=Figtree:wght@400;500;600;700", "Sora, 'Helvetica Neue', sans-serif",
                        "Figtree, ui-sans-serif, system-ui, sans-serif", "250 250 248", "237 237 233", "20 22 26",
                        "font-weight:600; letter-spacing:-0.02em; line-height:1.05;", "0.375rem", "clamp(1.9rem,7.6vw,4.25rem)"),
        "accent": "20 22 26", "on_accent": "250 250 248",
        "hero": "auto_hood", "side": "auto_engine",
        "kicker": "Independent Mercedes-Benz service · Baldwin Park, CA",
        "h1": "Mercedes-Benz service in Baldwin Park, without the dealership.",
        "sub": "Prestige Mercedes Imports is an independent Mercedes-Benz shop. Call and tell us what the car is doing, and we will tell you when to bring it in.",
        "cards_heading": "What we do",
        "cards": [
            ("Service and maintenance", "Oil services, fluids, filters and the scheduled work your Mercedes calls for."),
            ("Diagnostics", "Warning lights and odd behavior tracked down properly before any parts get replaced."),
            ("Repairs", "Engine, brakes, suspension and electrical work on Mercedes-Benz cars, old and new."),
        ],
    },
})

# Nov 11 sheet: no-website leads with a verified Instagram that takes messages.
CONTENT.update({
    "Karam construction inc": {
        "slug": "karam-construction-glendora", "short": "Karam Construction", "display": "Karam Construction",
        # No logo on Instagram: the profile picture is a white kitchen with a stone island.
        "logo": True, "logo_shape": "rounded-[10px]", "logo_alt": "Kitchen from Karam Construction's Instagram profile",
        "address": "1000 E Rte 66, Glendora, CA",
        "theme": _theme("family=Manrope:wght@700;800&family=Source+Sans+3:wght@400;500;600;700", "Manrope, 'Helvetica Neue', sans-serif",
                        "'Source Sans 3', ui-sans-serif, system-ui, sans-serif", "250 250 247", "236 238 234", "24 30 32",
                        "font-weight:800; letter-spacing:-0.025em; line-height:1.05;", "0.375rem", "clamp(1.9rem,7.6vw,4.25rem)"),
        "accent": "14 116 106", "on_accent": "255 255 255",
        "hero": "remodel_kitchen", "side": "remodel_plans",
        "kicker": "General contractor · Glendora, CA",
        "h1": "Remodeling in Glendora, from the cabinets to the last coat of paint.",
        "sub": "Karam Construction Inc. remodels kitchens, bathrooms and whole homes. Tell us about the job below or call, and we will come out and look at it.",
        "cards_heading": "What we do",
        "cards": [
            ("Kitchen remodels", "New layout, counters and appliances, built so the kitchen works the way you cook."),
            ("Cabinets", "Cabinet work is a big part of what we do. Our customers bring it up in their reviews."),
            ("Whole home remodeling", "One contractor for the whole job, so you always know who to call."),
        ],
        "form_field": "Property address",
        "form_placeholder": "Kitchen remodel, new cabinets and counters, hoping to start after the holidays",
        "closing": ("Rather talk it through?", "Call and tell us about the job. We answer every review, and we will answer you too."),
    },
    "Myrtle Auto Service": {
        "slug": "myrtle-auto-service-monrovia", "short": "Myrtle Auto", "display": "Myrtle Auto Service Center",
        # Red shield with a blue wrench and a blue MYRTLE ribbon, painted on a cream block wall (their sign).
        "logo": True, "logo_shape": "rounded-[10px]", "no_band": True,
        "address": "1827 S Myrtle Ave, Monrovia, CA",
        "theme": _theme("family=Barlow+Condensed:ital,wght@1,700;1,800&family=Barlow:wght@400;500;600;700", "'Barlow Condensed', 'Arial Narrow', sans-serif",
                        "Barlow, ui-sans-serif, system-ui, sans-serif", "245 239 227", "233 225 209", "22 36 58",
                        "font-weight:800; font-style:italic; text-transform:uppercase; letter-spacing:0.005em; line-height:0.98;", "0.375rem", "clamp(2.2rem,9.4vw,5rem)"),
        "accent": "200 32 44", "on_accent": "255 255 255",
        "hero": "auto_hood", "side": "auto_hands",
        "kicker": "Auto repair · Monrovia, CA",
        "h1": "Honest auto repair on Myrtle Avenue.",
        "sub": "Myrtle Auto Service Center is a complete repair shop for foreign and domestic cars in Monrovia. Call and tell us what the car is doing.",
        "cards_heading": "In the shop",
        "cards": [
            ("Foreign and domestic", "We work on both. Call with the year, make and model and we will tell you when to bring it in."),
            ("Diagnostics", "Check engine light or a noise you cannot place. We find the cause before we replace anything."),
            ("Maintenance", "Oil, brakes, fluids and the regular service that keeps you on the road."),
        ],
    },
    "Issa's Professional Mobile Detailing": {
        "slug": "issas-mobile-detailing-rancho-cucamonga", "short": "Issa's Detailing", "mobile": True,
        "city": "Rancho Cucamonga",
        # No logo: the Instagram profile picture is Issa hand washing a foamed-up car at sunset.
        "logo": True, "logo_shape": "rounded-[10px]", "logo_alt": "Hand washing a soaped-up car, from Issa's Instagram profile",
        "accent": "247 200 72", "on_accent": "18 14 2",
        "hero": "detail_foam", "side": "detail_sponge",
        "kicker": "Mobile detailing · Rancho Cucamonga, CA",
        "h1": "Detailing done at your place, down to the small stuff.",
        "sub": "Issa's Professional Mobile Detailing comes to you in Rancho Cucamonga and the cities around it. Call, tell us what you drive, and we will set a time.",
        "cards_heading": "What we do",
        "cards": [
            ("Interior cleaning", "Seats, carpets, vents and door panels cleaned out properly. It is what our customers mention most."),
            ("Exterior wash", "Foamed, hand washed and dried, with the wheels and glass done too."),
            ("Full detail", "Inside and out in one visit. Call with your make and model for a price."),
        ],
        "visit_h": "Serving Rancho Cucamonga",
        "closing": ("Book your detail", "Call and tell us what you drive and where it is parked. We will give you a price and a time."),
    },
    "Morralito Mexican Grill": {
        "slug": "morralito-mexican-grill-duarte", "short": "Morralito",
        # Dark red Western lettering with a white outline on gray barn wood (their Facebook profile picture).
        "logo": True, "logo_shape": "rounded-[8px]", "logo_box": "w-[132px] h-[132px] sm:w-[168px] sm:h-[168px]",
        "address": "1000 Las Lomas Rd, Duarte, CA",
        "theme": _theme("family=Rye&family=Libre+Franklin:wght@400;500;600;700", "Rye, Georgia, serif",
                        "'Libre Franklin', ui-sans-serif, system-ui, sans-serif", "40 40 42", "54 54 56", "246 242 236",
                        "font-weight:400; letter-spacing:0.01em; line-height:1.12;", "0.25rem", "clamp(1.75rem,7vw,3.75rem)"),
        "accent": "178 30 52", "on_accent": "255 246 240",
        "hero": "tacos_jarrito", "side": "margarita",
        "kicker": "Mexican grill and cantina · Duarte, CA",
        "h1": "Mexican food, margaritas and karaoke in Duarte.",
        "sub": "Morralito Mexican Grill is a restaurant and cantina on Las Lomas Road. Call ahead for a table or to place an order.",
        "cards_heading": "Why people come in",
        "cards": [
            ("Margaritas", "The drink our customers talk about more than anything else on the menu."),
            ("From the grill", "Tacos, burritos and plates with rice and beans, made to order."),
            ("Karaoke", "Call and ask which nights we have it going, then bring your friends."),
        ],
    },
    "Rich & Famous Barbershop": {
        "slug": "rich-and-famous-barbershop-la-verne", "short": "Rich & Famous",
        # Gold brush-script wordmark on black with "LAVERNE, CA" above it (their Instagram logo).
        "logo": True, "address": "1965 Foothill Blvd, La Verne, CA",
        "tagline": "Transforming lives daily, one haircut and shave at a time.",
        "theme": _theme("family=DM+Serif+Display&family=DM+Sans:wght@400;500;600;700", "'DM Serif Display', Georgia, serif",
                        "'DM Sans', ui-sans-serif, system-ui, sans-serif", "8 8 8", "24 22 17", "246 241 230",
                        "font-weight:400; letter-spacing:-0.005em; line-height:1.06;", "0.25rem", "clamp(2rem,8.2vw,4.5rem)"),
        "accent": "212 170 74", "on_accent": "18 13 2",
        "hero": "barber_shop", "side": "barber_shave",
        "kicker": "Barbershop · La Verne, CA",
        "h1": "Cuts and shaves on Foothill in La Verne.",
        "sub": "Rich & Famous Barbershop is the kind of shop where everybody gets a welcome, kids included. Call ahead and we will have a chair ready.",
        "cards_heading": "In the chair",
        "cards": [
            ("Haircuts", "Tell your barber how you wear it and leave looking the way you wanted."),
            ("Shaves", "A proper shave and a clean lineup to go with the cut."),
            ("Kids' cuts", "Bring the little ones. Parents tell us this is where their kids like to come."),
        ],
    },
    "Tacos Estrella": {
        "slug": "tacos-estrella-duarte", "short": "Tacos Estrella",
        # White slab lettering, red star and red banner on black (their Instagram logo).
        "logo": True, "address": "1112 Huntington Dr, Duarte, CA",
        "theme": _theme("family=Alfa+Slab+One&family=Work+Sans:wght@400;500;600;700", "'Alfa Slab One', Rockwell, Georgia, serif",
                        "'Work Sans', ui-sans-serif, system-ui, sans-serif", "10 10 10", "26 26 26", "250 248 244",
                        "font-weight:400; letter-spacing:0.005em; line-height:1.06;", "0.375rem", "clamp(1.9rem,7.8vw,4.25rem)"),
        "accent": "214 30 38", "on_accent": "255 255 255",
        "hero": "tacos_row", "side": "tacos_lime",
        "kicker": "Mexican restaurant · Duarte, CA",
        "h1": "Asada tacos on Huntington Drive.",
        "sub": "Tacos Estrella is a Mexican restaurant in Duarte. Call your order in and it will be ready when you get here.",
        "cards_heading": "On the menu",
        "cards": [
            ("Asada", "The one our customers order most. Get it in a taco, a burrito or on a plate."),
            ("Tacos", "On warm tortillas with onion, cilantro and salsa. Tell us the meat and how many."),
            ("Burritos", "Rolled to order and big enough to be the whole meal."),
        ],
    },
})

# Nov 11 sheet: leads with a published email and no real site of their own.
CONTENT.update({
    "Saavedra Automotive Specialties": {
        "slug": "saavedra-automotive-specialties-monrovia", "short": "Saavedra Auto",
        # Charcoal round badge with crossed wrenches, "S E T 2016" (the logo on their Wix page). Red accents on that page.
        "logo": True, "no_band": True, "address": "220 E Lime Ave, Monrovia, CA",
        "theme": _theme("family=Zilla+Slab:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600;700", "'Zilla Slab', Rockwell, Georgia, serif",
                        "'IBM Plex Sans', ui-sans-serif, system-ui, sans-serif", "244 242 238", "230 227 221", "32 32 34",
                        "font-weight:700; letter-spacing:-0.01em; line-height:1.04;", "0.25rem", "clamp(2rem,8.2vw,4.5rem)"),
        "accent": "190 34 38", "on_accent": "255 255 255",
        "hero": "auto_engine", "side": "auto_hands",
        "kicker": "Repair, restoration and custom work · Monrovia, CA",
        "h1": "New or old, I treat them all like classics.",
        "sub": "Saavedra Automotive Specialties does everything from regular maintenance to full reconditioning. Call and tell me what you are working with.",
        "cards_heading": "What I do",
        "cards": [
            ("Maintenance and repair", "All makes and models. You get a real cost and a real timeline before any work starts."),
            ("Parts installation", "Bring me the part you bought and never had time to put in. I will finish that weekend project for you."),
            ("Restoration or revival", "Back to its former glory, or just running again after sitting for a decade or two."),
        ],
    },
    "Luxe Express Mobile Auto Detail": {
        "slug": "luxe-express-mobile-auto-detail-fontana", "short": "Luxe Express", "mobile": True, "city": "Fontana",
        # Thin gold capitals and a gray sports car inside a white ring on black (their Facebook profile picture).
        "logo": True,
        "theme": _theme("family=Jost:wght@300;400;500;600", "Jost, 'Century Gothic', sans-serif",
                        "Jost, ui-sans-serif, system-ui, sans-serif", "6 6 6", "22 20 16", "244 240 230",
                        "font-weight:300; text-transform:uppercase; letter-spacing:0.04em; line-height:1.1;", "0", "clamp(1.8rem,7.4vw,4rem)"),
        "accent": "198 162 92", "on_accent": "14 11 4",
        "hero": "detail_polish", "side": "detail_headlight",
        "kicker": "Mobile auto detail · Fontana, CA",
        "h1": "Mobile detailing in Fontana that shows up on time.",
        "sub": "Luxe Express Mobile Auto Detail comes to your home in Fontana and the cities around it. Call, tell us what you drive, and we will set a time.",
        "cards_heading": "What we do",
        "cards": [
            ("Shampoo and extraction", "Stains pulled out of seats and carpets. It is one of the things our customers mention most."),
            ("Paint correction", "Swirls and dull paint polished out so the color looks right again."),
            ("Ceramic coating", "Long-term protection for the paint once it is corrected. Call for the options."),
        ],
        "visit_h": "Serving Fontana",
        "closing": ("Book your detail", "Call and tell us what you drive and where it is parked. We will give you a price and a time."),
    },
    "Delia's Barber & Beauty": {
        "slug": "delias-barber-and-beauty-la-verne", "short": "Delia's",
        # No logo: the Facebook profile picture is a staff photo, which stays off the page.
        "address": "2081 3rd St, La Verne, CA",
        "theme": _theme("family=Young+Serif&family=Nunito+Sans:wght@400;600;700", "'Young Serif', Georgia, serif",
                        "'Nunito Sans', ui-sans-serif, system-ui, sans-serif", "250 245 239", "239 230 220", "46 32 36",
                        "font-weight:400; letter-spacing:-0.01em; line-height:1.08;", "0.5rem", "clamp(2rem,8.2vw,4.5rem)"),
        "accent": "132 44 72", "on_accent": "255 248 244",
        "hero": "barber_shop", "side": "barber_cut",
        "kicker": "Barber and beauty shop · La Verne, CA",
        "h1": "A friendly chair for the whole family in La Verne.",
        "sub": "Delia's Barber & Beauty is on 3rd Street in old town La Verne. Call ahead and we will have a chair ready for you.",
        "cards_heading": "In the chair",
        "cards": [
            ("Haircuts", "Tell us how you wear it. We take our time and get it right."),
            ("Kids' cuts", "Parents bring their kids here because we are patient with them."),
            ("Barber and beauty", "Both under one roof, so the whole family can come in together."),
        ],
    },
})

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
    if "detailing" in s:
        return "detail"
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
    t = {**THEMES[cat], **c.get("theme", {})}
    brand = True  # ruled service list, no all-caps labels; logo shown when we have one
    city = c.get("city") or city_of(row["Search"])
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
    action_url = c.get("action_url") or (site if any(h in site for h in ACTION_URL_HINTS) else "")
    mobile = c.get("mobile", False)  # comes to the customer, so no directions button

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
        nav_label = "Estimate"
        closing_h, closing_p = c.get("closing", ("Rather talk it through?", "Call and tell us what is going on with the roof. The estimate is free either way."))
        visit_h = "Where we work"
    elif cat == "detail":
        second = f'<a href="#services" class="{ghost}">{e(c["cards_heading"])}</a>' if mobile else dir_btn
        cta = f'<a href="tel:{phone_tel}" class="{primary}">Call now · {e(phone)}</a>{second}'
        nav_label = "Call"
        closing_h, closing_p = c["closing"]
        visit_h = c.get("visit_h") or ("We come to you" if mobile else "Where to find us")
    else:
        second = (f'<a href="#estimate" class="{ghost}">Free estimate</a>' if has_form
                  else f'<a href="#hours" class="{ghost}">Hours</a>')
        cta = f'<a href="tel:{phone_tel}" class="{primary}">Call now · {e(phone)}</a>{second}{dir_btn}'
        nav_label, closing_h, closing_p = "Call", "Call before you come in", "A two minute call saves you a trip. We will tell you what we can do and when."
        visit_h = "Where to find us"

    # ---- hero variants -----------------------------------------------------
    kicker = f'<p class="kicker text-accent">{e(c["kicker"])}</p>'
    h1 = f'<h1 class="display mt-4 text-[{t.get("h1", "clamp(2.1rem,8.6vw,5.25rem)")}] max-w-[18ch]">{e(c["h1"])}</h1>'
    sub = f'<p class="mt-6 text-ink/75 text-[17px] sm:text-lg leading-relaxed max-w-[52ch]">{e(c["sub"])}</p>'
    ctas = f'<div class="mt-8 flex flex-col min-[480px]:flex-row min-[480px]:flex-wrap gap-3">{cta}</div>'

    if brand:
        tagline = f'<p class="mt-3 text-[15px] italic text-ink/70">{e(c["tagline"])}</p>' if c.get("tagline") else ""
        logo = "" if not c.get("logo") else (f'<img src="logo.jpg" alt="{e(c.get("logo_alt", display + " logo"))}" width="150" height="150" '
                f'class="{c.get("logo_box", "w-[88px] h-[88px] sm:w-[116px] sm:h-[116px]")} object-cover {c.get("logo_shape", "rounded-full")}" />')
        rating_inline = (f'<p class="mt-6 text-[15px] text-ink/70"><a class="underline underline-offset-4 decoration-accent decoration-2 hover:text-ink transition" '
                         f'href="{maps_link}" target="_blank" rel="noopener">{e(stars_plain)}</a></p>')
        hero = f"""
<section id="top" class="max-w-6xl mx-auto px-4 sm:px-8 pt-8 sm:pt-14 pb-10 sm:pb-16 grid lg:grid-cols-12 gap-8 lg:gap-12 items-end">
  <div class="lg:col-span-7">
    {logo}{tagline}
    {h1.replace("mt-4", "mt-6" if c.get("logo") else "mt-0")}
    {sub}
    {ctas}
    {rating_inline}
  </div>
  <figure class="lg:col-span-5 -mx-4 sm:mx-0">
    {img_tag(c["hero"], "w-full h-[220px] sm:h-[420px] object-cover sm:rounded-[var(--radius)]", eager=True)}
  </figure>
</section>"""
    elif cat == "taqueria":
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

    if brand:  # a ruled list, like a shop's service board, in place of three cards
        rows_html = "\n".join(
            f"""      <div class="border-t border-ink/20 py-5 sm:py-6 sm:grid sm:grid-cols-12 sm:gap-6">
        <dt class="display text-xl sm:text-2xl sm:col-span-4">{e(title)}</dt>
        <dd class="mt-1.5 sm:mt-0 sm:col-span-8 text-ink/75 leading-relaxed">{e(body)}</dd>
      </div>"""
            for title, body in c["cards"]
        )
        services = f"""
<section id="services" class="border-t border-ink/10">
  <div class="max-w-6xl mx-auto px-4 sm:px-8 py-12 sm:py-20 grid lg:grid-cols-12 gap-6 lg:gap-12">
    <h2 class="lg:col-span-4 display text-[clamp(1.7rem,6vw,3rem)]">{e(c["cards_heading"])}</h2>
    <dl class="lg:col-span-8 border-b border-ink/20">
{rows_html}
    </dl>
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
      {f'<p class="mt-4 text-ink/75">{e(c["address"])}</p>' if c.get("address") else ""}
      <p class="mt-6 kicker text-ink/55">Phone</p>
      <a href="tel:{phone_tel}" class="display block mt-1 text-3xl sm:text-4xl hover:text-accent transition">{e(phone)}</a>
      <div class="mt-6 flex flex-col min-[480px]:flex-row gap-3">
        {call_btn}
        {"" if mobile else dir_btn}
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

    top_band = '<div class="hazard h-1.5"></div>' if cat == "auto" and not c.get("no_band") else ""
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
  {".kicker { font-size: 14px; letter-spacing: 0; text-transform: none; }" if brand else ""}
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
    only = []
    if "--only" in sys.argv:  # --only "Name A|Name B": build just these, skip top N and ALSO
        only = [n.strip() for n in sys.argv[sys.argv.index("--only") + 1].split("|")]
        rows = []
    picked = {r["Business Name"].strip() for r in rows}
    for wanted in only or ALSO:
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
