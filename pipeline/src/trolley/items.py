"""What the ONS's item descriptions say about how an item is priced.

Splitting an item's prices into cheap and dear thirds only compares like with
like if the prices are for the same quantity. Most items are: a 750g loaf, a
kilo of carrots, a pint of milk. Some allow a size range ("olive oil, 500ml to
1 litre"), where a cheap price can partly mean a small bottle, and a few are
priced in two different units ("strawberries per kg or punnet"), where it can
mean a different unit altogether.

The mixed-unit items are left out of the cheap-and-dear comparison. The
size-range items stay in, and the study checks the gap is the same size with
and without them.
"""

from __future__ import annotations

import re

MIXED_UNITS = re.compile(r"KG OR|OR (PER )?KG|OR PUNNET|PUNNET OR|PACK/KG|KG/PACK|LOOSE OR")
SIZE_RANGE = re.compile(r"\d\s*(G|GM|GMS|KG|ML|MLS|L|LT|LTR|LITRE|PK|CL)?\s*-\s*\d|MAX \d")


def mixed_units(desc: str) -> bool:
    """Priced in two different units, so its prices are not comparable with each other."""
    return bool(MIXED_UNITS.search(desc))


def size_range(desc: str) -> bool:
    """Priced in one unit but allowing a range of sizes."""
    return not mixed_units(desc) and bool(SIZE_RANGE.search(desc))
