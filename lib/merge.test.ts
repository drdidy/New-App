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

describe("mergeData preserves all entities (no silent wipe)", () => {
  it("keeps buckets, recurring income, wishlist, and lastPaycheckDistributed", () => {
    const a = base({
      buckets: [{ id: "bk1", name: "Tithe", emoji: "🙏", color: "#111", kind: "give", balance: 420, createdAt: 1, updatedAt: 5 }],
      recurringIncome: [{ id: "ri1", name: "Salary", amount: 4200, dayOfMonth: 30, createdAt: 1, updatedAt: 5, lastPaidMonth: "2026-06" }],
      wishlist: [{ id: "w1", name: "AirPods", amount: 250, createdAt: 1 }],
      lastPaycheckDistributed: "2026-06",
    });
    const b = base({ settingsUpdatedAt: 2 });
    const merged = mergeData(b, a); // other device has none of it
    expect(merged.buckets).toHaveLength(1);
    expect(merged.recurringIncome?.[0].lastPaidMonth).toBe("2026-06");
    expect(merged.wishlist).toHaveLength(1);
    expect(merged.lastPaycheckDistributed).toBe("2026-06");
  });
  it("honors a bucket deletion via tombstones", () => {
    const a = base({ buckets: [{ id: "bk1", name: "Tithe", emoji: "", color: "#111", kind: "give", balance: 1, createdAt: 1, updatedAt: 5 }] });
    const b = base({ tombstones: ["bk1"], settingsUpdatedAt: 9 });
    expect(mergeData(a, b).buckets).toHaveLength(0);
  });
});

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
