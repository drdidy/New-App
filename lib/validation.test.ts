import { describe, expect, it } from "vitest";
import {
  parseAppDataInput,
  parsedResponseSchema,
  receiptResponseSchema,
} from "./validation";

describe("validation", () => {
  it("rejects invalid imported app data", () => {
    expect(parseAppDataInput({ transactions: [{ amount: -1 }] })).toBeNull();
  });

  it("bounds parsed AI entries", () => {
    expect(() =>
      parsedResponseSchema.parse({
        entries: [{ kind: "expense", amount: 5, summary: "Coffee" }],
      }),
    ).not.toThrow();

    expect(() =>
      parsedResponseSchema.parse({
        entries: [{ kind: "expense", amount: Number.POSITIVE_INFINITY, summary: "Bad" }],
      }),
    ).toThrow();
  });

  it("normalizes receipt items", () => {
    const parsed = receiptResponseSchema.parse({
      found: true,
      amount: 25,
      summary: "Market",
      items: [{ name: "Bananas", amount: 3, category: "Produce" }],
    });

    expect(parsed.items[0].category).toBe("Produce");
  });
});
