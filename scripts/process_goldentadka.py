"""Process Golden Tadka brand assets: photos to JPEG, sketch art to transparent PNG."""
import os
from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\louis\Downloads")
OUT = Path(r"sites\golden-tadka-west-covina\img")
OUT.mkdir(parents=True, exist_ok=True)


def to_jpeg(src_name, out_name, quality=85, max_edge=1600):
    img = Image.open(SRC / src_name).convert("RGB")
    if max(img.size) > max_edge:
        img.thumbnail((max_edge, max_edge), Image.LANCZOS)
    img.save(OUT / out_name, "JPEG", quality=quality, optimize=True, progressive=True)
    print(out_name, img.size, (OUT / out_name).stat().st_size // 1024, "KB")


def extract_art(src_name, box_frac, out_name, scale=1, erase=None):
    """Crop line art off a light background -> transparent PNG.
    box_frac = (x0, y0, x1, y1) as fractions. erase = optional rect to clear."""
    img = Image.open(SRC / src_name).convert("RGB")
    w, h = img.size
    crop = img.crop((int(w * box_frac[0]), int(h * box_frac[1]),
                     int(w * box_frac[2]), int(h * box_frac[3])))
    hist = crop.histogram()
    total = crop.size[0] * crop.size[1]
    bg = []
    for c in range(3):
        ch = hist[c * 256:(c + 1) * 256]
        acc = 0
        for v in range(256):
            acc += ch[v]
            if acc >= total * 0.85:
                bg.append(max(v, 1))
                break
    luts = []
    for c in range(3):
        luts += [min(255, round(v * 255 / bg[c])) for v in range(256)]
    crop = crop.point(luts)
    cw, chh = crop.size
    out = Image.new("RGBA", crop.size)
    src_px, dst = crop.load(), out.load()
    for y in range(chh):
        for x in range(cw):
            if erase and erase[0] * cw < x < erase[2] * cw and erase[1] * chh < y < erase[3] * chh:
                dst[x, y] = (255, 255, 255, 0)
                continue
            r, g, b = src_px[x, y]
            a = 255 - min(r, g, b)
            if a == 0:
                dst[x, y] = (255, 255, 255, 0)
            else:
                rr = max(0, min(255, round((r - (255 - a)) * 255 / a)))
                gg = max(0, min(255, round((g - (255 - a)) * 255 / a)))
                bb = max(0, min(255, round((b - (255 - a)) * 255 / a)))
                dst[x, y] = (rr, gg, bb, a)
    if scale != 1:
        out = out.resize((int(out.size[0] * scale), int(out.size[1] * scale)), Image.LANCZOS)
    out.save(OUT / out_name, optimize=True)
    print(out_name, out.size, os.path.getsize(OUT / out_name) // 1024, "KB")


to_jpeg("Golden-Tadka-Interior-Picture.png", "interior.jpg", quality=86)
to_jpeg("Golden-Tadka-soft-launch-post.png", "soft-launch.jpg")
to_jpeg("Golden-Tadka-logo.png", "logo-velvet.jpg", quality=88)

# gold kadai icon from the opening flyer (centered small icon)
extract_art("Golden-Tadka-Opening-Soon-Flyer.png", (0.40, 0.785, 0.60, 0.895), "kadai.png", scale=2)
# hand-sketched storefront from the opening flyer
extract_art("Golden-Tadka-Opening-Soon-Flyer.png", (0.13, 0.24, 0.84, 0.665), "storefront-sketch.png")
# pot-and-spices sketch from the bottom of their menu card
extract_art("Golden-Tadka-Menu.png", (0.22, 0.70, 0.80, 0.875), "pot-sketch.png")
