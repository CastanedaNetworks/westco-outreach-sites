"""
scrape_maps.py — Google Maps prospector for WestCo outreach.

Usage:
    python scripts/scrape_maps.py --category "auto repair" --city "Covina" --max 25
    python scripts/scrape_maps.py --category "salons" --city "Pomona" --max 25 --headless

Behavior:
  - Opens Google Maps in a real Chromium window (headed by default)
  - Searches "<category> <city> ca"
  - Scrolls the results panel to load more
  - For each listing:
      * Skips it if the listing has a "Website" button
      * Otherwise pulls name, address, phone, rating, review_count, category, top 5 reviews
  - Hashes name+address to form a stable place_id
  - Appends new rows to data/prospects.csv with status='new'
  - Dedupes against existing rows by place_id
  - Tags county (LA / SB / RIV / OR) from the city
  - Random delays: 2-5s between actions, 10-15s between businesses

Notes:
  - Google Maps DOM is volatile. Selectors use multiple fallbacks; if Google
    changes things and a field comes back empty, the row is still saved so
    you can fix it by hand.
  - Use --debug to drop screenshots into the project root when a listing fails.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from playwright.sync_api import (
    Page,
    Playwright,
    TimeoutError as PWTimeoutError,
    sync_playwright,
)

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROSPECTS_CSV = DATA_DIR / "prospects.csv"

CSV_COLUMNS = [
    "place_id", "name", "slug", "address", "city", "county",
    "phone", "rating", "review_count", "category", "reviews_json",
    "status", "generated_url", "created_at", "sent_at", "replied_at", "notes",
]

# --------------------------------------------------------------------------- #
# City -> county map (lowercase keys)
# --------------------------------------------------------------------------- #
CITY_COUNTY = {
    # LA County
    "west covina": "LA", "covina": "LA", "baldwin park": "LA", "pomona": "LA",
    "whittier": "LA", "pasadena": "LA", "el monte": "LA", "downey": "LA",
    "norwalk": "LA", "long beach": "LA", "glendora": "LA", "azusa": "LA",
    "la puente": "LA", "rowland heights": "LA", "hacienda heights": "LA",
    "diamond bar": "LA", "walnut": "LA", "monrovia": "LA", "arcadia": "LA",
    "alhambra": "LA", "san gabriel": "LA", "rosemead": "LA", "south el monte": "LA",
    "industry": "LA", "city of industry": "LA", "montebello": "LA", "pico rivera": "LA",
    "bellflower": "LA", "lakewood": "LA", "cerritos": "LA", "artesia": "LA",
    "santa fe springs": "LA", "la mirada": "LA",

    # San Bernardino County
    "ontario": "SB", "rancho cucamonga": "SB", "san bernardino": "SB",
    "fontana": "SB", "upland": "SB", "chino": "SB", "chino hills": "SB",
    "rialto": "SB", "colton": "SB", "redlands": "SB", "yucaipa": "SB",
    "highland": "SB", "loma linda": "SB", "montclair": "SB",

    # Riverside County
    "riverside": "RIV", "moreno valley": "RIV", "corona": "RIV", "norco": "RIV",
    "eastvale": "RIV", "jurupa valley": "RIV", "perris": "RIV", "hemet": "RIV",
    "menifee": "RIV", "temecula": "RIV", "murrieta": "RIV", "lake elsinore": "RIV",
    "wildomar": "RIV", "banning": "RIV", "beaumont": "RIV",

    # Orange County
    "anaheim": "OR", "orange": "OR", "santa ana": "OR", "fullerton": "OR",
    "garden grove": "OR", "irvine": "OR", "huntington beach": "OR",
    "costa mesa": "OR", "newport beach": "OR", "tustin": "OR", "yorba linda": "OR",
    "placentia": "OR", "brea": "OR", "la habra": "OR", "buena park": "OR",
    "cypress": "OR", "stanton": "OR", "westminster": "OR", "fountain valley": "OR",
    "mission viejo": "OR", "lake forest": "OR", "laguna hills": "OR",
    "laguna niguel": "OR", "aliso viejo": "OR", "san clemente": "OR",
    "san juan capistrano": "OR", "rancho santa margarita": "OR",
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def hash_place_id(name: str, address: str) -> str:
    h = hashlib.sha1(f"{name.lower().strip()}|{address.lower().strip()}".encode("utf-8")).hexdigest()
    return f"wco_{h[:16]}"


def county_for(city: str) -> str:
    return CITY_COUNTY.get(city.lower().strip(), "UNK")


def sleep_action() -> None:
    time.sleep(random.uniform(2.0, 5.0))


def sleep_business() -> None:
    time.sleep(random.uniform(10.0, 15.0))


# --------------------------------------------------------------------------- #
# CSV helpers
# --------------------------------------------------------------------------- #
def ensure_csv() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not PROSPECTS_CSV.exists() or PROSPECTS_CSV.stat().st_size == 0:
        with PROSPECTS_CSV.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(CSV_COLUMNS)


def load_existing_place_ids() -> set[str]:
    ensure_csv()
    ids: set[str] = set()
    with PROSPECTS_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get("place_id")
            if pid:
                ids.add(pid)
    return ids


def append_prospect(row: dict) -> None:
    with PROSPECTS_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow({k: row.get(k, "") for k in CSV_COLUMNS})


# --------------------------------------------------------------------------- #
# Playwright helpers
# --------------------------------------------------------------------------- #
def safe_text(page: Page, selector: str, timeout: int = 1500) -> str:
    try:
        el = page.wait_for_selector(selector, timeout=timeout, state="attached")
        return (el.inner_text() or "").strip() if el else ""
    except PWTimeoutError:
        return ""


def safe_attr(page: Page, selector: str, attr: str, timeout: int = 1500) -> str:
    try:
        el = page.wait_for_selector(selector, timeout=timeout, state="attached")
        if not el:
            return ""
        return (el.get_attribute(attr) or "").strip()
    except PWTimeoutError:
        return ""


def dismiss_consent(page: Page) -> None:
    """Click through Google's cookie/consent banner if it appears."""
    for text in ("Accept all", "I agree", "Reject all", "Got it"):
        try:
            btn = page.get_by_role("button", name=re.compile(text, re.I))
            if btn.count() > 0:
                btn.first.click(timeout=2000)
                time.sleep(1)
                return
        except Exception:
            continue


