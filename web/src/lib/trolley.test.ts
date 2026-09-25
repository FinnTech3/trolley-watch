import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { official, pushedMost, readChoice, rise, trolleyPath, type TrolleyFile, writeChoice } from "./trolley";

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
