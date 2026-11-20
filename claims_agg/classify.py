"""Tag each settlement with a topic and the US states it is limited to."""
from __future__ import annotations

import re

STATES = [
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware",
    "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
    "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi",
    "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico",
    "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania",
    "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming",
]
# Longest first so "West Virginia" wins over "Virginia".
_STATE_RE = re.compile(r"\b(" + "|".join(sorted(STATES, key=len, reverse=True)) + r")\b")
# Phrases where a state name does not limit who can claim.
_NOT_LIMIT = re.compile(r"Washington,? D\.?C\.?|Washington Nationals|University of \w+|Washington Post", re.I)
_LIMIT_HINT = re.compile(
    r"\b(in|of|from|resident[s]? of|residents|located in|worked in|lived in)\s+(the State of\s+)?$", re.I
)


def limited_states(name: str, description: str) -> list[str]:
    """States a settlement is limited to: '(California)' in the name, or 'in Illinois' / 'Illinois residents'
    in the description. Empty list = no state limit found (usually nationwide)."""
    found: set[str] = set()
    for m in re.finditer(r"\(([^)]+)\)", name):
        found |= set(_STATE_RE.findall(m.group(1)))
    desc = _NOT_LIMIT.sub(" ", description or "")
    for m in _STATE_RE.finditer(desc):
        before = desc[max(0, m.start() - 40):m.start()]
        after = desc[m.end():m.end() + 12].lower()
        if _LIMIT_HINT.search(before) or after.startswith((" resident", " consumer", " employee", " member")):
            found.add(m.group(1))
    return sorted(found)


TOPICS = {
    "privacy": ("Data Breach", "Privacy", "BIPA", "Health"),
    "vehicles": ("Automotive",),
    "shopping": ("Deceptive Pricing", "Consumer Protection", "Text Messages", "False Advertising",
                 "Antitrust", "Banking", "Fair Credit Reporting", "Debt Collection", "Fraud",
                 "Product Liability"),
    "jobs": ("Labor", "ERISA"),
    "investing": ("Securities",),
    "insurance": ("Insurance",),
    "housing": ("Housing",),
}
_KEYWORDS = [
    ("privacy", r"data breach|privacy|biometric|tracking|pixel|bipa"),
    ("vehicles", r"\b(ford|toyota|kia|hyundai|gm|ram trucks?|nissan|dodge|honda|jeep|chevrolet|chevy|"
                 r"subaru|tesla|bmw|vehicle|transmission|airbag|engine|brak|fuel pump)"),
    ("jobs", r"wage|labor|401\(k\)|retirement|job posting|benefits plan|vacation|background check|"
             r"faculty|employee|overtime|noncompete|pay transparency"),
    ("shopping", r"fees?\b|texts?\b|ticket|overdraft|atm|advertis|casino|games?\b|discount|products?|"
                 r"shingles|solar|insulation|antitrust|price|surcharge|auto-?renew|lending|tuition"),
    ("investing", r"securities|investor|stock|shares"),
    ("insurance", r"insurance|total loss"),
    ("housing", r"rent|apartment|housing|mortgage"),
]


def topic(category: str, name: str, description: str) -> str:
    for t, cats in TOPICS.items():
        if category in cats:
            return t
    text = f"{name} {category}".lower()
    for t, pat in _KEYWORDS:
        if re.search(pat, text):
            return t
    desc = (description or "").lower()
    for t, pat in _KEYWORDS:
        if re.search(pat, desc):
            return t
    return "other"
