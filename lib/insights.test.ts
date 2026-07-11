import { describe, expect, it } from "vitest";
import type { AppData } from "./types";
import {
  inferDebtKind,
  monthPace,
  payoffProjection,
  safeToSpend,
  simulatePayoff,
  spendableCash,
} from "./insights";
import { monthKey, todayISO } from "./format";

function base(overrides: Partial<AppData> = {}): AppData {
  return {
    version: 2,
    onboarded: true,
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
    ...overrides,
  };
}

describe("inferDebtKind", () => {
  it("detects credit cards by name", () => {
    expect(inferDebtKind({ party: "Visa card" })).toBe("card");
    expect(inferDebtKind({ party: "Chase Sapphire" })).toBe("card");
  });
  it("detects buy-now-pay-later", () => {
    expect(inferDebtKind({ party: "Klarna" })).toBe("bnpl");
  });
  it("detects loans", () => {
    expect(inferDebtKind({ party: "Student Loan" })).toBe("loan");
  });
  it("treats a bare first name with no APR as a person", () => {
    expect(inferDebtKind({ party: "James" })).toBe("person");
  });
  it("treats anything with an APR as an organization (card)", () => {
    expect(inferDebtKind({ party: "Mystery", apr: 19.9 })).toBe("card");
  });
  it("respects an explicit kind", () => {
    expect(inferDebtKind({ party: "Visa", kind: "person" })).toBe("person");
  });
});

describe("spendableCash", () => {
  it("counts only checking + cash when present", () => {
    const data = base({
      accounts: [
        { id: "a", name: "Checking", type: "checking", balance: 500, emoji: "", color: "#000", createdAt: 0 },
        { id: "b", name: "Savings", type: "savings", balance: 9000, emoji: "", color: "#000", createdAt: 0 },
        { id: "c", name: "Wallet", type: "cash", balance: 40, emoji: "", color: "#000", createdAt: 0 },
      ],
    });
    expect(spendableCash(data)).toBe(540);
  });
  it("falls back to all accounts when none are checking/cash", () => {
    const data = base({
      accounts: [
        { id: "b", name: "Savings", type: "savings", balance: 9000, emoji: "", color: "#000", createdAt: 0 },
      ],
    });
    expect(spendableCash(data)).toBe(9000);
  });
});

describe("matchPersonDebts", () => {
  const mk = (id: string, party: string, balance = 100): import("./types").Debt =>
    ({ id, party, balance, direction: "i_owe", createdAt: 0 });
  it("matches a first name to a full-name debt when unambiguous", async () => {
    const { matchPersonDebts } = await import("./insights");
    const r = matchPersonDebts([mk("d1", "James Allen")], "James");
    expect(r.exact).toBeUndefined();
    expect(r.candidates.map((c) => c.id)).toEqual(["d1"]);
  });
  it("returns multiple candidates when ambiguous", async () => {
    const { matchPersonDebts } = await import("./insights");
    const r = matchPersonDebts([mk("d1", "James Allen"), mk("d2", "James Brown")], "James");
    expect(r.candidates).toHaveLength(2);
  });
  it("prefers an exact match", async () => {
    const { matchPersonDebts } = await import("./insights");
    const r = matchPersonDebts([mk("d1", "James Allen"), mk("d2", "James")], "james");
    expect(r.exact?.id).toBe("d2");
  });
  it("ignores fully-paid debts", async () => {
    const { matchPersonDebts } = await import("./insights");
    const r = matchPersonDebts([mk("d1", "James Allen", 0)], "James");
    expect(r.candidates).toHaveLength(0);
  });
});

describe("cashOnHand reflects logged money", () => {
  it("adds income and subtracts expenses logged after the balance was set", async () => {
    const { cashOnHand } = await import("./insights");
    const data = base({
      accounts: [{ id: "a", name: "Checking", type: "checking", balance: 1850, emoji: "", color: "#000", createdAt: 1000, balanceAsOf: 1000 }],
      transactions: [
        { id: "t1", type: "income", amount: 1480, category: "Income", description: "Mom & Dad", date: "2026-06-20", createdAt: 2000 },
        { id: "t2", type: "expense", amount: 40, category: "Dining", description: "", date: "2026-06-21", createdAt: 3000 },
      ],
    });
    expect(cashOnHand(data)).toBe(1850 + 1480 - 40); // 3290
  });
  it("ignores transactions from before the balance was set (no double-count)", async () => {
    const { cashOnHand } = await import("./insights");
    const data = base({
      accounts: [{ id: "a", name: "Checking", type: "checking", balance: 1850, emoji: "", color: "#000", createdAt: 5000, balanceAsOf: 5000 }],
      transactions: [
        { id: "t1", type: "expense", amount: 100, category: "Dining", description: "", date: "2026-06-01", createdAt: 1000 },
      ],
    });
    expect(cashOnHand(data)).toBe(1850);
  });
});

