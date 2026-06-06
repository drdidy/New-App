import { describe, expect, it } from "vitest";
import { mergeData, sanitizeForSync } from "./merge";
import type { AppData } from "./types";

function base(overrides: Partial<AppData> = {}): AppData {
  return {
    version: 2,
    onboarded: true,
    householdName: "Test",
    members: [],
    transactions: [],
    debts: [],
    budgets: [],
    recurringBills: [],
    goals: [],
    accounts: [],
    netWorthHistory: [],
    payCycle: { type: "monthly" },
    currency: "USD",
    theme: "light",
    tombstones: [],
    settingsUpdatedAt: 1,
    ...overrides,
  };
}

describe("mergeData", () => {
  it("is commutative for tied members and budgets", () => {
    const a = base({
      members: [{ id: "m1", name: "Alex", emoji: "A", color: "#111", updatedAt: 100 }],
      budgets: [{ category: "Groceries", limit: 400, updatedAt: 100 }],
    });
    const b = base({
      members: [{ id: "m1", name: "Alexis", emoji: "B", color: "#222", updatedAt: 100 }],
      budgets: [{ category: "Groceries", limit: 450, updatedAt: 100 }],
    });

    expect(mergeData(a, b)).toEqual(mergeData(b, a));
  });

  it("keeps tombstones sorted and removes deleted records", () => {
    const a = base({
      transactions: [
        {
          id: "t1",
          type: "expense",
          amount: 12,
          category: "Dining",
          description: "Lunch",
          date: "2026-06-05",
          createdAt: 100,
        },
      ],
    });
    const b = base({ tombstones: ["t1", "budget:Dining"] });

    const merged = mergeData(a, b);
    expect(merged.transactions).toEqual([]);
    expect(merged.tombstones).toEqual(["budget:Dining", "t1"]);
  });

  it("strips local sync secrets before cloud writes", () => {
    const clean = sanitizeForSync(
      base({ syncCode: "secret-household-code", syncEnabled: true }),
    );

    expect(clean.syncCode).toBeUndefined();
    expect(clean.syncEnabled).toBeUndefined();
  });
});
