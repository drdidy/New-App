import type { AppData, Debt, DebtKind, RecurringBill } from "./types";
import { monthKey, prevMonthKey } from "./format";

// The household's monthly income baseline: this month's logged income if any,
// otherwise the sum of members' stated monthly incomes (or legacy single value).
export function baselineIncome(data: AppData): number {
  const month = monthKey();
  const logged = data.transactions
    .filter((t) => t.type === "income" && t.date.startsWith(month))
    .reduce((s, t) => s + t.amount, 0);
  if (logged > 0) return logged;
  const members = data.members.reduce((s, m) => s + (m.monthlyIncome || 0), 0);
  return members || data.monthlyIncome || 0;
}

export interface MoneyPlan {
  income: number;
  bills: number; // fixed recurring bills
  debtMin: number; // minimum debt payments
  savings: number; // planned goal contributions
  budgeted: number; // category spending budgets
  allocated: number;
  leftover: number; // income - allocated (negative = over-allocated)
}

// Zero-based "give every dollar a job" view of the month.
export function moneyPlan(data: AppData): MoneyPlan {
  const income = baselineIncome(data);
  const bills = (data.recurringBills || []).reduce((s, b) => s + b.amount, 0);
  const debtMin = data.debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + (d.minPayment || 0), 0);
  const savings = (data.goals || []).reduce(
    (s, g) => s + (g.monthlyContribution || 0),
    0,
  );
  const budgeted = data.budgets.reduce((s, b) => s + b.limit, 0);
  const allocated = bills + debtMin + savings + budgeted;
  return { income, bills, debtMin, savings, budgeted, allocated, leftover: income - allocated };
}

export interface Pace {
  daysLeft: number;
  periodLabel: string; // e.g. "left this month" / "until payday May 28"
  dailyAllowance: number; // safe-to-spend spread over the rest of the period
  projectedSpend: number; // end-of-month spend at the current rate
  forecastLeftover: number; // income - projected spend
}

// Turns the headline "safe to spend" into a daily allowance (over the current
// pay period) plus a month-end forecast based on the current spending pace.
export function pace(data: AppData, safeToSpend: number): Pace {
  const cycle = cycleInfo(data);
  const now = new Date();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const day = now.getDate();

  const month = monthKey();
  const monthExpenses = data.transactions
    .filter((t) => t.type === "expense" && t.date.startsWith(month))
    .reduce((s, t) => s + t.amount, 0);
  const projectedSpend = day > 0 ? (monthExpenses / day) * daysInMonth : monthExpenses;

  return {
    daysLeft: cycle.daysLeft,
    periodLabel: cycle.label,
    dailyAllowance: Math.max(0, safeToSpend) / cycle.daysLeft,
    projectedSpend,
    forecastLeftover: baselineIncome(data) - projectedSpend,
  };
}

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

