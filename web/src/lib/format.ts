// Numbers as the page prints them. British conventions throughout.

export function pct(x: number, dp = 1): string {
  return `${x < 0 ? "-" : "+"}${Math.abs(x * 100).toFixed(dp)}%`;
}

export function gbp(x: number, dp = 2): string {
  return `£${x.toLocaleString("en-GB", { minimumFractionDigits: dp, maximumFractionDigits: dp })}`;
}

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/** "202412" as "December 2024". */
export function month(ym: string): string {
  return `${MONTHS[Number(ym.slice(4)) - 1]} ${ym.slice(0, 4)}`;
}
