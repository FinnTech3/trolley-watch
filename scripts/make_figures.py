"""Draw the figures in docs/figures from the committed data.

    python3 scripts/make_figures.py

Every number comes from the same run the report prints, so a figure cannot
disagree with the text. CI regenerates them and fails on any difference. Each
figure comes in a light and a dark version, written as SVG directly: no
plotting library, nothing to install.
"""

from __future__ import annotations

import os
import sys
from xml.sax.saxutils import escape

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "pipeline", "src"))

from trolley.build import basket  # noqa: E402
from trolley import indices  # noqa: E402
from trolley.names import EVERYDAY, NAMES  # noqa: E402
from trolley.study import SPLICES, run  # noqa: E402

OUT = os.path.join(ROOT, "docs", "figures")
SANS = "'IBM Plex Sans', ui-sans-serif, system-ui, -apple-system, sans-serif"
MONO = "'IBM Plex Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

# Red for the cheapest third, blue for the dearest, grey between: red and blue
# stay distinct under protanopia and deuteranopia, and all three clear 3:1
# against both backgrounds.
LIGHT = {"bg": "#fbfaf7", "ink": "#111110", "dim": "#52514e", "muted": "#6b6a65",
         "grid": "#e6e4dc", "axis": "#c3c2b7", "rest": "#cfccc3",
         "cheap": "#d63f3e", "middle": "#86847c", "dear": "#2a78d6"}
DARK = {"bg": "#161614", "ink": "#f3f2ee", "dim": "#c3c2b7", "muted": "#9a988f",
        "grid": "#2a2a27", "axis": "#3d3d3a", "rest": "#4b4a46",
        "cheap": "#e66767", "middle": "#94928a", "dear": "#3987e5"}

W = 1120
LEFT = 64
TIERS = ("cheap", "middle", "dear")
LABEL = {"cheap": "cheapest third", "middle": "middle third", "dear": "dearest third"}


def pct(x: float, dp: int = 1) -> str:
    return f"{x:+.{dp}f}%"


