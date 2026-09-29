import type React from "react";
import { type ReactNode, useMemo, useState } from "react";
import { type Item, type TrolleyFile, rise } from "../lib/trolley";
import { useWidth } from "./hooks";

interface Props {
  d: TrolleyFile;
  chosen: Set<string>;
  onToggle: (id: string) => void;
}

/** One of eight drawn shapes, so 43 items are one family rather than 43 pictures. */
type Shape = "tin" | "bottle" | "carton" | "bag" | "jar" | "box" | "round" | "tray";

// The ONS's own division of food. A group picks the shape its items come in.
const SHAPE: Record<string, Shape> = {
  "10101": "box",
  "10102": "tray",
  "10103": "tin",
  "10104": "carton",
  "10105": "bottle",
  "10106": "round",
  "10107": "bag",
  "10108": "jar",
  "10109": "jar",
  "10201": "box",
  "10202": "bottle",
};

const SIZE: Record<Shape, [w: number, h: number]> = {
  tin: [22, 26],
  bottle: [18, 44],
  carton: [22, 38],
  bag: [26, 32],
  jar: [22, 30],
  box: [26, 36],
  round: [24, 24],
  tray: [30, 20],
};

/** Each shape drawn once, sitting on the shelf line at y = 0. */
function draw(shape: Shape, w: number, h: number): ReactNode {
  const x = -w / 2;
  switch (shape) {
    case "tin":
      return (
        <>
          <rect x={x} y={-h} width={w} height={h} rx={2} />
          <rect className="lid" x={x} y={-h} width={w} height={4} rx={1.5} />
          <rect className="band" x={x} y={-h * 0.62} width={w} height={h * 0.3} />
        </>
      );
    case "bottle":
      return (
        <>
          <path
            d={`M${x},0 L${x},${-h * 0.55} Q${x},${-h * 0.72} ${x + w * 0.32},${-h * 0.8} L${x + w * 0.32},${-h} L${x + w * 0.68},${-h} L${x + w * 0.68},${-h * 0.8} Q${x + w},${-h * 0.72} ${x + w},${-h * 0.55} L${x + w},0 Z`}
          />
          <rect className="lid" x={x + w * 0.28} y={-h} width={w * 0.44} height={5} rx={1.5} />
          <rect className="band" x={x} y={-h * 0.4} width={w} height={h * 0.22} />
        </>
      );
    case "carton":
      return (
        <>
          <path d={`M${x},0 L${x},${-h * 0.82} L${x + w / 2},${-h} L${x + w},${-h * 0.82} L${x + w},0 Z`} />
          <rect className="band" x={x} y={-h * 0.55} width={w} height={h * 0.26} />
        </>
      );
    case "bag":
      return (
        <>
          <path d={`M${x},0 L${x + w * 0.1},${-h * 0.86} L${x + w * 0.9},${-h * 0.86} L${x + w},0 Z`} />
          <path
            className="lid"
            d={`M${x + w * 0.1},${-h * 0.86} L${x + w * 0.22},${-h} L${x + w * 0.78},${-h} L${x + w * 0.9},${-h * 0.86} Z`}
          />
        </>
      );
    case "jar":
      return (
        <>
          <rect x={x} y={-h * 0.84} width={w} height={h * 0.84} rx={3} />
          <rect className="lid" x={x + 1} y={-h} width={w - 2} height={h * 0.2} rx={2} />
          <rect className="band" x={x} y={-h * 0.5} width={w} height={h * 0.26} />
        </>
      );
    case "box":
      return (
        <>
          <rect x={x} y={-h} width={w} height={h} rx={1.5} />
          <rect className="band" x={x + 2} y={-h * 0.78} width={w - 4} height={h * 0.34} rx={1} />
        </>
      );
    case "round":
      return (
        <>
          <circle cx={0} cy={-h / 2} r={h / 2} />
          <path className="lid" d={`M0,${-h} q3,-4 6,-3`} fill="none" strokeWidth={2} />
        </>
      );
    case "tray":
      return (
        <>
          <rect x={x} y={-h} width={w} height={h} rx={3} />
          <rect className="lid" x={x + 2} y={-h + 2} width={w - 4} height={h * 0.42} rx={2} />
        </>
      );
  }
}

function monthName(ym: string): string {
  const y = ym.slice(0, 4);
  const m = Number(ym.slice(4, 6));
  return `${["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][m - 1]} ${y}`;
}

/**
 * The 43 everyday items on shelves, cheapest rise on the left, dearest on the
 * right. Each carries a tag with what it costs that month against January 2021,
 * and the month can be scrubbed. Tap an item to put it in the trolley.
 */
