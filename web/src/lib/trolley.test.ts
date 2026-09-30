import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { extremes, looksLikeTrolleyFile, official, pushedMost, readChoice, rise, trolleyPath, type TrolleyFile, writeChoice } from "./trolley";

const d = JSON.parse(readFileSync(new URL("../../public/data/trolley.json", import.meta.url), "utf-8")) as TrolleyFile;

describe("the pipeline's numbers", () => {
  it("reproduces the worked example to six decimals", () => {
    const path = trolleyPath(d, d.example.items);
    expect(path[path.length - 1]).toBeCloseTo(d.example.december_2024, 6);
  });

  it("reads the headline rises the README quotes", () => {
    expect(rise(d.thirds.cheap)).toBeCloseTo(0.3855, 4);
    expect(rise(d.thirds.dear)).toBeCloseTo(0.2982, 4);
    expect(rise(official(d))).toBeCloseTo(137.8 / 103.4 - 1, 10);
  });
});

describe("a trolley", () => {
  it("of one item is that item", () => {
    const eggs = d.items.find((x) => x.id === "211604")!;
    expect(trolleyPath(d, ["211604"])).toEqual(eggs.path.map((v) => (eggs.weight * v) / eggs.weight));
  });

  it("of nothing is empty", () => {
    expect(trolleyPath(d, [])).toEqual([]);
    expect(pushedMost(d, [])).toBeNull();
  });

  it("names the item that pushed it up most: spending counts, not just the rise", () => {
    // olive oil rose furthest, but more is spent on milk
    const top = pushedMost(d, d.everyday)!;
    expect(top.item.name).toBe("Semi-skimmed milk, two pints");
    expect(top.share).toBeCloseTo(0.076, 3);
  });
});

describe("the address", () => {
  it("leaves the default out", () => {
    expect(writeChoice({ third: "cheap", items: [...d.everyday] }, d.everyday)).toBe("");
    expect(readChoice("", d)).toEqual({ third: "cheap", items: d.everyday });
  });

  it("round-trips a choice", () => {
    const c = { third: "dear" as const, items: ["211604", "212310", "210111"] };
    const s = writeChoice(c, d.everyday);
    expect(s).toBe("?s=dear&i=1604.2310.0111");
    expect(readChoice(s, d)).toEqual(c);
  });

  it("drops what it does not know, and repeats", () => {
    expect(readChoice("?s=cheapest&i=1604.9999.1604", d)).toEqual({ third: "cheap", items: ["211604"] });
    expect(readChoice("?i=", d).items).toEqual([]);
  });
});

describe("what the shelf says about a month", () => {
  // the shelf's own ordering: by rise to the latest month, smallest first
  const shelf = d.items.filter((i) => d.everyday.includes(i.id)).sort((a, b) => rise(a.path) - rise(b.path));

  it("names that month's cheapest and dearest, in every month", () => {
    for (let m = 0; m < d.months.length; m++) {
      const { low, high } = extremes(shelf, m);
      const vals = shelf.map((i) => i.path[m]!);
      expect(low.path[m]).toBe(Math.min(...vals));
      expect(high.path[m]).toBe(Math.max(...vals));
      expect(low.path[m]).toBeLessThanOrEqual(high.path[m]!);
    }
  });

  it("does not mistake the ends of the shelf for them", () => {
    // if the two were the same thing there would be no need for a function:
    // in most months neither end of the shelf is that month's extreme
    let ends = 0;
    for (let m = 0; m < d.months.length; m++) {
      const { low, high } = extremes(shelf, m);
      if (low.id === shelf[0]!.id && high.id === shelf[shelf.length - 1]!.id) ends++;
    }
    expect(ends).toBeLessThan(d.months.length);
  });
});

describe("the load guard", () => {
  it("accepts the real file and rejects anything that is not it", () => {
    expect(looksLikeTrolleyFile(d)).toBe(true);
    for (const bad of [null, undefined, {}, [], [1, 2, 3], { months: [] }, { items: {} }, "text", 5])
      expect(looksLikeTrolleyFile(bad)).toBe(false);
  });
});
