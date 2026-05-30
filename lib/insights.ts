import type { AppData, Debt, RecurringBill } from "./types";
import { monthKey, prevMonthKey } from "./format";

export interface BillView {
  bill: RecurringBill;
  paid: boolean;
  dueDay: number;
  daysAway: number; // days until due this month (negative if past)
}

// Recurring bills for the current month, with paid status + due-day info,
// sorted by due day.
export function billsThisMonth(data: AppData, memberId?: string): BillView[] {
  const month = monthKey();
  const now = new Date();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const today = now.getDate();
  return (data.recurringBills || [])
    .filter((b) => !memberId || b.memberId === memberId)
    .map((b) => {
      const dueDay = Math.min(b.dayOfMonth, daysInMonth);
      return {
        bill: b,
        paid: b.lastPaidMonth === month,
        dueDay,
        daysAway: dueDay - today,
      };
    })
    .sort((a, b) => a.dueDay - b.dueDay);
}

export interface CategorySlice {
  category: string;
  amount: number;
  pct: number; // share of total expenses, 0-100
}

// Expense totals by category for a month (default: current), highest first.
export function categoryBreakdown(
  data: AppData,
  month: string = monthKey(),
  memberId?: string,
): CategorySlice[] {
  const totals = new Map<string, number>();
  let sum = 0;
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    if (memberId && t.memberId !== memberId) continue;
    if (!t.date.startsWith(month)) continue;
    totals.set(t.category, (totals.get(t.category) || 0) + t.amount);
    sum += t.amount;
  }
  return [...totals.entries()]
    .map(([category, amount]) => ({
      category,
      amount,
      pct: sum ? (amount / sum) * 100 : 0,
    }))
    .sort((a, b) => b.amount - a.amount);
}

export interface BudgetStatus {
  category: string;
  spent: number;
  limit: number;
  pct: number; // spent / limit * 100 (can exceed 100)
  over: boolean;
}

export function budgetStatus(data: AppData): BudgetStatus[] {
  const month = monthKey();
  const spentByCat = new Map<string, number>();
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    if (!t.date.startsWith(month)) continue;
    spentByCat.set(t.category, (spentByCat.get(t.category) || 0) + t.amount);
  }
  return data.budgets
    .map((b) => {
      const spent = spentByCat.get(b.category) || 0;
      const pct = b.limit ? (spent / b.limit) * 100 : 0;
      return { category: b.category, spent, limit: b.limit, pct, over: spent > b.limit };
    })
    .sort((a, b) => b.pct - a.pct);
}

export interface MemberSplit {
  memberId: string;
  expenses: number;
  pct: number;
}

export function memberSplit(data: AppData): MemberSplit[] {
  const month = monthKey();
  const byMember = new Map<string, number>();
  let sum = 0;
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    if (!t.date.startsWith(month)) continue;
    const id = t.memberId || "unknown";
    byMember.set(id, (byMember.get(id) || 0) + t.amount);
    sum += t.amount;
  }
  return data.members.map((m) => ({
    memberId: m.id,
    expenses: byMember.get(m.id) || 0,
    pct: sum ? ((byMember.get(m.id) || 0) / sum) * 100 : 0,
  }));
}

// This-month vs last-month expense totals + percent change.
export function monthOverMonth(data: AppData): {
  thisMonth: number;
  lastMonth: number;
  changePct: number | null;
} {
  const cur = monthKey();
  const prev = prevMonthKey();
  let thisMonth = 0;
  let lastMonth = 0;
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    if (t.date.startsWith(cur)) thisMonth += t.amount;
    else if (t.date.startsWith(prev)) lastMonth += t.amount;
  }
  const changePct =
    lastMonth > 0 ? ((thisMonth - lastMonth) / lastMonth) * 100 : null;
  return { thisMonth, lastMonth, changePct };
}

export interface PayoffPlan {
  method: "snowball" | "avalanche";
  order: Debt[];
  months: number | null; // estimated months to clear, given extra
  totalBalance: number;
}

// Order "I owe" debts and roughly estimate payoff time. snowball = smallest
// balance first (motivation); avalanche = highest APR first (cheapest).
export function payoffPlan(
  data: AppData,
  method: "snowball" | "avalanche" = "snowball",
  extraPerMonth = 0,
): PayoffPlan {
  const debts = data.debts.filter((d) => d.direction === "i_owe" && d.balance > 0);
  const order = [...debts].sort((a, b) =>
    method === "snowball"
      ? a.balance - b.balance
      : (b.apr || 0) - (a.apr || 0),
  );
  const totalBalance = debts.reduce((s, d) => s + d.balance, 0);
  const totalMin = debts.reduce((s, d) => s + (d.minPayment || 0), 0);
  const monthlyPay = totalMin + extraPerMonth;
  // Very rough: ignore interest accrual for the headline estimate.
  const months = monthlyPay > 0 ? Math.ceil(totalBalance / monthlyPay) : null;
  return { method, order, months, totalBalance };
}

// One-line, human insights for the dashboard. Returns up to `max` strings.
export function quickInsights(data: AppData, currency: string, max = 3): string[] {
  const out: string[] = [];
  const mom = monthOverMonth(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);

  const overBudget = budgets.find((b) => b.over);
  if (overBudget) {
    out.push(
      `You're over your ${overBudget.category} budget this month — ${Math.round(
        overBudget.pct,
      )}% used.`,
    );
  }
  if (mom.changePct !== null && Math.abs(mom.changePct) >= 8) {
    const dir = mom.changePct > 0 ? "more" : "less";
    out.push(
      `You've spent ${Math.abs(Math.round(mom.changePct))}% ${dir} than last month so far.`,
    );
  }
  if (cats.length > 0 && cats[0].pct >= 35) {
    out.push(
      `${cats[0].category} is your biggest category — ${Math.round(
        cats[0].pct,
      )}% of spending.`,
    );
  }
  // Upcoming debt due dates.
  const soon = data.debts
    .filter((d) => d.direction === "i_owe" && d.dueDate)
    .map((d) => ({ d, days: Math.ceil((new Date(d.dueDate! + "T00:00:00").getTime() - Date.now()) / 86400000) }))
    .filter((x) => x.days >= 0 && x.days <= 7)
    .sort((a, b) => a.days - b.days)[0];
  if (soon) {
    out.push(
      `${soon.d.party} is due in ${soon.days} day${soon.days === 1 ? "" : "s"}.`,
    );
  }
  // Unpaid recurring bill due within the week.
  const billSoon = billsThisMonth(data)
    .filter((b) => !b.paid && b.daysAway >= 0 && b.daysAway <= 6)
    .sort((a, b) => a.daysAway - b.daysAway)[0];
  if (billSoon) {
    out.push(
      billSoon.daysAway === 0
        ? `${billSoon.bill.name} is due today.`
        : `${billSoon.bill.name} is due in ${billSoon.daysAway} day${billSoon.daysAway === 1 ? "" : "s"}.`,
    );
  }
  return out.slice(0, max);
}
