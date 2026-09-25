"""The app's data: what it carries, and that its worked example adds up."""

import json
import os

import pytest

from trolley.build import OUT


@pytest.fixture(scope="module")
def data():
    if not os.path.exists(OUT):
        pytest.skip("run python -m trolley.build first")
    with open(OUT, encoding="utf-8") as f:
        return json.load(f)


def test_shape(data):
    n = len(data["months"])
    assert n == 48 and data["months"][0] == "202101" and data["months"][-1] == "202412"
    assert len(data["published"]) == n
    for series in data["thirds"].values():
        assert len(series) == n and series[0] == 100
    for item in data["items"]:
        assert len(item["path"]) == n and item["path"][0] == 100
        assert item["weight"] > 0 and item["group"] in data["groups"]


def test_headline_numbers(data):
    rises = {k: round(v[-1] / v[0] * 100 - 100, 1) for k, v in data["thirds"].items()}
    assert rises == {"cheap": 38.5, "middle": 35.0, "dear": 29.8, "all": 33.5}
    assert data["published"][0] == 103.4 and data["published"][-1] == 137.8


def test_worked_example_adds_up(data):
    items = {x["id"]: x for x in data["items"]}
    ids = data["example"]["items"]
    total = sum(items[i]["weight"] for i in ids)
    value = sum(items[i]["weight"] * items[i]["path"][-1] for i in ids) / total
    assert value == pytest.approx(data["example"]["december_2024"], abs=1e-6)


def test_everyday_items_are_all_there(data):
    ids = {x["id"] for x in data["items"]}
    assert set(data["everyday"]) <= ids