class Svg:
    def __init__(self, h: int, p: dict, title: str, subtitle: str):
        self.p, self.h = p, h
        self.parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {h}" width="{W}" height="{h}" '
            f'role="img" aria-label="{escape(title)}">',
            f'<rect width="{W}" height="{h}" fill="{p["bg"]}"/>',
        ]
        self.text(LEFT, 44, title, 21, "ink", weight=600)
        self.text(LEFT, 70, subtitle, 14, "dim")

    def text(self, x, y, s, size=13, colour="ink", family=SANS, anchor="start", weight=400, halo=False):
        ring = f' stroke="{self.p["bg"]}" stroke-width="4" paint-order="stroke"' if halo else ""
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{self.p[colour]}" text-anchor="{anchor}"{ring}>{escape(s)}</text>')

    def line(self, x1, y1, x2, y2, colour="grid", width=1.0, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                          f'stroke="{self.p[colour]}" stroke-width="{width}"{extra}/>')

    def column(self, x, base, width, height, colour):
        """A column rounded at its data end and square at the baseline."""
        r = min(3.0, width / 2, abs(height))
        top = base - height
        self.parts.append(
            f'<path d="M{x:.1f},{base:.1f} V{top + r:.1f} Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} '
            f'H{x + width - r:.1f} Q{x + width:.1f},{top:.1f} {x + width:.1f},{top + r:.1f} V{base:.1f} Z" '
            f'fill="{self.p[colour]}"/>')

    def bar(self, x, y, length, thick, colour):
        """A horizontal bar rounded at its data end."""
        r = min(3.0, thick / 2, length)
        self.parts.append(
            f'<path d="M{x:.1f},{y:.1f} H{x + length - r:.1f} Q{x + length:.1f},{y:.1f} {x + length:.1f},{y + r:.1f} '
            f'V{y + thick - r:.1f} Q{x + length:.1f},{y + thick:.1f} {x + length - r:.1f},{y + thick:.1f} '
            f'H{x:.1f} Z" fill="{self.p[colour]}"/>')

    def dot(self, x, y, colour, r=5.0):
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r + 2:.1f}" fill="{self.p["bg"]}"/>')
        self.parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{self.p[colour]}"/>')

    def polyline(self, pts, colour, width=2.0, dash=None):
        d = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.parts.append(f'<polyline points="{d}" fill="none" stroke="{self.p[colour]}" '
                          f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round"{extra}/>')

    def footnote(self, s):
        self.text(LEFT, self.h - 24, s, 12, "muted")

    def svg(self) -> str:
        return "\n".join(self.parts + ["</svg>"]) + "\n"


def rise(path, a, b):
    return (path[b] / path[a] - 1) * 100


# --------------------------------------------------------------------------

def fig_thirds(r, p):
    months = list(r["paths"]["all"])
    a, b = months[0], months[-1]
    s = Svg(560, p, "Prices at the cheap end of the shelf rose fastest through the food price shock",
            "Food and non-alcoholic drink prices by third of the shelf, UK, January 2021 = 100")
    top, base = 110, 470
    x0, x1 = LEFT + 20, W - 190
    x = lambda i: x0 + i / (len(months) - 1) * (x1 - x0)
    lo, hi = 95, 145
    y = lambda v: base - (v - lo) / (hi - lo) * (base - top)
    for v in (100, 110, 120, 130, 140):
        s.line(x0, y(v), x1, y(v), "axis" if v == 100 else "grid")
        s.text(x0 - 10, y(v) + 4, str(v), 12, "muted", MONO, "end")
    for i, m in enumerate(months):
        if m.endswith("01"):
            s.text(x(i), base + 22, m[:4], 12, "muted", MONO, "start")
    pub = r["published"]
    s.polyline([(x(i), y(pub[m] / pub[a] * 100)) for i, m in enumerate(months)], "muted", 1.5, "4 4")
    ends = [(y(pub[b] / pub[a] * 100), "official", rise(pub, a, b))]
    for t in TIERS:
        path = r["paths"][t]
        s.polyline([(x(i), y(path[m])) for i, m in enumerate(months)], t, 2.6)
        ends.append((y(path[b]), t, rise(path, a, b)))
    # keep the end labels apart, in the order the lines end
    ends.sort()
    placed = []
    for yy, t, v in ends:
        yy = max(yy, placed[-1] + 34) if placed else yy
        placed.append(yy)
        colour = "muted" if t == "official" else t
        s.text(x1 + 12, yy - 2, pct(v), 15, colour, MONO, "start", 600)
        s.text(x1 + 12, yy + 14, "official food index" if t == "official" else LABEL[t], 12, "dim")
    s.footnote("Each third is the cheapest, middle or dearest third of the prices the ONS collected for each item, "
               "stacked with the CPI's weights. Dashed: the published CPI food index.")
    return s.svg()


def fig_years(r, p):
    s = Svg(540, p, "The gap opened in 2022 and 2023, and closed when inflation did",
            "Rise from January to December each year, by third of the shelf, UK food and non-alcoholic drinks")
    top, base = 120, 420
    years = ["2021", "2022", "2023", "2024"]
    slot = (W - LEFT - 60) / len(years)
    hi = 20
    y = lambda v: base - v / hi * (base - top)
    for v in (0, 5, 10, 15, 20):
        s.line(LEFT, y(v), W - 40, y(v), "axis" if v == 0 else "grid")
        s.text(LEFT - 10, y(v) + 4, f"{v}%", 12, "muted", MONO, "end")
    for k, yr in enumerate(years):
        cx = LEFT + slot * k + slot / 2
        for j, t in enumerate(TIERS):
            v = rise(r["paths"][t], f"{yr}01", f"{yr}12")
            xx = cx - 60 + j * 42
            s.column(xx, base, 34, base - y(v), t)
            s.text(xx + 17, y(v) - 8, f"{v:.1f}", 12, "ink", MONO, "middle", 600)
        s.text(cx, base + 26, yr, 14, "ink", MONO, "middle", 600)
    lx = LEFT
    for t in TIERS:
        s.parts.append(f'<rect x="{lx}" y="{base + 46}" width="12" height="12" rx="2" fill="{p[t]}"/>')
        s.text(lx + 18, base + 57, LABEL[t], 13, "dim")
        lx += 150
    s.footnote("In 2024, with food inflation back near 2%, the three thirds rose together: the method does not "
               "invent a gap when there is none.")
    return s.svg()


def fig_trap(r, p):
    months = list(r["paths"]["all"])
    a, b = months[0], months[-1]
    rows = [
        ("Ranked on January's price", r["trap"]["january"]),
        ("Ranked on this month's price", r["trap"]["this month"]),
        ("Ranked on both (what I use)", r["paths"]),
    ]
    s = Svg(410, p, "How you rank the prices decides the answer, unless you rank them fairly",
            "Rise from January 2021 to December 2024 of the cheapest and dearest thirds, three ways of "
            "deciding which third a price is in")
    x0, x1 = LEFT + 250, W - 60
    lo, hi = 0, 70
    x = lambda v: x0 + (v - lo) / (hi - lo) * (x1 - x0)
    top = 130
    for v in range(0, 71, 10):
        s.line(x(v), top - 20, x(v), top + 3 * 70 - 20, "grid")
        s.text(x(v), top + 3 * 70 + 2, f"{v}%", 12, "muted", MONO, "middle")
    for k, (label, paths) in enumerate(rows):
        yy = top + k * 70 + 10
        s.text(LEFT, yy + 5, label, 14, "ink", SANS, "start", 600 if k == 2 else 400)
        c, d = rise(paths["cheap"], a, b), rise(paths["dear"], a, b)
        s.line(x(min(c, d)), yy, x(max(c, d)), yy, "axis", 3)
        s.dot(x(c), yy, "cheap", 6)
        s.dot(x(d), yy, "dear", 6)
        s.text(x(c), yy - 14, f"cheap {c:.0f}%", 12, "cheap", MONO, "middle", 600)
        s.text(x(d), yy + 24, f"dear {d:.0f}%", 12, "dear", MONO, "middle", 600)
    s.footnote("A price that is low one month by chance tends to rise back. Ranking on either month alone turns "
               "that into a gap; ranking on the two together cancels it.")
    return s.svg()


def fig_everyday(r, p):
    months = list(r["paths"]["all"])
    a, b = months[0], months[-1]
    items = r["items"]
    w = indices.year_weights(2021)
    weights = {i: w.get(i, w.get(SPLICES.get(i, ""), 0.0)) for i in items}
    rows = sorted(((rise(items[i], a, b), i) for i in EVERYDAY), reverse=True)
    h = 130 + 19 * len(rows) + 60
    trolley = basket(EVERYDAY, items, weights, b) - 100
    pub = r["published"]
    food = rise(pub, a, b)
    above = sum(v > food for v, _ in rows)
    s = Svg(h, p, f"{above} of {len(rows)} everyday items rose more than food as a whole",
            "Rise in each item's price, January 2021 to December 2024, from the ONS's item indices")
    x0 = LEFT + 250
    hi = 160
    x = lambda v: x0 + max(v, 0) / hi * (W - 120 - x0)
    top = 110
    bottom = top + 19 * len(rows)
    s.line(x(food), top - 10, x(food), bottom, "ink", 1.2, "3 3")
    s.text(x(food) + 6, top - 14, f"all food {pct(food)}", 12, "ink", MONO, "start", 600)
    for k, (v, i) in enumerate(rows):
        yy = top + k * 19
        s.text(x0 - 12, yy + 11, NAMES[i], 12.5, "ink", SANS, "end")
        s.bar(x0, yy + 2, x(v) - x0, 12, "cheap" if v > food else "rest")
        s.text(x(v) + 8, yy + 12, f"{v:.0f}%", 12, "dim", MONO, "start", halo=True)
    s.footnote(f"Red: rose more than food as a whole. A trolley of all {len(rows)}, in the proportions the CPI weights "
               f"them, rose {trolley:.1f}%.")
    return s.svg()


FIGURES = {
    "thirds": fig_thirds,
    "years": fig_years,
    "trap": fig_trap,
    "everyday": fig_everyday,
}


def main() -> int:
    r = run()
    os.makedirs(OUT, exist_ok=True)
    for name, fig in FIGURES.items():
        for mode, palette in (("light", LIGHT), ("dark", DARK)):
            with open(os.path.join(OUT, f"{name}-{mode}.svg"), "w") as f:
                f.write(fig(r, palette))
    print(f"wrote {len(FIGURES) * 2} figures to docs/figures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
