"""claimdepot.com/settlements - paginated Webflow collection; a separate no-proof list."""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..http import Fetcher
from ..model import Settlement
from ._util import strings

NAME = "claimdepot.com"
BASE = "https://www.claimdepot.com"
URL = BASE + "/settlements"
NO_PROOF_URL = BASE + "/no-proof-class-action-settlements"
MAX_PAGES = 15


def _items(soup: BeautifulSoup):
    return soup.select(".c-collection_item")


def parse(html: str) -> tuple[list[Settlement], str | None]:
    """Return settlements on the page and the next-page href (or None)."""
    soup = BeautifulSoup(html, "lxml")
    out: list[Settlement] = []
    for it in _items(soup):
        title = it.select_one(".c-title-3")
        link = title if title and title.name == "a" else it.select_one("a[href*='/settlements/']")
        if not title or not link:
            continue
        vals = [s for s in (t.get_text(" ", strip=True) for t in it.select(".c-text-2"))]
        # observed order: status, payout, deadline, days-left number, "Days left", category, description
        status = vals[0] if vals else ""
        if status and "open" not in status.lower():
            continue
        payout = vals[1] if len(vals) > 1 else ""
        deadline = vals[2] if len(vals) > 2 else ""
        cats = [c.get_text(strip=True) for c in it.select("[fs-cmsfilter-field=category]")]
        cats = [c for c in cats if c and c != status]
        desc = vals[-1] if vals else ""
        out.append(
            Settlement(
                source=NAME,
                name=title.get_text(" ", strip=True),
                url=urljoin(BASE, link["href"]),
                payout_text=payout,
                deadline_text=deadline,
                description=desc,
                category=cats[-1] if cats else "",
            )
        )
    nxt = soup.select_one("a.w-pagination-next")
    return out, (nxt["href"] if nxt and nxt.get("href") else None)


def _no_proof_urls(f: Fetcher) -> set[str]:
    urls: set[str] = set()
    page_url: str | None = NO_PROOF_URL
    for _ in range(MAX_PAGES):
        r = f.get(page_url) if page_url else None
        if not r:
            break
        items, nxt = parse(r.text)
        urls |= {s.url for s in items}
        if not nxt or not items:
            break
        page_url = urljoin(NO_PROOF_URL, nxt)
    return urls


def fetch(f: Fetcher) -> list[Settlement]:
    out: list[Settlement] = []
    page_url: str | None = URL
    for _ in range(MAX_PAGES):
        r = f.get(page_url) if page_url else None
        if not r:
            break
        items, nxt = parse(r.text)
        out += items
        if not nxt or not items:
            break
        page_url = urljoin(URL, nxt)
    no_proof = _no_proof_urls(f)
    for s in out:
        if s.url in no_proof:
            s.proof_text = "No"
    # de-dupe (featured items can repeat)
    seen: dict[str, Settlement] = {}
    for s in out:
        seen.setdefault(s.url, s)
    return list(seen.values())
