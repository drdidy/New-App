import { describe, expect, it } from "vitest";
import { formatMoney, clampPct } from "./format";

describe("formatMoney", () => {
  it("formats whole and fractional amounts", () => {
    expect(formatMoney(840, "USD")).toBe("$840");
    expect(formatMoney(8.4, "USD")).toBe("$8.40");
  });
  it("never renders $NaN or $Infinity", () => {
    expect(formatMoney(NaN, "USD")).toBe("$0");
    expect(formatMoney(Infinity, "USD")).toBe("$0");
    expect(formatMoney(-Infinity, "USD")).toBe("$0");
  });
});

describe("clampPct", () => {
  it("clamps to 0..100", () => {
    expect(clampPct(150)).toBe(100);
    expect(clampPct(-10)).toBe(0);
    expect(clampPct(42)).toBe(42);
  });
  it("coerces NaN/Infinity to 0 (no broken progress bars)", () => {
    expect(clampPct(NaN)).toBe(0);
    expect(clampPct(Infinity)).toBe(0);
  });
});