function expenseParts(t: { category: string; amount: number; lineItems?: { category: string; amount: number }[] }) {
  const items = (t.lineItems || []).filter((x) => x.amount > 0);
  if (items.length === 0) return [{ category: t.category, amount: t.amount }];
  const parts = items.map((x) => ({ category: x.category || t.category, amount: x.amount }));
  const itemTotal = parts.reduce((s, x) => s + x.amount, 0);
  const remainder = Math.round((t.amount - itemTotal) * 100) / 100;
  if (remainder > 0.01) parts.push({ category: t.category, amount: remainder });
  return parts;
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
    for (const part of expenseParts(t)) {
      totals.set(part.category, (totals.get(part.category) || 0) + part.amount);
      sum += part.amount;
    }
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
    for (const part of expenseParts(t)) {
      spentByCat.set(part.category, (spentByCat.get(part.category) || 0) + part.amount);
    }
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

// --- accounts / net worth ---------------------------------------------------

export function cashOnHand(data: AppData): number {
  return (data.accounts || []).reduce((s, a) => s + a.balance, 0);
}

// Cash you can actually spend *now*: checking + cash balances. Savings and
// investments are real assets but aren't day-to-day spending money, so they're
// excluded from "safe to spend". Falls back to all accounts if the household
// hasn't typed any as checking/cash.
export function spendableCash(data: AppData): number {
  const accounts = data.accounts || [];
  const liquid = accounts.filter((a) => a.type === "checking" || a.type === "cash");
  const pool = liquid.length > 0 ? liquid : accounts;
  return pool.reduce((s, a) => s + a.balance, 0);
}

export interface SafeToSpend {
  // "cash" = grounded in real money on hand (preferred); "income" = fallback
  // projection from monthly income when no accounts are tracked yet.
  mode: "cash" | "income";
  safe: number; // free to spend before the next payday
  spendable: number; // cash on hand (or income left, in income mode)
  committed: number; // obligations due before payday (bills + debt minimums)
  billsDue: number;
  debtDue: number;
  daysLeft: number;
  periodLabel: string; // e.g. "until payday May 28" / "left this month"
  dailyAllowance: number;
  hasAccounts: boolean;
}

// The real headline number. Instead of "income minus everything", this answers
// the question the user actually has mid-month: *of the money I have right now,
// how much is free to spend before my next payday* — after the bills and debt
// minimums that fall due before then. Grounded in real cash when accounts
// exist; otherwise falls back to an income-based projection.
export function safeToSpend(data: AppData, memberId?: string): SafeToSpend {
  const cycle = cycleInfo(data);
  const month = monthKey();
  const accounts = data.accounts || [];
  const hasAccounts = accounts.length > 0;

  // Bills not yet paid this month whose due date lands on or before the next
  // payday — only those reduce *this period's* spendable cash.
  const now = new Date();
  const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
  const endTime = cycle.end.getTime();
  const billsDue = (data.recurringBills || [])
    .filter((b) => !memberId || b.memberId === memberId)
    .filter((b) => b.lastPaidMonth !== month)
    .filter((b) => {
      const day = Math.min(b.dayOfMonth, daysInMonth);
      const dueThisMonth = new Date(now.getFullYear(), now.getMonth(), day);
      return dueThisMonth.getTime() <= endTime;
    })
    .reduce((s, b) => s + b.amount, 0);

  // Debt minimums (money you owe) due before the next payday, less anything
  // already paid toward debt this month.
  const myDebts = (memberId ? data.debts.filter((d) => d.memberId === memberId) : data.debts)
    .filter((d) => d.direction === "i_owe" && d.balance > 0);
  const debtMinDue = myDebts
    .filter((d) => {
      if (!d.dueDate) return cycle.label === "left this month"; // monthly: assume due this month
      return new Date(d.dueDate + "T00:00:00").getTime() <= endTime;
    })
    .reduce((s, d) => s + Math.min(d.minPayment || 0, d.balance), 0);
  const debtPaidThisMonth = data.transactions
    .filter(
      (t) =>
        t.type === "expense" &&
        t.category === "Debt payment" &&
        t.date.startsWith(month) &&
        (!memberId || t.memberId === memberId),
    )
    .reduce((s, t) => s + t.amount, 0);
  const debtDue = Math.max(0, debtMinDue - debtPaidThisMonth);

  const committed = billsDue + debtDue;

  if (hasAccounts) {
    const spendable = spendableCash(data);
    const safe = spendable - committed;
    return {
      mode: "cash",
      safe,
      spendable,
      committed,
      billsDue,
      debtDue,
      daysLeft: cycle.daysLeft,
      periodLabel: cycle.label,
      dailyAllowance: Math.max(0, safe) / cycle.daysLeft,
      hasAccounts: true,
    };
  }

  // Income-mode fallback: income left this month minus committed money.
  const income = baselineIncome(data);
  const expenses = data.transactions
    .filter((t) => t.type === "expense" && t.date.startsWith(month) && (!memberId || t.memberId === memberId))
    .reduce((s, t) => s + t.amount, 0);
  const spendable = income - expenses;
  const safe = spendable - committed;
  return {
    mode: "income",
    safe,
    spendable,
    committed,
    billsDue,
    debtDue,
    daysLeft: cycle.daysLeft,
    periodLabel: cycle.label,
    dailyAllowance: Math.max(0, safe) / cycle.daysLeft,
    hasAccounts: false,
  };
}

// --- debt classification -----------------------------------------------------

// Infer whether a debt is owed to a person or an organization. Used to migrate
// legacy debts that predate the explicit `kind` field, and to default the form.
export function inferDebtKind(d: { party: string; apr?: number; kind?: DebtKind }): DebtKind {
  if (d.kind) return d.kind;
  const p = (d.party || "").toLowerCase();
  if (/(visa|mastercard|amex|card|capital one|chase|barclay|discover|credit)/.test(p)) return "card";
  if (/(klarna|afterpay|affirm|paypal pay|zip|sezzle|bnpl)/.test(p)) return "bnpl";
  if (/(loan|finance|bank|mortgage|auto|student|sofi|lending|credit union)/.test(p)) return "loan";
  // Cards/loans tend to carry interest; a bare APR is a strong organization tell.
  if ((d.apr || 0) > 0) return "card";
  // A single-word, capitalized-looking name with no APR reads as a person.
  return /^\s*\S+\s*$/.test(d.party || "") ? "person" : "other";
}

export const DEBT_KIND_IS_ORG: Record<DebtKind, boolean> = {
  person: false,
  card: true,
  loan: true,
  bnpl: true,
  other: true,
};

export function netWorth(data: AppData): number {
  const owedToMe = data.debts
    .filter((d) => d.direction === "owed_to_me")
    .reduce((s, d) => s + d.balance, 0);
  const iOwe = data.debts
    .filter((d) => d.direction === "i_owe")
    .reduce((s, d) => s + d.balance, 0);
  return cashOnHand(data) + owedToMe - iOwe;
}

// --- trends ------------------------------------------------------------------

export interface MonthTotal {
  month: string; // "YYYY-MM"
  label: string; // short month label, e.g. "May"
  income: number;
  expense: number;
}

// Income vs expense for the last `n` months (oldest → newest).
export function monthlyTotals(data: AppData, n = 6): MonthTotal[] {
  const now = new Date();
  const out: MonthTotal[] = [];
  for (let i = n - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = monthKey(d);
    out.push({
      month: key,
      label: d.toLocaleDateString(undefined, { month: "short" }),
      income: 0,
      expense: 0,
    });
  }
  const idx = new Map(out.map((m, i) => [m.month, i]));
  for (const t of data.transactions) {
    const key = t.date.slice(0, 7);
    const i = idx.get(key);
    if (i === undefined) continue;
    if (t.type === "income") out[i].income += t.amount;
    else out[i].expense += t.amount;
  }
  return out;
}

// --- pay cycle ---------------------------------------------------------------

export interface CycleInfo {
  daysLeft: number; // days remaining in the current period (incl. today)
  label: string; // e.g. "left this month" / "until payday May 28"
  end: Date;
}

function addDays(d: Date, n: number): Date {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
}

// The current budgeting period based on the household's pay cycle.
export function cycleInfo(data: AppData): CycleInfo {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const pc = data.payCycle || { type: "monthly" };

  if (pc.type === "monthly" || !pc.anchor) {
    const end = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    const daysLeft = Math.max(1, Math.round((end.getTime() - today.getTime()) / 86400000) + 1);
    return { daysLeft, label: "left this month", end };
  }

  const len = pc.type === "weekly" ? 7 : pc.type === "biweekly" ? 14 : 15;
  const anchor = new Date(pc.anchor + "T00:00:00");
  // Walk forward from the anchor in steps of `len` to the next payday > today.
  let next = new Date(anchor);
  if (pc.type === "semimonthly") {
    // Paydays on the anchor day and ~15 days later, each month.
    const day = anchor.getDate();
    const candidates = [
      new Date(now.getFullYear(), now.getMonth(), day),
      new Date(now.getFullYear(), now.getMonth(), Math.min(day + 15, 28)),
      new Date(now.getFullYear(), now.getMonth() + 1, day),
    ];
    next = candidates.find((c) => c.getTime() > today.getTime()) || candidates[2];
  } else {
    while (next.getTime() <= today.getTime()) next = addDays(next, len);
  }
  const daysLeft = Math.max(1, Math.round((next.getTime() - today.getTime()) / 86400000));
  return {
    daysLeft,
    label: `until payday ${next.toLocaleDateString(undefined, { month: "short", day: "numeric" })}`,
    end: next,
  };
}

// --- what-if debt simulator --------------------------------------------------

export interface PayoffSim {
  months: number | null; // null = never clears at this payment level
  totalInterest: number;
}

// Simulate paying off all "I owe" debts with the given method + extra/month,
// accruing monthly interest. Used by the what-if slider.
export function simulatePayoff(
  data: AppData,
  method: "snowball" | "avalanche",
  extraPerMonth: number,
  maxMonths = 720,
): PayoffSim {
  const bal = data.debts
    .filter((d) => d.direction === "i_owe" && d.balance > 0)
    .map((d) => ({ balance: d.balance, apr: d.apr || 0, min: d.minPayment || 0 }));
  if (bal.length === 0) return { months: 0, totalInterest: 0 };

  const order = [...bal].sort((a, b) =>
    method === "snowball" ? a.balance - b.balance : b.apr - a.apr,
  );

  let months = 0;
  let totalInterest = 0;
  while (bal.some((d) => d.balance > 0.01) && months < maxMonths) {
    months++;
    // Accrue interest.
    for (const d of bal) {
      if (d.balance > 0) {
        const i = d.balance * (d.apr / 100 / 12);
        d.balance += i;
        totalInterest += i;
      }
    }
    let pool =
      bal.reduce((s, d) => s + (d.balance > 0 ? d.min : 0), 0) + extraPerMonth;
    // Minimums first.
    for (const d of bal) {
      if (d.balance > 0 && pool > 0) {
        const pay = Math.min(d.min, d.balance, pool);
        d.balance -= pay;
        pool -= pay;
      }
    }
    // Funnel the rest by method order.
    for (const d of order) {
      if (pool <= 0) break;
      if (d.balance > 0) {
        const pay = Math.min(pool, d.balance);
        d.balance -= pay;
        pool -= pay;
      }
    }
  }
  return { months: months >= maxMonths ? null : months, totalInterest };
}

// Month-by-month total remaining balance under a given method + extra payment,
// using the same interest-accruing engine as simulatePayoff. Drives the real
// payoff projection chart (no more hardcoded curve).
export function payoffProjection(
  data: AppData,
  method: "snowball" | "avalanche",
  extraPerMonth: number,
  maxMonths = 600,
): number[] {
  const bal = data.debts
    .filter((d) => d.direction === "i_owe" && d.balance > 0)
    .map((d) => ({ balance: d.balance, apr: d.apr || 0, min: d.minPayment || 0 }));
  const series: number[] = [bal.reduce((s, d) => s + d.balance, 0)];
  if (bal.length === 0) return series;
  const order = [...bal].sort((a, b) =>
    method === "snowball" ? a.balance - b.balance : b.apr - a.apr,
  );
  let months = 0;
  while (bal.some((d) => d.balance > 0.01) && months < maxMonths) {
    months++;
    for (const d of bal) {
      if (d.balance > 0) d.balance += d.balance * (d.apr / 100 / 12);
    }
    let pool = bal.reduce((s, d) => s + (d.balance > 0 ? d.min : 0), 0) + extraPerMonth;
    for (const d of bal) {
      if (d.balance > 0 && pool > 0) {
        const pay = Math.min(d.min, d.balance, pool);
        d.balance -= pay;
        pool -= pay;
      }
    }
    for (const d of order) {
      if (pool <= 0) break;
      if (d.balance > 0) {
        const pay = Math.min(pool, d.balance);
        d.balance -= pay;
        pool -= pay;
      }
    }
    series.push(Math.max(0, bal.reduce((s, d) => s + d.balance, 0)));
  }
  return series;
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
