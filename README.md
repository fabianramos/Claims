# Claims - open settlements finder

Pulls every **open** class action settlement from several listing sites, merges duplicates
(the same case listed on two or three sites becomes one row), drops expired ones, and ranks them
by payout so you can see which claims are worth filing.

| Source | How it's read |
|---|---|
| [classaction.org/settlements](https://www.classaction.org/settlements) | single page; gives payout, deadline, proof-required and the **official claim site** |
| [claimdepot.com/settlements](https://www.claimdepot.com/settlements) | all pages, "Open for Claims" only; its no-proof list marks proof = no |
| [topclassactions.com open settlements](https://topclassactions.com/category/lawsuit-settlements/open-lawsuit-settlements/) | all pages. **Currently blocked:** the site serves a Cloudflare bot check to scripts, so the run skips it with a warning |
| [theclassactionlawsuit.com/settlements](https://www.theclassactionlawsuit.com/settlements/?stage=open) | "Claims open" stage, all pages |

## Use it

Open **`docs/index.html`** in a browser. It works offline: the data is built into the page.

- **Sort** by biggest possible payout, biggest base payout (the amount you get without receipts),
  soonest deadline, or total fund size.
- **Filter** by "No proof needed", "Has a dollar amount", source, or search (company, product, state...).
- Mark each one **★ Shortlist**, **✓ Filed** or **Not me**. The marks are saved in your browser
  only, and the header adds up the base payouts of what you've filed.

The same data is in `docs/settlements.csv` (spreadsheet) and `docs/settlements.json`.

## Phone app

`app/index.html` is the phone-first version, published as a private claude.ai page:
https://claude.ai/artifact/TnMXy5fUfWZ982LBdq7wA9 (add it to your home screen). It loads
`settlements.json` published next to it, and syncs Shortlist / Filed / Not me marks to your account
so phone and computer match. The published list is a snapshot: ask Claude to republish it with a
fresh `docs/settlements.json` to update it.

## Refresh the list

```
pip install -e .
python -m claims_agg            # writes docs/index.html, settlements.csv, settlements.json
python -m claims_agg --only classaction.org claimdepot.com
```

It waits 1.5 s between requests to the same site (`--delay` to change). A full run takes about 40 s.

`.github/workflows/update.yml` runs this every day on GitHub and commits the new `docs/`. Turn on
GitHub Pages (Settings > Pages > Deploy from branch > `main` / `docs`) to get the page at a URL.

## How ranking works

- Dollar amounts are pulled from each site's payout text. Figures over $100,000 are treated as
  fund totals, not per-person payouts. `payout_min` is the smallest per-person figure (usually the
  flat cash option) and `payout_max` the largest (usually "up to", which needs documented losses).
- Default order: highest `payout_max`, then no-proof before proof-required, then soonest deadline.
  "Varies" settlements have no number and sort to the bottom of that view.
- Two listings are the same case when their names share their distinctive words and their
  deadlines are within 3 days of each other.

## Tests

```
pip install -e ".[test]" && pytest
```

The payout and deadline figures are what the listing sites publish. File only for settlements
you qualify for, and always through the official settlement website.
