"""How the ONS turns price quotes into an item index, and into the food index.

An item is something like "white sliced loaf, branded, 750g". Each month a
collector prices it in a few hundred shops, and every quote carries the same
product's January price. The CPI's item index for the month is then:

  1. within each stratum (a region, a shop type, or both), the geometric mean
     of the quotes' price relatives (this month's price over January's), each
     quote weighted by its shop weight: the Jevons formula;
  2. across strata, the arithmetic mean of those, weighted by stratum weight.

That is the whole method for food, and verify.py shows it reproduces the
published item index for every item and month it is meant to.

The food index stacks the items: within a year, the weighted arithmetic mean
of the item indices, each relative to January; across years, each January is
linked to the December before it by the ONS's own January item indices.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence

from .sources import Quote, item_indices

Mean = Callable[[Sequence[Quote]], float]


def jevons(qs: Sequence[Quote]) -> float:
    """Shop-weighted geometric mean of the price relatives."""
    total = sum(q.shop_weight for q in qs)
    return math.exp(sum(q.shop_weight * math.log(q.relative) for q in qs) / total)


def carli(qs: Sequence[Quote]) -> float:
    """Shop-weighted arithmetic mean of the price relatives: the formula the CPI does not use."""
    return sum(q.shop_weight * q.relative for q in qs) / sum(q.shop_weight for q in qs)


def strata(qs: Iterable[Quote]) -> dict[str, list[Quote]]:
    out: dict[str, list[Quote]] = defaultdict(list)
    for q in qs:
        out[q.cell].append(q)
    return out


def item_index(qs: Iterable[Quote], mean: Mean = jevons) -> float:
    """An item's index, January = 100, from its usable quotes for one month."""
    num = den = 0.0
    for group in strata(qs).values():
        w = group[0].stratum_weight
        num += w * mean(group)
        den += w
    return 100 * num / den


def by_item(qs: Iterable[Quote], rule: Callable[[Quote], bool] = lambda q: q.usable) -> dict[str, list[Quote]]:
    out: dict[str, list[Quote]] = defaultdict(list)
    for q in qs:
        if rule(q):
            out[q.item].append(q)
    return out


# ---------------------------------------------------------------------------
# Cheap, middle and dear
# ---------------------------------------------------------------------------

TIERS = ("cheap", "middle", "dear")


def midpoint(q: Quote) -> float:
    """Where a quote sits, judged on January's price and this month's together.

    Ranking quotes on their January price alone builds in regression to the
    mean: a price that was low in January by chance (a promotion, say) tends to
    rise back, so "cheap in January" rises fastest even when nothing real is
    going on. Ranking on this month's price alone does the opposite. The
    geometric midpoint of the two cancels the effect when the chance part of a
    price is as large in one month as the other; the tests check that on
    made-up prices where the true answer is known.
    """
    return math.log(q.price) + math.log(q.base)


def tier_of(position: int, n: int) -> str:
    """Thirds by rank. With one quote it is the middle; with two, one cheap and one dear."""
    x = (position + 0.5) / n
    return TIERS[0] if x < 1 / 3 else TIERS[1] if x < 2 / 3 else TIERS[2]


def split(qs: Sequence[Quote], rank: Callable[[Quote], float] = midpoint) -> dict[str, list[Quote]]:
    """Split an item's quotes into thirds within each stratum, cheapest first.

    Within the stratum, so each region and shop type keeps its own cheap end
    and the ONS's stratum weights still apply. Ties are broken on the shop,
    region and series, so the split never depends on file order.
    """
    out: dict[str, list[Quote]] = {t: [] for t in TIERS}
    for group in strata(qs).values():
        ordered = sorted(group, key=lambda q: (rank(q), q.shop, q.region, q.start, q.price))
        for i, q in enumerate(ordered):
            out[tier_of(i, len(ordered))].append(q)
    return out


def tier_indices(qs: Sequence[Quote], rank: Callable[[Quote], float] = midpoint) -> dict[str, float]:
    """An item's index for each third, and for all its quotes, January = 100."""
    parts = split(qs, rank)
    out = {t: item_index(parts[t]) for t in TIERS if parts[t]}
    out["all"] = item_index(qs)
    return out


# ---------------------------------------------------------------------------
# From items to food
# ---------------------------------------------------------------------------

def year_weights(year: int) -> dict[str, float]:
    """The CPI weights for a year's items, as the February to December files carry them.

    January's file still carries the previous year's weights, because its
    index links the old year to the new one.
    """
    return {i: x.weight for i, x in item_indices()[f"{year}02"].items()}


def january_link(year: int) -> float:
    """The food index for January over the December before it, from the ONS's item indices.

    January item indices are published relative to the previous December.
    They are combined with the new year's weights.
    """
    jan = item_indices()[f"{year}01"]
    w = year_weights(year)
    items = [i for i in w if i in jan and jan[i].index is not None]
    return sum(w[i] * jan[i].index for i in items) / sum(w[i] for i in items) / 100


def chain(months: Sequence[str], within: Callable[[str], dict[str, float]], start: float = 100.0,
          weights: Callable[[int], dict[str, float]] = year_weights) -> dict[str, float]:
    """A food index from item indices.

    `within(month)` gives each item's index for a month from February to
    December, relative to that year's January = 100. Items without one that
    month drop out and the rest are reweighted.
    """
    level = {months[0]: start}
    for prev, month in zip(months, months[1:]):
        year = int(month[:4])
        if month.endswith("01"):
            level[month] = level[prev] * january_link(year)
            continue
        w = weights(year)
        idx = within(month)
        items = [i for i in w if i in idx]
        level[month] = level[f"{year}01"] * sum(w[i] * idx[i] for i in items) / sum(w[i] for i in items) / 100
    return level
