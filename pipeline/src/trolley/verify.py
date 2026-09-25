"""Rebuild the ONS's own numbers before measuring anything new.

Two checks, each with a twin that has to fail:

1. Every food item's published index, February to December of 2021 to 2024,
   rebuilt from the price quotes. The ONS publishes indices to three decimal
   places; a rebuild has to land within 0.02 of an index point. Items the ONS
   flagged as partly or fully imputed during the pandemic are reported but not
   gated, because their published values were not made from these quotes
   alone. Two twins must fail: one averages the same quotes arithmetically
   (the Carli formula), the other also counts series that began after January,
   whose January price the ONS worked out rather than collected.

2. The published CPI index for food and non-alcoholic beverages (D7BU),
   rebuilt from the ONS's item indices and weights, every month from February
   2021 to December 2024 within 0.15 of an index point. It is published to one
   decimal place, so rounding alone accounts for 0.05. The twin weights every
   item equally and must fail.

Nothing in study.py runs unless both pass.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import csv
import os

from . import indices
from .sheets import read_xlsx
from .sources import MONTHS, SOURCES, food_index, is_food, item_indices, quotes

ITEM_TOLERANCE = 0.02
FOOD_TOLERANCE = 0.15


@dataclass
class Result:
    name: str
    passed: bool
    summary: str
    detail: dict = field(default_factory=dict)


def rebuilt_items(month: str, mean: indices.Mean = indices.jevons, rule=lambda q: q.usable) -> dict[str, float]:
    return {i: indices.item_index(qs, mean) for i, qs in indices.by_item(quotes(month), rule).items()}


def check_items(mean: indices.Mean = indices.jevons, name: str = "Every food item index, rebuilt from its quotes",
                rule=lambda q: q.usable) -> Result:
    gaps: list[tuple[float, str, str]] = []
    imputed: list[tuple[float, str, str]] = []
    unpublished = 0
    for month in MONTHS:
        if month.endswith("01"):
            continue
        published = item_indices()[month]
        for item, value in rebuilt_items(month, mean, rule).items():
            pub = published.get(item)
            if pub is None or pub.index is None:
                unpublished += 1
                continue
            gap = (abs(value - pub.index), month, item)
            (imputed if pub.imputed else gaps).append(gap)
    worst = max(gaps)
    exact = sum(g < 0.0005 for g, _, _ in gaps)
    within = sum(g <= ITEM_TOLERANCE for g, _, _ in gaps)
    passed = within == len(gaps)
    return Result(
        name, passed,
        f"{within:,} of {len(gaps):,} item-months within {ITEM_TOLERANCE} "
        f"({exact:,} to the published three decimals); worst {worst[0]:.4f}, item {worst[2]} in {worst[1]}",
        {"item_months": len(gaps), "within": within, "exact": exact, "worst": worst,
         "imputed": len(imputed), "imputed_worst": max(imputed) if imputed else None,
         "unpublished": unpublished})


def check_items_carli() -> Result:
    """The twin: the same quotes, averaged the wrong way."""
    return check_items(indices.carli, "Twin: the same quotes averaged arithmetically")


def check_items_with_worked_out_january() -> Result:
    """The twin: also count series whose January price the ONS worked out rather than collected."""
    return check_items(name="Twin: counting quotes without a collected January price", rule=lambda q: q.valid_now)


def published_within(month: str) -> dict[str, float]:
    return {i: x.index for i, x in item_indices()[month].items() if x.index is not None}


def check_food(weights=indices.year_weights, name: str = "The CPI food index, rebuilt from its items") -> Result:
    pub = food_index()
    mine = indices.chain(MONTHS, published_within, start=pub[MONTHS[0]], weights=weights)
    gaps = [(abs(mine[m] - pub[m]), m) for m in MONTHS[1:]]
    worst = max(gaps)
    passed = worst[0] <= FOOD_TOLERANCE
    return Result(
        name, passed,
        f"{sum(g <= FOOD_TOLERANCE for g, _ in gaps)} of {len(gaps)} months within {FOOD_TOLERANCE} "
        f"of the published index; worst {worst[0]:.3f} in {worst[1]}",
        {"worst": worst, "mine": mine, "published": {m: pub[m] for m in MONTHS}})


def check_food_unweighted() -> Result:
    """The twin: every item counted equally."""
    equal = lambda year: {i: 1.0 for i in indices.year_weights(year)}  # noqa: E731
    return check_food(equal, "Twin: the items weighted equally")


def classification(year: int) -> dict[str, str]:
    """Item to COICOP class for the items in the CPI during a year, from the ONS's framework file.

    The 2021 and 2023 files are Excel (the 2021 one despite its .csv address);
    2022 has no header row. Each row: item, class, subclass, start, end.
    """
    path = next(os.path.join(SOURCES, f) for f in sorted(os.listdir(SOURCES))
                if f.startswith(f"cpi_classification_{year}"))
    if path.endswith(".xlsx"):
        rows = next(iter(read_xlsx(path).values()))
    else:
        with open(path, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
    out = {}
    for r in rows:
        if len(r) < 5 or not r[0].strip().isdigit():
            continue
        item, cls, start, end = r[0].strip(), r[1].strip(), r[3].strip(), r[4].strip()
        if start <= f"{year}12" and (end == "999999" or end >= f"{year}01"):
            out[item] = cls
    return out


def check_classification() -> Result:
    """Items numbered 21xxxx are exactly the CPI's division 01, food and non-alcoholic beverages."""
    wrong = []
    for year in range(2021, 2025):
        for item, cls in classification(year).items():
            in_division = cls[:-4] == "1"      # class 10102 is 01.1.2; 110101 is 11.1.1
            if in_division != is_food(item):
                wrong.append((year, item, cls))
    return Result("Items numbered 21 are exactly food and non-alcoholic drinks", not wrong,
                  "every year 2021 to 2024" if not wrong else f"{len(wrong)} items disagree", {"wrong": wrong})


def run() -> list[Result]:
    return [check_classification(), check_items(), check_items_carli(), check_items_with_worked_out_january(),
            check_food(), check_food_unweighted()]


def gate() -> list[Result]:
    """The two checks that must pass, or nothing downstream means anything."""
    results = [check_classification(), check_items(), check_food()]
    failed = [r for r in results if not r.passed]
    if failed:
        raise SystemExit("verification failed: " + "; ".join(f"{r.name}: {r.summary}" for r in failed))
    return results
