"""topclassactions.com open settlements - WordPress category, /page/N/ pagination."""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..http import Fetcher
from ..model import Settlement
from ._util import strings, value_after

NAME = "topclassactions.com"
URL = "https://topclassactions.com/category/lawsuit-settlements/open-lawsuit-settlements/"
MAX_PAGES = 20
LINK_RE = re.compile(r"/lawsuit-settlements/open-lawsuit-settlements/[^/]+/?$")


def parse(html: str) -> list[Settlement]:
    soup = BeautifulSoup(html, "lxml")
    out: dict[str, Settlement] = {}
    for a in soup.find_all("a", href=LINK_RE):
        url = a["href"].rstrip("/") + "/"
        if url in out:
            continue
        # climb to the smallest ancestor that holds this post's Deadline box
        box = a
        for _ in range(6):
            box = box.parent
            if box is None:
                break
            if box.find(string=re.compile(r"^\s*Deadline\s*$")):
                break
        if box is None or not box.find(string=re.compile(r"^\s*Deadline\s*$")):
            continue
        # skip boxes that hold several posts (we climbed too far)
        if len({x["href"].rstrip("/") for x in box.find_all("a", href=LINK_RE)}) > 1:
            continue
        name_el = box.find(["h2", "h3", "h4"]) or a
        strs = strings(box)
        out[url] = Settlement(
            source=NAME,
            name=name_el.get_text(" ", strip=True),
            url=url,
            payout_text=value_after(strs, "settlement"),
            deadline_text=value_after(strs, "deadline"),
        )
    return list(out.values())


def fetch(f: Fetcher) -> list[Settlement]:
    out: dict[str, Settlement] = {}
    for page in range(1, MAX_PAGES + 1):
        r = f.get(URL if page == 1 else f"{URL}page/{page}/")
        if not r:
            break
        items = parse(r.text)
        new = [s for s in items if s.url not in out]
        if not new:
            break
        for s in new:
            out[s.url] = s
    return list(out.values())
