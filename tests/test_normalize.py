from datetime import date

from claims_agg.merge import merge
from claims_agg.model import Settlement
from claims_agg.normalize import fund_size, parse_deadline, parse_payout, parse_proof

TODAY = date(2026, 11, 20)


def test_payout_ranges():
    assert parse_payout("Up to $5,000 for documented losses or a cash payment of $100") == (100, 5000)
    assert parse_payout("$375 – $4,500") == (375, 4500)
    assert parse_payout("Varies") == (None, None)
    assert parse_payout("$229.33 per share") == (229.33, 229.33)
    # fund totals are not per-person payouts
    assert parse_payout("$2,000 to $750,000") == (2000, 2000)


def test_fund_size():
    assert fund_size("$16.1M Columbia University data breach class action settlement") == 16_100_000
    assert fund_size("Blank Rome LLP $991,508 Data Breach") == 991_508
    assert fund_size("iPhone - Siri") is None


def test_deadlines():
    assert parse_deadline("11/27/26", TODAY) == date(2026, 11, 27)
    assert parse_deadline("03/26/2027", TODAY) == date(2027, 3, 26)
    assert parse_deadline("November 29, 2026", TODAY) == date(2026, 11, 29)
    assert parse_deadline("Mar 31, 2027", TODAY) == date(2027, 3, 31)
    assert parse_deadline("Dec 29", TODAY) == date(2026, 12, 29)
    assert parse_deadline("Jan 5", TODAY) == date(2027, 1, 5)
    assert parse_deadline("Varies", TODAY) is None


def test_proof():
    assert parse_proof("No") is False
    assert parse_proof("Yes") is True
    assert parse_proof("N/A") is None


def test_merge_same_case_across_sites():
    items = [
        Settlement("classaction.org", "Columbia University - Data Breach", "a", "Up to $8,500",
                   "1/21/27", "No", official_url="https://official.example"),
        Settlement("topclassactions.com", "$16.1M Columbia University data breach class action settlement",
                   "b", "Up to $8,500", "01/21/2027"),
        Settlement("claimdepot.com", "Columbia Gas Overcharge Settlement", "c", "$50", "March 3, 2027"),
    ]
    rows = merge(items, TODAY)
    assert len(rows) == 2
    col = next(r for r in rows if "University" in r.name)
    assert set(col.sources) == {"classaction.org", "topclassactions.com"}
    assert col.proof_required is False
    assert col.fund_size == 16_100_000
    assert col.official_url == "https://official.example"
    assert rows[0] is col  # ranked first: bigger payout


def test_merge_drops_expired():
    rows = merge([Settlement("x", "Old Co", "u", "$10", "11/01/26")], TODAY)
    assert rows == []
