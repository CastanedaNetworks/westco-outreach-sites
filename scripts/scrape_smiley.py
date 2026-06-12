"""Render the Happy Tik Smiley page with a real browser and dump visible text,
the about section, and any booking/service info hidden behind JS."""
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://business.joinsmiley.com/Walnut-Valley-Happy-Tik-Pet-Grooming-KGX3y"
out_dir = Path(__file__).resolve().parent.parent / "_shots"
out_dir.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(3000)
    page.screenshot(path=str(out_dir / "smiley-page.png"), full_page=True)
    print("=== PAGE TEXT ===")
    print(page.evaluate("document.body.innerText"))
    print("=== LINKS ===")
    for link in page.eval_on_selector_all("a", "els => els.map(e => e.href + ' | ' + e.innerText.trim().slice(0,40))"):
        print(link)
    print("=== IMAGES ===")
    for src in page.eval_on_selector_all("img", "els => els.map(e => e.src)"):
        print(src)
    # try the Book Now button to expose the services menu
    try:
        page.click("text=Book Now", timeout=4000)
        page.wait_for_timeout(4000)
        print("=== AFTER BOOK NOW (url:", page.url, ") ===")
        print(page.evaluate("document.body.innerText")[:4000])
        page.screenshot(path=str(out_dir / "smiley-booking.png"), full_page=True)
    except Exception as e:
        print("Book Now click failed:", e)
    browser.close()
