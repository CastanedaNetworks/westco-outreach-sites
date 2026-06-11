"""One-off: convert Mansae source photos from Downloads into web-weight
JPEGs inside the site folder. Max 1600px on the long edge, quality 82."""
import shutil
from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\louis\Downloads")
OUT = Path(r"C:\Users\louis\westco-outreach\sites\mansae-sandwiches-west-covina\img")
OUT.mkdir(parents=True, exist_ok=True)

MAPPING = {
    "Mansae-Sandwiches-product-Korean-Egg-Toast-Sandwich.png": "hero-bulgogi-hand.jpg",
    "Mansae-Sandwiches-product-Pork-Belly-Kimchi-Sandwich.png": "pork-belly-kimchi.jpg",
    "Mansae-Sandwiches-product-Bulgogi-Korean-Egg-Toast-Sandwich.png": "bulgogi-box.jpg",
    "Mansae-Sandwiches-product-egg-toast-sandwiches.png": "duo-orange.jpg",
    "Mansae-Sandwiches-product-sea-salt-foam-green-ice-tea.png": "sea-salt-tea.jpg",
    "Mansae-Sandwiches-product-corn-cheese-melted-on-fries-loaded-with-beef-bulgogi.png": "corn-cheese-fries.jpg",
    "Mansae-Sandwiches-Branding.png": "booth-banner.jpg",
    "Mansae-Sandwiches-Chef-Cooking-picture.png": "chef-griddle.jpg",
    "Mansae-Sandwiches-Cooking-picture.png": "toast-griddle.jpg",
}

MAX_EDGE = 1600

for src_name, out_name in MAPPING.items():
    src = SRC / src_name
    img = Image.open(src).convert("RGB")
    if max(img.size) > MAX_EDGE:
        img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    out = OUT / out_name
    img.save(out, "JPEG", quality=82, optimize=True, progressive=True)
    print(f"{out_name}: {img.size[0]}x{img.size[1]}, {out.stat().st_size // 1024} KB")

shutil.copy(SRC / "Mansae_sandwiches_logo.jpg", OUT / "logo.jpg")
print("logo.jpg: copied as-is")
