"""Plain local-business previews for the Outreach Nov 12 sheet.

    python -I -X utf8 scripts/generate_shop_pages.py            # build all
    python -I -X utf8 scripts/generate_shop_pages.py slug-a slug-b

Built to read like a shop's own site, not a template: the business name is the
headline, the logo is theirs, copy is short and only says things we can back up
(address, phone, what their reviews mention). Pages differ in hero, buttons,
list style, footer and whether they carry a photo at all, so a batch does not
share one skeleton. Each page expects sites/<slug>/logo.jpg (or cover.jpg).
"""
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_weak_batch import (IMG, PAGES_BASE, SITES, WESTCO_PHONE, WESTCO_TEL, YEAR,  # noqa: E402
                                 preview_banner, unsplash)


def e(s):
    return html.escape(str(s), quote=True)


def tel(phone):
    return "+1" + re.sub(r"\D", "", phone)[-10:]


WHITE = dict(bg="#ffffff", ink="#1a1a1a", soft="#555555", line="#d9d9d9")
BLACK = dict(bg="#000000", ink="#f2f2f2", soft="#b0b0b0", line="#333333")

# hero: center | left | cover.   cta: pair | big | text.   lst: bullets | cols | rule
# rate: stars | text.   foot: plain | solid.   Optional: photo, nav, bar, info, two, action.
DET = {'logo': None, 'nologo': True, 'mobile': True, 'address': '', 'cta': 'big', 'call': 'Call or text', 'items': ['Exterior hand wash', 'Interior detail', 'Full detail'], 'list_h': 'Services', 'lst': 'bullets', 'note': 'Call or text with your make and model for a price.', 'about_h': ''}

