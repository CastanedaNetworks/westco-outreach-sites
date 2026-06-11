"""Mobile audit for a deployed preview: horizontal overflow at common phone
widths, undersized tap targets, and device-emulated screenshots."""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

url = sys.argv[1]
out_dir = Path(__file__).resolve().parent.parent / "_shots"
out_dir.mkdir(exist_ok=True)

WIDTHS = [320, 360, 375, 390, 414, 768]

JS_OVERFLOW = """
() => {
  const vw = document.documentElement.clientWidth;
  const clipped = el => {
    for (let a = el.parentElement; a; a = a.parentElement) {
      const o = getComputedStyle(a).overflowX;
      if (o === 'hidden' || o === 'clip') return true;
    }
    return false;
  };
  const bad = [];
  for (const el of document.querySelectorAll('*')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && (r.right > vw + 1 || r.left < -1) && !clipped(el)) {
      bad.push({tag: el.tagName, cls: (el.className + '').slice(0, 70),
                left: Math.round(r.left), right: Math.round(r.right)});
    }
  }
  return {vw, scrollW: document.documentElement.scrollWidth, bad: bad.slice(0, 12)};
}
"""

JS_TAP_TARGETS = """
() => {
  const small = [];
  for (const el of document.querySelectorAll('a, button')) {
    const r = el.getBoundingClientRect();
    if (r.width > 0 && r.height > 0 && (r.height < 40 || r.width < 40)) {
      small.push({text: (el.textContent || '').trim().slice(0, 40),
                  w: Math.round(r.width), h: Math.round(r.height)});
    }
  }
  return small;
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch()
    issues = 0
    for w in WIDTHS:
        page = browser.new_page(viewport={"width": w, "height": 800},
                                device_scale_factor=2, has_touch=True, is_mobile=True)
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(1200)
        page.evaluate("document.querySelectorAll('.reveal').forEach(e => e.classList.add('in'))")
        # marquee moves elements past the edge by design; ignore inside ticker
        page.evaluate("document.querySelectorAll('.ticker-track').forEach(e => e.remove())")
        page.wait_for_timeout(400)
        res = page.evaluate(JS_OVERFLOW)
        status = "OK" if res["scrollW"] <= res["vw"] + 1 else "OVERFLOW"
        if status != "OK":
            issues += 1
        print(f"[{w}px] scrollWidth={res['scrollW']} viewport={res['vw']} -> {status}")
        for b in res["bad"]:
            print(f"    <{b['tag'].lower()}> left={b['left']} right={b['right']} class={b['cls']}")
        if w == 320:
            for t in page.evaluate(JS_TAP_TARGETS):
                print(f"    small tap target ({t['w']}x{t['h']}): {t['text']}")
        if w in (320, 414):
            page.screenshot(path=str(out_dir / f"live-{w}-full.png"), full_page=True)
        page.close()
    browser.close()
    print("AUDIT", "FAIL" if issues else "PASS")
