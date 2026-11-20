"""Turn the free-text fields each site uses into comparable values."""
from __future__ import annotations

import re
from datetime import date, datetime

MONEY_RE = re.compile(
    r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*(k|m|b|thousand|million|billion)?\b", re.IGNORECASE
)
MULT = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "billion": 1e9}

# Per-person payouts above this are almost always fund totals, not what one person gets.
PER_PERSON_CAP = 100_000


def money_values(text: str) -> list[float]:
    vals = []
    for num, suf in MONEY_RE.findall(text or ""):
        v = float(num.replace(",", ""))
        if suf:
            v *= MULT[suf.lower()]
        vals.append(round(v, 2))
    return vals


def parse_payout(text: str) -> tuple[float | None, float | None]:
    """(min, max) per-person dollar figures in a payout string; (None, None) if none."""
    vals = [v for v in money_values(text) if 0 < v <= PER_PERSON_CAP]
    if vals and max(vals) < 10 and re.search(r"per (share|unit|option)", text or "", re.I):
        return None, None  # securities: total depends on how many shares you held
    if not vals:
        return None, None
    return min(vals), max(vals)


def fund_size(name: str) -> float | None:
    """Total fund from a title like '$16.1M Columbia University ...'."""
    vals = [v for v in money_values(name) if v >= 50_000]
    return max(vals) if vals else None


_FORMATS = ("%m/%d/%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y", "%b. %d, %Y", "%Y-%m-%d")


def parse_deadline(text: str, today: date | None = None) -> date | None:
    """Parse the deadline formats the sites use. Year-less dates ('Nov 20') get the next occurrence."""
    today = today or date.today()
    t = " ".join((text or "").replace("Sept ", "Sep ").split()).strip()
    if not t:
        return None
    for fmt in _FORMATS:
        try:
            return datetime.strptime(t, fmt).date()
        except ValueError:
            pass
    for fmt in ("%b %d", "%B %d"):
        try:
            d = datetime.strptime(t, fmt).date().replace(year=today.year)
        except ValueError:
            continue
        if d < today and (today - d).days > 31:
            d = d.replace(year=today.year + 1)
        return d
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", t)
    if m and m.group(1) != t:
        return parse_deadline(m.group(1), today)
    return None


def parse_proof(text: str, payout_text: str = "") -> bool | None:
    t = (text or "").strip().lower()
    if t in ("no", "none", "not required", "no proof"):
        return False
    if t in ("yes", "required"):
        return True
    return None


STOP = {
    "class", "action", "settlement", "settlements", "lawsuit", "the", "a", "an", "of", "and",
    "for", "in", "inc", "llc", "corp", "co", "claims", "claim", "case", "&", "-", "privacy",
    "data", "breach", "proposed", "s",
}


def name_tokens(name: str) -> frozenset[str]:
    n = MONEY_RE.sub(" ", name.lower())
    n = re.sub(r"\b\d+(\.\d+)?\s*(k|m|million|billion)\b", " ", n)
    n = re.sub(r"[^a-z0-9]+", " ", n)
    return frozenset(w for w in n.split() if w not in STOP and len(w) > 1)
