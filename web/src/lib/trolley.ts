// The app's arithmetic. Everything here is checked against the pipeline's
// worked example in trolley.test.ts, so the page and the write-up agree.

export type Third = "cheap" | "middle" | "dear";
export const THIRDS: Third[] = ["cheap", "middle", "dear"];

export interface Item {
  id: string;
  name: string;
  desc: string;
  group: string;
  weight: number;
  path: number[];
}

export interface TrolleyFile {
  months: string[];
  published: number[];
  thirds: Record<Third | "all", number[]>;
  trap: Record<string, { cheap: number; dear: number }>;
  groups: Record<string, string>;
  items: Item[];
  everyday: string[];
  left_out: number;
  checks: {
    item_months: number;
    item_within: number;
    item_exact: number;
    item_worst: number;
    item_imputed: number;
    carli_within: number;
    january_within: number;
    food_months: number;
    food_worst: number;
    equal_worst: number;
  };
  example: { items: string[]; december_2024: number };
}

/** The change in a path from one month to another, as a fraction. */
export function rise(path: number[], from = 0, to = path.length - 1): number {
  return path[to]! / path[from]! - 1;
}

/** The published food index, January 2021 = 100. */
export function official(d: TrolleyFile): number[] {
  return d.published.map((v) => (100 * v) / d.published[0]!);
}

/**
 * A January 2021 trolley of these items, month by month, January 2021 = 100.
 * Each item counts in proportion to its 2021 CPI weight among those chosen:
 * the ONS's estimate of how household spending divides between them.
 */
export function trolleyPath(d: TrolleyFile, ids: string[]): number[] {
  const chosen = d.items.filter((x) => ids.includes(x.id));
  const total = chosen.reduce((s, x) => s + x.weight, 0);
  if (!total) return [];
  return d.months.map((_, m) => chosen.reduce((s, x) => s + x.weight * x.path[m]!, 0) / total);
}

/** The chosen item that did most to push the trolley's cost up, and its share of the rise. */
export function pushedMost(d: TrolleyFile, ids: string[]): { item: Item; share: number } | null {
  const chosen = d.items.filter((x) => ids.includes(x.id));
  const end = d.months.length - 1;
  const parts = chosen.map((x) => ({ item: x, part: x.weight * (x.path[end]! - 100) }));
  const total = parts.reduce((s, p) => s + p.part, 0);
  if (!parts.length || total <= 0) return null;
  const top = parts.reduce((a, b) => (b.part > a.part ? b : a));
  return { item: top.item, share: top.part / total };
}

/** Where a rise sits among every item's: the share of items that rose less. */
export function share(d: TrolleyFile, value: number): number {
  const rises = d.items.map((x) => rise(x.path));
  return rises.filter((r) => r < value).length / rises.length;
}

// The choice lives in the address, so a shared link opens on the same answer.
// Items are written without their shared "21" prefix; the everyday trolley,
// the default, is not written at all.

export interface Choice {
  third: Third;
  items: string[];
}

export function readChoice(search: string, d: Pick<TrolleyFile, "items" | "everyday">): Choice {
  const q = new URLSearchParams(search);
  const t = q.get("s");
  const third: Third = t === "middle" || t === "dear" ? t : "cheap";
  const known = new Set(d.items.map((x) => x.id));
  const raw = q.get("i");
  const items =
    raw === null
      ? [...d.everyday]
      : raw
          .split(".")
          .map((s) => `21${s}`)
          .filter((id, i, all) => known.has(id) && all.indexOf(id) === i);
  return { third, items };
}

export function writeChoice(c: Choice, everyday: string[]): string {
  const q = new URLSearchParams();
  if (c.third !== "cheap") q.set("s", c.third);
  const same = c.items.length === everyday.length && everyday.every((id) => c.items.includes(id));
  if (!same) q.set("i", c.items.map((id) => id.slice(2)).join("."));
  const s = q.toString();
  return s ? `?${s}` : "";
}
