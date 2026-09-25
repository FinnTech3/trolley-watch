"""Write the app's data, data/built/trolley.json, from the checked pipeline.

    PYTHONPATH=pipeline/src python3 -m trolley.build

Everything the app shows comes from here: the index for each third of the
shelf, the published food index beside it, each item's own path, and the
checks. The file also carries a worked example the app's tests must reproduce
to the penny, so the page and the write-up cannot drift apart.
"""

from __future__ import annotations

import json
import os
import sys

from . import indices, study, verify
from .names import EVERYDAY, GROUPS, NAMES
from .sources import MONTHS, ROOT

OUT = os.path.join(ROOT, "data", "built", "trolley.json")


def basket(ids: list[str], paths: dict, weights: dict[str, float], month: str) -> float:
    """What a January 2021 trolley of these items cost in `month`, January 2021 = 100.

    Each item's share of the trolley is its share of the CPI's 2021 weights
    among the items chosen: the ONS's estimate of how household spending
    divides between them.
    """
    total = sum(weights[i] for i in ids)
    return sum(weights[i] * paths[i][month] for i in ids) / total


def groups() -> dict[str, str]:
    out: dict[str, str] = {}
    for year in range(2021, 2025):
        for item, cls in verify.classification(year).items():
            out.setdefault(item, cls)
    return out


def main() -> int:
    r = study.run()
    items = r["items"]
    w2021 = indices.year_weights(2021)
    weights = {i: w2021.get(i, w2021.get(study.SPLICES.get(i, ""), 0.0)) for i in items}
    cls = groups()
    checks = {c.name: c for c in verify.run()}
    item_check = next(c for n, c in checks.items() if n.startswith("Every food item"))
    food_check = next(c for n, c in checks.items() if n.startswith("The CPI food index"))
    carli = next(c for n, c in checks.items() if n.startswith("Twin: the same quotes"))
    january = next(c for n, c in checks.items() if n.startswith("Twin: counting"))
    equal = next(c for n, c in checks.items() if n.startswith("Twin: the items weighted"))

    r2 = lambda x: round(x, 2)  # noqa: E731
    data = {
        "months": MONTHS,
        "published": [r["published"][m] for m in MONTHS],
        "thirds": {s: [r2(r["paths"][s][m]) for m in MONTHS] for s in study.SERIES},
        "trap": {name: {s: r2(p[s][MONTHS[-1]]) for s in ("cheap", "dear")} for name, p in r["trap"].items()},
        "groups": GROUPS,
        "items": [
            {"id": i, "name": NAMES[i], "desc": r["descriptions"][i], "group": cls[i],
             "weight": weights[i], "path": [r2(items[i][m]) for m in MONTHS]}
            for i in sorted(items, key=lambda i: (cls[i], NAMES[i]))
        ],
        "everyday": EVERYDAY,
        "left_out": len(r["left_out"]),
        "checks": {
            "item_months": item_check.detail["item_months"],
            "item_within": item_check.detail["within"],
            "item_exact": item_check.detail["exact"],
            "item_worst": round(item_check.detail["worst"][0], 4),
            "item_imputed": item_check.detail["imputed"],
            "carli_within": carli.detail["within"],
            "january_within": january.detail["within"],
            "food_months": len(MONTHS) - 1,
            "food_worst": round(food_check.detail["worst"][0], 3),
            "equal_worst": round(equal.detail["worst"][0], 3),
        },
    }
    # Worked from the rounded paths the app reads, so it can match exactly.
    stored = {x["id"]: dict(zip(MONTHS, x["path"])) for x in data["items"]}
    data["example"] = {"items": EVERYDAY, "december_2024": round(basket(EVERYDAY, stored, weights, MONTHS[-1]), 6)}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        f.write("\n")
    print(f"{OUT}: {os.path.getsize(OUT):,} bytes, {len(data['items'])} items")
    return 0


if __name__ == "__main__":
    sys.exit(main())
