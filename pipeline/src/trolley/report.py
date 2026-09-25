"""Print every number the README quotes, in the order it quotes them.

    PYTHONPATH=pipeline/src python3 -m trolley.report

Refuses to print findings if a check has failed.
"""

from __future__ import annotations

import sys

from . import items as item_kinds, study, verify
from .names import NAMES
from .sources import quotes
from .study import change


def pct(x: float) -> str:
    return f"{x:+.1%}"


def month(m: str) -> str:
    names = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
             "October", "November", "December"]
    return f"{names[int(m[4:]) - 1]} {m[:4]}"


def line(label: str, paths: dict, a: str, b: str) -> str:
    parts = ", ".join(f"{s} {pct(change(paths[s], a, b))}" for s in study.SERIES)
    return f"  {label:<24} {parts}"


def main() -> int:
    print("Verification")
    for r in verify.run():
        twin = r.name.startswith("Twin")
        ok = r.passed != twin
        print(f"  [{'pass' if ok else 'FAIL'}] {r.name}: {r.summary}"
              + (" (a twin, so failing is the pass)" if twin else ""))
        if not ok:
            print("\nA check did not behave; nothing below would mean anything.", file=sys.stderr)
            return 1

    r = study.run()
    a, b = r["start"], r["end"]
    pub = r["published"]
    p = r["paths"]
    print(f"\nFood and non-alcoholic drinks, {month(a)} to {month(b)}")
    print(f"  published CPI food index: {pct(pub[b] / pub[a] - 1)}")
    print(f"  rebuilt, every item: {pct(change(r['all_items'], a, b))}")
    print(f"  left out of the thirds (priced in two units): {len(r['left_out'])} items: "
          + "; ".join(r["descriptions"][i] for i in r["left_out"]))
    desc_all = r["descriptions"]
    print(f"  share of the 2022 food weight: priced in two units "
          f"{study.weight_share(lambda i: not study.comparable(i)):.1%}, sold in a range of sizes "
          f"{study.weight_share(lambda i: item_kinds.size_range(desc_all.get(i, ''))):.1%}")
    print(line("the thirds", p, a, b))

    months = list(p["all"])
    for s in ("cheap", "dear"):
        rate, m = max((p[s][months[i]] / p[s][months[i - 12]] - 1, months[i]) for i in range(12, len(months)))
        print(f"  {s} third's fastest twelve months: {pct(rate)} in the year to {month(m)}")
    print(f"  the cheapest third against the dearest: {p['cheap'][b] / p['dear'][b] - 1:+.1%} since {month(a)}")
    counted = sum(q.usable for m in months if not m.endswith("01") for q in quotes(m))
    print(f"  prices in the extracts: {sum(len(quotes(m)) for m in months):,}; counted in an index, "
          f"February to December: {counted:,}")

    print("\nYear by year, January to December")
    for y in range(int(a[:4]), int(b[:4]) + 1):
        print(line(str(y), p, f"{y}01", f"{y}12"))
    print(line("Sep 2021 to Sep 2022", p, "202109", "202209"))

    spread = [change(p[t], f"{b[:4]}01", b) for t in ("cheap", "middle", "dear")]
    print(f"  spread between the thirds in {b[:4]}: {max(spread) - min(spread):.2%}")
    cereal = study.item_thirds("210213")
    print("  one item's thirds, too noisy to report item by item, breakfast cereal (ONS item 1): "
          + ", ".join(f"{t} {pct(v)}" for t, v in cereal.items()))

    print("\nThe same comparison, other ways")
    for name, paths in r["by_size"].items():
        print(line(f"items sold in {name}", paths, a, b))
    print(line("thirds of the whole UK", r["robust"]["national"], a, b))
    print("  the trap, ranking each quote on one month's price:")
    for name, paths in r["trap"].items():
        print(line(f"  on {name}'s price", paths, a, b))
        print(line(f"  on {name}'s price, 2021", paths, "202101", "202112"))
    print("  price levels instead of the same products, January to December:")
    for y in range(int(a[:4]), int(b[:4]) + 1):
        print(f"    {y}: {pct(study.price_levels(y))}, against {pct(change(p['all'], f'{y}01', f'{y}12'))} "
              f"following the same products")

    items = r["items"]
    desc = {i: f"{NAMES[i].lower()}" for i in items}
    print(f"\nItems priced in every month: {len(items)}")
    rises = sorted(((it[b] / it[a] - 1, i) for i, it in items.items()), reverse=True)
    print("  rose most: " + "; ".join(f"{desc[i]} {pct(x)}" for x, i in rises[:6]))
    print("  rose least: " + "; ".join(f"{desc[i]} {pct(x)}" for x, i in rises[-4:]))
    print("  largest shares of the rise (2021 weights): "
          + "; ".join(f"{desc[i]} {s:.1%}" for i, _, s in r["contributions"][:6]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