export function Shelf({ d, chosen, onToggle }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>(360);
  const [m, setM] = useState(d.months.length - 1);
  // One tab stop for the whole shelf, with the arrow keys moving between
  // items: forty-three separate stops would be a wall to tab through.
  const [cursor, setCursor] = useState(0);
  const items = useMemo(
    () => d.items.filter((i) => d.everyday.includes(i.id)).sort((a, b) => rise(a.path) - rise(b.path)),
    [d],
  );

  const perShelf = W < 520 ? 5 : W < 900 ? 7 : 9;
  const shelves = Math.ceil(items.length / perShelf);
  const L = 10;
  const R = 10;
  const slot = (W - L - R) / perShelf;
  const rowH = 96;
  const T = 30;
  const H = T + shelves * rowH + 26;
  const shelfY = (row: number) => T + row * rowH + 58;

  const at = (it: Item) => it.path[m]!;
  const dearest = items[items.length - 1]!;
  // How far along the shelf an item's rise sits, 0 to 1, by rank rather than
  // by size: one item ran away with it and would flatten everything else.
  const heat = (i: number) => i / (items.length - 1);

  return (
    <div ref={ref} className="shelf-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} className="shelf" role="group" aria-labelledby="shelf-desc">
        <desc id="shelf-desc">
          {`The ${items.length} everyday items, cheapest rise on the left. In ${monthName(d.months[m]!)} each one costs this much for every £100 it cost in January 2021, from ${Math.round(at(items[0]!))} for ${items[0]!.name.toLowerCase()} to ${Math.round(at(dearest))} for ${dearest.name.toLowerCase()}. ${chosen.size} are in the trolley.`}
        </desc>
        {Array.from({ length: shelves }, (_, row) => (
          <line key={row} className="board" x1={L} x2={W - R} y1={shelfY(row)} y2={shelfY(row)} />
        ))}
        {items.map((it, i) => {
          const row = Math.floor(i / perShelf);
          const cx = L + (i % perShelf) * slot + slot / 2;
          const shape = SHAPE[it.group] ?? "box";
          const [w, h] = SIZE[shape];
          const scale = Math.min(1, (slot - 10) / (w + 16));
          const picked = chosen.has(it.id);
          const price = at(it);
          return (
            <g
              key={it.id}
              className={picked ? "good picked" : "good"}
              style={{ "--heat": heat(i).toFixed(3) } as React.CSSProperties}
              transform={`translate(${cx},${shelfY(row)})`}
              role="button"
              tabIndex={i === cursor ? 0 : -1}
              aria-pressed={picked}
              aria-label={`${it.name}, ${Math.round(price)} for every £100 in January 2021. ${picked ? "In the trolley" : "Not in the trolley"}`}
              onFocus={() => setCursor(i)}
              onClick={() => onToggle(it.id)}
              onKeyDown={(e) => {
                const step: Record<string, number> = {
                  ArrowRight: 1,
                  ArrowLeft: -1,
                  ArrowDown: perShelf,
                  ArrowUp: -perShelf,
                  Home: -i,
                  End: items.length - 1 - i,
                };
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  onToggle(it.id);
                } else if (e.key in step) {
                  e.preventDefault();
                  const next = Math.min(items.length - 1, Math.max(0, i + step[e.key]!));
                  setCursor(next);
                  e.currentTarget.parentElement?.querySelectorAll<SVGGElement>("g.good")[next]?.focus();
                }
              }}
            >
              {/* one target covering the item and its tag: without it a tap in
                  the gap between them falls through to the background */}
              <rect className="hit" x={-slot / 2} y={-58} width={slot} height={90} />
              <g transform={`scale(${scale.toFixed(3)})`}>{draw(shape, w, h)}</g>
              <g className="tag" transform={`translate(0,${14})`}>
                <rect x={-19} y={-1} width={38} height={17} rx={3} />
                <line className="pin" x1={-19} x2={-19} y1={7.5} y2={7.5} />
                <text x={0} y={11.5} textAnchor="middle">
                  {Math.round(price)}
                </text>
              </g>
            </g>
          );
        })}
        <text className="c-note" x={L} y={16}>
          {W < 520
            ? `per £100 in Jan 2021 · ${monthName(d.months[m]!)}`
            : `what each costs for every £100 it cost in January 2021, ${monthName(d.months[m]!)}`}
        </text>
      </svg>

      <div className="scrub">
        <label htmlFor="month">Scrub the months</label>
        <input
          id="month"
          type="range"
          min={0}
          max={d.months.length - 1}
          value={m}
          onChange={(e) => setM(Number(e.target.value))}
          aria-valuetext={monthName(d.months[m]!)}
        />
        <div className="ends" aria-hidden="true">
          <span>{monthName(d.months[0]!)}</span>
          <span>{monthName(d.months[d.months.length - 1]!)}</span>
        </div>
      </div>
    </div>
  );
}
