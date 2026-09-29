import { gbp } from "../lib/format";
import { type TrolleyFile, official, pushedMost, rise, share, trolleyPath } from "../lib/trolley";

/** A share as a plain percentage: format's pct() prints a sign, wrong for "more than 79% of items". */
const plain = (x: number) => `${Math.round(x * 100)}%`;

interface Props {
  d: TrolleyFile;
  items: string[];
  onClear: () => void;
  onEveryday: () => void;
}

function month(ym: string): string {
  const y = ym.slice(0, 4);
  const m = Number(ym.slice(4, 6));
  return `${["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][m - 1]} ${y}`;
}

/**
 * The trolley as a till receipt: £100 of it in January 2021, what that same
 * shopping costs at the end, and the published food figure beside it. Every
 * number is the engine's, printed rather than charted.
 */
export function Receipt({ d, items, onClear, onEveryday }: Props) {
  const chosen = d.items.filter((x) => items.includes(x.id));
  const path = trolleyPath(d, items);
  const off = official(d);
  const last = d.months[d.months.length - 1]!;
  const mine = path.length ? path[path.length - 1]! : null;
  const food = off[off.length - 1]!;
  const top = pushedMost(d, items);

  return (
    <div className="receipt" aria-live="polite">
      <div className="head">
        <b>Your trolley</b>
        <span>{`${month(d.months[0]!)} to ${month(last)}`}</span>
      </div>

      {chosen.length === 0 ? (
        <p className="empty">
          Nothing in the trolley yet. Tap anything on the shelves, or{" "}
          <button type="button" className="link" onClick={onEveryday}>
            fill it with all 43
          </button>
          .
        </p>
      ) : (
        <>
          <ul className="lines">
            {chosen
              .slice()
              .sort((a, b) => rise(b.path) - rise(a.path))
              .map((x) => (
                <li key={x.id}>
                  <span className="what">{x.name}</span>
                  <span className="dots" aria-hidden="true" />
                  <span className="was">{gbp(x.path[x.path.length - 1]!)}</span>
                </li>
              ))}
          </ul>

          <dl className="total">
            <div>
              <dt>{`£100 of this trolley in ${month(d.months[0]!)} now costs`}</dt>
              <dd className="big">{gbp(mine!)}</dd>
            </div>
            <div>
              <dt>The published food and drink figure</dt>
              <dd>{gbp(food)}</dd>
            </div>
          </dl>

          <p className="verdict">
            {mine === null
              ? ""
              : Math.abs(mine - food) < 0.5
                ? `That is the same as food as a whole, to the pound.`
                : mine > food
                  ? `That is ${gbp(mine - food)} more than food as a whole, on every £100.`
                  : `That is ${gbp(food - mine)} less than food as a whole, on every £100.`}
            {mine !== null &&
              ` It rose by more than ${plain(share(d, rise(path)))} of the ${d.items.length} items priced here.`}
          </p>

          {top && (
            <p className="blame">
              {`${top.item.name} did most of it: ${plain(top.share)} of the whole rise, on its weight in the trolley.`}
            </p>
          )}

          <div className="actions">
            <button className="btn quiet" type="button" onClick={onEveryday}>
              All 43
            </button>
            <button className="btn quiet" type="button" onClick={onClear}>
              Empty it
            </button>
          </div>
        </>
      )}
    </div>
  );
}
