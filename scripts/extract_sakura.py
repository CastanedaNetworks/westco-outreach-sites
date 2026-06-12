"""Extract the sakura branch from the Yama House flyer as a transparent PNG,
masking out the enso arc that shares the corner."""
import os

from PIL import Image

flyer = Image.open(r"C:\Users\louis\Downloads\Yama-House-flyer.png").convert("RGB")
w, h = flyer.size
crop = flyer.crop((0, 0, int(w * 0.21), int(h * 0.155)))

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
src, dst = crop.load(), out.load()
for y in range(chh):
    for x in range(cw):
        if x > cw * 0.55 and y > chh * 0.42:  # the enso arc corner, not branch
            dst[x, y] = (255, 255, 255, 0)
            continue
        r, g, b = src[x, y]
        a = 255 - min(r, g, b)
        if a == 0:
            dst[x, y] = (255, 255, 255, 0)
        else:
            rr = max(0, min(255, round((r - (255 - a)) * 255 / a)))
            gg = max(0, min(255, round((g - (255 - a)) * 255 / a)))
            bb = max(0, min(255, round((b - (255 - a)) * 255 / a)))
            dst[x, y] = (rr, gg, bb, a)

out = out.resize((out.size[0] * 2, out.size[1] * 2), Image.LANCZOS)
dest = r"sites\yama-house-west-covina\img\sakura-branch.png"
out.save(dest, optimize=True)
print("branch:", out.size, os.path.getsize(dest) // 1024, "KB")