def scroll_results_panel(page: Page, target_count: int, debug: bool = False) -> None:
    """Scroll the left-hand results feed until we have enough cards or it stops growing."""
    try:
        feed = page.wait_for_selector('div[role="feed"]', timeout=10_000)
    except PWTimeoutError:
        if debug:
            page.screenshot(path=str(ROOT / "debug-no-feed.png"))
        return

    last_count = 0
    stalled = 0
    while stalled < 4:
        cards = feed.query_selector_all('a[href*="/maps/place/"]')
        if len(cards) >= target_count:
            return
        if len(cards) == last_count:
            stalled += 1
        else:
            stalled = 0
            last_count = len(cards)
        feed.evaluate("(el) => el.scrollBy(0, el.scrollHeight)")
        time.sleep(random.uniform(1.6, 2.8))


def has_website(page: Page) -> bool:
    """True if the detail panel exposes a Website link."""
    for sel in [
        'a[data-item-id="authority"]',
        'a[aria-label^="Website"]',
        'button[aria-label^="Website"]',
        'a[data-tooltip="Open website"]',
    ]:
        try:
            if page.locator(sel).count() > 0:
                return True
        except Exception:
            continue
    # last-ditch: visible link with text "Website"
    try:
        if page.get_by_role("link", name=re.compile(r"^Website$", re.I)).count() > 0:
            return True
    except Exception:
        pass
    return False


