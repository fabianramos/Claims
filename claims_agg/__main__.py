"""Usage: python -m claims_agg [--out docs] [--only SOURCE ...]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .http import Blocked, Fetcher
from .merge import merge
from .report import write_all
from .sources import SOURCES


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Aggregate open class action settlements.")
    ap.add_argument("--out", default="docs", help="output folder (default: docs)")
    ap.add_argument("--only", nargs="*", choices=list(SOURCES), help="limit to these sources")
    ap.add_argument("--delay", type=float, default=1.5, help="seconds between requests to one site")
    args = ap.parse_args(argv)

    f = Fetcher(delay=args.delay)
    items, counts, failed = [], {}, []
    for name, fetch in SOURCES.items():
        if args.only and name not in args.only:
            continue
        try:
            got = fetch(f)
        except Blocked as e:
            print(f"[{name}] BLOCKED: {e}", file=sys.stderr)
            failed.append(name)
            continue
        except Exception as e:  # one broken site should not sink the rest
            print(f"[{name}] FAILED: {e}", file=sys.stderr)
            failed.append(name)
            continue
        print(f"[{name}] {len(got)} open settlements", file=sys.stderr)
        if not got:
            failed.append(name)
        counts[name] = len(got)
        items += got

    rows = merge(items)
    write_all(rows, Path(args.out), counts)
    print(f"{len(rows)} unique open settlements -> {args.out}/index.html", file=sys.stderr)
    if failed:
        print(f"WARNING: no results from {', '.join(failed)}", file=sys.stderr)
    # fail only when nothing at all came back, so one blocked site does not stop the daily update
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
