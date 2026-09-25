"""Did the cheapest groceries rise faster than the dearest?

For every food item, every month, the quotes are split into the cheapest
third, the middle third and the dearest third of the prices collected (within
each region and shop type, ranked on the midpoint of January's price and this
month's; see indices.midpoint for why). Each third gets its own index by the
ONS's own method, and the thirds are stacked into food indices with the CPI's
weights, exactly as the published food index is.

Two things are shared or left out:

- Between December and January the ONS refreshes its sample and publishes no
  January prices for the outgoing one, so quotes cannot be followed across the
  new year. Every third of an item takes that item's published January
  change. The gap between the thirds is measured over the other 44 of the 47
  months, and if anything understated.
- Items priced in two different units (per kilo or per punnet, say) are left
  out of the comparison, because their thirds would partly sort by unit.

An item's own thirds are too noisy to report one by one: with a few dozen
quotes in each and products coming and going, a single item's cheap third can
come out below its dear third one year and far above it the next. Stacked
across a hundred and fifty items the noise averages out, so the thirds are
only ever reported for food as a whole or for large groups of items.
"""

from __future__ import annotations

import functools
from collections.abc import Callable

from . import indices, items as item_kinds, verify
from .sources import MONTHS, Quote, food_index, item_indices, quotes

SERIES = ("cheap", "middle", "dear", "all")


def _national(qs: list[Quote]) -> dict[str, float]:
    """Thirds of the whole country's quotes rather than of each stratum's; each third still stratified."""
    ordered = sorted(qs, key=lambda q: (indices.midpoint(q), q.shop, q.region, q.start, q.price))
    parts: dict[str, list[Quote]] = {t: [] for t in indices.TIERS}
    for i, q in enumerate(ordered):
        parts[indices.tier_of(i, len(ordered))].append(q)
    out = {t: indices.item_index(p) for t, p in parts.items() if p}
    out["all"] = indices.item_index(qs)
    return out


# How quotes are ranked into thirds. Only "midpoint" and "national" are fair;
# the other two show the regression-to-the-mean trap in the real data.
RANKS: dict[str, Callable[[list[Quote]], dict[str, float]]] = {
    "midpoint": lambda qs: indices.tier_indices(qs, indices.midpoint),
    "national": _national,
    "january": lambda qs: indices.tier_indices(qs, lambda q: q.base),
    "this month": lambda qs: indices.tier_indices(qs, lambda q: q.price),
}


@functools.lru_cache(maxsize=None)
def tier_items(month: str, rank: str = "midpoint") -> dict[str, dict[str, float]]:
    """Each item's index for each third this month, January = 100."""
    return {item: RANKS[rank](qs) for item, qs in indices.by_item(quotes(month)).items()}


@functools.lru_cache(maxsize=None)
def descriptions() -> dict[str, str]:
    """Each item's description, the latest the ONS used."""
    out = {}
    for month in MONTHS:
        for item, x in item_indices()[month].items():
            out[item] = x.desc
    return out


def comparable(item: str) -> bool:
    return not item_kinds.mixed_units(descriptions().get(item, ""))


def food_paths(rank: str = "midpoint", keep: Callable[[str], bool] = comparable) -> dict[str, dict[str, float]]:
    """A food index for each third and for all quotes of the same items, January 2021 = 100."""
    weights = lambda year: {i: w for i, w in indices.year_weights(year).items() if keep(i)}  # noqa: E731
    out = {}
    for s in SERIES:
        within = lambda m, s=s: {i: t[s] for i, t in tier_items(m, rank).items() if s in t and keep(i)}  # noqa: E731
        out[s] = indices.chain(MONTHS, within, weights=weights)
    return out


def change(path: dict[str, float], start: str, end: str) -> float:
    return path[end] / path[start] - 1


@functools.lru_cache(maxsize=None)
def item_paths() -> dict[str, dict[str, float]]:
    """Each item's own index, all quotes, January 2021 = 100, for items priced in every month.

    Within each year this is the item index rebuilt from its quotes, which
    verify.py shows matches the published one; across years it takes the
    published January change.
    """
    out = {}
    published = item_indices()
    for item in published[MONTHS[0]]:
        level = {MONTHS[0]: 100.0}
        for prev, month in zip(MONTHS, MONTHS[1:]):
            if month.endswith("01"):
                link = published.get(month, {}).get(item)
                if link is None or link.index is None:
                    break
                level[month] = level[prev] * link.index / 100
                continue
            t = tier_items(month).get(item)
            if t is None:
                break
            level[month] = level[f"{month[:4]}01"] * t["all"] / 100
        else:
            out[item] = level
    return out


def contributions(start: str = MONTHS[0], end: str = MONTHS[-1]) -> list[tuple[str, float, float]]:
    """(item, its change, its share of the rise), for items priced throughout, largest share first.

    Each item's share uses its 2021 CPI weight and its own price change, the
    way a fixed 2021 basket would count it.
    """
    paths = item_paths()
    w = indices.year_weights(int(start[:4]))
    rises = {i: p[end] / p[start] - 1 for i, p in paths.items() if i in w}
    total = sum(w[i] * r for i, r in rises.items())
    return sorted(((i, r, w[i] * r / total) for i, r in rises.items()), key=lambda x: -x[2])


def run() -> dict:
    checks = verify.gate()
    start, end = MONTHS[0], MONTHS[-1]
    desc = descriptions()
    fixed = lambda i: comparable(i) and not item_kinds.size_range(desc.get(i, ""))  # noqa: E731
    ranged = lambda i: item_kinds.size_range(desc.get(i, ""))  # noqa: E731
    return {
        "checks": checks,
        "start": start,
        "end": end,
        "paths": food_paths(),
        "published": {m: food_index()[m] for m in MONTHS},
        "all_items": food_paths(keep=lambda i: True)["all"],
        "left_out": sorted(i for i in desc if not comparable(i)),
        "by_size": {"one size or per kilo": food_paths(keep=fixed), "a range of sizes": food_paths(keep=ranged)},
        "robust": {"national": food_paths("national")},
        "trap": {"january": food_paths("january"), "this month": food_paths("this month")},
        "items": item_paths(),
        "descriptions": desc,
        "contributions": contributions(),
    }