def get_phone(page: Page) -> str:
    for sel in [
        'button[data-item-id^="phone:tel:"]',
        'button[aria-label^="Phone:"]',
        'a[href^="tel:"]',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            aria = loc.get_attribute("aria-label") or ""
            href = loc.get_attribute("href") or ""
            if href.startswith("tel:"):
                return href.replace("tel:", "").strip()
            # "Phone: (626) 699-2348" — strip the prefix, then take everything left.
            if ":" in aria:
                tail = aria.split(":", 1)[1].strip()
                if tail:
                    return tail
            m = re.search(r"[\(\d][\d\s\-\(\)\.]{8,}", aria)
            if m:
                return m.group(0).strip()
            text = (loc.inner_text() or "").strip()
            if text:
                return text
        except Exception:
            continue
    return ""


def get_address(page: Page) -> str:
    for sel in [
        'button[data-item-id="address"]',
        'button[aria-label^="Address:"]',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            aria = loc.get_attribute("aria-label") or ""
            if aria.lower().startswith("address:"):
                return aria.split(":", 1)[1].strip()
            text = (loc.inner_text() or "").strip()
            if text:
                return text
        except Exception:
            continue
    return ""


def get_name(page: Page) -> str:
    # The page itself has a global <h1>Results</h1> when listing search results.
    # We want the detail-panel h1 only, so we scope to role=main and reject the
    # generic Results/Sponsored values as a belt-and-suspenders guard.
    JUNK = {"results", "sponsored", ""}
    scoped = [
        'div[role="main"] h1.DUwDvf',
        'div[role="main"] h1[class*="DUwDvf"]',
        'div[role="main"] h1',
    ]
    for sel in scoped:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                t = (loc.inner_text() or "").strip()
                if t and t.lower() not in JUNK:
                    return t
        except Exception:
            continue
    # last-resort fallback — class-based, still rejecting junk
    for sel in ['h1.DUwDvf', 'h1[class*="DUwDvf"]']:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                t = (loc.inner_text() or "").strip()
                if t and t.lower() not in JUNK:
                    return t
        except Exception:
            continue
    return ""


def get_rating_and_count(page: Page) -> tuple[str, str]:
    rating, count = "", ""
    try:
        # Aria like "4.7 stars" near the header
        rating_el = page.locator('div.F7nice span[aria-hidden="true"]').first
        if rating_el.count() > 0:
            rating = (rating_el.inner_text() or "").strip()
    except Exception:
        pass
    try:
        count_el = page.locator('div.F7nice span[aria-label$="reviews"]').first
        if count_el.count() > 0:
            aria = count_el.get_attribute("aria-label") or ""
            m = re.search(r"([\d,]+)", aria)
            if m:
                count = m.group(1).replace(",", "")
    except Exception:
        pass
    if not rating or not count:
        # Fallback: parse the F7nice block as a whole
        try:
            block = page.locator('div.F7nice').first
            if block.count() > 0:
                txt = (block.inner_text() or "").replace("\n", " ")
                m_r = re.search(r"(\d\.\d)", txt)
                m_c = re.search(r"\(([\d,]+)\)", txt)
                if not rating and m_r:
                    rating = m_r.group(1)
                if not count and m_c:
                    count = m_c.group(1).replace(",", "")
        except Exception:
            pass
    return rating, count


def get_category(page: Page) -> str:
    for sel in ['button.DkEaL', 'button[jsaction*="category"]']:
        try:
            loc = page.locator(sel).first
            if loc.count() > 0:
                t = (loc.inner_text() or "").strip()
                if t:
                    return t
        except Exception:
            continue
    return ""


def get_reviews(page: Page, top_n: int = 5) -> list[dict]:
    """Open the reviews section and capture the top N unique reviews.

    Google's detail panel varies: sometimes there's a Reviews *tab*, sometimes
    a Reviews *button*, sometimes reviews are already inline and you just need
    to scroll to load more. We try several navigation strategies, then scroll
    the side panel to lazy-load review cards.
    """
    reviews: list[dict] = []

    # --- Step 1: try to focus the reviews section -----------------------------
    navigated = False
    for role, pattern in (
        ("tab",    re.compile(r"^Reviews", re.I)),
        ("button", re.compile(r"^Reviews$", re.I)),
        ("link",   re.compile(r"(more|all)\s+reviews", re.I)),
    ):
        try:
            loc = page.get_by_role(role, name=pattern)
            if loc.count() > 0:
                loc.first.click(timeout=2500)
                navigated = True
                time.sleep(random.uniform(1.4, 2.2))
                break
        except Exception:
            continue

    # --- Step 2: scroll the side panel so review cards lazy-load --------------
    # Whether or not we navigated, the cards are loaded inside role=main. Scroll
    # it a few times. We use page.evaluate so we don't depend on cursor position.
    for _ in range(4):
        try:
            page.evaluate(
                "() => { const m = document.querySelector('div[role=\"main\"]');"
                " if (m) m.scrollBy(0, 1400); }"
            )
        except Exception:
            pass
        time.sleep(random.uniform(0.7, 1.2))

    # --- Step 3: expand any "See more" buttons so we get full text -----------
    try:
        more_buttons = page.locator('button[aria-label="See more"]')
        for i in range(min(more_buttons.count(), top_n + 3)):
            try:
                more_buttons.nth(i).click(timeout=400)
            except Exception:
                continue
    except Exception:
        pass

    # --- Step 4: capture cards with dedupe -----------------------------------
    try:
        cards = page.locator('div[data-review-id]')
        seen: set[tuple[str, str]] = set()
        total = cards.count()
        for i in range(min(total, top_n * 4)):
            card = cards.nth(i)
            author = ""
            text = ""
            try:
                author = (card.locator('div.d4r55').first.inner_text() or "").strip()
            except Exception:
                pass
            for text_sel in ('span.wiI7pd', 'div.MyEned', 'span[class*="wiI7"]'):
                try:
                    t = (card.locator(text_sel).first.inner_text() or "").strip()
                    if t:
                        text = t
                        break
                except Exception:
                    continue
            key = (author, text[:80])
            if key in seen or not (author or text):
                continue
            seen.add(key)
            reviews.append({"author": author or "Google reviewer", "text": text})
            if len(reviews) >= top_n:
                break
    except Exception:
        pass

    return reviews


# --------------------------------------------------------------------------- #
# Main scrape loop
# --------------------------------------------------------------------------- #
def split_address(full: str) -> tuple[str, str]:
    """Return (line_1, line_2) by splitting on first comma — best-effort."""
    if "," in full:
        a, b = full.split(",", 1)
        return a.strip(), b.strip()
    return full.strip(), ""


def run(category: str, city: str, max_results: int, headless: bool, debug: bool) -> None:
    ensure_csv()
    existing = load_existing_place_ids()

    scraped = 0
    new_count = 0
    skipped_with_site = 0

    query = f"{category} {city} ca"
    print(f"[westco] searching: {query!r}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="en-US",
            timezone_id="America/Los_Angeles",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/130.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()
        page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        dismiss_consent(page)
        time.sleep(random.uniform(1.5, 3))

        # Run search. Google Maps swapped the static id 'searchboxinput' for a
        # dynamic id (the input still has name="q" and role="combobox"), so we
        # match on a few fallbacks rather than the old id.
        try:
            search_box = None
            for sel in ('input[name="q"]', 'input[role="combobox"]', 'input#searchboxinput'):
                loc = page.locator(sel).first
                if loc.count() > 0:
                    search_box = loc
                    break
            if not search_box:
                raise RuntimeError("no search box found on /maps")
            search_box.click(timeout=8000)
            search_box.fill(query)
            page.keyboard.press("Enter")
        except Exception as e:
            print(f"[westco] could not run search: {e}")
            browser.close()
            return

        try:
            page.wait_for_selector('div[role="feed"]', timeout=15_000)
        except PWTimeoutError:
            # Single-result page can land directly on a place — handle as a single card
            print("[westco] no results feed appeared")
            browser.close()
            return

        sleep_action()
        scroll_results_panel(page, target_count=max_results, debug=debug)

        feed = page.locator('div[role="feed"]')
        cards = feed.locator('a[href*="/maps/place/"]')
        total = min(cards.count(), max_results)
        print(f"[westco] {total} candidate listings loaded")

        for i in range(total):
            try:
                card = cards.nth(i)
                try:
                    card.scroll_into_view_if_needed(timeout=2000)
                except Exception:
                    pass
                card.click(timeout=4000)
            except Exception as e:
                if debug:
                    page.screenshot(path=str(ROOT / f"debug-card-{i}.png"))
                print(f"[westco] [{i+1}/{total}] click failed: {e}")
                continue

            try:
                page.wait_for_selector('h1', timeout=8_000)
            except PWTimeoutError:
                print(f"[westco] [{i+1}/{total}] detail panel didn't load")
                continue
            sleep_action()

            scraped += 1
            name = get_name(page)
            if not name or name.strip().lower() in ("results", "sponsored"):
                print(f"[westco] [{i+1}/{total}] junk/empty name ({name!r}), skipping")
                continue

            if has_website(page):
                skipped_with_site += 1
                print(f"[westco] [{i+1}/{total}] {name} — has website, skip")
                sleep_business()
                continue

            address = get_address(page)
            phone = get_phone(page)
            rating, review_count = get_rating_and_count(page)
            cat = get_category(page) or category
            reviews = get_reviews(page, top_n=5)

            place_id = hash_place_id(name, address)
            if place_id in existing:
                print(f"[westco] [{i+1}/{total}] {name} — already in CSV, skip")
                sleep_business()
                continue

            row = {
                "place_id": place_id,
                "name": name,
                "slug": slugify(f"{name} {city}"),
                "address": address,
                "city": city,
                "county": county_for(city),
                "phone": phone,
                "rating": rating,
                "review_count": review_count,
                "category": cat,
                "reviews_json": json.dumps(reviews, ensure_ascii=False),
                "status": "new",
                "generated_url": "",
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "sent_at": "",
                "replied_at": "",
                "notes": "",
            }
            append_prospect(row)
            existing.add(place_id)
            new_count += 1
            print(f"[westco] [{i+1}/{total}] + {name}  ({phone or 'no phone'}, {len(reviews)} reviews)")
            sleep_business()

        browser.close()

    print()
    print("[westco] ===== summary =====")
    print(f"[westco] scraped:        {scraped}")
    print(f"[westco] new prospects:  {new_count}")
    print(f"[westco] skipped (site): {skipped_with_site}")
    print(f"[westco] csv:            {PROSPECTS_CSV}")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Google Maps prospector for WestCo outreach")
    parser.add_argument("--category", required=True, help='e.g. "auto repair"')
    parser.add_argument("--city", required=True, help='e.g. "Covina"')
    parser.add_argument("--max", type=int, default=25, dest="max_results", help="max listings to inspect")
    parser.add_argument("--headless", action="store_true", help="run without showing the browser")
    parser.add_argument("--debug", action="store_true", help="dump screenshots when selectors fail")
    args = parser.parse_args(argv)

    try:
        run(args.category, args.city, args.max_results, args.headless, args.debug)
    except KeyboardInterrupt:
        print("\n[westco] interrupted by user")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
