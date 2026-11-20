from __future__ import annotations

from bs4 import Tag


def strings(tag: Tag) -> list[str]:
    return [" ".join(s.split()) for s in tag.stripped_strings if s.strip()]


def value_after(strs: list[str], *labels: str) -> str:
    """First string after the one matching any of `labels` (case-insensitive, ignores ':' and '?')."""
    wanted = {l.lower() for l in labels}
    for i, s in enumerate(strs):
        if s.lower().rstrip(":?").strip() in wanted and i + 1 < len(strs):
            return strs[i + 1]
    return ""