describe("safeToSpend", () => {
  it("uses cash mode when accounts exist and subtracts obligations due before payday", () => {
    const data = base({
      accounts: [
        { id: "a", name: "Checking", type: "checking", balance: 1000, emoji: "", color: "#000", createdAt: 0 },
      ],
      recurringBills: [
        { id: "rent", name: "Rent", amount: 600, category: "Rent", dayOfMonth: 1, createdAt: 0 },
      ],
      debts: [
        { id: "d1", direction: "i_owe", party: "Visa", balance: 2000, minPayment: 50, createdAt: 0 },
      ],
    });
    const sts = safeToSpend(data);
    expect(sts.mode).toBe("cash");
    expect(sts.spendable).toBe(1000);
    // 600 bill (unpaid, due this month) + 50 debt min = 650 committed
    expect(sts.committed).toBe(650);
    expect(sts.safe).toBe(350);
  });

  it("falls back to income mode when there are no accounts", () => {
    const month = monthKey();
    const data = base({
      members: [{ id: "m1", name: "Dana", emoji: "", color: "#000", monthlyIncome: 3000 }],
      transactions: [
        { id: "t1", type: "expense", amount: 200, category: "Food", description: "", date: `${month}-05`, createdAt: 0 },
      ],
    });
    const sts = safeToSpend(data);
    expect(sts.mode).toBe("income");
    expect(sts.hasAccounts).toBe(false);
    // income 3000 - expenses 200 = 2800 spendable, no committed
    expect(sts.spendable).toBe(2800);
    expect(sts.safe).toBe(2800);
  });

  it("does not double-count debt minimums already paid this month", () => {
    const month = monthKey();
    const data = base({
      accounts: [
        { id: "a", name: "Checking", type: "checking", balance: 500, emoji: "", color: "#000", createdAt: 0 },
      ],
      debts: [
        { id: "d1", direction: "i_owe", party: "Visa", balance: 2000, minPayment: 80, createdAt: 0 },
      ],
      transactions: [
        { id: "p1", type: "expense", amount: 80, category: "Debt payment", description: "", date: `${month}-03`, createdAt: 0 },
      ],
    });
    const sts = safeToSpend(data);
    // min already covered -> no remaining committed debt
    expect(sts.debtDue).toBe(0);
    expect(sts.safe).toBe(500);
  });
});

describe("baselineIncome", () => {
  it("uses recurring income when no income is logged this month", async () => {
    const { baselineIncome } = await import("./insights");
    const data = base({
      recurringIncome: [{ id: "i1", name: "Salary", amount: 4200, dayOfMonth: 30, createdAt: 0 }],
    });
    expect(baselineIncome(data)).toBe(4200);
  });
  it("prefers actually-logged income over the recurring estimate", async () => {
    const { baselineIncome } = await import("./insights");
    const month = monthKey();
    const data = base({
      recurringIncome: [{ id: "i1", name: "Salary", amount: 4200, dayOfMonth: 30, createdAt: 0 }],
      transactions: [{ id: "t1", type: "income", amount: 5000, category: "Salary", description: "", date: `${month}-30`, createdAt: 0 }],
    });
    expect(baselineIncome(data)).toBe(5000);
  });
});

describe("payoffProjection", () => {
  it("returns a decreasing series that reaches zero", () => {
    const data = base({
      debts: [
        { id: "d1", direction: "i_owe", party: "Card A", balance: 1000, apr: 0, minPayment: 100, createdAt: 0 },
      ],
    });
    const series = payoffProjection(data, "snowball", 100);
    expect(series[0]).toBe(1000);
    expect(series[series.length - 1]).toBe(0);
    for (let i = 1; i < series.length; i++) {
      expect(series[i]).toBeLessThanOrEqual(series[i - 1]);
    }
  });

  it("extra payments clear debt faster than minimums alone", () => {
    const data = base({
      debts: [
        { id: "d1", direction: "i_owe", party: "Card A", balance: 5000, apr: 20, minPayment: 100, createdAt: 0 },
      ],
    });
    const slow = simulatePayoff(data, "avalanche", 0);
    const fast = simulatePayoff(data, "avalanche", 300);
    expect(fast.months!).toBeLessThan(slow.months!);
    expect(fast.totalInterest).toBeLessThan(slow.totalInterest);
  });

  it("handles no debt", () => {
    expect(payoffProjection(base(), "snowball", 50)).toEqual([0]);
    expect(safeToSpend(base()).safe).toBe(0);
    expect(todayISO()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});

describe("monthPace", () => {
  function txAt(monthsBack: number, day: number, amount: number) {
    const d = new Date();
    const m = new Date(d.getFullYear(), d.getMonth() - monthsBack, Math.min(day, 28));
    const iso = `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, "0")}-${String(m.getDate()).padStart(2, "0")}`;
    return { id: `t${monthsBack}-${day}-${amount}`, type: "expense" as const, amount, category: "Groceries", description: "", date: iso, createdAt: 0 };
  }

  it("returns null with no prior-month history", () => {
    expect(monthPace(base())).toBeNull();
    expect(monthPace(base({ transactions: [txAt(0, 1, 50)] }))).toBeNull();
  });

  it("averages prior months capped at today's day and reports current spend", () => {
    const today = new Date().getDate();
    const data = base({
      transactions: [
        txAt(0, 1, 40),        // this month
        txAt(1, 1, 100),       // last month, always within cap
        txAt(2, 1, 200),       // two months ago
      ],
    });
    const p = monthPace(data)!;
    expect(p).not.toBeNull();
    expect(p.day).toBe(today);
    expect(p.months).toBe(2);
    expect(p.actual).toBe(40);
    expect(p.typical).toBe(150);
  });
});
