"""The findings, pinned, so a change that moves them has to say so."""

import functools

import pytest

from trolley import study
from trolley.sources import MONTHS, item_indices

A, B = MONTHS[0], MONTHS[-1]


@functools.lru_cache(maxsize=None)
def result():
    return study.run()


def rise(path, a=A, b=B):
    return path[b] / path[a] - 1


def test_the_thirds_rise_in_order():
    p = result()["paths"]
    assert rise(p["cheap"]) == pytest.approx(0.385, abs=0.0005)
    assert rise(p["middle"]) == pytest.approx(0.350, abs=0.0005)
    assert rise(p["dear"]) == pytest.approx(0.298, abs=0.0005)


def test_all_quotes_of_the_same_items_track_the_published_index():
    r = result()
    published = r["published"]
    assert rise(r["paths"]["all"]) == pytest.approx(published[B] / published[A] - 1, abs=0.003)
    assert rise(r["all_items"]) == pytest.approx(published[B] / published[A] - 1, abs=0.002)


def test_the_gap_is_the_shock_not_the_method():
    """In 2024, with food inflation back near 2%, the thirds move together."""
    p = result()["paths"]
    rises = [rise(p[t], "202401", "202412") for t in ("cheap", "middle", "dear")]
    assert max(rises) - min(rises) < 0.003
    assert rise(p["cheap"], "202201", "202212") - rise(p["dear"], "202201", "202212") > 0.03


def test_the_gap_is_not_about_pack_sizes():
    for paths in result()["by_size"].values():
        assert rise(paths["cheap"]) - rise(paths["dear"]) > 0.08


def test_splitting_the_whole_country_gives_the_same_answer():
    main, national = result()["paths"], result()["robust"]["national"]
    for t in ("cheap", "middle", "dear"):
        assert rise(national[t]) == pytest.approx(rise(main[t]), abs=0.005)


def test_the_trap_is_real_in_the_data_too():
    trap = result()["trap"]
    assert rise(trap["january"]["cheap"]) - rise(trap["january"]["dear"]) > 0.4
    assert rise(trap["this month"]["cheap"]) - rise(trap["this month"]["dear"]) < -0.25


def test_mixed_unit_items_are_the_ones_left_out():
    left = result()["left_out"]
    desc = result()["descriptions"]
    assert len(left) == 8
    assert all(" OR " in desc[i] or "/" in desc[i] for i in left)


def test_item_paths_chain_the_published_item_indices():
    """Each item's own path, rebuilt within each year, agrees with chaining what the ONS published."""
    published = item_indices()
    for item, path in result()["items"].items():
        jan = level = 100.0
        for month in MONTHS[1:]:
            x = published[month][item]
            if month.endswith("01"):
                jan = level = level * x.index / 100
                continue
            level = jan * x.index / 100
            if not x.imputed:
                assert path[month] == pytest.approx(level, abs=0.1), (item, month)
