"""classaction.org/settlements - one page with every open settlement as a card."""
from __future__ import annotations

from bs4 import BeautifulSoup

from ..http import Fetcher
from ..model import Settlement
from ._util import strings, value_after

NAME = "classaction.org"
URL = "https://www.classaction.org/settlements"


def parse(html: str) -> list[Settlement]:
    soup = BeautifulSoup(html, "lxml")
    out: list[Settlement] = []
    seen: set[str] = set()
    for card in soup.select("div.settlement-card[id]"):
        slug = card["id"]
        if slug in seen:
            continue
        seen.add(slug)
        a = card.select_one("a.js-settlement-link")
        if not a:
            continue
        name = (a.get("data-name") or a.get_text(" ", strip=True)).strip()
        strs = strings(card)
        # labels are split by <br>: "Settlement" "Payout" / "Deadline" / "Proof" "Required?"
        payout = value_after(strs, "payout")
        deadline = value_after(strs, "deadline")
        proof = value_after(strs, "required")
        p = card.select_one("p")
        out.append(
            Settlement(
                source=NAME,
                name=name,
                url=f"{URL}#{slug}",
                payout_text=payout,
                deadline_text=deadline,
                proof_text=proof,
                description=p.get_text(" ", strip=True) if p else "",
                official_url=a.get("href", ""),
            )
        )
    return out


def fetch(f: Fetcher) -> list[Settlement]:
    r = f.get(URL)
    return parse(r.text) if r else []
