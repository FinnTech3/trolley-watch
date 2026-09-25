"""Read an Excel file without a spreadsheet library.

Two of the ONS files used here are .xlsx rather than CSV: the item indices for
February 2022 and the 2023 classification framework. An .xlsx is a zip archive
of XML, so the standard library is enough, and the package stays free of
dependencies.

The reader returns every sheet as a list of rows, each row a list of strings,
with empty cells as "". Numbers stay as the text the file stored them as.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile

_XLSX = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_XLSX_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def _column(ref: str) -> int:
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(path: str) -> dict[str, list[list[str]]]:
    z = zipfile.ZipFile(path)
    shared: list[str] = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(_XLSX + "si"):
            shared.append("".join(t.text or "" for t in si.iter(_XLSX + "t")))
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets = {r.get("Id"): r.get("Target", "") for r in rels}

    sheets: dict[str, list[list[str]]] = {}
    for sheet in workbook.iter(_XLSX + "sheet"):
        target = targets[sheet.get(_XLSX_REL + "id")].lstrip("/")
        if not target.startswith("xl/"):
            target = "xl/" + target
        rows: list[list[str]] = []
        for row in ET.fromstring(z.read(target)).iter(_XLSX + "row"):
            cells: dict[int, str] = {}
            for c in row.findall(_XLSX + "c"):
                v = c.find(_XLSX + "v")
                if v is not None:
                    text = v.text or ""
                    if c.get("t") == "s":
                        text = shared[int(text)]
                else:
                    inline = c.find(_XLSX + "is")
                    text = "".join(x.text or "" for x in inline.iter(_XLSX + "t")) if inline is not None else ""
                cells[_column(c.get("r", "A"))] = text
            if cells:
                width = max(cells) + 1
                rows.append([cells.get(i, "") for i in range(width)])
        sheets[sheet.get("name", "")] = rows
    return sheets
