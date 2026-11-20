"""Write the merged list as JSON, CSV and a self-contained, filterable HTML page."""
from __future__ import annotations

import csv
import html
import json
from datetime import datetime, timezone
from pathlib import Path

from .model import Merged

TEMPLATE = Path(__file__).with_name("template.html")


def write_all(rows: list[Merged], out_dir: Path, source_counts: dict[str, int]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = [r.to_json() for r in rows]
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    (out_dir / "settlements.json").write_text(
        json.dumps({"generated": generated, "sources": source_counts, "settlements": data}, indent=1)
    )
    with (out_dir / "settlements.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "deadline", "payout_min", "payout_max", "payout_text", "proof_required",
                    "fund_size", "category", "official_url", "sources", "description"])
        for r in rows:
            w.writerow([r.name, r.deadline or "", r.payout_min or "", r.payout_max or "", r.payout_text,
                        {True: "yes", False: "no", None: ""}[r.proof_required], r.fund_size or "",
                        r.category, r.official_url, " ".join(r.sources.values()), r.description])
    page = TEMPLATE.read_text()
    blob = json.dumps({"generated": generated, "sources": source_counts, "settlements": data})
    page = page.replace("__DATA__", blob.replace("</", "<\\/"))
    page = page.replace("__GENERATED__", html.escape(generated))
    (out_dir / "index.html").write_text(page)
