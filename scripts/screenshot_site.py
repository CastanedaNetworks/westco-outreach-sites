"""Screenshot a local site folder at mobile + desktop widths for design review."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

slug = sys.argv[1] if len(sys.argv) > 1 else "mansae-sandwiches-west-covina"
site = Path(__file__).resolve().parent.parent / "sites" / slug / "index.html"
out_dir = Path(__file__).resolve().parent.parent / "_shots"
out_dir.mkdir(exist_ok=True)

VIEWPORTS = {"mobile320": (320, 660), "mobile390": (390, 760), "desktop": (1366, 850)}

with sync_playwright() as p:
    browser = p.chromium.launch()
    for name, (w, h) in VIEWPORTS.items():
        page = browser.new_page(viewport={"width": w, "height": h})
        page.goto(site.as_uri())
        page.wait_for_timeout(2500)
        # force reveal animations to finished state for full-page capture
        page.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('in'))")
        page.wait_for_timeout(800)
        page.screenshot(path=str(out_dir / f"{slug}-{name}-full.png"), full_page=True)
        page.screenshot(path=str(out_dir / f"{slug}-{name}-hero.png"))
        page.close()
    browser.close()
print("done:", out_dir)
