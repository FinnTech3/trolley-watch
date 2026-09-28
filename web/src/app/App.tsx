import { useEffect, useMemo, useState } from "react";
import { gbp, month, pct } from "../lib/format";
import {
  type Third,
  type TrolleyFile,
  official,
  pushedMost,
  readChoice,
  rise,
  trolleyPath,
  writeChoice,
} from "../lib/trolley";
import { ItemsStrip } from "./ItemsStrip";
import { ShareCard } from "./ShareCard";
import { ThirdsChart } from "./ThirdsChart";
import { useCountUp } from "./hooks";

const REPO = "https://github.com/FinnTech3/trolley-watch";
const PORTFOLIO = "https://finn-lakin-portfolio.netlify.app/";

const WHERE: Record<Third, string> = {
  cheap: "the cheap end",
  middle: "the middle",
  dear: "the dear end",
};
const THIRD_NAME: Record<Third, string> = {
  cheap: "The cheapest third of the shelf",
  middle: "The middle third of the shelf",
  dear: "The dearest third of the shelf",
};
// the dark-theme colours, for the picture
const CARD_COLOUR: Record<Third, string> = { cheap: "#e66767", middle: "#b5b3aa", dear: "#3987e5" };

function readThird(search: string): Third {
  const t = new URLSearchParams(search).get("s");
  return t === "middle" || t === "dear" ? t : "cheap";
}

function useTheme() {
  const [theme, setTheme] = useState<string | undefined>(() => document.documentElement.dataset.theme);
  const systemDark = typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
  const dark = theme ? theme === "dark" : systemDark;
  function toggle() {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Private windows may refuse; the choice then lasts for this visit only.
    }
    setTheme(next);
  }
  return { dark, toggle };
}

/** The fastest twelve months in a path, and the month they ended. */
function fastestYear(path: number[], months: string[]): { rate: number; month: string } {
  let best = { rate: -Infinity, month: months[12]! };
  for (let i = 12; i < path.length; i++) {
    const rate = path[i]! / path[i - 12]! - 1;
    if (rate > best.rate) best = { rate, month: months[i]! };
  }
  return best;
}

