"""theclassactionlawsuit.com/settlements/?stage=open - card grid, query-31-page pagination."""
from __future__ import annotations

from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..http import Fetcher
from ..model import Settlement
from ._util import strings, value_after

NAME = "theclassactionlawsuit.com"
BASE = "https://www.theclassactionlawsuit.com"
URL = BASE + "/settlements/?stage=open"
MAX_PAGES = 15


def parse(html: str) -> list[Settlement]:
    soup = BeautifulSoup(html, "lxml")
    out: dict[str, Settlement] = {}
    for card in soup.select("article"):
        a = card.select_one("a[href*='/settlement/']")
        if not a:
            continue
        url = urljoin(BASE, a["href"])
        if url in out:
            continue
        strs = strings(card)
        if strs and "open" not in strs[0].lower():
            continue
        title = card.find(["h2", "h3", "h4"])
        name = title.get_text(" ", strip=True) if title else a.get_text(" ", strip=True)
        desc_el = title.find_next("p") if title else None
        text = " ".join(strs).lower()
        out[url] = Settlement(
            source=NAME,
            name=name,
            url=url,
            payout_text=value_after(strs, "payout"),
            deadline_text=value_after(strs, "deadline"),
            proof_text="No" if "no proof" in text else "",
            description=desc_el.get_text(" ", strip=True) if desc_el else "",
        )
    return list(out.values())


def fetch(f: Fetcher) -> list[Settlement]:
    out: dict[str, Settlement] = {}
    for page in range(1, MAX_PAGES + 1):
        r = f.get(URL if page == 1 else f"{URL}&query-31-page={page}")
        if not r:
            break
        new = [s for s in parse(r.text) if s.url not in out]
        if not new:
            break
        for s in new:
            out[s.url] = s
    return list(out.values())