SHOPS = [
    # ------------------------------------------------------------- taquerias
    dict(name="Tacos Los Mismos", slug="tacos-los-mismos-el-monte", city="El Monte", hero="center",
         address="3057 Tyler Ave, El Monte, CA 91731", phone="(626) 542-3257", rating="4.6", reviews=466,
         logo=dict(w=230), photo="tacos_paper", **WHITE, accent="#1f55b5", on="#ffffff",
         fonts="family=Nunito:wght@400;700;800", head="Nunito, Arial, sans-serif", body="Nunito, Arial, sans-serif", head_css="font-weight:800;",
         what="Taqueria on Tyler Ave in El Monte",
         about_h="", about=["Stop by for tacos, burritos and plates. The carne asada and the chicharron are our most popular, and people love the chile verde burrito.",
                            "Call ahead and we'll have your order ready."],
         list_h="Popular", items=["Carne asada", "Chicharron", "Chile verde burrito"], lst="bullets", note="Full menu in store.",
         call="Call to order", cta="pair", rate="stars", foot="solid", bar=True),
    dict(name="Taqueria La Cabaña E&E", short="La Cabaña E&E", slug="taqueria-la-cabana-el-monte", city="El Monte", hero="left",
         address="3402 Cogswell Rd, Suite A, El Monte, CA 91732", phone="(626) 956-7122", rating="4.5", reviews=146,
         logo=dict(w=190), photo="tacos_tile", **WHITE, accent="#111111", on="#ffffff",
         fonts="family=Montserrat:wght@400;500;800", head="Montserrat, Arial, sans-serif", body="Montserrat, Arial, sans-serif", head_css="font-weight:800;",
         what="Taqueria in El Monte",
         about_h="Welcome", about=["We're at 3402 Cogswell Rd, Suite A. Try the torta de asada, it's our best seller.",
                                   "Call in your order for pickup."],
         items=[], call="Call", cta="big", rate="text", foot="plain"),
    dict(name="Los Chilitos Restaurant", short="Los Chilitos", slug="los-chilitos-restaurant-south-el-monte", city="South El Monte", hero="cover",
         address="1648 Tyler Ave, Unit E, South El Monte, CA 91733", phone="(626) 279-1561", rating="4.6", reviews=334,
         logo=dict(w=128, shape="soft"), photo="tacos_plate", bg="#fbf3e4", ink="#3a1c10", soft="#75574a", line="#e2d0b4", accent="#b3201a", on="#fff6e0",
         fonts="family=Bitter:wght@500;700&family=Open+Sans:wght@400;600", head="Bitter, Georgia, serif", body="'Open Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Mexican breakfast and lunch in South El Monte",
         about_h="About us", about=["We serve Mexican breakfast and lunch. Our chilaquiles are the most popular plate, and don't leave without trying the café de olla.",
                                    "Dine in, or order online for pickup."],
         list_h="Favorites", items=["Chilaquiles", "Café de olla"], lst="bullets", note="See the full menu on our online ordering page.",
         call="Call", cta="pair", rate="text", foot="solid", info=True,
         action=("Order online", "https://order.toasttab.com/online/los-chilitos-1648-tyler-avenue-e")),
    dict(name="Son Tacos", display="Son Tacos & Beer", slug="son-tacos-and-beer-montclair", city="Montclair", hero="center",
         address="9359 Central Ave, Suite A, Montclair, CA 91763", phone="(909) 447-0613", rating="4.8", reviews=90,
         logo=dict(w=200), photo="tacos_row", **WHITE, accent="#4d7a2a", on="#ffffff",
         fonts="family=Oswald:wght@500;600&family=Roboto:wght@400;500", head="Oswald, 'Arial Narrow', sans-serif", body="Roboto, Arial, sans-serif", head_css="font-weight:600; text-transform:uppercase;",
         what="Tacos and cold beer in Montclair",
         about_h="", about=["Birria tacos, ribeye tacos and cold beer. We're in Suite A at 9359 Central Ave.",
                            "Dine in or call for takeout."],
         items=[], call="Call", cta="pair", rate="stars", foot="solid", footbg="#111111", nav=True),
    dict(name="Los Portales Mexican Grill - Montclair", display="Los Portales Mexican Grill", short="Los Portales", slug="los-portales-mexican-grill-montclair",
         city="Montclair", hero="left",
         address="10244 Central Ave, Montclair, CA 91763", phone="(909) 621-2013", rating="4.4", reviews=875,
         logo=dict(w=180, shape="round"), photo="tacos_radish", bg="#fdf1cf", ink="#4a1712", soft="#7c5246", line="#e3cf9c", accent="#c0392b", on="#fff7e0",
         fonts="family=Lora:wght@500;700&family=Lato:wght@400;700", head="Lora, Georgia, serif", body="Lato, Arial, sans-serif", head_css="font-weight:700;",
         what="Mexican grill and seafood. Family restaurant.",
         about_h="Family Restaurant", about=["Mexican grill and seafood, with beer and wine. Our stuffed peppers and shredded beef tacos are customer favorites.",
                                             "Call for a table or to order to go. We also have a location in Chino."],
         items=[], call="Call us", cta="pair", rate="text", foot="plain", info=True, bar=True),
    dict(name="Chuy's Cocina", slug="chuys-cocina-montclair", city="Montclair", hero="center",
         address="10285 Central Ave, Montclair, CA 91763", phone="(909) 445-9111", rating="4.5", reviews=515,
         logo=dict(w=270), photo="tacos_jarrito", **WHITE, accent="#1a1a1a", on="#ffffff",
         fonts="family=Cormorant+Garamond:wght@500;600&family=Karla:wght@400;500", head="'Cormorant Garamond', Georgia, serif", body="Karla, Arial, sans-serif", head_css="font-weight:600;",
         h1_css="letter-spacing:.05em; text-transform:uppercase;",
         what="Mexican restaurant in Montclair",
         about_h="", about=["Pozole, al pastor and handmade tortillas. Come in and eat with us, or call to order ahead."],
         items=[], call="Call", cta="text", rate="text", foot="plain"),
    dict(name="Tepeque's Mexican Food Restaurant", short="Tepeque's", slug="tepeques-mexican-food-montclair", city="Montclair", hero="center",
         address="9863 Central Ave, Montclair, CA 91763", phone="(909) 445-0490", rating="4.4", reviews=288,
         logo=dict(w=280, shape="soft"), photo="tacos_basket", bg="#2f2f2f", ink="#f6efdc", soft="#c9c0aa", line="#4c4a45", accent="#e2b93b", on="#27220f",
         fonts="family=Merriweather:wght@700&family=Source+Sans+3:wght@400;600", head="Merriweather, Georgia, serif", body="'Source Sans 3', Arial, sans-serif", head_css="font-weight:700;",
         what="Comida casera estilo Michoacán",
         about_h="", about=["Home-style Mexican food, Michoacán style. Birria is our specialty and our tortillas are handmade.",
                            "Call ahead for pickup."],
         list_h="Specialties", items=["Birria", "Handmade tortillas"], lst="bullets", note="",
         call="Call to order", cta="big", rate="stars", foot="plain"),
    dict(name="TACOS LOS 3 POTRILLOS", display="Tacos Los 3 Potrillos", short="Los 3 Potrillos", slug="tacos-los-3-potrillos-south-el-monte", city="South El Monte", hero="center",
         address="1959 Durfee Ave, South El Monte, CA 91733", phone="(626) 489-8167", rating="4.3", reviews=219,
         logo=dict(w=220), photo="tacos_lime", bg="#ffb401", ink="#2a1602", soft="#5a3a06", line="#d99a07", accent="#b01e23", on="#ffffff",
         fonts="family=Rubik:wght@400;500;800", head="Rubik, Arial, sans-serif", body="Rubik, Arial, sans-serif", head_css="font-weight:800;",
         what="Birria and al pastor in South El Monte",
         about_h="", about=["Birria and tacos al pastor. Come by 1959 Durfee Ave or call in your order."],
         items=[], call="Call to order", cta="pair", rate="text", foot="solid"),
    dict(name="TAQUERIA ROSA & SUL", display="Taqueria Rosa & Sul", short="Rosa & Sul", slug="taqueria-rosa-and-sul-el-monte", city="El Monte", hero="cover",
         address="9853 Garvey Ave, El Monte, CA 91733", phone="(626) 534-9680", rating="4.7", reviews=120,
         logo=None, cover="cover.jpg", cover_alt="The front of Taqueria Rosa & Sul on Garvey Avenue",
         bg="#ffffff", ink="#17302d", soft="#526b67", line="#cfdcd9", accent="#c2185b", on="#ffffff",
         fonts="family=Poppins:wght@400;500;700", head="Poppins, Arial, sans-serif", body="Poppins, Arial, sans-serif", head_css="font-weight:700;",
         what="Taqueria on Garvey Ave in El Monte",
         about_h="", about=["Come see us on Garvey Ave. Our birria and carne asada are customer favorites. Call ahead for pickup."],
         list_h="Menu", items=["Tacos", "Tortas", "Burritos", "Flautas", "Sopes", "Huaraches", "Combos"], lst="cols", note="",
         call="Call to order", cta="pair", rate="stars", foot="solid", footbg="#17302d"),
    # --------------------------------------------------------------- barbers
    dict(name="Aves Barbershop", slug="aves-barbershop-upland", city="Upland", hero="center",
         address="560 N Mountain Ave, Suite A, Upland, CA 91786", phone="(909) 243-3981", rating="5.0", reviews=118,
         logo=dict(w=210, shape="round"), bg="#161616", ink="#f1ead8", soft="#b8b09c", line="#383838", accent="#d0a54c", on="#17140b",
         fonts="family=Libre+Baskerville:wght@700&family=Open+Sans:wght@400;600", head="'Libre Baskerville', Georgia, serif", body="'Open Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Barber shop in Upland",
         about_h="", about=["Haircuts, fades and beard trims. We're at 560 N Mountain Ave, Suite A.",
                            "Call the shop to get in."],
         items=[], call="Call", cta="big", rate="stars", foot="plain"),
    dict(name="5Rs barber and salon", display="5Rs Barber & Salon", slug="5rs-barber-and-salon-upland", city="Upland", hero="left",
         address="302 N Mountain Ave, Upland, CA 91786", phone="(909) 204-2671", rating="4.9", reviews=115,
         logo=dict(w=170), **WHITE, accent="#7a1f2b", on="#ffffff",
         fonts="family=EB+Garamond:wght@500;700&family=Mulish:wght@400;600", head="'EB Garamond', Georgia, serif", body="Mulish, Arial, sans-serif", head_css="font-weight:700;",
         what="Barber and salon in Upland",
         about_h="", about=["Barber and salon services on Mountain Ave. Call to book an appointment, or message us on Instagram @5rsbarber."],
         list_h="Services", items=["Haircuts", "Fades", "Beard trims", "Salon services"], lst="bullets", note="Call for prices.",
         call="Call to book", cta="pair", rate="text", foot="solid", info=True),
    dict(name="Proera Barbers", display="Pro Era Barbers", slug="pro-era-barbers-upland", city="Upland", hero="center",
         address="130 S Mountain Ave, Suite C, Upland, CA 91786", phone="(909) 981-1200", rating="4.8", reviews=54,
         logo=dict(w=190, shape="round"), bg="#17110c", ink="#f5ecdf", soft="#bcad9a", line="#3d3128", accent="#e8791c", on="#1a0f04",
         fonts="family=Bebas+Neue&family=Roboto:wght@400;500", head="'Bebas Neue', Impact, sans-serif", body="Roboto, Arial, sans-serif", head_css="font-weight:400; letter-spacing:.03em;",
         what="Barbershop in Upland, right off the 10",
         about_h="", about=["Haircuts for men and kids at 130 S Mountain Ave, Suite C. Book online or call the shop."],
         list_h="Services", items=["Haircuts", "Fades", "Beard trims", "Kids' cuts"], lst="bullets", note="Prices are on our booking page.",
         call="Call", cta="pair", rate="stars", foot="plain", bar=True,
         action=("Book online", "https://proerabarbers.booksy.com")),
    dict(name="Elite Barber", slug="elite-barber-upland", city="Upland", hero="center",
         address="1667 N Mountain Ave, Suite 122, Upland, CA 91784", phone="(909) 981-5225", rating="4.6", reviews=52,
         logo=dict(w=250), **WHITE, accent="#111111", on="#ffffff",
         fonts="family=Raleway:wght@300;400;600", head="Raleway, Arial, sans-serif", body="Raleway, Arial, sans-serif", head_css="font-weight:600;",
         h1_css="font-weight:300; letter-spacing:.2em; text-transform:uppercase;",
         what="Barber shop in the Northwest Center, Upland",
         about_h="", about=["Haircuts and beard trims in the Northwest Center on Mountain Ave. Call the shop for availability."],
         items=[], call="Call", cta="text", rate="text", foot="plain"),
    dict(name="Classic Barbers", slug="classic-barbers-upland", city="Upland", hero="left",
         address="80 E Foothill Blvd, Upland, CA 91786", phone="(909) 727-2355", rating="4.7", reviews=90,
         logo=dict(w=150, shape="round"), **BLACK, accent="#e9e4d8", on="#0c0c0c",
         fonts="family=Old+Standard+TT:wght@400;700&family=Work+Sans:wght@400;500", head="'Old Standard TT', Georgia, serif", body="'Work Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Traditional barber shop on Foothill Blvd",
         about_h="", about=["Haircuts, beard trims and hot towel shaves in Upland. Call for availability."],
         list_h="Services", items=["Haircuts", "Hot towel shaves", "Beard trims"], lst="rule", note="",
         call="Call", cta="big", rate="text", foot="plain",
         price="$350"),  # rebuild on their existing domain, as quoted in the email
    # ------------------------------------------------------------------ auto
    dict(name="Leyva auto repair", display="Leyva Auto Repair", slug="leyva-auto-repair-la-puente", city="La Puente", hero="center",
         address="", phone="(626) 672-5568", rating="5.0", reviews=37, mobile=True,
         logo=dict(w=230), bg="#1f1f21", ink="#efe9da", soft="#b6ae9b", line="#3e3e41", accent="#c9a44c", on="#17130a",
         fonts="family=Jost:wght@400;500;600", head="Jost, Arial, sans-serif", body="Jost, Arial, sans-serif", head_css="font-weight:600;",
         what="Auto repair in La Puente",
         about_h="", about=["Auto repair and maintenance in La Puente. Call or text Octavio with your year, make and model and what's going on with the car."],
         items=[], call="Call or text", cta="big", rate="stars", foot="plain"),
    dict(name="HMS Automotive", slug="hms-automotive-la-puente", city="La Puente", hero="left", two=True,
         address="161 4th Ave, La Puente, CA 91746", phone="(626) 333-0984", rating="4.8", reviews=43,
         logo=dict(w=200), photo="auto_engine", **WHITE, accent="#b8912f", on="#ffffff",
         fonts="family=Archivo:wght@400;500;700", head="Archivo, Arial, sans-serif", body="Archivo, Arial, sans-serif", head_css="font-weight:700;",
         what="Auto repair and transmission specialists",
         about_h="", about=["Full-service auto repair and transmission specialists at 161 4th Ave in La Puente. Give us a call and tell us what's going on with your car."],
         list_h="Services", items=["Transmissions", "Brakes", "Tune ups", "Timing belts", "Electrical", "Diagnostics", "Suspension", "Axles", "Clutches", "Radiators", "Engine overhaul"],
         lst="cols", note="", call="Call the shop", cta="pair", rate="text", foot="solid", footbg="#1a1a1a", info=True),
    dict(name="Fontana Tires Complete Auto & Collision Repair", display="Fontana Tires", slug="fontana-tires-fontana", city="Fontana", hero="cover",
         address="15614 Arrow Route, Fontana, CA 92335", phone="(909) 854-1300", rating="4.8", reviews=1134,
         logo=dict(w=128), photo="auto_tires", **BLACK, accent="#e02127", on="#ffffff",
         fonts="family=Saira+Condensed:wght@600;700&family=Saira:wght@400;500", head="'Saira Condensed', 'Arial Narrow', sans-serif", body="Saira, Arial, sans-serif", head_css="font-weight:700; text-transform:uppercase;",
         what="Complete auto and collision repair",
         about_h="", about=["Tires, wheel alignment, complete auto repair and collision repair, all at one shop on Arrow Route. Stop by or call for a quote."],
         list_h="Services", items=["Tires", "Alignment", "Brakes", "Auto repair", "Collision repair"], lst="bullets", note="",
         call="Call", cta="pair", rate="stars", foot="solid", footbg="#e02127", bar=True),
    dict(name="Best Tire Shop of Fontana", short="Best Tire Shop", slug="best-tire-shop-of-fontana", city="Fontana", hero="center",
         address="15750 Arrow Blvd, Unit X, Fontana, CA 92335", phone="(909) 637-6882", rating="4.4", reviews=125,
         logo=dict(w=240), **WHITE, accent="#d0202a", on="#ffffff",
         fonts="family=Barlow:wght@400;500;700", head="Barlow, Arial, sans-serif", body="Barlow, Arial, sans-serif", head_css="font-weight:700;",
         what="Tires and alignment in Fontana",
         about_h="", about=["New and used tires, alignment, balancing and flat repair. We're at 15750 Arrow Blvd, Unit X.",
                            "Call with your tire size and we'll give you a price."],
         items=[], call="Call", cta="big", rate="text", foot="solid", footbg="#111111"),
    dict(name="Sonora Tires Route 66 Inc", display="Sonora Tires Route 66", short="Sonora Tires", slug="sonora-tires-route-66-fontana", city="Fontana", hero="left",
         address="15979 Foothill Blvd, Fontana, CA 92335", phone="(909) 823-7878", rating="4.6", reviews=630,
         logo=dict(w=220), **WHITE, accent="#c8102e", on="#ffffff",
         fonts="family=Kanit:ital,wght@1,600&family=Kanit:wght@400;500", head="Kanit, Arial, sans-serif", body="Kanit, Arial, sans-serif", head_css="font-weight:600; font-style:italic;",
         what="Tire shop on Foothill Blvd (Route 66) in Fontana",
         about_h="", about=["Tires, alignments and installation. Call with your tire size for a quote.",
                            "We also have a shop in Bloomington."],
         list_h="Services", items=["New tires", "Used tires", "Alignment", "Installation and balancing"], lst="bullets", note="",
         call="Call", cta="pair", rate="stars", foot="solid", info=True),
    # ------------------------------------------ Facebook Messenger leads (11/11)
    dict(name="Taqueria Periban Inc.", display="Taqueria Periban", slug="taqueria-periban-south-el-monte", city="South El Monte", hero="center",
         address="2129 Chico Ave, South El Monte, CA 91733", phone="(626) 444-6923", rating="4.5", reviews=1008,
         logo=dict(w=210, shape="round"), photo="burrito", bg="#111111", ink="#f6f1e7", soft="#b9b2a4", line="#333333", accent="#e4572e", on="#ffffff",
         fonts="family=Roboto+Slab:wght@700&family=Roboto:wght@400;500", head="'Roboto Slab', Georgia, serif", body="Roboto, Arial, sans-serif", head_css="font-weight:700;",
         what="Donde se hacen las mejores carnitas",
         about_h="", about=["Carnitas are what we're known for. We also do taquizas for parties and events, so call us for your next one."],
         list_h="Menu", items=["Carnitas", "Tacos", "Burritos", "Tortas", "Asada", "Al pastor", "Pollo", "Platillos", "Taquizas"], lst="cols", note="",
         call="Call to order", cta="pair", rate="stars", foot="solid", bar=True),
    dict(name="Upland Barber Shop", slug="upland-barber-shop-upland", city="Upland", hero="cover",
         address="260 N 2nd Ave, Suite B, Upland, CA 91786", phone="(909) 981-5501", rating="4.7", reviews=236,
         logo=None, cover="cover.jpg", cover_alt="Old barber tools from the Upland Barber Shop Facebook page",
         bg="#f6f1e6", ink="#1d2a44", soft="#5b6477", line="#d8d0bf", accent="#1d2a44", on="#ffffff",
         fonts="family=Arvo:wght@700&family=Lato:wght@400;700", head="Arvo, Georgia, serif", body="Lato, Arial, sans-serif", head_css="font-weight:700;",
         what="Good ol' fashioned barber shop in downtown Upland",
         about_h="", about=["Haircuts, fades and a friendly shop on 2nd Ave. Call ahead to check the wait."],
         items=[], call="Call", cta="big", rate="text", foot="solid"),
    dict(name="David's Auto Tech", slug="davids-auto-tech-la-puente", city="La Puente", hero="cover",
         address="121 Turnbull Canyon Rd, La Puente, CA 91745", phone="(626) 330-2536", rating="4.9", reviews=145,
         logo=None, cover="cover.jpg", cover_alt="A truck in the shop at David's Auto Tech",
         **WHITE, accent="#1c4e9c", on="#ffffff",
         fonts="family=Roboto+Condensed:wght@700&family=Roboto:wght@400;500", head="'Roboto Condensed', Arial, sans-serif", body="Roboto, Arial, sans-serif", head_css="font-weight:700;",
         what="Auto repair in La Puente, foreign and domestic",
         about_h="", about=["Maintenance and repair on all vehicles, foreign or domestic. Call the shop and tell us what's going on with your car."],
         items=[], call="Call the shop", cta="pair", rate="stars", foot="solid", footbg="#1a1a1a"),
    dict(name="Vicente's Barber Shop", short="Vicente's", slug="vicentes-barber-shop-rosemead", city="Rosemead", hero="center",
         address="3044 San Gabriel Blvd, Rosemead, CA 91770", phone="(626) 573-9644", rating="4.5", reviews=95,
         logo=None, nologo=True, bg="#0d0d0d", ink="#f3e7c9", soft="#b9ad8e", line="#333026", accent="#b8232c", on="#ffffff",
         fonts="family=Rye&family=Roboto:wght@400;500", head="Rye, Georgia, serif", body="Roboto, Arial, sans-serif", head_css="font-weight:400;",
         what="Barber shop on San Gabriel Blvd. Est. 1998.",
         about_h="", about=["Haircuts in Rosemead since 1998. Call the shop for availability."],
         items=[], call="Call", cta="big", rate="text", foot="plain"),
    dict(name="Big Mike's Barber Shop", slug="big-mikes-barber-shop-rosemead", city="Rosemead", hero="left",
         address="7849 Garvey Ave, Rosemead, CA 91770", phone="(626) 573-0486", rating="4.4", reviews=75,
         logo=dict(w=180, shape="soft"), **WHITE, accent="#1f3f7a", on="#ffffff",
         fonts="family=Oswald:wght@500;600&family=Open+Sans:wght@400;600", head="Oswald, 'Arial Narrow', sans-serif", body="'Open Sans', Arial, sans-serif", head_css="font-weight:600;",
         what="Barbershop on Garvey Ave in Rosemead",
         about_h="", about=["Haircuts for men and kids. Closed on Sundays. Call the shop for availability."],
         items=[], call="Call", cta="pair", rate="text", foot="solid", info=True),
    dict(name="Carlo Barber Shop", slug="carlo-barber-shop-upland", city="Upland", hero="left",
         address="250 N 2nd Ave, Suite B, Upland, CA 91786", phone="(909) 920-5352", rating="4.7", reviews=64,
         logo=None, nologo=True, **WHITE, accent="#1565c0", on="#ffffff",
         fonts="family=Merriweather+Sans:wght@400;700", head="'Merriweather Sans', Arial, sans-serif", body="'Merriweather Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Barber shop in downtown Upland",
         about_h="", about=["We make you feel at home, always. Haircuts on 2nd Ave in downtown Upland. Call the shop for availability."],
         items=[], call="Call", cta="pair", rate="stars", foot="solid", info=True),
    # ------------------------------------------ mobile detailers to text (11/11)
    dict(name="MD DETAILING Professional mobile detail", display="MD Detailing", slug="md-detailing-rancho-cucamonga", city="Rancho Cucamonga",
         hero="center", phone="(909) 346-8041", rating="4.7", reviews=33, **DET, photo="detail_buckets", photo2="detail_headlight",
         bg="#0f1720", ink="#eef3f7", soft="#9db0c0", line="#243241", accent="#3aa0ff", on="#04121f",
         fonts="family=Sora:wght@400;600;800", head="Sora, Arial, sans-serif", body="Sora, Arial, sans-serif", head_css="font-weight:800;",
         what="Professional mobile detailing in Rancho Cucamonga",
         about=["We come to your home or work in Rancho Cucamonga and the cities around it.", "Call or text Leonardo or Carolina with what you drive and we'll get you a price and a time."],
         rate="stars", foot="solid", footbg="#0a1017", bar=True),
    dict(name="Convenient Mobile Detail LLC", display="Convenient Mobile Detail", slug="convenient-mobile-detail-fontana", city="Fontana",
         hero="left", phone="(909) 441-6963", rating="5.0", reviews=36, **DET, photo="detail_polish", photo2="detail_rinse",
         **WHITE, accent="#0f766e", on="#ffffff",
         fonts="family=Manrope:wght@400;600;800", head="Manrope, Arial, sans-serif", body="Manrope, Arial, sans-serif", head_css="font-weight:800;",
         what="Mobile detailing in Fontana. We come to you.",
         about=["We bring the detail to your home or work in Fontana and nearby, so you don't have to go anywhere.", "Call or text with what you drive and we'll send you a price."],
         rate="stars", foot="solid", bar=True),
    dict(name="Ayman mobile detailing", display="Ayman Mobile Detailing", slug="ayman-mobile-detailing-rancho-cucamonga", city="Rancho Cucamonga",
         hero="center", phone="(909) 232-9675", rating="5.0", reviews=7, **DET, photo="detail_foam", photo2="detail_headlight",
         bg="#101010", ink="#f4f4f1", soft="#aaa9a3", line="#2c2c2a", accent="#f2c230", on="#1a1400",
         fonts="family=Outfit:wght@400;600;800", head="Outfit, Arial, sans-serif", body="Outfit, Arial, sans-serif", head_css="font-weight:800;",
         what="Mobile detailing in Rancho Cucamonga",
         about=["Fast, clean work at your home or your job. Call or text Ayman with what you drive for a price."],
         rate="text", foot="plain"),
    dict(name="Ontario Mobile Detail", slug="ontario-mobile-detail-ontario", city="Ontario",
         hero="left", phone="(909) 488-3690", rating="5.0", reviews=22, **DET, photo="detail_foam", photo2="detail_sponge",
         **WHITE, accent="#c2410c", on="#ffffff",
         fonts="family=Rubik:wght@400;500;700", head="Rubik, Arial, sans-serif", body="Rubik, Arial, sans-serif", head_css="font-weight:700;",
         what="Mobile detailing in Ontario",
         about=["We detail cars at your home or work in Ontario and the cities around it.", "Call or text with what you drive and where it's parked."],
         rate="stars", foot="solid", footbg="#1a1a1a"),
    dict(name="Dirty & Clean Mobile Detailing", slug="dirty-and-clean-mobile-detailing-montclair", city="Montclair",
         hero="center", phone="(909) 260-5283", rating="5.0", reviews=33, **DET, photo="detail_rinse", photo2="detail_buckets",
         bg="#f4f7fb", ink="#10233b", soft="#566b84", line="#d3dde9", accent="#1d4ed8", on="#ffffff",
         fonts="family=Lexend:wght@400;600;800", head="Lexend, Arial, sans-serif", body="Lexend, Arial, sans-serif", head_css="font-weight:800;",
         what="Mobile detailing in Montclair. Dirty to clean.",
         about=["It shows up dirty and leaves clean. We come to you in Montclair and nearby.", "Call or text with what you drive for a price."],
         rate="stars", foot="solid", bar=True),
    dict(name="Johnny's Mobile Auto Wash and Detail", short="Johnny's Mobile Detail", slug="johnnys-mobile-auto-wash-and-detail-el-monte", city="El Monte",
         hero="left", phone="(626) 561-8532", rating="4.9", reviews=34, **DET, photo="detail_sponge", photo2="detail_polish",
         bg="#fffaf0", ink="#2b1d0e", soft="#7a6650", line="#e8dcc6", accent="#b91c1c", on="#ffffff",
         fonts="family=Fredoka:wght@500;700&family=Nunito+Sans:wght@400;600", head="Fredoka, Arial, sans-serif", body="'Nunito Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Mobile car wash and detailing in El Monte",
         about=["Johnny comes to you in El Monte and nearby for a wash or a full detail.", "Call or text with what you drive and we'll set a time."],
         rate="text", foot="solid", bar=True),
    dict(name="El Monte Auto Car Detail Wash", slug="el-monte-auto-car-detail-wash-el-monte", city="El Monte",
         hero="center", phone="(626) 483-0423", rating="4.9", reviews=19, **{**DET, "items": ["Hand wash", "Interior detail", "Full detail"]}, photo="detail_headlight", photo2="detail_foam",
         bg="#0b1b2b", ink="#eef4fa", soft="#9fb3c7", line="#22384d", accent="#38bdf8", on="#04121c",
         fonts="family=Kanit:wght@400;500;700", head="Kanit, Arial, sans-serif", body="Kanit, Arial, sans-serif", head_css="font-weight:700;",
         what="Car wash and detailing in El Monte",
         about=["Hand washes and details in El Monte. Call or text with what you drive for a price."],
         rate="stars", foot="plain"),
]

