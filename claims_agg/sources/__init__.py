from __future__ import annotations

from typing import Callable

from ..http import Fetcher
from ..model import Settlement
from . import classaction_org, claimdepot, theclassactionlawsuit, topclassactions

SOURCES: dict[str, Callable[[Fetcher], list[Settlement]]] = {
    classaction_org.NAME: classaction_org.fetch,
    claimdepot.NAME: claimdepot.fetch,
    topclassactions.NAME: topclassactions.fetch,
    theclassactionlawsuit.NAME: theclassactionlawsuit.fetch,
}

