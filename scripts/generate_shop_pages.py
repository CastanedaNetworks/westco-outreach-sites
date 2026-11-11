"""Plain local-business previews for the Outreach Nov 12 sheet.

    python -I -X utf8 scripts/generate_shop_pages.py            # build all
    python -I -X utf8 scripts/generate_shop_pages.py slug-a slug-b

These pages are built to read like a shop's own site: the business name is the
headline, the logo is theirs, and the address and phone sit at the top. Three
layouts ("center", "cover", "side") so a batch does not share one skeleton.
Each page expects sites/<slug>/logo.jpg (their own profile picture or logo).
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


WHITE = dict(bg="#ffffff", ink="#1a1a1a", soft="#5c5c5c", line="#dddddd")
BLACK = dict(bg="#000000", ink="#f3f1ec", soft="#b3aea4", line="#2e2e2e")

# name: exact Business Name in the sheet. items: str or (name, note).
SHOPS = [
    # ------------------------------------------------------------- taquerias
    dict(name="Tacos Los Mismos", slug="tacos-los-mismos-el-monte", city="El Monte", layout="center",
         address="3057 Tyler Ave, El Monte, CA 91731", phone="(626) 542-3257", rating="4.6", reviews=466,
         logo=dict(w=230, shape="none"), photo="tacos_paper", **WHITE, accent="#1f55b5", on="#ffffff",
         fonts="family=Nunito:wght@400;600;800", head="Nunito, Arial, sans-serif", body="Nunito, Arial, sans-serif", head_css="font-weight:800;",
         what="Tacos and burritos on Tyler Avenue in El Monte.",
         about_h="About us",
         about=["We are a taqueria on Tyler Avenue. Most people who come in order the carne asada, and a lot of them come back for the chicharron.",
                "Call your order in and it will be ready when you get here."],
         list_h="What people order", items=["Carne asada", "Chicharron", "Chile verde burrito", "Tacos", "Burritos"],
         note="Ask at the counter for the full menu and today's prices.", call="Call to order"),
    dict(name="Taqueria La Cabaña E&E", slug="taqueria-la-cabana-el-monte", city="El Monte", layout="side",
         address="3402 Cogswell Rd, Suite A, El Monte, CA 91732", phone="(626) 956-7122", rating="4.5", reviews=146,
         logo=dict(w=200, shape="none"), photo="tacos_tile", **WHITE, accent="#111111", on="#ffffff",
         fonts="family=Montserrat:wght@400;500;800", head="Montserrat, Arial, sans-serif", body="Montserrat, Arial, sans-serif", head_css="font-weight:800;",
         what="Taqueria on Cogswell Road in El Monte.",
         about_h="Come by",
         about=["Taqueria La Cabaña E&E is in Suite A at 3402 Cogswell Road. The torta de asada is the one people talk about, and so are the tortillas.",
                "Call ahead if you are picking up for the family."],
         list_h="From the kitchen", items=[("Torta de asada", "the favorite"), "Tacos", "Burritos", "Quesadillas"],
         note="Call for the full menu.", call="Call to order"),
    dict(name="Los Chilitos Restaurant", slug="los-chilitos-restaurant-south-el-monte", city="South El Monte", layout="cover",
         address="1648 Tyler Ave, Unit E, South El Monte, CA 91733", phone="(626) 279-1561", rating="4.6", reviews=334,
         logo=dict(w=132, shape="soft"), photo="tacos_plate", bg="#fbf3e4", ink="#3a1c10", soft="#7a5a48", line="#e6d6bc", accent="#b3201a", on="#fff6e0",
         fonts="family=Bitter:wght@500;700&family=Open+Sans:wght@400;600", head="Bitter, Georgia, serif", body="'Open Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Mexican breakfast and lunch on Tyler Avenue in South El Monte.",
         about_h="Breakfast is what we are known for",
         about=["Chilaquiles are the plate people order most here, and the café de olla goes with them. Come in and sit down, or order ahead online and pick it up."],
         list_h="Favorites", items=[("Chilaquiles", "the most ordered plate"), ("Café de olla", "made in the pot, the traditional way"), "Breakfast plates", "Tacos and burritos"],
         note="The full menu is on our online ordering page.", call="Call us",
         action=("Order online", "https://order.toasttab.com/online/los-chilitos-1648-tyler-avenue-e")),
    dict(name="Son Tacos", display="Son Tacos & Beer", slug="son-tacos-and-beer-montclair", city="Montclair", layout="center",
         address="9359 Central Ave, Suite A, Montclair, CA 91763", phone="(909) 447-0613", rating="4.8", reviews=90,
         logo=dict(w=210, shape="none"), photo="tacos_row", **WHITE, accent="#4d7a2a", on="#ffffff",
         fonts="family=Oswald:wght@500;600&family=Roboto:wght@400;500", head="Oswald, 'Arial Narrow', sans-serif", body="Roboto, Arial, sans-serif", head_css="font-weight:600; text-transform:uppercase; letter-spacing:.02em;",
         what="Tacos and cold beer on Central Avenue in Montclair.",
         about_h="Tacos first, then a beer",
         about=["The birria tacos and the ribeye taco are the two our customers bring up the most. We are in Suite A at 9359 Central Avenue.",
                "Come in, or call ahead and take it to go."],
         list_h="Try these", items=["Birria tacos", "Ribeye taco", "Beer"],
         note="See the full menu when you come in.", call="Call to order"),
    dict(name="Los Portales Mexican Grill - Montclair", display="Los Portales Mexican Grill", short="Los Portales", slug="los-portales-mexican-grill-montclair",
         city="Montclair", layout="side",
         address="10244 Central Ave, Montclair, CA 91763", phone="(909) 621-2013", rating="4.4", reviews=875,
         logo=dict(w=190, shape="round"), photo="tacos_radish", bg="#fdf1cf", ink="#4a1712", soft="#80564a", line="#e8d6a6", accent="#c0392b", on="#fff7e0",
         fonts="family=Lora:wght@500;700&family=Lato:wght@400;700", head="Lora, Georgia, serif", body="Lato, Arial, sans-serif", head_css="font-weight:700;",
         what="Mexican grill and seafood. Family restaurant on Central Avenue in Montclair.",
         about_h="A family restaurant",
         about=["Los Portales is a sit-down Mexican grill and seafood restaurant. The stuffed peppers and the shredded beef tacos are what our regulars order.",
                "Call for a table or to place an order to go. We also have a restaurant in Chino."],
         list_h="What our regulars order", items=["Stuffed peppers", "Shredded beef tacos", "Seafood", "Beer and wine"],
         note="Ask your server for the full menu.", call="Call the restaurant"),
    dict(name="Chuy's Cocina", slug="chuys-cocina-montclair", city="Montclair", layout="center",
         address="10285 Central Ave, Montclair, CA 91763", phone="(909) 445-9111", rating="4.5", reviews=515,
         logo=dict(w=270, shape="none"), photo="tacos_jarrito", **WHITE, accent="#1a1a1a", on="#ffffff",
         fonts="family=Cormorant+Garamond:wght@500;600&family=Karla:wght@400;500", head="'Cormorant Garamond', Georgia, serif", body="Karla, Arial, sans-serif", head_css="font-weight:600; letter-spacing:.04em; text-transform:uppercase;",
         what="Restaurante on Central Avenue in Montclair.",
         about_h="Made by hand",
         about=["Our tortillas are made by hand, and people notice. The pozole and the al pastor are the other two things our customers keep coming back for.",
                "Call ahead to order, or come in and eat with us."],
         list_h="From our kitchen", items=["Pozole", "Al pastor", "Handmade tortillas"],
         note="Call or come in for the full menu.", call="Call to order"),
    dict(name="Tepeque's Mexican Food Restaurant", short="Tepeque's", slug="tepeques-mexican-food-montclair", city="Montclair", layout="cover",
         address="9863 Central Ave, Montclair, CA 91763", phone="(909) 445-0490", rating="4.4", reviews=288,
         logo=dict(w=250, shape="soft", wide=True), photo="tacos_basket", bg="#2b2a28", ink="#f6efdc", soft="#c5bba3", line="#47443f", accent="#e2b93b", on="#27220f",
         fonts="family=Merriweather:wght@700&family=Source+Sans+3:wght@400;600", head="Merriweather, Georgia, serif", body="'Source Sans 3', Arial, sans-serif", head_css="font-weight:700;",
         what="Comida casera estilo Michoacán, on Central Avenue in Montclair.",
         about_h="Comida casera",
         about=["We cook home-style food the way it is made in Michoacán. The birria is what people order most, and the tortillas are made by hand.",
                "Call ahead and your order will be ready when you get here."],
         list_h="What people order", items=["Birria", "Handmade tortillas", "Tacos", "Burritos"],
         note="Call for the full menu.", call="Call to order"),
    dict(name="TACOS LOS 3 POTRILLOS", display="Tacos Los 3 Potrillos", slug="tacos-los-3-potrillos-south-el-monte", city="South El Monte", layout="center",
         address="1959 Durfee Ave, South El Monte, CA 91733", phone="(626) 489-8167", rating="4.3", reviews=219,
         logo=dict(w=220, shape="none"), photo="tacos_lime", bg="#ffb401", ink="#2a1602", soft="#5e3d08", line="#d99a07", accent="#b01e23", on="#ffffff",
         fonts="family=Rubik:wght@400;500;800", head="Rubik, Arial, sans-serif", body="Rubik, Arial, sans-serif", head_css="font-weight:800; text-transform:uppercase;",
         what="Birria and al pastor on Durfee Avenue in South El Monte.",
         about_h="Birria y al pastor",
         about=["Birria is the first thing people ask us for. The al pastor tacos are the second. We are at 1959 Durfee Avenue.",
                "Call your order in and we will have it ready."],
         list_h="On the menu", items=["Birria", "Tacos al pastor", "Tacos", "Burritos"],
         note="Ask for the full menu when you call.", call="Call to order"),
    dict(name="TAQUERIA ROSA & SUL", display="Taqueria Rosa & Sul", slug="taqueria-rosa-and-sul-el-monte", city="El Monte", layout="cover",
         address="9853 Garvey Ave, El Monte, CA 91733", phone="(626) 534-9680", rating="4.7", reviews=120,
         logo=None, cover="cover.jpg", cover_alt="The front of Taqueria Rosa & Sul on Garvey Avenue",
         bg="#f7f9f7", ink="#17302d", soft="#55706c", line="#cfdcd9", accent="#c2185b", on="#ffffff",
         fonts="family=Poppins:wght@400;500;700", head="Poppins, Arial, sans-serif", body="Poppins, Arial, sans-serif", head_css="font-weight:700;",
         what="Tacos, tortas, burritos, flautas, sopes and huaraches on Garvey Avenue in El Monte.",
         about_h="Look for the flowers out front",
         about=["We are the taqueria at 9853 Garvey Avenue with the table by the door. Birria and carne asada are what people order most.",
                "Call ahead and we will have it ready for you."],
         list_h="On our sign", items=["Tacos", "Tortas", "Burritos", "Flautas", "Sopes", "Huaraches", "Combos"],
         note="Birria and carne asada are the favorites.", call="Call to order"),
    # --------------------------------------------------------------- barbers
    dict(name="Aves Barbershop", slug="aves-barbershop-upland", city="Upland", layout="center",
         address="560 N Mountain Ave, Suite A, Upland, CA 91786", phone="(909) 243-3981", rating="5.0", reviews=118,
         logo=dict(w=200, shape="round"), photo="barber_fade", bg="#151614", ink="#f1ead8", soft="#b5ad98", line="#34352f", accent="#d0a54c", on="#17140b",
         fonts="family=Playfair+Display:wght@600;700&family=Inter:wght@400;500", head="'Playfair Display', Georgia, serif", body="Inter, Arial, sans-serif", head_css="font-weight:700;",
         what="Barber shop on Mountain Avenue in Upland.",
         about_h="Come in and get comfortable",
         about=["People tell us the shop feels welcoming the minute they walk in. That matters to us as much as the haircut does.",
                "We take our time on the details. Call the shop and we will get you a chair."],
         list_h="Services", items=["Haircuts", "Fades", "Beard trims", "Kids' cuts"],
         note="Call for prices and open times.", call="Call the shop"),
    dict(name="5Rs barber and salon", display="5Rs Barber & Salon", slug="5rs-barber-and-salon-upland", city="Upland", layout="side",
         address="302 N Mountain Ave, Upland, CA 91786", phone="(909) 204-2671", rating="4.9", reviews=115,
         logo=dict(w=180, shape="none"), photo="barber_cut", **WHITE, accent="#7a1f2b", on="#ffffff",
         fonts="family=EB+Garamond:wght@500;700&family=Mulish:wght@400;600", head="'EB Garamond', Georgia, serif", body="Mulish, Arial, sans-serif", head_css="font-weight:700;",
         what="Barber and salon on Mountain Avenue in Upland.",
         about_h="Barber and salon in one shop",
         about=["Our customers say two things about us more than anything else: the work is professional, and nothing gets rushed.",
                "Call to book, or send us a message on Instagram."],
         list_h="Services", items=["Men's haircuts", "Fades and tapers", "Beard trims", "Salon services"],
         note="Call for prices.", call="Call to book"),
    dict(name="Proera Barbers", display="Pro Era Barbers", slug="pro-era-barbers-upland", city="Upland", layout="cover",
         address="130 S Mountain Ave, Suite C, Upland, CA 91786", phone="(909) 981-1200", rating="4.8", reviews=54,
         logo=dict(w=128, shape="round"), photo="barber_shop", bg="#16110d", ink="#f5ecdf", soft="#b9aa97", line="#3a2f26", accent="#e8791c", on="#1a0f04",
         fonts="family=Bebas+Neue&family=Roboto:wght@400;500", head="'Bebas Neue', Impact, sans-serif", body="Roboto, Arial, sans-serif", head_css="font-weight:400; letter-spacing:.03em;",
         what="Barbershop on Mountain Avenue in Upland, right off the 10.",
         about_h="Bring the kids too",
         about=["Parents bring their kids here because our barbers are good with them. Everybody else comes for the attention to detail.",
                "Book a time online or call the shop."],
         list_h="Services", items=["Haircuts", "Fades", "Beard trims", "Kids' cuts"],
         note="Prices and open times are on the booking page.", call="Call the shop",
         action=("Book online", "https://proerabarbers.booksy.com")),
    dict(name="Elite Barber", slug="elite-barber-upland", city="Upland", layout="center",
         address="1667 N Mountain Ave, Suite 122, Upland, CA 91784", phone="(909) 981-5225", rating="4.6", reviews=52,
         logo=dict(w=260, shape="none", wide=True), photo="barber_tools", **WHITE, accent="#111111", on="#ffffff",
         fonts="family=Raleway:wght@300;400;500", head="Raleway, Arial, sans-serif", body="Raleway, Arial, sans-serif", head_css="font-weight:300; letter-spacing:.22em; text-transform:uppercase;",
         what="Barber shop in the Northwest Center, Upland.",
         about_h="A good haircut and friendly people",
         about=["That is what our customers say about us, and it is what we try to do every day. We are in Suite 122 at the Northwest Center on Mountain Avenue.",
                "Call the shop to ask about open times."],
         list_h="Services", items=["Haircuts", "Beard trims", "Kids' cuts"],
         note="Call for prices.", call="Call the shop"),
    dict(name="Classic Barbers", slug="classic-barbers-upland", city="Upland", layout="side",
         address="80 E Foothill Blvd, Upland, CA 91786", phone="(909) 727-2355", rating="4.7", reviews=90,
         logo=dict(w=170, shape="round"), photo="barber_shave", **BLACK, accent="#e9e4d8", on="#0c0c0c",
         fonts="family=Old+Standard+TT:wght@400;700&family=Work+Sans:wght@400;500", head="'Old Standard TT', Georgia, serif", body="'Work Sans', Arial, sans-serif", head_css="font-weight:700;",
         what="Barber shop on Foothill Boulevard in Upland.",
         about_h="The hot towel is part of it",
         about=["Ask anybody who comes here and they will bring up the hot towel. The cut is done the old way, and nobody hurries you out of the chair.",
                "Call the shop for an open time."],
         list_h="Services", items=["Haircuts", "Hot towel shaves", "Beard trims"],
         note="Call for prices.", call="Call the shop"),
    # ------------------------------------------------------------------ auto
    dict(name="Leyva auto repair", display="Leyva Auto Repair", slug="leyva-auto-repair-la-puente", city="La Puente", layout="center",
         address="", phone="(626) 672-5568", rating="5.0", reviews=37, mobile=True,
         logo=dict(w=220, shape="none"), photo="auto_hands", bg="#1f1f21", ink="#efe9da", soft="#b3ab98", line="#3b3b3e", accent="#c9a44c", on="#17130a",
         fonts="family=Jost:wght@400;500;600", head="Jost, Arial, sans-serif", body="Jost, Arial, sans-serif", head_css="font-weight:500; letter-spacing:.08em; text-transform:uppercase;",
         what="Auto repair in La Puente. Call Octavio.",
         about_h="Honest work",
         about=["I tell you what the car needs and what it does not. That is why my customers keep calling me, and why they send their family.",
                "Call or text with the year, make and model and what the car is doing."],
         list_h="What I work on", items=["Diagnostics", "Brakes", "Tune ups", "General repair"],
         note="Call first so I can set a time for you.", call="Call Octavio"),
    dict(name="HMS Automotive", slug="hms-automotive-la-puente", city="La Puente", layout="side",
         address="161 4th Ave, La Puente, CA 91746", phone="(626) 333-0984", rating="4.8", reviews=43,
         logo=dict(w=210, shape="none", wide=True), photo="auto_engine", **WHITE, accent="#b8912f", on="#ffffff",
         fonts="family=Archivo:wght@400;500;700", head="Archivo, Arial, sans-serif", body="Archivo, Arial, sans-serif", head_css="font-weight:700;",
         what="Auto repair and transmission specialist on 4th Avenue in La Puente.",
         about_h="Transmission specialist",
         about=["We do transmissions, and we do the rest of the car too. Customers say our people are helpful and the work holds up.",
                "Call the shop and tell us what the car is doing."],
         list_h="Services", items=["Transmissions", "Brakes", "Tune ups", "Timing belts", "Electrical", "Diagnostics", "Suspension", "Axles", "Clutches", "Radiators", "Engine overhaul"],
         note="Do not see it here? Call and ask.", call="Call the shop"),
    dict(name="Fontana Tires Complete Auto & Collision Repair", display="Fontana Tires", slug="fontana-tires-fontana", city="Fontana", layout="cover",
         address="15614 Arrow Route, Fontana, CA 92335", phone="(909) 854-1300", rating="4.8", reviews=1134,
         logo=dict(w=132, shape="none"), photo="auto_tires", **BLACK, accent="#e02127", on="#ffffff",
         fonts="family=Saira+Condensed:wght@600;700&family=Saira:wght@400;500", head="'Saira Condensed', 'Arial Narrow', sans-serif", body="Saira, Arial, sans-serif", head_css="font-weight:700; text-transform:uppercase; letter-spacing:.02em;",
         what="Tires, complete auto repair and collision repair on Arrow Route in Fontana.",
         about_h="Tires, repair and body work in one place",
         about=["Alignments are what we are best known for, and our customers will tell you the crew is friendly. Bring it in or call first."],
         list_h="What we do", items=["Tires", "Alignment", "Brakes", "Auto repair", "Collision repair"],
         note="Call for a price before you come in.", call="Call the shop"),
    dict(name="Best Tire Shop of Fontana", slug="best-tire-shop-of-fontana", city="Fontana", layout="center",
         address="15750 Arrow Blvd, Unit X, Fontana, CA 92335", phone="(909) 637-6882", rating="4.4", reviews=125,
         logo=dict(w=240, shape="none"), photo=None, **WHITE, accent="#d0202a", on="#ffffff",
         fonts="family=Barlow:wght@400;500;700", head="Barlow, Arial, sans-serif", body="Barlow, Arial, sans-serif", head_css="font-weight:700;",
         what="Tires and alignment on Arrow Boulevard in Fontana.",
         about_h="Whatever your tires need",
         about=["New tires, used tires, a flat, or an alignment that is pulling to one side. Come by Unit X at 15750 Arrow Boulevard or call first."],
         list_h="Services", items=["New and used tires", "Alignment", "Mounting and balancing", "Flat repair"],
         note="Call with your tire size for a price.", call="Call the shop"),
    dict(name="Sonora Tires Route 66 Inc", display="Sonora Tires Route 66", short="Sonora Tires", slug="sonora-tires-route-66-fontana", city="Fontana", layout="side",
         address="15979 Foothill Blvd, Fontana, CA 92335", phone="(909) 823-7878", rating="4.6", reviews=630,
         logo=dict(w=220, shape="none", wide=True), photo="auto_hood", bg="#ffffff", ink="#161616", soft="#595959", line="#dcdcdc", accent="#c8102e", on="#ffffff",
         fonts="family=Kanit:ital,wght@1,600&family=Kanit:wght@400;500", head="Kanit, Arial, sans-serif", body="Kanit, Arial, sans-serif", head_css="font-weight:600; font-style:italic;",
         what="Tire shop on Foothill Boulevard (Route 66) in Fontana.",
         about_h="On Route 66",
         about=["People come to us for alignments, used tires and quick installs. Pull in at 15979 Foothill Boulevard or call with your tire size.",
                "We also have a shop in Bloomington."],
         list_h="Services", items=["Alignment", "New tires", "Used tires", "Installation and balancing"],
         note="Call with your tire size for a price.", call="Call the shop"),
]

CSS = """
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:400 17px/1.6 var(--body)}
img{max-width:100%;display:block}a{color:inherit}
h1,h2{font-family:var(--head);HEADCSS;line-height:1.15;margin:0}
h1{font-size:clamp(1.55rem,6.2vw,2.5rem)}h2{font-size:clamp(1.25rem,4.6vw,1.6rem)}
p{margin:0 0 .9em}.soft{color:var(--soft)}
.wrap{max-width:1040px;margin:0 auto;padding:0 18px}
.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 18px;border-bottom:1px solid var(--line);font-size:15px}
.top b{font-family:var(--head);HEADCSS;font-size:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.top a{white-space:nowrap;font-weight:600;text-decoration:none;padding:8px 0}
.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 20px;border:2px solid var(--accent);border-radius:RADIUS;text-decoration:none;font-weight:600;font-size:16px}
.btn.p{background:var(--accent);color:var(--on)}.btn:hover{opacity:.88}
.logo.round{border-radius:50%}.logo.soft{border-radius:10px}
.what{font-size:18px;margin-top:10px}.rate{font-size:15px;margin-top:14px}
.info{margin:18px 0 0;padding:0;border-top:1px solid var(--line)}
.info div{display:flex;gap:14px;padding:10px 0;border-bottom:1px solid var(--line);font-size:16px}
.info dt{flex:0 0 76px;color:var(--soft)}.info dd{margin:0}
.photo{width:100%;height:220px;object-fit:cover}
.sec{padding:34px 0;border-top:1px solid var(--line)}
.items{list-style:none;margin:14px 0 12px;padding:0}
.items li{padding:9px 0;border-bottom:1px solid var(--line)}
.items small{display:block;color:var(--soft);font-size:14px}
.map{width:100%;height:300px;border:1px solid var(--line);margin-top:16px}
.foot{border-top:1px solid var(--line);padding:22px 0 30px;font-size:13px;color:var(--soft)}
.foot p{margin:0 0 6px}
/* center */
.c-hero{text-align:center;padding:34px 0 30px}.c-hero .logo{margin:0 auto 18px}.c-hero .btns{justify-content:center}
.c-two{display:grid;gap:30px}
/* cover */
.cover{width:100%;height:190px;object-fit:cover}
.v-head{padding:0 0 30px}.v-head .logo{margin-top:-46px;border:4px solid var(--bg);background:var(--bg)}
.v-head.nologo{padding-top:22px}.v-head h1{margin-top:14px}
/* side */
.s-grid{display:grid;gap:0}.s-card{padding:28px 0 30px}.s-card .logo{margin-bottom:16px}
@media(min-width:800px){
 .photo{height:380px}.cover{height:330px}.map{height:380px}
 .c-two{grid-template-columns:1.15fr 1fr;gap:56px}
 .items.cols{columns:2;column-gap:40px}.items.cols li{break-inside:avoid}
 .v-body{display:grid;grid-template-columns:1fr 1.2fr;gap:56px}.v-body .sec{border-top:0}
 .v-head{display:grid;grid-template-columns:1.1fr 1fr;gap:56px;align-items:end}
 .s-grid{grid-template-columns:330px 1fr;gap:56px;align-items:start}
 .s-card{position:sticky;top:0;padding-top:40px}.s-main{padding-top:40px}.s-main .sec:first-of-type{border-top:0;padding-top:28px}
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

    logo = ""
    if lg:
        w = lg["w"]
        box = f'width="{w}"'
        logo = f'<img class="logo {lg["shape"]}" src="logo.jpg" alt="{e(display)} logo" {box} style="width:{w}px;max-width:78%;height:auto" />'
    rate = (f'<p class="rate soft"><a href="{maps_link}" target="_blank" rel="noopener">{e(s["rating"])} stars on Google</a> '
            f'from {s["reviews"]:,} reviews</p>')
    act = s.get("action")
    btns = '<div class="btns">'
    if act:
        btns += f'<a class="btn p" href="{e(act[1])}" target="_blank" rel="noopener">{e(act[0])}</a><a class="btn" href="tel:{t}">{e(s["call"])}</a>'
    else:
        btns += f'<a class="btn p" href="tel:{t}">{e(s["call"])}</a>'
    if not mobile:
        btns += f'<a class="btn" href="{maps_link}" target="_blank" rel="noopener">Directions</a>'
    btns += "</div>"

    info = '<dl class="info">'
    if s["address"]:
        info += f'<div><dt>Address</dt><dd>{e(s["address"])}</dd></div>'
    else:
        info += f'<div><dt>Area</dt><dd>{e(city)} and nearby</dd></div>'
    info += f'<div><dt>Phone</dt><dd><a href="tel:{t}">{e(phone)}</a></dd></div></dl>'

    photo = ""
    if s.get("photo"):
        pid, alt = IMG[s["photo"]]
        photo = f'<img class="photo" src="{unsplash(pid, 1400)}" alt="{e(alt)}" />'

    def li(it):
        if isinstance(it, tuple):
            return f"<li><span>{e(it[0])}</span><small>{e(it[1])}</small></li>"
        return f"<li><span>{e(it)}</span></li>"
    cols = " cols" if len(s["items"]) >= 6 else ""
    items = (f'<h2>{e(s["list_h"])}</h2><ul class="items{cols}">' + "".join(li(i) for i in s["items"]) +
             f'</ul><p class="soft" style="font-size:15px">{e(s["note"])}</p>')
    about = f'<h2>{e(s["about_h"])}</h2>' + "".join(f"<p style='margin-top:12px'>{e(p)}</p>" for p in s["about"])
    find_h = f"Serving {city}" if mobile else "Find us"
    where = f'<p style="margin-top:10px">{e(s["address"])}<br />' if s["address"] else '<p style="margin-top:10px">'
    visit = (f'<section class="sec" id="find"><h2>{e(find_h)}</h2>{where}<a href="tel:{t}">{e(phone)}</a></p>'
             f'<iframe class="map" title="Map" src="{maps_embed}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe></section>')

    L = s["layout"]
    if L == "center":
        addr_line = f'<p class="soft" style="margin-top:6px">{e(s["address"])}</p>' if s["address"] else ""
        body = f"""<div class="wrap"><section class="c-hero">{logo}<h1>{e(display)}</h1><p class="what">{e(s["what"])}</p>{addr_line}{btns}{rate}</section></div>
{photo}
<div class="wrap"><section class="sec c-two"{' style="border-top:0"' if photo else ''}><div>{about}</div><div>{items}</div></section>
{visit}</div>"""
    elif L == "cover":
        if s.get("cover"):
            cover = f'<img class="cover" src="{e(s["cover"])}" alt="{e(s["cover_alt"])}" style="height:auto;max-height:420px" />'
        else:
            pid, alt = IMG[s["photo"]]
            cover = f'<img class="cover" src="{unsplash(pid, 1600)}" alt="{e(alt)}" />'
        body = f"""{cover}
<div class="wrap"><section class="v-head{'' if lg else ' nologo'}"><div>{logo}<h1>{e(display)}</h1><p class="what">{e(s["what"])}</p>{btns}{rate}</div><div>{info}</div></section>
<div class="v-body"><section class="sec">{items}</section><section class="sec">{about}</section></div>
{visit}</div>"""
    else:
        body = f"""<div class="wrap s-grid"><aside class="s-card">{logo}<h1>{e(display)}</h1><p class="what">{e(s["what"])}</p>{info}{btns}{rate}</aside>
<div class="s-main">{photo}<section class="sec">{about}</section><section class="sec">{items}</section>
{visit}</div></div>"""

    css = (CSS.replace("HEADCSS;", s["head_css"]).replace("RADIUS", s.get("radius", "4px")))
    desc = f'{display} in {city}, CA. {s["what"]}'
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
:root{{--bg:{s["bg"]};--ink:{s["ink"]};--soft:{s["soft"]};--line:{s["line"]};--accent:{s["accent"]};--on:{s["on"]};--head:{s["head"]};--body:{s["body"]}}}
{css}</style>
</head>
<body>
{preview_banner(display)}
<header class="top"><b>{e(short)}</b><a href="tel:{t}">{e(phone)}</a></header>
{body}
<footer class="foot"><div class="wrap">
<p>© {YEAR} {e(display)} · {e(city)}, CA · <a href="tel:{t}">{e(phone)}</a></p>
<p>Website preview · not the official site. Built by WestCo App Studio, <a href="tel:{WESTCO_TEL}">{WESTCO_PHONE}</a>.{' Photo is a stand-in until the owner sends their own.' if s.get("photo") else ''}</p>
</div></footer>
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
        if not (out / need).exists():
            sys.exit(f"missing {need} for {s['slug']}")
        (out / "index.html").write_text(render(s), encoding="utf-8", newline="\n")
        print(f"BUILT\t{s['name']}\t{PAGES_BASE}/sites/{s['slug']}/")


if __name__ == "__main__":
    main()
