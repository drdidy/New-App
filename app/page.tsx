"use client";

import Link from "next/link";
import {
  AlertCircle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  HeartPulse,
  Home,
  PiggyBank,
  ReceiptText,
  ShieldCheck,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  budgetStatus,
  categoryBreakdown,
  monthlyTotals,
  netWorth,
  pace,
  quickInsights,
} from "@/lib/insights";
import { clampPct, formatMoney, friendlyDate } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";
import QuickCapture from "@/components/QuickCapture";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import { ActionButton, EmptyState, PageHeader, StatPill } from "@/components/PremiumUI";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function healthScore(safeToSpend: number, net: number, budgetPct: number) {
  let score = 72;
  if (safeToSpend > 0) score += 8;
  if (net >= 0) score += 8;
  if (budgetPct <= 75) score += 8;
  if (budgetPct > 100) score -= 16;
  if (safeToSpend < 0) score -= 18;
  return clampPct(score);
}

export default function TodayPage() {
  const { data, ready } = useStore();
  if (!ready) return null;

  const summary = summarize(data);
  const firstName = data.members[0]?.name?.split(" ")[0] || "there";
  const bills = billsThisMonth(data).filter((b) => !b.paid);
  const recent = data.transactions.slice(0, 4);
  const trend = monthlyTotals(data, 7);
  const trendValues = trend.map((m) => m.expense);
  const budgets = budgetStatus(data);
  const avgBudget =
    budgets.length > 0
      ? budgets.reduce((sum, b) => sum + Math.min(b.pct, 140), 0) / budgets.length
      : 0;
  const score = healthScore(summary.safeToSpend, netWorth(data), avgBudget);
  const daily = pace(data, summary.safeToSpend);
  const goal = data.goals[0];
  const insights = quickInsights(data, data.currency, 3);
  const topCategory = categoryBreakdown(data)[0];
  const budgetSpent = data.budgets.reduce((sum, b) => sum + b.limit, 0);
  const trendForChart = trendValues.some(Boolean) ? trendValues : trend.map(() => 0);
  const hasTransactions = data.transactions.length > 0;
  const hasBudgets = data.budgets.length > 0;
  const hasFinancialInputs =
    hasTransactions ||
    hasBudgets ||
    data.recurringBills.length > 0 ||
    data.debts.length > 0 ||
    data.goals.length > 0 ||
    data.accounts.length > 0 ||
    data.members.some((m) => (m.monthlyIncome || 0) > 0) ||
    (data.monthlyIncome || 0) > 0;
  const planStatus =
    !hasFinancialInputs
      ? "Ready to start"
      : summary.safeToSpend < 0
        ? "Needs attention"
        : budgets.some((b) => b.over)
          ? "Budget pressure"
          : "Plan looks steady";

  return (
    <main className="vision-page today-dashboard">
      <PageHeader
        title={`${greeting()}, ${firstName === "there" ? "David" : firstName}`}
        subtitle="Here's what your money can safely do today."
        action={<StatPill>Today · {planStatus}</StatPill>}
      />

      <section className="vision-grid today-grid">
        <article className="vision-card safe-card hero-money-card span-5">
          <div className="vision-card-title">
            <span><ShieldCheck size={16} /> Safe to Spend</span>
            <small>Protected money first</small>
          </div>
          <div className="metric-xl">
            {hasFinancialInputs ? (
              <AnimatedNumber value={summary.safeToSpend} currency={data.currency} />
            ) : (
              <span className="metric-text">Ready</span>
            )}
          </div>
          <p>
            {hasFinancialInputs
              ? "Available after protected bills and goals."
              : "Add income, bills, or spending to calculate your safe-to-spend number."}
          </p>
          <div className="mini-progress">
            <span style={{ width: `${hasFinancialInputs ? (summary.safeToSpend > 0 ? 68 : 18) : 24}%` }} />
          </div>
          <small>
            {hasFinancialInputs
              ? summary.safeToSpend >= 0
                ? `For the rest of ${daily.periodLabel}.`
                : "Pause flexible spending and recover the plan."
              : "Quick Capture can start with text, voice, or a receipt."}
          </small>
          <ActionButton href="/plan">Review plan</ActionButton>
        </article>

        <article className="vision-card budget-snapshot span-3">
          <div className="vision-card-title">
            <span><WalletCards size={16} /> Budget Snapshot</span>
            <small>Today</small>
          </div>
          {hasBudgets ? (
            <div className="split-card-content">
            <Ring pct={avgBudget} size={150} stroke={12} color="#84d6a5">
              <strong>{Math.round(avgBudget)}%</strong>
              <span>of budget</span>
            </Ring>
            <div className="stacked-stats">
              <span>Spent <b>{formatMoney(summary.expenses, data.currency)}</b></span>
              <span>Budget <b>{budgetSpent ? formatMoney(budgetSpent, data.currency) : "Set one"}</b></span>
              <span>Daily pace <b>{formatMoney(daily.dailyAllowance, data.currency)}</b></span>
            </div>
            </div>
          ) : (
            <EmptyState
              Icon={WalletCards}
              title="No daily budget set"
              body="Set a monthly budget so Money Coach can show your daily pace."
              action="Set daily budget"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card health-score span-4">
          <div className="vision-card-title">
            <span><HeartPulse size={16} /> Financial Health Score</span>
          </div>
          {hasFinancialInputs ? (
            <>
              <Ring pct={score} size={152} stroke={12} color="#84d6a5">
                <strong>{Math.round(score)}</strong>
                <span>{score >= 80 ? "Great" : score >= 65 ? "Stable" : "Needs care"}</span>
              </Ring>
              <p>You are making smart financial choices.</p>
              <Link href="/spending" className="soft-button">See insights</Link>
            </>
          ) : (
            <EmptyState
              Icon={HeartPulse}
              title="Score is waiting"
              body="Add a few real numbers and Money Coach will build your financial health view."
              action="Start tracking"
              href="/"
            />
          )}
        </article>

        <article className="vision-card quick-capture-card span-12">
          <div className="vision-card-title">
            <span><ReceiptText size={16} /> Quick Capture</span>
            <small>Type, voice, or scan receipt</small>
          </div>
          <QuickCapture />
        </article>

        <article className="vision-card span-6">
          <div className="vision-card-title">
            <span><TrendingUp size={16} /> Spending Trend</span>
            <small>This week</small>
          </div>
          {hasTransactions ? (
            <>
              <div className="metric-row">
                <strong>{formatMoney(summary.expenses, data.currency)}</strong>
                <span>{topCategory ? `${topCategory.category} leads spending` : "Building pattern"}</span>
              </div>
              <Sparkline
                values={trendForChart}
                labels={trend.map((m) => m.label.slice(0, 3))}
                color="#6EE7A8"
                height={150}
              />
            </>
          ) : (
            <EmptyState
              Icon={ReceiptText}
              title="No spending logged yet"
              body="Add a transaction or scan a receipt to start seeing patterns."
              action="Quick capture"
              href="/"
            />
          )}
        </article>

        <article className="vision-card span-5">
          <div className="vision-card-title">
            <span><Calendar size={16} /> Upcoming Bills</span>
            <small>This week</small>
          </div>
          <div className="vision-list">
            {(bills.length ? bills.slice(0, 4) : []).map((b) => (
              <div className="vision-list-row" key={b.bill.id}>
                <span className="icon-tile"><Home size={16} /></span>
                <div>
                  <strong>{b.bill.name}</strong>
                  <small>{b.daysAway === 0 ? "Due today" : `Due day ${b.dueDay}`}</small>
                </div>
                <b>{formatMoney(b.bill.amount, data.currency)}</b>
              </div>
            ))}
            {bills.length === 0 && (
              <EmptyState
                Icon={Calendar}
                title="No upcoming bills"
                body="Add bills and subscriptions so your safe-to-spend can protect them."
                action="Add bill"
                href="/bills"
              />
            )}
          </div>
          <Link href="/bills" className="text-link">View all bills <ArrowRight size={14} /></Link>
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title">
            <span><ReceiptText size={16} /> Recent Transactions</span>
            <Link href="/spending">See all</Link>
          </div>
          <div className="vision-list">
            {recent.map((t) => (
              <div className="vision-list-row" key={t.id}>
                <span className="icon-tile">{t.type === "income" ? "+" : "-"}</span>
                <div>
                  <strong>{t.description || t.category}</strong>
                  <small>{friendlyDate(t.date)} - {t.category}</small>
                </div>
                <b className={t.type === "income" ? "positive" : "negative"}>
                  {t.type === "income" ? "+" : "-"}{formatMoney(t.amount, data.currency)}
                </b>
              </div>
            ))}
            {recent.length === 0 && (
              <EmptyState
                Icon={ReceiptText}
                title="No recent activity"
                body="Log your first transaction to start building a useful money timeline."
                action="Log transaction"
                href="/"
              />
            )}
          </div>
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title">
            <span><PiggyBank size={16} /> Savings Goal</span>
          </div>
          {goal ? (
            <>
              <h3>{goal.name}</h3>
              <div className="metric-xl small">{formatMoney(goal.saved, data.currency)}</div>
              <p>of {formatMoney(goal.target, data.currency)}</p>
              <div className="mini-progress">
                <span style={{ width: `${clampPct((goal.saved / goal.target) * 100)}%` }} />
              </div>
              <Link href="/plan" className="soft-button">Contribute</Link>
            </>
          ) : (
            <EmptyState
              Icon={PiggyBank}
              title="No savings goal yet"
              body="Create your first goal to protect your future."
              action="Create goal"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title">
            <span><AlertCircle size={16} /> Alerts & Reminders</span>
            <Link href="/coach">See all</Link>
          </div>
          <div className="vision-list compact">
            {(insights.length ? insights : ["You are ready for a weekly money check-in."]).map((text) => (
              <div className="vision-list-row" key={text}>
                <span className="icon-tile glow"><CheckCircle2 size={15} /></span>
                <div>
                  <strong>{text}</strong>
                  <small>Money Coach</small>
                </div>
              </div>
            ))}
          </div>
        </article>

      </section>
    </main>
  );
}
