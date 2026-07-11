import type { AppData, Debt, DebtKind, RecurringBill } from "./types";
import { monthKey, prevMonthKey, formatMoney } from "./format";

// The household's monthly income baseline: this month's logged income if any,
// otherwise the sum of members' stated monthly incomes (or legacy single value).
export function baselineIncome(data: AppData): number {
  const month = monthKey();
  const logged = data.transactions
    .filter((t) => t.type === "income" && t.date.startsWith(month))
    .reduce((s, t) => s + t.amount, 0);
  if (logged > 0) return logged;
  // Planned recurring income (e.g. a salary) is the next-best baseline.
  const recurring = (data.recurringIncome || []).reduce((s, x) => s + (x.amount || 0), 0);
  if (recurring > 0) return recurring;
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
  // Compare like-for-like: this month so far vs the previous month up to the
  // SAME day, so early in the month we don't claim a huge spurious drop.
  const dayCap = new Date().getDate();
  let thisMonth = 0;
  let lastMonth = 0;
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    const dom = parseInt(t.date.slice(8, 10), 10) || 1;
    if (t.date.startsWith(cur)) thisMonth += t.amount;
    else if (t.date.startsWith(prev) && dom <= dayCap) lastMonth += t.amount;
  }
  const changePct =
    lastMonth > 0 ? ((thisMonth - lastMonth) / lastMonth) * 100 : null;
  return { thisMonth, lastMonth, changePct };
}

// Your typical cumulative spend by this point in the month, averaged over up
// to three prior months (each capped at today's day-of-month so the comparison
// is like-for-like). Powers the "you're usually at $X by now" pace line.
export function monthPace(data: AppData): { typical: number; actual: number; day: number; months: number } | null {
  const day = new Date().getDate();
  const cur = monthKey();
  const keys: string[] = [];
  {
    const d = new Date();
    for (let i = 1; i <= 3; i++) {
      const m = new Date(d.getFullYear(), d.getMonth() - i, 1);
      keys.push(monthKey(m));
    }
  }
  const sums = new Map<string, number>(keys.map((k) => [k, 0]));
  const seen = new Set<string>();
  let actual = 0;
  for (const t of data.transactions) {
    if (t.type !== "expense") continue;
    const m = t.date.slice(0, 7);
    if (m === cur) { actual += t.amount; continue; }
    if (!sums.has(m)) continue;
    seen.add(m);
    const dom = parseInt(t.date.slice(8, 10), 10) || 1;
    if (dom <= day) sums.set(m, (sums.get(m) || 0) + t.amount);
  }
  if (seen.size === 0) return null;
  let total = 0;
  for (const k of seen) total += sums.get(k) || 0;
  // No baseline worth speaking of (prior months spent nothing by this day) —
  // "you're usually at $0" is noise, not insight.
  if (total <= 0) return null;
  return { typical: total / seen.size, actual, day, months: seen.size };
}

// --- accounts / net worth ---------------------------------------------------

// Net of money logged since the balances were last set by hand. Income adds,
// expenses subtract — so logging "received $1,480" or "spent $40" actually
// moves your cash on hand. Anchored per the primary liquid account's
// balanceAsOf so a hand-set balance is never double-counted against old logs.
function loggedSinceBalance(data: AppData): number {
  const accounts = data.accounts || [];
  if (accounts.length === 0) return 0;
  // Logged transactions are attributed to the primary liquid account, so anchor
  // to ITS balanceAsOf. (Adding or moving money to other accounts must not shift
  // this anchor, or previously-logged cash would vanish.)
  const anchor = accounts.find((a) => a.type === "checking" || a.type === "cash") || accounts[0];
  const since = anchor.balanceAsOf ?? anchor.createdAt ?? 0;
  let adj = 0;
  for (const t of data.transactions) {
    if ((t.createdAt ?? 0) <= since) continue;
    adj += t.type === "income" ? t.amount : -t.amount;
  }
  return adj;
}

export function cashOnHand(data: AppData): number {
  return (data.accounts || []).reduce((s, a) => s + a.balance, 0) + loggedSinceBalance(data);
}

// --- engagement: daily logging streak --------------------------------------

