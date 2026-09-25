import { pct } from "../lib/format";
import { type Item, rise } from "../lib/trolley";
import { useWidth } from "./hooks";

interface Props {
  items: Item[];
  chosen: Set<string>;
  trolley: number | null;
  food: number;
}

/**
 * Every item's rise as a dot, stacked where they crowd, with the chosen ones
 * lit and the trolley and food as a whole marked: you among everything.
 */
export function ItemsStrip({ items, chosen, trolley, food }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const L = 12;
  const R = 12;
  const lo = -0.1;
  const hi = 1.6;
  const x = (v: number) => L + ((Math.min(hi, Math.max(lo, v)) - lo) / (hi - lo)) * (W - L - R);
  const r = W < 520 ? 3.2 : 3.8;
  const step = 2 * r + 1;

  // place each dot in the lowest row where it clears the dots already there
  const dots = items
    .map((it) => ({ it, v: rise(it.path) }))
    .sort((a, b) => a.v - b.v)
    .map((d) => ({ ...d, cx: x(d.v), row: 0 }));
  const rows: number[][] = [];
  for (const d of dots) {
    let row = 0;
    while (rows[row]?.some((cx) => Math.abs(cx - d.cx) < step)) row++;
    (rows[row] ??= []).push(d.cx);
    d.row = row;
  }
  const depth = Math.max(1, rows.length);
  const T = 44;
  const base = T + depth * step + 4;
  const H = base + 40;
  const cy = (row: number) => base - r - 2 - row * step;
  const ticks = [0, 0.5, 1, 1.5];
  const above = trolley === null || trolley >= food;

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="strip-desc">
        <desc id="strip-desc">
          {`The rise in each of ${items.length} items' prices, January 2021 to December 2024, from ${pct(Math.min(...dots.map((d) => d.v)), 0)} to ${pct(Math.max(...dots.map((d) => d.v)), 0)}. Food as a whole rose ${pct(food)}${trolley === null ? "." : `; your trolley ${pct(trolley)}.`}`}
        </desc>
        <line className="c-base" x1={L} x2={W - R} y1={base + 0.5} y2={base + 0.5} />
        {ticks.map((v) => (
          <text key={v} className="c-tick" x={x(v)} y={base + 18} textAnchor="middle">
            {v === 0 ? "0%" : `+${v * 100}%`}
          </text>
        ))}
        <line className="c-official-mark" x1={x(food)} x2={x(food)} y1={T - 4} y2={base} />
        {dots.map((d) => (
          <circle
            key={d.it.id}
            cx={d.cx}
            cy={cy(d.row)}
            r={chosen.has(d.it.id) ? r + 0.6 : r}
            className={chosen.has(d.it.id) ? "c-you" : "c-rest"}
          >
            <title>{`${d.it.name}: ${pct(d.v, 0)}`}</title>
          </circle>
        ))}
        {/* the two labels face away from each other, whichever side the trolley falls */}
        <text className="c-note" x={x(food) + (above ? -6 : 6)} y={T - 10} textAnchor={above ? "end" : "start"}>
          {`all food ${pct(food)}`}
        </text>
        {trolley !== null && (
          <>
            <line className="c-you-mark" x1={x(trolley)} x2={x(trolley)} y1={T - 26} y2={base} />
            <text
              className="c-strong c-halo"
              x={x(trolley) + (above ? 6 : -6)}
              y={T - 16}
              textAnchor={above ? "start" : "end"}
            >
              {`your trolley ${pct(trolley)}`}
            </text>
          </>
        )}
        <text className="c-note" x={W - R} y={base + 34} textAnchor="end">
          {`each dot is one of ${items.length} items`}
        </text>
      </svg>
    </div>
  );
}
