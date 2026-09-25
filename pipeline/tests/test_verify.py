"""The ONS's own numbers, rebuilt, and the twins that show the checks can fail."""

import functools

from trolley import verify


@functools.lru_cache(maxsize=None)
def results():
    return {r.name: r for r in verify.run()}


def by_prefix(prefix):
    return next(r for name, r in results().items() if name.startswith(prefix))


def test_items_are_food_and_nothing_else():
    assert by_prefix("Items numbered 21").passed


def test_every_item_index_rebuilds_from_its_quotes():
    r = by_prefix("Every food item index")
    assert r.passed, r.summary
    assert r.detail["item_months"] == 7715
    assert r.detail["worst"][0] < 0.017
    # most match to the three decimals the ONS publishes, not just within tolerance
    assert r.detail["exact"] / r.detail["item_months"] > 0.6


def test_imputed_items_are_reported_not_hidden():
    r = by_prefix("Every food item index")
    assert r.detail["imputed"] == 135
    assert r.detail["imputed_worst"][0] > verify.ITEM_TOLERANCE


def test_twin_arithmetic_mean_fails():
    r = by_prefix("Twin: the same quotes averaged")
    assert not r.passed
    assert r.detail["within"] < 100


def test_twin_worked_out_january_prices_fail():
    r = by_prefix("Twin: counting quotes without")
    assert not r.passed
    assert r.detail["within"] < r.detail["item_months"] / 2


def test_food_index_rebuilds_from_its_items():
    r = by_prefix("The CPI food index")
    assert r.passed, r.summary
    assert r.detail["worst"][0] < 0.11


def test_twin_equal_weights_fail():
    r = by_prefix("Twin: the items weighted equally")
    assert not r.passed
    assert r.detail["worst"][0] > 1
