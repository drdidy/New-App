"use client";

import Link from "next/link";
import {
  AlertTriangle,
  ArrowRight,
  Download,
  Filter,
  ReceiptText,
  RotateCcw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  budgetStatus,
  categoryBreakdown,
  monthOverMonth,
  monthlyTotals,
} from "@/lib/insights";
import { formatMoney } from "@/lib/format";
import Donut from "@/components/Donut";
import Sparkline from "@/components/Sparkline";
import { ActionButton, EmptyState, PageHeader } from "@/components/PremiumUI";

const CHART_COLORS = ["#8dbbff", "#84d6a5", "#e3bf74", "#ef8b7d", "#bca7ff", "#9fb4c7", "#7fb7b2"];

export default function SpendingPage() {
  const { data, ready } = useStore();
  if (!ready) return null;

  const summary = summarize(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);
  const mom = monthOverMonth(data);
  const trend = monthlyTotals(data, 7);
  const bills = billsThisMonth(data);
  const budgetTotal = data.budgets.reduce((sum, b) => sum + b.limit, 0);
  const pctBudget = budgetTotal ? Math.round((summary.expenses / budgetTotal) * 100) : 0;
  const outflow = summary.expenses + bills.reduce((sum, b) => sum + b.bill.amount, 0);
  const merchantTotals = new Map<string, { category: string; amount: number }>();

  for (const t of data.transactions.filter((t) => t.type === "expense")) {
    const key = t.description || t.category;
    const prev = merchantTotals.get(key) || { category: t.category, amount: 0 };
    merchantTotals.set(key, { category: prev.category, amount: prev.amount + t.amount });
  }

  const merchants = [...merchantTotals.entries()]
    .map(([name, value]) => ({ name, ...value }))
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 5);

  const slices = (cats.length ? cats : [{ category: "No data", amount: 1, pct: 100 }]).slice(0, 6).map((c, i) => ({
    label: c.category,
    value: c.amount,
    color: CHART_COLORS[i % CHART_COLORS.length],
  }));
  const unusual = cats.find((c) => c.pct > 28) || cats[0];
  const recurring = bills.slice(0, 4);
  const topCategory = cats[0];
  const trendValues = trend.map((m) => m.expense);
  const trendForChart = trendValues.some(Boolean) ? trendValues : trend.map(() => 0);
  const itemTotals = new Map<string, { category: string; amount: number; count: number }>();

  for (const t of data.transactions.filter((t) => t.type === "expense")) {
    for (const item of t.lineItems || []) {
      if (!item.name || item.amount <= 0) continue;
      const key = `${item.category || t.category}::${item.name}`.toLowerCase();
      const prev = itemTotals.get(key) || {
        category: item.category || t.category,
        amount: 0,
        count: 0,
      };
      itemTotals.set(key, {
        category: prev.category,
        amount: prev.amount + item.amount,
        count: prev.count + 1,
      });
    }
  }

  const itemSpending = [...itemTotals.entries()]
    .map(([key, value]) => ({
      name: key.split("::").slice(1).join("::"),
      ...value,
    }))
    .sort((a, b) => b.amount - a.amount)
    .slice(0, 6);
  const hasExpenses = data.transactions.some((t) => t.type === "expense");

  return (
    <main className="vision-page spending-dashboard">
      <PageHeader
        title="Spending"
        subtitle="Understand where your money goes and make smarter choices."
        action={<button className="soft-button icon-button"><Download size={16} aria-hidden="true" /> Export</button>}
      />

      <div className="vision-filters">
        <button>This Month</button>
        <button>All Categories</button>
        <button>All Accounts</button>
        <button className="filter-only"><Filter size={16} /></button>
      </div>

      <section className="vision-grid spending-grid">
        <article className="vision-card stat-card span-4">
          <div className="vision-card-title">
            <span>Total Spending</span>
            <TrendingUp size={16} />
          </div>
          <div className="metric-lg">{hasExpenses ? formatMoney(summary.expenses, data.currency) : <span className="metric-text">Start</span>}</div>
          <p className={mom.changePct != null && mom.changePct > 0 ? "negative" : "positive"}>
            {mom.changePct == null ? "Start tracking this month" : `${mom.changePct > 0 ? "Up" : "Down"} ${Math.abs(Math.round(mom.changePct))}% vs last month`}
          </p>
          {hasExpenses ? (
            <Sparkline values={trendForChart} color="#6EE7A8" height={72} />
          ) : (
            <EmptyState Icon={ReceiptText} title="Start tracking this month" body="Log a few expenses to see your spending pulse." action="Add transaction" href="/" />
          )}
        </article>

        <article className="vision-card stat-card span-4">
          <div className="vision-card-title">
            <span>Budget vs Actual</span>
            <RotateCcw size={16} />
          </div>
          {budgetTotal ? (
            <>
              <div className="dual-metric">
                <span><b>{formatMoney(budgetTotal, data.currency)}</b><small>Budget</small></span>
                <span><b>{formatMoney(summary.expenses, data.currency)}</b><small>Actual</small></span>
              </div>
              <div className="split-progress">
                <span className="ok" style={{ width: `${Math.min(100, pctBudget)}%` }} />
                <span className="bad" style={{ width: `${Math.max(0, pctBudget - 100)}%` }} />
              </div>
              <p className={pctBudget > 100 ? "negative" : "positive"}>{pctBudget}% of budget</p>
            </>
          ) : (
            <EmptyState
              Icon={Filter}
              title="No budget set yet"
              body="Create category budgets so spending has a useful target."
              action="Create budgets"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card stat-card span-4">
          <div className="vision-card-title">
            <span>Cash Outflow</span>
          </div>
          <div className="metric-lg">{hasExpenses ? formatMoney(outflow, data.currency) : "Waiting"}</div>
          <p>{hasExpenses ? "Total outflow this month" : "Cash outflow appears after transactions."}</p>
          {hasExpenses ? (
            <div className="bar-spark">
              {trend.map((m) => (
                <i key={m.month} style={{ height: `${Math.max(10, Math.min(100, m.expense / Math.max(1, outflow) * 160))}%` }} />
              ))}
            </div>
          ) : (
            <EmptyState Icon={TrendingDown} title="No cash outflow yet" body="Expenses, bills, and receipt totals will build this view." action="Log spending" href="/" />
          )}
        </article>

        <article className="vision-card span-6">
          <div className="vision-card-title">
            <span>Spending by Category</span>
            <small>Total</small>
          </div>
          {cats.length > 0 ? (
            <div className="donut-wrap">
              <Donut slices={slices} centerTop={formatMoney(summary.expenses, data.currency)} centerSub="Total" size={190} stroke={24} />
              <div className="legend">
                {cats.slice(0, 6).map((c, i) => (
                  <div className="legend-row" key={c.category}>
                    <span className="swatch" style={{ background: CHART_COLORS[i % CHART_COLORS.length] }} />
                    <span className="legend-label">{c.category}</span>
                    <span>{formatMoney(c.amount, data.currency)}</span>
                    <small>{Math.round(c.pct)}%</small>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              Icon={ReceiptText}
              title="Log expenses to see category detail"
              body="Your category view will show groceries, dining, transport, bills, and receipt-level patterns."
              action="Add transaction"
              href="/"
            />
          )}
          <Link href="/coach" className="text-link">View all categories <ArrowRight size={14} aria-hidden="true" /></Link>
        </article>

        <article className="vision-card span-5">
          <div className="vision-card-title">
            <span>Weekly Trend</span>
            <small>Average per week</small>
          </div>
          <div className="metric-row">
            <strong className={!hasExpenses ? "metric-phrase" : undefined}>{hasExpenses ? formatMoney(summary.expenses / 4 || 0, data.currency) : "Building"}</strong>
            <span>{mom.changePct == null ? "Building trend" : `${Math.abs(Math.round(mom.changePct))}% vs last month`}</span>
          </div>
          {hasExpenses ? (
            <Sparkline values={trendForChart} labels={trend.map((m) => m.label.slice(0, 3))} color="#6EE7A8" height={170} />
          ) : (
            <EmptyState Icon={TrendingUp} title="Building trend" body="This chart will become useful after a few logged expenses." action="Quick capture" href="/" />
          )}
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title">
            <span>Top Merchants</span>
            <small>This Month</small>
          </div>
          <div className="vision-list">
            {merchants.map((m) => (
              <div className="vision-list-row" key={m.name}>
                <span className="icon-tile">{m.name.slice(0, 1).toUpperCase()}</span>
                <div>
                  <strong>{m.name}</strong>
                  <small>{m.category}</small>
                </div>
                <b>{formatMoney(m.amount, data.currency)}</b>
              </div>
            ))}
            {merchants.length === 0 && <EmptyState Icon={ReceiptText} title="No merchants yet" body="Your top merchants will appear after you log expenses." action="Add transaction" href="/" />}
          </div>
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title">
            <span>Budget by Category</span>
            <small>This Month</small>
          </div>
          <div className="budget-bars">
            {budgets.slice(0, 5).map((b) => (
              <div className="budget-bar-row" key={b.category}>
                <div>
                  <strong>{b.category}</strong>
                  <span>{formatMoney(b.spent, data.currency)} of {formatMoney(b.limit, data.currency)}</span>
                </div>
                <div className="mini-progress"><span style={{ width: `${Math.min(100, b.pct)}%` }} /></div>
              </div>
            ))}
            {budgets.length === 0 && <EmptyState Icon={Filter} title="No budgets set" body="Set budgets on the Plan tab to compare spending against intention." action="Create budgets" href="/settings" />}
          </div>
        </article>

        <article className="vision-card span-3 alert-card">
          <div className="vision-card-title">
            <span><AlertTriangle size={16} /> Unusual Spending Alert</span>
          </div>
          {unusual ? (
            <>
              <p>{`${unusual.category} is taking ${Math.round(unusual.pct)}% of spending this month.`}</p>
              <div className="metric-lg small">{formatMoney(unusual.amount, data.currency)}</div>
              <Link href="/coach" className="text-link">Review spending <ArrowRight size={14} aria-hidden="true" /></Link>
            </>
          ) : (
            <EmptyState Icon={AlertTriangle} title="No unusual category pressure yet" body="Money Coach will flag categories that start moving faster than normal." action="Ask Coach" href="/coach" />
          )}
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title">
            <span><ReceiptText size={16} /> Recurring Charges</span>
          </div>
          {recurring.length > 0 ? (
            <>
              <div className="metric-lg small">{formatMoney(recurring.reduce((s, b) => s + b.bill.amount, 0), data.currency)}</div>
              <p>Due within this cycle</p>
              <div className="recurring-dots">
                {recurring.map((b) => <span key={b.bill.id}>{b.bill.name.slice(0, 1)}</span>)}
              </div>
              <Link href="/bills" className="text-link">View all <ArrowRight size={14} aria-hidden="true" /></Link>
            </>
          ) : (
            <EmptyState Icon={RotateCcw} title="No recurring charges" body="Add subscriptions and repeat bills so recurring pressure stays visible." action="Add recurring charge" href="/bills" />
          )}
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title">
            <span><ReceiptText size={16} /> Item-Level Spending</span>
            <small>From receipts</small>
          </div>
          <div className="vision-list">
            {itemSpending.map((item) => (
              <div className="vision-list-row" key={`${item.category}-${item.name}`}>
                <span className="icon-tile">{item.category.slice(0, 1).toUpperCase()}</span>
                <div>
                  <strong>{item.name}</strong>
                  <small>{item.category} - {item.count} receipt{item.count === 1 ? "" : "s"}</small>
                </div>
                <b>{formatMoney(item.amount, data.currency)}</b>
              </div>
            ))}
            {itemSpending.length === 0 && (
              <EmptyState
                Icon={ReceiptText}
                title="Unlock item-level spending"
                body="Scan grocery receipts to see items like chicken, snacks, paper towels, and produce inside each category."
                action="Scan receipt"
                href="/"
              />
            )}
          </div>
        </article>

        <article className="vision-card span-8 insight-banner">
          <strong>{topCategory ? `Save more on ${topCategory.category}` : "Build your spending picture"}</strong>
          <span>{topCategory ? `You could review receipts and trim a few repeat items in ${topCategory.category}.` : "Add a few transactions and receipts to unlock smarter advice."}</span>
          <ActionButton href={topCategory ? "/coach" : "/"} variant="secondary">See how</ActionButton>
        </article>
      </section>
    </main>
  );
}
