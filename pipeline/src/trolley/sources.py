"""Where the committed sources live, and the loaders for them.

A price quote is one price one collector recorded for one item in one shop in
one month. The ONS's files carry about 45,000 of them a month for food and
non-alcoholic drinks. Each quote also carries its January price, the base the
year's index is measured from, and the weights the ONS gives its shop and its
stratum (a region, a shop type, or both).
"""

from __future__ import annotations

import csv
import functools
import io
import lzma
import os
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SOURCES = os.path.join(ROOT, "data", "sources")
RAW = os.path.join(ROOT, "data", "raw")

# January 2021 to December 2024: four whole years, the food price shock and
# the year after it. The price quotes go on to January 2026, but from February
# 2025 the ONS publishes its indices for new consumption segments that pool
# several items with weights it does not publish, so they cannot be rebuilt
# item by item. From February 2026 it prices groceries from supermarket scanner
# data and stops publishing food quotes at all.
MONTHS = [f"{y}{m:02d}" for y in range(2021, 2025) for m in range(1, 13)]


def is_food(item_id: str) -> bool:
    """Items numbered 21xxxx are exactly COICOP division 01, food and non-alcoholic beverages."""
    return item_id.startswith("21")


@dataclass(frozen=True, slots=True)
class Quote:
    item: str
    shop: str
    region: str
    cell: str               # the stratum the quote belongs to
    start: str              # the month this quote's series began
    stratum_weight: float
    shop_weight: float
    price: float
    base: float             # the same product's price in January
    indicator: str          # the collector's note: S sale, R recovery, C comparable replacement, N not comparable...
    valid_now: bool         # validated this month (codes 3 and 4), with a price this month and in January
    usable: bool            # counted in the index; see `usable` below

    @property
    def relative(self) -> float:
        return self.price / self.base


def valid_now(r: dict) -> bool:
    return r["VALIDITY"] in ("3", "4") and float(r["PRICE"] or 0) > 0 and float(r["BASE_PRICE"] or 0) > 0


def usable(r: dict) -> bool:
    """Whether the ONS counts this quote in the item's index.

    Validated this month and in January (codes 3 and 4), with a price in both.
    A series that started after January has a January price the ONS worked
    out rather than collected, and is not counted until the next January. The
    rule was found by rebuilding the published indices, and verify.py checks
    it still does. It also excludes every non-comparable replacement (N): none
    has a validated January price.
    """
    return valid_now(r) and r["BASE_VALIDITY"] in ("3", "4")


@functools.lru_cache(maxsize=None)
def _year(year: str) -> dict[str, tuple[Quote, ...]]:
    path = os.path.join(SOURCES, f"quotes_food_{year}.csv.xz")
    text = lzma.decompress(open(path, "rb").read()).decode("utf-8")
    months: dict[str, list[Quote]] = {}
    intern: dict[str, str] = {}
    for r in csv.DictReader(io.StringIO(text)):
        s = lambda k: intern.setdefault(r[k], r[k])  # noqa: E731 - the same few thousand strings repeat
        months.setdefault(r["QUOTE_DATE"], []).append(Quote(
            item=s("ITEM_ID"), shop=s("SHOP_CODE"), region=s("REGION"), cell=s("STRATUM_CELL"),
            start=s("START_DATE"), stratum_weight=float(r["STRATUM_WEIGHT"] or 0),
            shop_weight=float(r["SHOP_WEIGHT"] or 0), price=float(r["PRICE"] or 0),
            base=float(r["BASE_PRICE"] or 0), indicator=s("INDICATOR_BOX"), valid_now=valid_now(r), usable=usable(r)))
    return {m: tuple(q) for m, q in months.items()}


def quotes(month: str) -> tuple[Quote, ...]:
    """Every food quote published for a month, usable or not."""
    return _year(month[:4])[month]


@dataclass(frozen=True, slots=True)
class ItemIndex:
    item: str
    desc: str
    index: float | None     # the CPI item index, January = 100 (January: previous December = 100)
    weight: float           # the item's CPI weight, parts per thousand
    imputed: str            # the ONS's flag for items it imputed during the pandemic


@functools.lru_cache(maxsize=None)
def item_indices() -> dict[str, dict[str, ItemIndex]]:
    """The ONS's published index for every food item, by month and item."""
    out: dict[str, dict[str, ItemIndex]] = {}
    with open(os.path.join(SOURCES, "item_indices_food.csv"), newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["INDEX_DATE"], {})[r["ITEM_ID"]] = ItemIndex(
                item=r["ITEM_ID"], desc=r["ITEM_DESC"],
                index=float(r["ALL_GM_INDEX"]) if r["ALL_GM_INDEX"].strip() else None,
                weight=float(r["COICOP_WEIGHT"]), imputed=r["IMPUTATION_FLAG"])
    return out


@functools.lru_cache(maxsize=None)
def food_index() -> dict[str, float]:
    """The published CPI index for food and non-alcoholic beverages (D7BU), 2015 = 100, by month."""
    names = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
    out = {}
    with open(os.path.join(SOURCES, "ons_d7bu.csv"), newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) == 2 and len(row[0]) == 8 and row[0][4] == " " and row[0][5:] in names:
                out[f"{row[0][:4]}{names.index(row[0][5:]) + 1:02d}"] = float(row[1])
    return out
