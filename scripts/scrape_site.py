"""Render a URL with Playwright and dump title, generator, text, and links."""
import sys
from playwright.sync_api import sync_playwright

url = sys.argv[1]
shot = sys.argv[2] if len(sys.argv) > 2 else "_shots/site.png"

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1280, "height": 900})
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    page.screenshot(path=shot, full_page=True)
    print("TITLE:", page.title())
    gen = page.query_selector("meta[name=generator]")
    print("GENERATOR:", gen.get_attribute("content") if gen else "n/a")
    txt = page.evaluate("document.body.innerText")
    print("=== TEXT (first 2500) ===")
    print(txt[:2500])
    print("=== LINKS ===")
    links = page.eval_on_selector_all(
        "a", "els => els.map(e => e.href + ' | ' + e.innerText.trim().slice(0,40))")
    for l in links[:25]:
        print(l)
    b.close()