function localDayMinus(n: number): string {
  const d = new Date();
  d.setDate(d.getDate() - n);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export interface Streak {
  count: number; // consecutive days (up to today) with at least one logged entry
  loggedToday: boolean;
  best: number; // longest streak ever
}

// A gentle habit loop: how many days in a row the household has logged something.
// Counts any day with at least one transaction. If today isn't logged yet the
// streak is still "alive" (counted through yesterday) so we can nudge to keep it.
export function loggingStreak(data: AppData): Streak {
  const days = new Set<string>();
  for (const t of data.transactions) days.add(t.date.slice(0, 10));
  const loggedToday = days.has(localDayMinus(0));

  let count = 0;
  let offset = loggedToday ? 0 : 1; // if not logged today, start from yesterday
  while (days.has(localDayMinus(offset))) {
    count++;
    offset++;
  }

  // Longest run anywhere in history.
  const sorted = [...days].sort();
  let best = 0;
  let run = 0;
  let prev: string | null = null;
  for (const d of sorted) {
    if (prev) {
      const a = new Date(prev + "T00:00:00");
      const b = new Date(d + "T00:00:00");
      const gap = Math.round((b.getTime() - a.getTime()) / 86400000);
      run = gap === 1 ? run + 1 : 1;
    } else {
      run = 1;
    }
    best = Math.max(best, run);
    prev = d;
  }

  return { count, loggedToday, best: Math.max(best, count) };
}

// Consecutive days (back from today) with zero spending — a gentle game that
// rewards restraint. Resets the moment you log an expense today. Never counts
// days before the user started using the app.
export function noSpendStreak(data: AppData): number {
  if (data.transactions.length === 0) return 0;
  const spendDays = new Set<string>();
  let earliest = "9999-99-99";
  for (const t of data.transactions) {
    const d = t.date.slice(0, 10);
    if (d < earliest) earliest = d;
    if (t.type === "expense") spendDays.add(d);
  }
  let count = 0;
  for (let offset = 0; offset <= 366; offset++) {
    const day = localDayMinus(offset);
    if (day < earliest) break;
    if (spendDays.has(day)) break;
    count++;
  }
  return count;
}

// Cash you can actually spend *now*: checking + cash balances. Savings and
// investments are real assets but aren't day-to-day spending money, so they're
// excluded from "safe to spend". Falls back to all accounts if the household
// hasn't typed any as checking/cash.
export function spendableCash(data: AppData): number {
  const accounts = data.accounts || [];
  const liquid = accounts.filter((a) => a.type === "checking" || a.type === "cash");
  const pool = liquid.length > 0 ? liquid : accounts;
  return pool.reduce((s, a) => s + a.balance, 0) + loggedSinceBalance(data);
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
  setAside: number; // money earmarked in buckets (not free to spend)
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
  // Money assigned a job in buckets (tithe, savings, giving…) isn't free to
  // spend — true envelope behavior. Member-scoped buckets honor the filter.
  const setAside = (data.buckets || [])
    .filter((b) => !memberId || b.memberId === memberId)
    .reduce((s, b) => s + Math.max(0, b.balance), 0);

  if (hasAccounts) {
    const spendable = spendableCash(data);
    const safe = spendable - committed - setAside;
    return {
      mode: "cash",
      safe,
      spendable,
      committed,
      billsDue,
      debtDue,
      setAside,
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
  const safe = spendable - committed - setAside;
  return {
    mode: "income",
    safe,
    spendable,
    committed,
    billsDue,
    debtDue,
    setAside,
    daysLeft: cycle.daysLeft,
    periodLabel: cycle.label,
    dailyAllowance: Math.max(0, safe) / cycle.daysLeft,
    hasAccounts: false,
  };
}

// People you owe rarely give you a payment plan — they just want it back. When
// you can't pay in full, this suggests a fair, affordable amount to send now,
// grounded in what's actually safe to spend, so you can chip away without going
// broke (and so you have something concrete to offer them).
export interface PersonPaymentAdvice {
  mode: "full" | "partial" | "tight";
  amount: number; // suggested to send now
  months: number; // months to clear at that pace (partial only)
  spare: number; // safe to spend right now
}

export function suggestPersonPayment(data: AppData, debt: Debt): PersonPaymentAdvice | null {
  if (debt.direction !== "i_owe" || debt.balance <= 0) return null;
  const spare = Math.max(0, safeToSpend(data, debt.memberId).safe);
  const bal = debt.balance;

  // Can clear it without going under — just settle up.
  if (spare >= bal) return { mode: "full", amount: bal, months: 1, spare };

  // Otherwise aim to clear in ~3 months, but never send more than half of
  // what's spare so a buffer stays. Tidy to the nearest $5.
  let amount = Math.round(Math.min(bal / 3, spare * 0.5) / 5) * 5;
  if (amount < 5 && spare > 0) amount = Math.min(bal, Math.max(5, Math.round(spare)));
  if (amount <= 0) return { mode: "tight", amount: 0, months: 0, spare };

  const months = Math.max(1, Math.ceil(bal / amount));
  return { mode: "partial", amount, months, spare };
}

// "Future you" — a motivating, honest projection of where the current pace
// leads: debt down, savings up, net worth climbing. Clearly an estimate.
export interface FutureProjection {
  months: number;
  debtNow: number;
  debtThen: number;
  savedAdded: number;
  netWorthThen: number;
  debtFreeInMonths: number | null;
  monthlySave: number;
}

export function futureProjection(data: AppData, months = 12): FutureProjection | null {
  const income = baselineIncome(data);
  const iOwe = (data.debts || []).filter((d) => d.direction === "i_owe" && d.balance > 0);
  const debtNow = iOwe.reduce((s, d) => s + d.balance, 0);
  const monthlyDebtPay = iOwe.reduce((s, d) => s + (d.minPayment || 0), 0);
  const goalSave = (data.goals || []).reduce((s, g) => s + (g.monthlyContribution || 0), 0);
  const bucketSave = (data.buckets || [])
    .filter((b) => (b.kind === "save" || b.kind === "invest") && b.allocType && b.allocValue)
    .reduce((s, b) => s + (b.allocType === "percent" ? (income * (b.allocValue || 0)) / 100 : (b.allocValue || 0)), 0);
  // Reality cap: you can't save + pay debt faster than you earn. Debt minimums
  // are mandatory, so savings flexes down to what income can actually cover.
  const monthlySaveRaw = goalSave + bucketSave;
  const monthlySave = income > 0 ? Math.min(monthlySaveRaw, Math.max(0, income - monthlyDebtPay)) : monthlySaveRaw;
  if (debtNow <= 0 && monthlySave <= 0) return null;
  const debtThen = Math.max(0, debtNow - monthlyDebtPay * months);
  const savedAdded = monthlySave * months;
  const netWorthThen = netWorth(data) + savedAdded + (debtNow - debtThen);
  const sim = simulatePayoff(data, "avalanche", 0);
  return { months, debtNow, debtThen, savedAdded, netWorthThen, debtFreeInMonths: sim.months, monthlySave };
}

// "Give & save first" — when income has landed this month and the household has
// buckets with auto-fill rules, preview how a paycheck would split so we can
// nudge them to set aside their tithe / savings before it gets spent.
export interface PaycheckPlan {
  income: number;
  setAside: number;
  tithe: number;
  bucketCount: number;
}

export function paycheckPlan(data: AppData): PaycheckPlan | null {
  const month = monthKey();
  const income = data.transactions
    .filter((t) => t.type === "income" && t.date.startsWith(month))
    .reduce((s, t) => s + t.amount, 0);
  if (income <= 0) return null;
  const buckets = (data.buckets || []).filter((b) => b.allocType && b.allocValue);
  if (buckets.length === 0) return null;
  const items = buckets
    .map((b) => ({ kind: b.kind, amount: b.allocType === "percent" ? (income * (b.allocValue || 0)) / 100 : (b.allocValue || 0) }))
    .filter((i) => i.amount > 0);
  if (items.length === 0) return null;
  return {
    income,
    setAside: items.reduce((s, i) => s + i.amount, 0),
    tithe: items.filter((i) => i.kind === "give").reduce((s, i) => s + i.amount, 0),
    bucketCount: items.length,
  };
}

// "Can I afford this?" — an instant gut-check for a one-off purchase, grounded
// in real safe-to-spend (cash − what's due before payday), not vibes.
export interface AffordVerdict {
  verdict: "yes" | "caution" | "wait";
  headline: string;
  detail: string;
}

export function affordCheck(data: AppData, amount: number): AffordVerdict | null {
  if (!(amount > 0)) return null;
  const sts = safeToSpend(data);
  const cur = data.currency;
  const m = (n: number) => formatMoney(n, cur);
  const periodTail = sts.daysLeft > 0 ? `the ${sts.daysLeft} days ${sts.periodLabel}` : sts.periodLabel;

  if (amount <= sts.safe) {
    const after = sts.safe - amount;
    return {
      verdict: "yes",
      headline: "Yes — you've got this.",
      detail: `You'd still have ${m(after)} safe to spend for ${periodTail}.`,
    };
  }
  // Technically have the cash, but it eats into money set aside for what's due.
  if (sts.mode === "cash" && amount <= sts.spendable) {
    const into = amount - Math.max(0, sts.safe);
    return {
      verdict: "caution",
      headline: "You can — but it's tight.",
      detail: `This dips ${m(into)} into the ${m(sts.committed)} set aside for bills and debts due before payday. Doable if you trim elsewhere.`,
    };
  }
  const over = amount - Math.max(0, sts.spendable);
  return {
    verdict: "wait",
    headline: "Not yet — give it a few days.",
    detail: `That's about ${m(over)} more than you can safely spend right now${sts.daysLeft > 0 ? `. It'll feel easier after payday in ${sts.daysLeft} day${sts.daysLeft === 1 ? "" : "s"}.` : "."}`,
  };
}

// Match a spoken/typed payee ("James") against debts you owe, tolerant of
// partial names ("James" ⇄ "James Allen"). Returns an exact hit if there is
// one, plus all loose candidates so the UI can confirm when it's ambiguous.
export function matchPersonDebts(
  debts: Debt[],
  party: string,
): { exact?: Debt; candidates: Debt[] } {
  const p = (party || "").trim().toLowerCase();
  if (!p) return { candidates: [] };
  const owed = (debts || []).filter((d) => d.direction === "i_owe" && d.balance > 0);
  const exact = owed.find((d) => d.party.trim().toLowerCase() === p);
  if (exact) return { exact, candidates: [exact] };
  const tokens = (s: string) => s.toLowerCase().split(/\s+/).filter(Boolean);
  const pTok = tokens(p);
  const candidates = owed.filter((d) => {
    const dp = d.party.trim().toLowerCase();
    if (dp.includes(p) || p.includes(dp)) return true; // substring either way
    const dTok = tokens(dp);
    return pTok.some((t) => t.length >= 2 && dTok.includes(t)); // shared name token
  });
  return { candidates };
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
    // Two paydays a month: the anchor day and ~15 days later, wrapping the
    // second into the next month when day+15 overflows (so high anchor days
    // like the 20th give the 20th + ~5th, not a clamped 28th).
    const day = anchor.getDate();
    const dim = (y: number, m: number) => new Date(y, m + 1, 0).getDate();
    const onDay = (y: number, m: number, d: number) => new Date(y, m, Math.min(d, dim(y, m)));
    const second = (y: number, m: number) => {
      const d = day + 15;
      return d <= dim(y, m) ? new Date(y, m, d) : onDay(y, m + 1, d - dim(y, m));
    };
    const y = now.getFullYear();
    const mo = now.getMonth();
    const candidates = [
      onDay(y, mo, day),
      second(y, mo),
      onDay(y, mo + 1, day),
      second(y, mo + 1),
    ].sort((c1, c2) => c1.getTime() - c2.getTime());
    next = candidates.find((c) => c.getTime() > today.getTime()) || candidates[candidates.length - 1];
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
// A proactive "worth knowing" digest — the app noticing things for you, leading
// with wins and useful heads-ups rather than nagging. Returns toned items,
// ranked good → info → warn, so the screen feels encouraging first.
export interface Knowable {
  tone: "good" | "info" | "warn";
  text: string;
}

export function worthKnowing(data: AppData, max = 3): Knowable[] {
  const cur = data.currency;
  const m = (n: number) => formatMoney(n, cur);
  const good: Knowable[] = [];
  const info: Knowable[] = [];
  const warn: Knowable[] = [];

  const mom = monthOverMonth(data);
  const sts = safeToSpend(data);
  const budgets = budgetStatus(data);

  // 🎉 Wins first.
  if (mom.changePct !== null && mom.changePct <= -8) {
    good.push({ tone: "good", text: `You're spending ${Math.abs(Math.round(mom.changePct))}% less than this point last month — nice work.` });
  }
  for (const d of data.debts.filter((x) => x.direction === "i_owe" && (x.original || 0) > 0 && x.balance > 0)) {
    const paidPct = ((d.original! - d.balance) / d.original!) * 100;
    for (const mk of [75, 50, 25]) {
      if (paidPct >= mk && paidPct < mk + 10) { good.push({ tone: "good", text: `You've cleared ${Math.round(paidPct)}% of ${d.party} — momentum's on your side. 🎉` }); break; }
    }
  }

  // ℹ️ Useful heads-ups.
  // Payday runway: project current discretionary pace forward to payday.
  if (sts.daysLeft > 0) {
    const dayOfMonth = new Date().getDate();
    const monthSpend = data.transactions
      .filter((t) => t.type === "expense" && t.date.startsWith(monthKey()) && t.category !== "Debt payment")
      .reduce((s, t) => s + t.amount, 0);
    const dailyAvg = dayOfMonth > 0 ? monthSpend / dayOfMonth : 0;
    if (dailyAvg > 0) {
      const atPayday = sts.safe - dailyAvg * sts.daysLeft;
      if (atPayday >= 0) {
        info.push({ tone: "info", text: `On your current pace you'll reach payday with about ${m(atPayday)} to spare.` });
      } else {
        const easeOff = Math.ceil(-atPayday / sts.daysLeft);
        warn.push({ tone: "warn", text: `At this pace you'd come up short before payday — easing off about ${m(easeOff)}/day keeps you safe.` });
      }
    }
  }
  if (sts.committed > 0) {
    info.push({ tone: "info", text: `${m(sts.committed)} in bills & payments land before payday — already set aside.` });
  }
  // Subscription / recurring radar: a merchant that keeps charging but isn't a
  // tracked bill — likely a subscription worth planning for (or cancelling).
  {
    const billNames = new Set((data.recurringBills || []).map((b) => b.name.toLowerCase().trim()));
    const now = new Date();
    const recent = [0, 1, 2].map((i) => {
      const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    });
    const monthsSeen = new Map<string, Set<string>>();
    const lastAmt = new Map<string, number>();
    for (const t of data.transactions) {
      if (t.type !== "expense" || t.category === "Debt payment") continue;
      const mo = t.date.slice(0, 7);
      if (!recent.includes(mo)) continue;
      const key = (t.description || t.category).trim();
      if (!key || billNames.has(key.toLowerCase())) continue;
      if (!monthsSeen.has(key)) monthsSeen.set(key, new Set());
      monthsSeen.get(key)!.add(mo);
      lastAmt.set(key, t.amount);
    }
    for (const [key, set] of monthsSeen) {
      if (set.size >= 2) {
        info.push({ tone: "info", text: `${key} (~${m(lastAmt.get(key) || 0)}) has charged ${set.size} months running — make it a bill so it's planned for?` });
        break;
      }
    }
  }
  // A category running hot vs last month (subscription / spending creep).
  const thisCats = categoryBreakdown(data);
  const prevCats = categoryBreakdown(data, prevMonthKey());
  for (const c of thisCats) {
    if (c.category === "Debt payment") continue;
    const prev = prevCats.find((p) => p.category === c.category)?.amount || 0;
    if (prev > 0 && c.amount - prev >= 50 && c.amount >= prev * 1.3) {
      info.push({ tone: "info", text: `${c.category} is ${m(c.amount - prev)} higher than last month so far — worth a glance.` });
      break;
    }
  }

  // ⚠️ Gentle alerts.
  if (sts.safe < 0) {
    warn.push({ tone: "warn", text: `You're ${m(-sts.safe)} short for what's due before payday — tap Coach for a plan.` });
  }
  const over = budgets.find((b) => b.over);
  if (over) warn.push({ tone: "warn", text: `Over your ${over.category} budget — ${Math.round(over.pct)}% used.` });
  const billSoon = billsThisMonth(data).filter((b) => !b.paid && b.daysAway >= 0 && b.daysAway <= 4).sort((a, b) => a.daysAway - b.daysAway)[0];
  if (billSoon) warn.push({ tone: "warn", text: billSoon.daysAway === 0 ? `${billSoon.bill.name} is due today.` : `${billSoon.bill.name} is due in ${billSoon.daysAway} day${billSoon.daysAway === 1 ? "" : "s"}.` });

  // Encouraging fallback so the digest is never empty / never doom-only.
  if (good.length === 0 && info.length === 0 && sts.safe >= 0) {
    good.push({ tone: "good", text: `You're on track — ${m(Math.max(0, sts.dailyAllowance))}/day to play with for the ${sts.daysLeft} days ${sts.periodLabel}.` });
  }

  return [...good, ...info, ...warn].slice(0, max);
}

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
  // Biggest *discretionary* category — debt payments are obligations, not
  // spending choices, and calling them "your biggest category" only demoralizes.
  const topSpend = cats.find((c) => c.category !== "Debt payment");
  if (topSpend && topSpend.pct >= 35) {
    out.push(
      `${topSpend.category} is your biggest category — ${Math.round(
        topSpend.pct,
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
