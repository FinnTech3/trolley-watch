"""Download the ONS files this project uses and cut them down to food.

    PYTHONPATH=pipeline/src python -m trolley.fetch [--from DIR]

Each month the ONS publishes every price its collectors recorded for the CPI,
about 140,000 rows and 13 MB, and the index it built for each item. Only the
food and non-alcoholic drink rows are used here, so the committed files keep
those rows and the columns the indices need, compressed. The originals are
fetched into data/raw (not committed) and checked against the SHA-256 in
data/sources/originals.csv before anything is cut from them, so a fresh clone
can rebuild the extracts and confirm they came from the same files.

With --from, the originals are read from a directory instead of downloaded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import lzma
import os
import sys
import urllib.request

from .sheets import read_xlsx
from .sources import MONTHS, RAW, SOURCES, is_food

BASE = ("https://www.ons.gov.uk/file?uri=/economy/inflationandpriceindices/datasets/"
        "consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes/")

# The columns of the price quote files that the indices use, in their order.
QUOTE_COLUMNS = [
    "QUOTE_DATE", "ITEM_ID", "SHOP_CODE", "REGION", "SHOP_TYPE", "STRATUM_TYPE", "STRATUM_CELL",
    "STRATUM_WEIGHT", "SHOP_WEIGHT", "PRICE", "BASE_PRICE", "VALIDITY", "BASE_VALIDITY",
    "INDICATOR_BOX", "START_DATE", "END_DATE",
]
INDEX_COLUMNS = ["INDEX_DATE", "ITEM_ID", "ITEM_DESC", "ALL_GM_INDEX", "COICOP_WEIGHT", "IMPUTATION_FLAG"]


def manifest() -> list[dict]:
    with open(os.path.join(SOURCES, "originals.csv"), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def get(entry: dict, source_dir: str | None) -> str:
    name = entry["file"] or os.path.basename(entry["path"])
    local = os.path.join(RAW, name)
    if not os.path.exists(local):
        os.makedirs(RAW, exist_ok=True)
        if source_dir:
            with open(os.path.join(source_dir, name), "rb") as src, open(local, "wb") as dst:
                dst.write(src.read())
        else:
            url = entry["path"] if entry["path"].startswith("https://") else BASE + entry["path"]
            with urllib.request.urlopen(url, timeout=120) as r, open(local, "wb") as dst:
                dst.write(r.read())
    digest = sha256(local)
    if digest != entry["sha256"]:
        raise SystemExit(f"{name}: SHA-256 {digest} is not the {entry['sha256']} recorded in originals.csv")
    return local


def _tidy(cell: str) -> str:
    """Excel stores 99.846 as 99.846000000000004; write it the way the CSV months do."""
    if "." in cell and len(cell) > 12:
        try:
            return repr(float(cell))
        except ValueError:
            pass
    return cell


def _rows(path: str) -> list[dict]:
    """Every row of a CSV or the first sheet of an .xlsx, keyed by upper-case column name."""
    if path.endswith(".xlsx"):
        rows = next(iter(read_xlsx(path).values()))
        head = [h.strip().upper() for h in rows[0]]
        return [dict(zip(head, [_tidy(c) for c in r] + [""] * (len(head) - len(r)))) for r in rows[1:] if any(r)]
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [{k.strip().upper(): v for k, v in r.items()} for r in csv.DictReader(f)]


def write_xz(path: str, header: list[str], rows: list[list[str]]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    with open(path, "wb") as f:
        f.write(lzma.compress(buf.getvalue().encode("utf-8"), preset=9))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="source_dir", help="read the originals from this directory")
    args = parser.parse_args()

    entries = manifest()
    by_kind: dict[tuple[str, str], dict] = {(e["kind"], e["month"]): e for e in entries}

    quotes: dict[str, list[list[str]]] = {}
    for month in MONTHS:
        for r in _rows(get(by_kind[("quotes", month)], args.source_dir)):
            if is_food(r["ITEM_ID"]):
                quotes.setdefault(month[:4], []).append([r[c] for c in QUOTE_COLUMNS])
    for year, rows in quotes.items():
        write_xz(os.path.join(SOURCES, f"quotes_food_{year}.csv.xz"), QUOTE_COLUMNS, rows)
        print(f"quotes_food_{year}.csv.xz: {len(rows):,} quotes")

    index_rows: list[list[str]] = []
    for month in MONTHS:
        for r in _rows(get(by_kind[("item_indices", month)], args.source_dir)):
            if is_food(r["ITEM_ID"]):
                flag = (r.get("IMPUTATION_FLAG") or r.get("IMPUTATION_FLAGS") or "").strip()
                index_rows.append([month, r["ITEM_ID"], r["ITEM_DESC"].strip(), r["ALL_GM_INDEX"],
                                   r["COICOP_WEIGHT"], flag])
    with open(os.path.join(SOURCES, "item_indices_food.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(INDEX_COLUMNS)
        w.writerows(index_rows)
    print(f"item_indices_food.csv: {len(index_rows):,} item-months")

    for e in entries:
        if e["kind"] in ("classification", "series"):
            local = get(e, args.source_dir)
            with open(local, "rb") as src, open(os.path.join(SOURCES, e["file"]), "wb") as dst:
                dst.write(src.read())
            print(f"{e['file']}: copied as downloaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
