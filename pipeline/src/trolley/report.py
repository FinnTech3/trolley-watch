"""Print every number the README quotes, in the order it quotes them.

    PYTHONPATH=pipeline/src python3 -m trolley.report

Refuses to print findings if a check has failed.
"""

from __future__ import annotations

import sys

from . import study, verify
from .names import NAMES
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
    print(line("the thirds", p, a, b))

    print("\nYear by year, January to December")
    for y in range(int(a[:4]), int(b[:4]) + 1):
        print(line(str(y), p, f"{y}01", f"{y}12"))
    print(line("Sep 2021 to Sep 2022", p, "202109", "202209"))

    print("\nThe same comparison, other ways")
    for name, paths in r["by_size"].items():
        print(line(f"items sold in {name}", paths, a, b))
    print(line("thirds of the whole UK", r["robust"]["national"], a, b))
    print("  the trap, ranking each quote on one month's price:")
    for name, paths in r["trap"].items():
        print(line(f"  on {name}'s price", paths, a, b))

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