CSS = """
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.6 var(--body)}
img{max-width:100%;display:block}a{color:inherit}
h1,h2{font-family:var(--head);HEADCSS;line-height:1.2;margin:0}
h1{font-size:clamp(1.6rem,6.4vw,2.4rem);H1CSS}h2{font-size:1.35rem;margin-bottom:10px}
p{margin:0 0 12px}.soft{color:var(--soft)}
.wrap{max-width:760px;margin:0 auto;padding:0 18px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 18px;border-bottom:1px solid var(--line);font-size:15px}
.top b{font-family:var(--head);HEADCSS;font-size:16px}
.top a{white-space:nowrap;font-weight:600;text-decoration:none;padding:8px 0}
.top nav{display:none}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 22px;border:2px solid var(--accent);border-radius:5px;text-decoration:none;font-weight:600;font-size:16px}
.btn.p{background:var(--accent);color:var(--on)}.btn.big{width:100%;min-height:56px;font-size:18px}
.bigtel{display:inline-block;font-family:var(--head);font-size:1.7rem;font-weight:600;text-decoration:none;margin-top:14px;padding:6px 0}
.logo.round{border-radius:50%}.logo.soft{border-radius:8px}
.what{font-size:18px;margin:8px 0 0}.rate{font-size:15px;margin:14px 0 0}.rate .st{color:#e7a80c;letter-spacing:1px}
.info{margin:18px 0 0;font-size:16px}.info p{margin:0 0 4px}
.photo{width:100%;height:210px;object-fit:cover}
.sec{padding:28px 0}
ul.bul{margin:0 0 10px;padding-left:22px}ul.bul li{padding:2px 0}
ul.rule{list-style:none;margin:0 0 10px;padding:0}ul.rule li{padding:9px 0;border-bottom:1px solid var(--line)}
ul.cols{list-style:none;margin:0 0 10px;padding:0;columns:2;column-gap:24px}ul.cols li{padding:4px 0;break-inside:avoid}
.map{width:100%;height:300px;border:0;margin-top:10px}
.foot{padding:22px 0 30px;font-size:13px;color:var(--soft);border-top:1px solid var(--line)}
.foot.solid{background:var(--footbg);color:#fff;border:0}.foot.solid .name{font-family:var(--head);font-size:18px;font-weight:700;margin-bottom:4px}
.foot p{margin:0 0 6px}.foot .pv{opacity:.8}
.hero{padding:30px 0 26px}.hero.center{text-align:center}.hero.center .logo{margin:0 auto 16px}.hero.center .btns{justify-content:center}
.hero.left .logo{margin-bottom:14px}
.cimg{width:100%;height:190px;object-fit:cover}
.hero.cover{padding-top:0}.hero.cover .logo{margin:-44px 0 12px;border:4px solid var(--bg);background:var(--bg)}.hero.cover.nologo{padding-top:20px}
.bar{display:none}
@media(max-width:699px){.hasbar{padding-bottom:64px}.bar{display:flex;position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--accent);color:var(--on);height:56px;align-items:center;justify-content:center;font-weight:700;font-size:17px;text-decoration:none}}
@media(min-width:700px){
 .photo{height:360px}.cimg{height:320px}.map{height:380px}
 .top{padding:14px 28px}.top nav{display:flex;gap:22px}.top nav a{font-weight:500}
 .btn.big{width:auto;min-width:300px}
 .two{display:grid;grid-template-columns:1fr 1fr;gap:44px}
 ul.cols{columns:3}
}
"""


