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
import math
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


def price_levels(year: int) -> float:
    """The rejected alternative: compare the prices on offer, not the same products.

    For each item, the geometric mean of every usable price in December over
    that of every price in January, stacked with the year's weights. It has no
    regression to the mean, because no quote is followed, but it moves
    whenever the mix of products priced changes.
    """
    w = {i: x for i, x in indices.year_weights(year).items() if comparable(i)}
    jan = indices.by_item(quotes(f"{year}01"), lambda q: q.valid_now)
    dec = indices.by_item(quotes(f"{year}12"))
    num = den = 0.0
    for item, weight in w.items():
        if item in jan and item in dec:
            g = lambda qs: math.exp(sum(math.log(q.price) for q in qs) / len(qs))  # noqa: E731
            num += weight * g(dec[item]) / g(jan[item])
            den += weight
    return num / den - 1


def item_thirds(item: str) -> dict[str, float]:
    """One item's thirds, chained over the whole period: the numbers too noisy to report item by item."""
    published = item_indices()
    level = {t: 100.0 for t in indices.TIERS}
    jan = dict(level)
    for month in MONTHS[1:]:
        if month.endswith("01"):
            link = published[month][item].index / 100
            level = {t: v * link for t, v in level.items()}
            jan = dict(level)
        else:
            t = tier_items(month)[item]
            level = {k: jan[k] * t[k] / 100 for k in indices.TIERS}
    return {t: v / 100 - 1 for t, v in level.items()}


def weight_share(keep: Callable[[str], bool], year: int = 2022) -> float:
    w = indices.year_weights(year)
    return sum(v for i, v in w.items() if keep(i)) / sum(w.values())


def change(path: dict[str, float], start: str, end: str) -> float:
    return path[end] / path[start] - 1


# Items the ONS re-coded during the period, new code: old code. Each pair is
# the same product under a new description, judged from the descriptions; the
# old item's path runs to the January the new one starts from, which is how the
# CPI itself chains its annual basket changes.
SPLICES = {
    "211604": "211602",   # eggs per dozen, from February 2022: medium eggs before
    "212309": "212399",   # new potatoes, February 2022
    "212310": "212360",   # old white potatoes, February 2022
    "212311": "212361",   # baking potatoes, February 2022
    "211410": "211407",   # dairy spread or margarine, February 2023
    "212736": "212731",   # melon, February 2023
    "212737": "212728",   # pineapple, February 2023
    "210707": "210703",   # pork chops, February 2024
    "212537": "212527",   # pre-packed salad, February 2024
}


def _chain_published(item: str, start: str) -> dict[str, float]:
    """An item's published index chained from `start` (a January) = 100, for as long as it runs."""
    published = item_indices()
    level = {start: 100.0}
    prev = start
    for month in MONTHS[MONTHS.index(start) + 1:]:
        x = published.get(month, {}).get(item)
        if x is None or x.index is None:
            break
        base = level[prev] if month.endswith("01") else level[f"{month[:4]}01"]
        level[month] = base * x.index / 100
        prev = month
    return level


@functools.lru_cache(maxsize=None)
def item_paths() -> dict[str, dict[str, float]]:
    """Each item's price path, January 2021 = 100, for items priced to December 2024.

    This is the ONS's own item index, chained: February to December relative
    to January, each January relative to the December before. verify.py shows
    the same numbers come back from the quotes wherever the ONS priced the
    item from quotes; a few items, potatoes in 2021 among them, were priced
    centrally and have no quotes to rebuild them from. Items new in the 2021
    basket start from January 2021 prices like everything else.
    """
    published = item_indices()
    out = {}
    for item in published[MONTHS[1]]:
        p = _chain_published(item, MONTHS[0])
        if MONTHS[-1] in p:
            out[item] = p
    for new, old in SPLICES.items():
        before = _chain_published(old, MONTHS[0])
        first = next(m for m in MONTHS if m.endswith("02") and new in published.get(m, {}))
        link = f"{first[:4]}01"
        after = _chain_published(new, link)
        if link in before and MONTHS[-1] in after:
            out[new] = {**{m: v for m, v in before.items() if m <= link},
                        **{m: before[link] * v / 100 for m, v in after.items()}}
    return out


def contributions(start: str = MONTHS[0], end: str = MONTHS[-1]) -> list[tuple[str, float, float]]:
    """(item, its change, its share of the rise), for items priced throughout, largest share first.

    Each item's share uses its 2021 CPI weight and its own price change, the
    way a fixed 2021 basket would count it.
    """
    paths = item_paths()
    w = indices.year_weights(int(start[:4]))
    weight = {i: w.get(i, w.get(SPLICES.get(i, ""), 0.0)) for i in paths}
    rises = {i: p[end] / p[start] - 1 for i, p in paths.items() if weight[i]}
    total = sum(weight[i] * r for i, r in rises.items())
    return sorted(((i, r, weight[i] * r / total) for i, r in rises.items()), key=lambda x: -x[2])


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
