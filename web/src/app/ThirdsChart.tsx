import { pct } from "../lib/format";
import { type Third, THIRDS, rise } from "../lib/trolley";
import { useWidth } from "./hooks";

interface Props {
  months: string[];
  thirds: Record<Third, number[]>;
  official: number[];
  chosen: Third;
}

const NAME: Record<Third, string> = { cheap: "cheapest third", middle: "middle third", dear: "dearest third" };

/** The three thirds of the shelf and the official index, January 2021 = 100. */
export function ThirdsChart({ months, thirds, official, chosen }: Props) {
  const [ref, W] = useWidth<HTMLDivElement>();
  const narrow = W < 520;
  const H = narrow ? 260 : 300;
  const L = 34;
  const R = narrow ? 66 : 128;
  const T = 16;
  const B = H - 30;
  const lo = 95;
  const hi = 145;
  const x = (i: number) => L + (i / (months.length - 1)) * (W - L - R);
  const y = (v: number) => B - ((v - lo) / (hi - lo)) * (B - T);
  const line = (path: number[]) => path.map((v, i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = months.length - 1;

  // end labels, pushed apart so they never overlap
  const ends = [
    ...THIRDS.map((t) => ({ key: t, v: thirds[t][last]!, text: pct(rise(thirds[t])), name: NAME[t] })),
    { key: "official", v: official[last]!, text: pct(rise(official)), name: "official" },
  ].sort((a, b) => b.v - a.v);
  let prev = -Infinity;
  const placed = ends.map((e) => {
    const yy = Math.max(y(e.v), prev + (narrow ? 18 : 30));
    prev = yy;
    return { ...e, yy };
  });

  return (
    <div ref={ref}>
      <svg viewBox={`0 0 ${W} ${H}`} width={W} height={H} role="img" aria-labelledby="thirds-desc">
        <desc id="thirds-desc">
          {`Food prices by third of the shelf, January 2021 = 100, to December 2024: ${THIRDS.map((t) => `${NAME[t]} ${pct(rise(thirds[t]))}`).join(", ")}; the official food index ${pct(rise(official))}.`}
        </desc>
        {[100, 110, 120, 130, 140].map((v) => (
          <g key={v}>
            <line className={v === 100 ? "c-base" : "c-grid"} x1={L} x2={W - R} y1={y(v) + 0.5} y2={y(v) + 0.5} />
            <text className="c-tick" x={L - 6} y={y(v) + 4} textAnchor="end">
              {v}
            </text>
          </g>
        ))}
        {months.map((m, i) =>
          m.endsWith("01") ? (
            <text key={m} className="c-tick" x={x(i)} y={B + 20} textAnchor="start">
              {m.slice(0, 4)}
            </text>
          ) : null,
        )}
        <polyline points={line(official)} fill="none" className="c-official" strokeWidth={1.5} />
        {THIRDS.filter((t) => t !== chosen).map((t) => (
          <polyline key={t} points={line(thirds[t])} fill="none" className={`c-${t}`} strokeWidth={2} opacity={0.55} />
        ))}
        <polyline points={line(thirds[chosen])} fill="none" className={`c-${chosen}`} strokeWidth={3.2} />
        {placed.map((e) => (
          <g key={e.key}>
            <text
              className={`c-end ${e.key === "official" ? "c-end-official" : `c-end-${e.key}`}`}
              x={W - R + 8}
              y={e.yy + 4}
              fontWeight={e.key === chosen ? 700 : 500}
            >
              {e.text}
            </text>
            {!narrow && (
              <text className="c-note" x={W - R + 60} y={e.yy + 4}>
                {e.name}
              </text>
            )}
          </g>
        ))}
      </svg>
    </div>
  );
}
