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

  it("keeps debtId on payment transactions through validation", () => {
    const data = parseAppDataInput({
      version: 2,
      onboarded: true,
      members: [],
      transactions: [{
        id: "t1", type: "expense", amount: 50, category: "Debt payment",
        description: "Payment to James Allen", date: "2026-07-11", createdAt: 1, debtId: "d1",
      }],
      debts: [], budgets: [], recurringBills: [], goals: [], accounts: [],
      netWorthHistory: [], payCycle: { type: "monthly" }, currency: "USD", theme: "dark",
    });
    expect(data).not.toBeNull();
    const txs = data!.transactions as Array<{ debtId?: string }>;
    expect(txs[0].debtId).toBe("d1");
  });
});
