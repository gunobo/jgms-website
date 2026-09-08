/**
 * Backend timestamps are naive-UTC (no "Z"/offset suffix), e.g.
 * "2026-09-08T03:30:52". `new Date(...)` on a string like that is parsed as
 * LOCAL time by the browser, not UTC, which silently shifts every displayed
 * time by the viewer's UTC offset. Always go through this instead.
 */
export function parseUtc(isoString: string): Date {
  const hasTimezone = /Z$|[+-]\d{2}:?\d{2}$/.test(isoString);
  return new Date(hasTimezone ? isoString : `${isoString}Z`);
}

/** For a <input type="datetime-local"> value, in the viewer's local time. */
export function toDatetimeLocalValue(isoString: string): string {
  const d = parseUtc(isoString);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** Converts a <input type="datetime-local"> value (local time, no timezone)
 * into a UTC ISO string suitable for sending to the backend. */
export function fromDatetimeLocalValue(localValue: string): string {
  return new Date(localValue).toISOString();
}
