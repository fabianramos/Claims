from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date


@dataclass
class Settlement:
    """One settlement as listed by one source site."""

    source: str
    name: str
    url: str  # the source site's page (or the official site if that is all the source gives)
    payout_text: str = ""
    deadline_text: str = ""
    proof_text: str = ""  # raw "proof required" value if the source has one
    description: str = ""
    category: str = ""
    official_url: str = ""  # official settlement / claim-form website, when known


@dataclass
class Merged:
    """A settlement after merging the same case across sources."""

    name: str
    deadline: date | None
    payout_text: str
    payout_min: float | None  # smallest per-person dollar figure mentioned
    payout_max: float | None  # largest per-person dollar figure mentioned
    fund_size: float | None  # total settlement fund, when the title says it
    proof_required: bool | None  # None = unknown
    description: str
    category: str
    official_url: str
    sources: dict[str, str] = field(default_factory=dict)  # source name -> url
    topic: str = "other"  # privacy, vehicles, shopping, jobs, investing, insurance, housing, other
    states: list[str] = field(default_factory=list)  # states it is limited to; empty = no limit found

    def to_json(self) -> dict:
        d = asdict(self)
        d["deadline"] = self.deadline.isoformat() if self.deadline else None
        return d