export function App() {
  const [d, setD] = useState<TrolleyFile | null>(null);
  const [failed, setFailed] = useState(false);
  const [third, setThird] = useState<Third>(() => readThird(location.search));
  const [items, setItems] = useState<string[] | null>(null);
  const theme = useTheme();

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}data/trolley.json`)
      .then((r) => r.json() as Promise<TrolleyFile>)
      .then((file) => {
        setItems(readChoice(location.search, file).items);
        setD(file);
      })
      .catch(() => setFailed(true));
  }, []);

  useEffect(() => {
    if (!d || !items) return;
    history.replaceState(null, "", `${location.pathname}${writeChoice({ third, items }, d.everyday)}`);
  }, [d, third, items]);

  return (
    <div className="wrap">
      <header>
        <div className="mark">
          <span className="ladder" aria-hidden="true">
            {[16, 12, 8].map((h, i) => (
              <i key={i} className={i === 0 ? "d" : undefined} style={{ height: h }} />
            ))}
          </span>
          <b>Trolley watch</b>
          <small>whose food inflation?</small>
        </div>
        <button
          className="toggle"
          type="button"
          onClick={theme.toggle}
          aria-label={`Switch to ${theme.dark ? "light" : "dark"} theme`}
        >
          {theme.dark ? "Light" : "Dark"}
        </button>
      </header>

      <main>
        <div className="hero">
          <h1>Did your end of the shelf rise faster than food inflation?</h1>
          <p className="lede">
            Official food inflation, January 2021 to December 2024, was 33.3%. I rebuilt it from the 2.2 million prices
            the ONS's collectors wrote down, then split every item's prices into the cheapest, middle and dearest third.
          </p>
          <div className="controls">
            <div className="field">
              <span id="shelf">Where on the shelf do you usually buy?</span>
              <div className="segmented" role="group" aria-labelledby="shelf">
                {(
                  [
                    ["cheap", "The cheapest"],
                    ["middle", "The middle"],
                    ["dear", "The dearest"],
                  ] as [Third, string][]
                ).map(([t, text]) => (
                  <button key={t} type="button" aria-pressed={third === t} onClick={() => setThird(t)}>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={d ? "answer" : "answer skeleton"} aria-live="polite">
          {failed ? (
            <p>The data did not load. Refresh the page to try again.</p>
          ) : d ? (
            <Answer d={d} third={third} />
          ) : (
            <p>Loading 2.2 million prices, cut down to one small file</p>
          )}
        </div>

        {d && items && <Sections d={d} third={third} items={items} setItems={setItems} />}

        {d && items && (
          <aside className="signoff">
            <p>
              I built this because "switch to the budget range" kept getting repeated as if it still worked as well as
              it used to, and nobody had actually checked. If your own trolley told you something worth knowing, I've
              got more like it at <a href={PORTFOLIO}>finn-lakin-portfolio.netlify.app</a>.
            </p>
          </aside>
        )}
      </main>

      <footer>
        <p>
          Sources: ONS consumer price inflation item indices and price quotes, January 2021 to December 2024; ONS CPI
          index for food and non-alcoholic beverages (D7BU). Open Government Licence v3.0.
        </p>
        <p>
          A third of the prices collected is not a third of what is sold, and the cheap third mixes cheaper products
          with cheaper shops. Items priced both by the kilo and by the pack are left out of the thirds. The run stops at
          December 2024, the last month whose indices can be rebuilt from the quotes.
        </p>
        <p>
          Built by Finn Lakin. The method, the code and every check are at{" "}
          <a href={REPO}>github.com/FinnTech3/trolley-watch</a>. No cookies, no tracking.
        </p>
      </footer>
    </div>
  );
}

function Answer({ d, third }: { d: TrolleyFile; third: Third }) {
  const path = d.thirds[third];
  const off = official(d);
  const r = rise(path);
  const shown = useCountUp(r);
  const last = d.months[d.months.length - 1]!;
  const peak = fastestYear(path, d.months);
  const y2022 = path[23]! / path[12]! - 1;

  return (
    <>
      <div className="answer-main">
        <div className="where">
          <b>{THIRD_NAME[third]}</b>
          <span>{`${month(d.months[0]!)} to ${month(last)}`}</span>
        </div>
        <div className="big">
          <span className={`num t-${third}`}>{pct(shown ?? r)}</span>
          <span className="unit">{`rise in food prices at ${WHERE[third]}, against ${pct(rise(off))} for food as a whole`}</span>
        </div>
        <p className="context">
          {`£100 of shopping at ${WHERE[third]} in ${month(d.months[0]!)} cost ${gbp(path[path.length - 1]!)} by ${month(last)}. The official index says ${gbp(off[off.length - 1]!)}.`}
        </p>
      </div>
      <div className="answer-side">
        <dl className="facts">
          <div>
            <dt>In 2022 alone</dt>
            <dd>{pct(y2022)}</dd>
          </div>
          <div>
            <dt>{`Fastest twelve months, to ${month(peak.month)}`}</dt>
            <dd>{pct(peak.rate)}</dd>
          </div>
          <div>
            <dt>In 2024, when inflation eased</dt>
            <dd>{pct(path[47]! / path[36]! - 1)}</dd>
          </div>
        </dl>
      </div>
    </>
  );
}

function Sections({
  d,
  third,
  items,
  setItems,
}: {
  d: TrolleyFile;
  third: Third;
  items: string[];
  setItems: (ids: string[]) => void;
}) {
  const off = useMemo(() => official(d), [d]);
  const food = rise(off);
  const path = useMemo(() => trolleyPath(d, items), [d, items]);
  const mine = path.length ? rise(path) : null;
  const top = useMemo(() => pushedMost(d, items), [d, items]);
  const chosen = useMemo(() => new Set(items), [items]);
  const [all, setAll] = useState(false);
  const [filter, setFilter] = useState("");
  const shown = useCountUp(mine);

  const byGroup = useMemo(() => {
    const everyday = new Set(d.everyday);
    const words = filter.trim().toLowerCase();
    const list = d.items.filter((x) =>
      words ? `${x.name} ${x.desc}`.toLowerCase().includes(words) : all || everyday.has(x.id) || chosen.has(x.id),
    );
    const out = new Map<string, typeof list>();
    for (const x of list) out.set(x.group, [...(out.get(x.group) ?? []), x]);
    return [...out.entries()];
  }, [d, all, filter, chosen]);

  const toggle = (id: string) => setItems(chosen.has(id) ? items.filter((i) => i !== id) : [...items, id]);

  const card = useMemo(
    () => ({
      lead: `Food prices at ${WHERE[third]} of the shelf, ${month(d.months[0]!)} to ${month(d.months[d.months.length - 1]!)}:`,
      big: pct(rise(d.thirds[third])),
      unit: `against ${pct(food)} for food as a whole`,
      lines: [
        mine === null ? "" : `My trolley of ${items.length} ${items.length === 1 ? "item" : "items"}: ${pct(mine)}.`,
        "Rebuilt from 2.2 million prices the ONS collected.",
      ].filter(Boolean),
      path: d.thirds[third],
      official: off,
      colour: CARD_COLOUR[third],
    }),
    [d, third, food, mine, items.length, off],
  );

  return (
    <>
      <section>
        <h2>Three ends of the shelf</h2>
        <p className="sub">
          Each month, within each item and each region and type of shop, the prices collected are ranked and split into
          thirds; each third is followed through the year by the ONS's own method and stacked with its weights. The
          three moved together in 2021 and 2024 and came apart in between.
        </p>
        <div className="fig">
          <ThirdsChart months={d.months} thirds={d.thirds} official={off} chosen={third} />
          <ul className="legend" aria-hidden="true">
            <li className="l-cheap">cheapest third</li>
            <li className="l-middle">middle third</li>
            <li className="l-dear">dearest third</li>
            <li className="l-official">official food index</li>
          </ul>
        </div>
      </section>

      <section>
        <h2>Your trolley</h2>
        <p className="sub">
          Tick what you buy. Each item is the ONS's own index for it, and each counts as much as households spend on it.
          One item's thirds are too noisy to show on their own, so these are all its prices, not one end.
        </p>
        <div className="trolley-result" aria-live="polite">
          {mine === null ? (
            <p>Your trolley is empty. Tick a few things you buy.</p>
          ) : (
            <>
              <p className="big">
                <span className="num t-you">{pct(shown ?? mine)}</span>
                <span className="unit">{`your trolley of ${items.length} ${items.length === 1 ? "item" : "items"}, ${month(d.months[0]!)} to ${month(d.months[d.months.length - 1]!)}`}</span>
              </p>
              <p className="context">
                {`£100 of it in ${month(d.months[0]!)} cost ${gbp(path[path.length - 1]!)} by ${month(d.months[d.months.length - 1]!)}.`}
                {top && top.share > 0 && items.length > 1
                  ? ` The biggest push came from ${top.item.name.toLowerCase()}: ${pct(rise(top.item.path), 0).slice(1)} dearer, and ${Math.round(top.share * 100)}% of the rise.`
                  : ""}
              </p>
            </>
          )}
        </div>
        <div className="fig">
          <ItemsStrip items={d.items} chosen={chosen} trolley={mine} food={food} />
        </div>
        <div className="picker">
          <div className="picker-bar">
            <label className="visually-hidden" htmlFor="find">
              Find an item
            </label>
            <input
              id="find"
              type="search"
              placeholder={`Find one of ${d.items.length} items`}
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
            />
            <button className="btn quiet" type="button" onClick={() => setAll(!all)} aria-pressed={all}>
              {all ? "Everyday items only" : `Show all ${d.items.length}`}
            </button>
            <button className="btn quiet" type="button" onClick={() => setItems([...d.everyday])}>
              Everyday trolley
            </button>
            <button className="btn quiet" type="button" onClick={() => setItems([])}>
              Empty it
            </button>
          </div>
          {byGroup.length === 0 && <p className="note">Nothing matches. Try "milk" or "bread".</p>}
          {byGroup.map(([group, list]) => (
            <fieldset key={group} className="group">
              <legend>{d.groups[group]}</legend>
              <div className="chips">
                {list.map((x) => (
                  <button
                    key={x.id}
                    type="button"
                    className="chip"
                    aria-pressed={chosen.has(x.id)}
                    onClick={() => toggle(x.id)}
                    title={x.desc}
                  >
                    {x.name}
                    <small>{pct(rise(x.path), 0)}</small>
                  </button>
                ))}
              </div>
            </fieldset>
          ))}
        </div>
      </section>

      <section>
        <h2>How I know this is right</h2>
        <p className="sub">
          Before splitting anything, I rebuilt the ONS's own numbers from its own files, and made each check with a twin
          that has to fail.
        </p>
        <ul className="checks">
          <li>
            <span className="pill">Pass</span>
            <div>
              <b>Every food item's index, rebuilt from its prices</b>
              <span>
                {`All ${d.checks.item_months.toLocaleString("en-GB")} item-months from 2021 to 2024 within 0.02 of the published index, ${d.checks.item_exact.toLocaleString("en-GB")} of them to all three decimal places. Averaged the wrong way, the same prices get ${d.checks.carli_within} right.`}
              </span>
            </div>
          </li>
          <li>
            <span className="pill">Pass</span>
            <div>
              <b>The official food index, rebuilt from its items</b>
              <span>
                {`All ${d.checks.food_months} months within 0.15 of an index point, the largest gap ${d.checks.food_worst.toFixed(3)}. With every item weighted equally, it misses by up to ${d.checks.equal_worst.toFixed(1)}.`}
              </span>
            </div>
          </li>
          <li>
            <span className="pill neutral">Stated</span>
            <div>
              <b>The trap in the obvious method</b>
              <span>
                {`Rank each price on its January price alone and the cheap end seems to rise ${Math.round(d.trap.january!.cheap - 100)}% and the dear end ${Math.round(d.trap.january!.dear - 100)}%: regression to the mean, not a finding. Prices here are ranked on January's and this month's together, which cancels it.`}
              </span>
            </div>
          </li>
        </ul>
      </section>

      <section>
        <h2>Save your result</h2>
        <ShareCard content={card} file={`trolley-watch-${third}.png`} />
      </section>
    </>
  );
}
