"""Group the same settlement listed on several sites into one row."""
from __future__ import annotations

from datetime import date

from .classify import limited_states, topic
from .model import Merged, Settlement
from .normalize import fund_size, name_tokens, parse_deadline, parse_payout, parse_proof

# Source preference when fields disagree: classaction.org links straight to the official site.
PRIORITY = ["classaction.org", "claimdepot.com", "topclassactions.com", "theclassactionlawsuit.com"]


def _same(a: tuple[frozenset[str], date | None], b: tuple[frozenset[str], date | None]) -> bool:
    ta, da = a
    tb, db = b
    if not ta or not tb:
        return False
    if da and db and abs((da - db).days) > 3:
        return False
    common = len(ta & tb)
    if common < 1:
        return False
    overlap = common / min(len(ta), len(tb))
    if da and db:  # same deadline: one shared distinctive word is plenty
        return overlap >= 0.5
    return common >= 2 and overlap >= 0.8


def merge(items: list[Settlement], today: date | None = None) -> list[Merged]:
    today = today or date.today()
    keyed = [(s, name_tokens(s.name), parse_deadline(s.deadline_text, today)) for s in items]
    groups: list[list[tuple[Settlement, frozenset[str], date | None]]] = []
    for row in keyed:
        for g in groups:
            if any(_same((row[1], row[2]), (o[1], o[2])) for o in g):
                g.append(row)
                break
        else:
            groups.append([row])

    out: list[Merged] = []
    for g in groups:
        g.sort(key=lambda r: PRIORITY.index(r[0].source) if r[0].source in PRIORITY else 99)
        deadlines = [r[2] for r in g if r[2]]
        deadline = min(deadlines) if deadlines else None
        if deadline and deadline < today:
            continue  # expired
        mins, maxs = [], []
        payout_texts = []
        for s, _, _ in g:
            lo, hi = parse_payout(s.payout_text)
            if lo is not None:
                mins.append(lo)
                maxs.append(hi)
            if s.payout_text and s.payout_text not in payout_texts:
                payout_texts.append(s.payout_text)
        informative = [t for t in payout_texts if t.lower() not in ("varies", "tbd", "n/a")]
        proofs = [parse_proof(s.proof_text) for s, _, _ in g]
        proof = False if False in proofs else (True if True in proofs else None)
        names = [s.name for s, _, _ in g]
        out.append(
            Merged(
                name=min(names, key=len) if g[0][0].source != "classaction.org" else names[0],
                deadline=deadline,
                payout_text=" / ".join(informative) or (payout_texts[0] if payout_texts else ""),
                payout_min=min(mins) if mins else None,
                payout_max=max(maxs) if maxs else None,
                fund_size=next((f for f in (fund_size(n) for n in names) if f), None),
                proof_required=proof,
                description=next((s.description for s, _, _ in g if s.description), ""),
                category=next((s.category for s, _, _ in g if s.category), ""),
                official_url=next((s.official_url for s, _, _ in g if s.official_url), ""),
                sources={s.source: s.url for s, _, _ in g},
            )
        )
    for m in out:
        m.topic = topic(m.category, m.name, m.description)
        m.states = limited_states(m.name, m.description)
    out.sort(key=rank_key)
    return out


def rank_key(m: Merged):
    """Highest known payout first; no-proof before proof on ties; then soonest deadline."""
    return (
        -(m.payout_max or 0),
        {False: 0, None: 1, True: 2}[m.proof_required],
        m.deadline or date.max,
    )