def render(s):
    display = s.get("display", s["name"])
    short = s.get("short", display)
    city, phone = s["city"], s["phone"]
    t = tel(phone)
    mobile = s.get("mobile", False)
    q = quote_plus(f"{city} CA" if mobile else f"{display} {s['address']}")
    maps_link = f"https://www.google.com/maps/search/?api=1&query={q}"
    maps_embed = f"https://www.google.com/maps?q={q}&output=embed"
    url = f"{PAGES_BASE}/sites/{s['slug']}/"
    lg = s.get("logo")
    hero = s["hero"]

    logo = ""
    if lg:
        w = lg["w"]
        logo = (f'<img class="logo {lg.get("shape", "")}" src="logo.jpg" alt="{e(display)} logo" width="{w}" '
                f'style="width:{w}px;max-width:78%;height:auto" />')

    if s["rate"] == "stars":
        rate = (f'<p class="rate"><span class="st">★★★★★</span> <a href="{maps_link}" target="_blank" rel="noopener">'
                f'{e(s["rating"])} on Google</a> <span class="soft">({s["reviews"]:,} reviews)</span></p>')
    else:
        rate = (f'<p class="rate soft"><a href="{maps_link}" target="_blank" rel="noopener">Rated {e(s["rating"])} on Google</a>, '
                f'{s["reviews"]:,} reviews</p>')

    act = s.get("action")
    directions = "" if mobile else f'<a class="btn" href="{maps_link}" target="_blank" rel="noopener">Directions</a>'
    if s["cta"] == "big":
        btns = f'<div class="btns"><a class="btn p big" href="tel:{t}">{e(s["call"])} {e(phone)}</a></div>'
    elif s["cta"] == "text":
        dl = "" if mobile else f' <p style="margin:2px 0 0"><a href="{maps_link}" target="_blank" rel="noopener">Get directions</a></p>'
        btns = f'<a class="bigtel" href="tel:{t}">{e(phone)}</a>{dl}'
    elif act:
        btns = (f'<div class="btns"><a class="btn p" href="{e(act[1])}" target="_blank" rel="noopener">{e(act[0])}</a>'
                f'<a class="btn" href="tel:{t}">{e(s["call"])}</a>{directions}</div>')
    else:
        btns = f'<div class="btns"><a class="btn p" href="tel:{t}">{e(s["call"])}</a>{directions}</div>'

    if s.get("info"):
        where = f'<div class="info"><p>{e(s["address"])}</p><p><a href="tel:{t}">{e(phone)}</a></p></div>'
    elif s["address"]:
        where = f'<p class="soft" style="margin:6px 0 0">{e(s["address"])}</p>'
    else:
        where = ""

    cover = ""
    if hero == "cover":
        if s.get("cover"):
            cover = f'<img class="cimg" src="{e(s["cover"])}" alt="{e(s["cover_alt"])}" style="height:auto;max-height:440px;object-position:center 22%" />'
        else:
            pid, alt = IMG[s["photo"]]
            cover = f'<img class="cimg" src="{unsplash(pid, 1600)}" alt="{e(alt)}" />'
    photo = ""
    if s.get("photo") and hero != "cover":
        pid, alt = IMG[s["photo"]]
        photo = f'<img class="photo" src="{unsplash(pid, 1400)}" alt="{e(alt)}" />'

    head = (f'<section class="hero {hero}{"" if lg else " nologo"}">{logo}<h1>{e(display)}</h1>'
            f'<p class="what">{e(s["what"])}</p>{where}{btns}{rate}</section>')

    about = (f'<h2>{e(s["about_h"])}</h2>' if s["about_h"] else "") + "".join(f"<p>{e(p)}</p>" for p in s["about"])
    items = ""
    if s["items"]:
        cls = {"bullets": "bul", "rule": "rule", "cols": "cols"}[s["lst"]]
        note = f'<p class="soft" style="font-size:15px">{e(s["note"])}</p>' if s.get("note") else ""
        items = f'<h2>{e(s["list_h"])}</h2><ul class="{cls}">' + "".join(f"<li>{e(i)}</li>" for i in s["items"]) + f"</ul>{note}"
    if items and s.get("two"):
        middle = f'<section class="sec two" id="about"><div>{about}</div><div id="menu">{items}</div></section>'
    else:
        middle = f'<section class="sec" id="about" style="padding-bottom:{"8px" if items else "28px"}">{about}</section>'
        if items:
            middle += f'<section class="sec" id="menu">{items}</section>'

    photo2 = ""
    if s.get("photo2"):
        pid2, alt2 = IMG[s["photo2"]]
        photo2 = f'<img class="photo" src="{unsplash(pid2, 1200)}" alt="{e(alt2)}" style="border-radius:6px" loading="lazy" />\n'
    find_h = f"Serving {city} and nearby" if mobile else "Location"
    addr = f'{e(s["address"])}<br />' if s["address"] else ""
    visit = photo2 + (f'<section class="sec" id="location"><h2>{e(find_h)}</h2><p>{addr}<a href="tel:{t}">{e(phone)}</a></p>'
             f'<iframe class="map" title="Map" src="{maps_embed}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></section>')

    nav = ""
    if s.get("nav"):
        nav = '<nav><a href="#about">About</a><a href="#location">Location</a></nav>'
    standin = (" Photos are stand-ins until the owner sends their own." if s.get("photo2")
               else " Photo is a stand-in until the owner sends their own." if s.get("photo") else "")
    pv = (f'<p class="pv">Website preview · not the official site. Built by WestCo App Studio, '
          f'<a href="tel:{WESTCO_TEL}">{WESTCO_PHONE}</a>.{standin}</p>')
    if s["foot"] == "solid":
        fa = f"<p>{e(s['address'])}</p>" if s["address"] else ""
        foot = (f'<footer class="foot solid"><div class="wrap"><p class="name">{e(display)}</p>{fa}'
                f'<p><a href="tel:{t}">{e(phone)}</a></p><p style="margin-top:14px">© {YEAR} {e(display)}</p>{pv}</div></footer>')
    else:
        foot = (f'<footer class="foot"><div class="wrap"><p>© {YEAR} {e(display)} · {e(city)}, CA · '
                f'<a href="tel:{t}">{e(phone)}</a></p>{pv}</div></footer>')
    bar = f'<a class="bar" href="tel:{t}">Call {e(phone)}</a>' if s.get("bar") else ""

    css = CSS.replace("HEADCSS;", s["head_css"]).replace("H1CSS", s.get("h1_css", ""))
    desc = f'{display} in {city}, CA. {s["what"]}.'
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>{e(display)} | {e(city)}, CA</title>
<meta name="description" content="{e(desc)}" />
<meta name="robots" content="noindex,nofollow" />
<link rel="canonical" href="{url}" />
<meta property="og:title" content="{e(display)}" />
<meta property="og:description" content="{e(s["what"])}" />
<meta property="og:type" content="website" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{url}{'logo.jpg' if lg else s.get('cover', '')}" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?{s["fonts"]}&display=swap" rel="stylesheet" />
<style>
:root{{--bg:{s["bg"]};--ink:{s["ink"]};--soft:{s["soft"]};--line:{s["line"]};--accent:{s["accent"]};--on:{s["on"]};--footbg:{s.get("footbg", s["accent"])};--head:{s["head"]};--body:{s["body"]}}}
{css}</style>
</head>
<body{' class="hasbar"' if bar else ''}>
{preview_banner(display, s.get("price", ""))}
<header class="top"><b>{e(short)}</b>{nav}<a href="tel:{t}">{e(phone)}</a></header>
{cover}
<div class="wrap">{head}</div>
{photo}
<div class="wrap">{middle}
{visit}</div>
{foot}
{bar}
</body>
</html>
"""
    assert "—" not in page and "–" not in page, f"dash crept into {s['slug']}"
    return page


def main():
    want = set(sys.argv[1:])
    for s in SHOPS:
        if want and s["slug"] not in want:
            continue
        out = SITES / s["slug"]
        out.mkdir(parents=True, exist_ok=True)
        need = s["cover"] if s.get("cover") else "logo.jpg"
        if not s.get("nologo") and not (out / need).exists():
            sys.exit(f"missing {need} for {s['slug']}")
        (out / "index.html").write_text(render(s), encoding="utf-8", newline="\n")
        print(f"BUILT\t{s['name']}\t{PAGES_BASE}/sites/{s['slug']}/")


if __name__ == "__main__":
    main()
