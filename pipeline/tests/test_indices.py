"""The index formulas, and the cheap-to-dear split, on prices where the answer is known."""

import math
import random

import pytest

from trolley import indices
from trolley.sources import Quote


def quote(price, base, cell="1", shop="1", shop_weight=1.0, stratum_weight=1.0, start="202101"):
    return Quote(item="210000", shop=shop, region=cell, cell=cell, start=start, stratum_weight=stratum_weight,
                 shop_weight=shop_weight, price=price, base=base, indicator="", valid_now=True, usable=True)


def test_jevons_is_the_shop_weighted_geometric_mean():
    qs = [quote(2.0, 1.0, shop_weight=3), quote(1.0, 1.0, shop_weight=1)]
    assert indices.jevons(qs) == pytest.approx(2 ** 0.75)
    assert indices.carli(qs) == pytest.approx(1.75)


def test_strata_are_averaged_arithmetically_by_stratum_weight():
    qs = [quote(1.2, 1.0, cell="a", stratum_weight=1), quote(1.5, 1.0, cell="b", stratum_weight=3)]
    assert indices.item_index(qs) == pytest.approx(100 * (1.2 + 3 * 1.5) / 4)


@pytest.mark.parametrize("n, expected", [
    (1, ["middle"]),
    (2, ["cheap", "dear"]),
    (3, ["cheap", "middle", "dear"]),
    (6, ["cheap", "cheap", "middle", "middle", "dear", "dear"]),
])
def test_thirds_by_rank(n, expected):
    assert [indices.tier_of(i, n) for i in range(n)] == expected


def test_split_does_not_depend_on_order():
    rng = random.Random(1)
    qs = [quote(round(rng.uniform(1, 3), 2), round(rng.uniform(1, 3), 2), shop=str(i)) for i in range(60)]
    shuffled = qs[:]
    rng.shuffle(shuffled)
    assert indices.split(qs) == indices.split(shuffled)


def market(rng, n, rise, cheap_extra=0.0, noise=0.12):
    """Products whose long-run price levels differ, each priced with a chance part in January and now.

    Every product's true price rises by `rise`; the cheapest third's by
    `cheap_extra` more. The chance part (promotions, a collector's pick) is
    the same size in both months.
    """
    qs = []
    for i in range(n):
        level = math.exp(rng.gauss(0, 0.4))
        true_rise = rise + (cheap_extra if level < math.exp(-0.4 * 0.43) else 0.0)
        base = level * math.exp(rng.gauss(0, noise))
        price = level * (1 + true_rise) * math.exp(rng.gauss(0, noise))
        qs.append(quote(price, base, shop=str(i)))
    return qs


def gap(qs, rank):
    t = indices.tier_indices(qs, rank)
    return t["cheap"] - t["dear"]


def test_ranking_on_january_price_invents_a_gap():
    """The trap: with no real difference, "cheap in January" still rises fastest."""
    qs = market(random.Random(7), 6000, rise=0.10)
    assert gap(qs, lambda q: q.base) > 6


def test_ranking_on_this_months_price_invents_the_opposite():
    qs = market(random.Random(7), 6000, rise=0.10)
    assert gap(qs, lambda q: q.price) < -6


def test_midpoint_ranking_finds_no_gap_when_there_is_none():
    qs = market(random.Random(7), 6000, rise=0.10)
    assert abs(gap(qs, indices.midpoint)) < 1


def test_midpoint_ranking_finds_a_real_gap_and_slightly_understates_it():
    """A true 10-point gap comes out at about 9: chance still puts a few products in the wrong third."""
    qs = market(random.Random(7), 6000, rise=0.10, cheap_extra=0.10)
    assert 7 < gap(qs, indices.midpoint) < 10
