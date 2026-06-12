"""Re-extract the storefront sketch, erasing the red script strokes in the corners."""
import os
from pathlib import Path

from PIL import Image

SRC = Path(r"C:\Users\louis\Downloads\Golden-Tadka-Opening-Soon-Flyer.png")
OUT = Path(r"sites\golden-tadka-west-covina\img\storefront-sketch.png")

img = Image.open(SRC).convert("RGB")
w, h = img.size
crop = img.crop((int(w * 0.13), int(h * 0.24), int(w * 0.84), int(h * 0.665)))

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
        r, g, b = src_px[x, y]
        # red script strokes live in the corners + top strip; the centered sign sits lower
        in_script_zone = ((x < cw * 0.32 or x > cw * 0.66) and y < chh * 0.50) or y < chh * 0.18
        if in_script_zone and r - max(g, b) > 35:
            dst[x, y] = (255, 255, 255, 0)
            continue
        a = 255 - min(r, g, b)
        if a == 0:
            dst[x, y] = (255, 255, 255, 0)
        else:
            rr = max(0, min(255, round((r - (255 - a)) * 255 / a)))
            gg = max(0, min(255, round((g - (255 - a)) * 255 / a)))
            bb = max(0, min(255, round((b - (255 - a)) * 255 / a)))
            dst[x, y] = (rr, gg, bb, a)

out.save(OUT, optimize=True)
print("storefront:", out.size, os.path.getsize(OUT) // 1024, "KB")
