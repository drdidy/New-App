"use client";

import Link from "next/link";
import {
  ArrowRight,
  CalendarDays,
  Check,
  Home,
  PiggyBank,
  Plus,
  ShieldCheck,
  Target,
  Wallet,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { billsThisMonth, budgetStatus, moneyPlan, monthlyTotals } from "@/lib/insights";
import { clampPct, formatMoney } from "@/lib/format";
import Donut from "@/components/Donut";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import { ActionButton, EmptyState, PageHeader } from "@/components/PremiumUI";

const ALLOC_COLORS = ["#8dbbff", "#84d6a5", "#e3bf74", "#ef8b7d"];

export default function PlanPage() {
  const { data, ready } = useStore();
  if (!ready) return null;

  const plan = moneyPlan(data);
  const bills = billsThisMonth(data);
  const budgets = budgetStatus(data);
  const goals = data.goals || [];
  const trend = monthlyTotals(data, 6);
  const allocationPct = plan.income ? clampPct((plan.allocated / plan.income) * 100) : 0;
  const slices = [
    { label: "Needs", value: plan.bills + plan.budgeted * 0.5, color: ALLOC_COLORS[0] },
    { label: "Savings & Goals", value: plan.savings, color: ALLOC_COLORS[1] },
    { label: "Wants", value: plan.budgeted * 0.3, color: ALLOC_COLORS[2] },
    { label: "Debt Paydown", value: plan.debtMin, color: ALLOC_COLORS[3] },
  ].filter((x) => x.value > 0);

  const eventList = [
    ...bills.slice(0, 3).map((b) => ({
      id: b.bill.id,
      label: b.bill.name,
      sub: `Day ${b.dueDay}`,
      amount: b.bill.amount,
      Icon: b.bill.category.toLowerCase().includes("rent") ? Home : CalendarDays,
    })),
    ...goals.slice(0, 2).map((g) => ({
      id: g.id,
      label: g.name,
      sub: "Goal contribution",
      amount: g.monthlyContribution || 0,
      Icon: PiggyBank,
    })),
  ];
  const protectedFunds = goals
    .filter((g) => (g.monthlyContribution || 0) > 0 || g.saved > 0)
    .slice(0, 4);
  const automationRows = [
    ...bills
      .filter((b) => b.bill.autoLog)
      .slice(0, 3)
      .map((b) => ({
        label: `${b.bill.name} auto-log`,
        detail: `Day ${b.dueDay}`,
        active: true,
        Icon: CalendarDays,
      })),
    ...goals
      .filter((g) => (g.monthlyContribution || 0) > 0)
      .slice(0, 3)
      .map((g) => ({
        label: `${g.name} contribution`,
        detail: `${formatMoney(g.monthlyContribution || 0, data.currency)}/mo`,
        active: true,
        Icon: PiggyBank,
      })),
    ...(data.remindersEnabled
      ? [{ label: "Weekly check-in reminder", detail: "Enabled", active: true, Icon: ShieldCheck }]
      : []),
  ].slice(0, 4);
  const hasEmergencyFund = goals.some((g) => /emergency|buffer/i.test(g.name) && g.saved > 0);
  const debtTotal = data.debts
    .filter((d) => d.direction === "i_owe")
    .reduce((sum, d) => sum + d.balance, 0);
  const hasForecastData = trend.map((m) => m.income - m.expense).some(Boolean);
  const hasPlanInputs =
    plan.income > 0 ||
    plan.allocated > 0 ||
    budgets.length > 0 ||
    goals.length > 0 ||
    bills.length > 0 ||
    debtTotal > 0 ||
    data.transactions.length > 0 ||
    data.accounts.length > 0;

  return (
    <main className="vision-page plan-dashboard">
      <PageHeader
        title="Your Plan Overview"
        subtitle="Turn income into a calm monthly system."
      />

      <section className="vision-grid plan-grid">
        <article className="vision-card span-3 center-card">
          <div className="vision-card-title"><span>Plan Progress</span></div>
          {hasPlanInputs ? (
            <Ring pct={allocationPct} size={126} stroke={11} color="#84d6a5">
              <strong>{Math.round(allocationPct)}%</strong>
              <span>{allocationPct <= 100 ? "On track" : "Over"}</span>
            </Ring>
          ) : (
            <EmptyState
              Icon={Target}
              title="Build your plan"
              body="Add income and a few priorities to see plan progress."
              action="Start plan"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card metric-card span-3">
          <span>Income This Month</span>
          <strong className={!plan.income ? "metric-phrase" : undefined}>{plan.income ? formatMoney(plan.income, data.currency) : "Add income"}</strong>
          <small>{plan.income ? "After-tax income" : "Log a paycheck or set a monthly baseline."}</small>
        </article>

        <article className="vision-card metric-card span-3">
          <span>Planned Savings</span>
          <strong className={!plan.savings ? "metric-phrase" : undefined}>{plan.savings ? formatMoney(plan.savings, data.currency) : "Create goal"}</strong>
          <small>{plan.savings ? `${plan.income ? Math.round((plan.savings / plan.income) * 100) : 0}% of income` : "Create your first goal to protect your future."}</small>
        </article>

        <article className="vision-card metric-card span-3">
          <span>Projected Surplus</span>
          <strong className={!hasPlanInputs ? "metric-phrase" : undefined}>{hasPlanInputs ? formatMoney(plan.leftover, data.currency) : "Waiting"}</strong>
          <small>{hasPlanInputs ? "This month" : "Appears after income and commitments."}</small>
        </article>

        <article className="vision-card span-5">
          <div className="vision-card-title">
            <span>Income Allocation</span>
            <small>Manage</small>
          </div>
          {slices.length ? (
            <div className="donut-wrap">
              <Donut
                slices={slices}
                centerTop={`${Math.round(allocationPct)}%`}
                centerSub="Allocated"
                size={190}
                stroke={25}
              />
              <div className="legend">
                {slices.map((s) => (
                  <div className="legend-row" key={s.label}>
                    <span className="swatch" style={{ background: s.color }} />
                    <span className="legend-label">{s.label}</span>
                    <span>{formatMoney(s.value, data.currency)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <EmptyState
              Icon={Wallet}
              title="Income allocation is waiting"
              body="Add income, bills, budgets, or goals so every dollar can get a role."
              action="Allocate income"
              href="/settings"
            />
          )}
          {plan.leftover > 0 && (
            <div className="assignment-callout">
              <strong>{formatMoney(plan.leftover, data.currency)} unassigned</strong>
              <span>Give every dollar a role.</span>
              <ActionButton href="/settings" variant="secondary">Allocate income</ActionButton>
            </div>
          )}
        </article>

        <article className="vision-card span-5">
          <div className="vision-card-title">
            <span>Cash Flow Forecast</span>
            <small>{hasForecastData ? "6M" : "Forecast preview"}</small>
          </div>
          <Sparkline
            values={hasForecastData ? trend.map((m) => m.income - m.expense) : [1200, 900, 1420, 980, 1550, 1247]}
            labels={trend.map((m) => m.label.slice(0, 3))}
            color="#8dbbff"
            height={190}
          />
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title"><span>Upcoming Money Events</span></div>
          <div className="vision-list">
            {eventList.slice(0, 4).map((event) => (
              <div className="vision-list-row" key={event.id}>
                <span className="icon-tile"><event.Icon size={15} /></span>
                <div>
                  <strong>{event.label}</strong>
                  <small>{event.sub}</small>
                </div>
                <b>{formatMoney(event.amount, data.currency)}</b>
              </div>
            ))}
            {eventList.length === 0 && (
              <EmptyState
                Icon={CalendarDays}
                title="No money events yet"
                body="Add bills, subscriptions, or goal dates so your calendar becomes useful."
                action="Add bill or event"
                href="/bills"
              />
            )}
          </div>
          <Link href="/bills" className="text-link">View full calendar <ArrowRight size={14} /></Link>
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title"><span>Category Budgets</span><Link href="/settings">Edit</Link></div>
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
            {budgets.length === 0 && (
              <EmptyState
                Icon={Target}
                title="No category budgets"
                body="Create budgets for groceries, dining, bills, and other repeat categories."
                action="Create budgets"
                href="/settings"
              />
            )}
          </div>
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title"><span>Savings Goals</span><Link href="/settings">See all</Link></div>
          <div className="budget-bars">
            {goals.slice(0, 4).map((g) => (
              <div className="budget-bar-row" key={g.id}>
                <div>
                  <strong>{g.name}</strong>
                  <span>{formatMoney(g.saved, data.currency)} of {formatMoney(g.target, data.currency)}</span>
                </div>
                <div className="mini-progress"><span style={{ width: `${clampPct((g.saved / g.target) * 100)}%` }} /></div>
              </div>
            ))}
            {goals.length === 0 && (
              <EmptyState
                Icon={PiggyBank}
                title="No savings goals yet"
                body="Create your first goal to protect your future."
                action="Create first goal"
                href="/settings"
              />
            )}
          </div>
          <button className="soft-button full"><Plus size={14} /> Add New Goal</button>
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title"><span>Protected Funds</span><small>From goals</small></div>
          <div className="budget-bars">
            {protectedFunds.map((fund) => (
              <div className="budget-bar-row" key={fund.id}>
                <div>
                  <strong><PiggyBank size={13} /> {fund.name}</strong>
                  <span>
                    {formatMoney(fund.saved, data.currency)} of {formatMoney(fund.target, data.currency)}
                    {fund.monthlyContribution ? ` - ${formatMoney(fund.monthlyContribution, data.currency)}/mo` : ""}
                  </span>
                </div>
                <div className="mini-progress"><span style={{ width: `${clampPct((fund.saved / fund.target) * 100)}%` }} /></div>
              </div>
            ))}
            {protectedFunds.length === 0 && (
              <EmptyState
                Icon={ShieldCheck}
                title="No protected funds yet"
                body="Create a goal with a monthly contribution to protect money before you spend it."
                action="Add protected fund"
                href="/settings"
              />
            )}
          </div>
          <Link href="/settings" className="soft-button full"><Plus size={14} /> Add New Fund</Link>
        </article>

        <article className="vision-card span-3">
          <div className="vision-card-title"><span>Automation</span><small>Manage</small></div>
          <div className="toggle-list">
            {automationRows.map((row) => (
              <div className="toggle-row" key={row.label}>
                <span><row.Icon size={14} /> {row.label}</span>
                <i>{row.active ? <Check size={12} /> : <Wallet size={12} />}</i>
              </div>
            ))}
            {automationRows.length === 0 && (
              <EmptyState
                Icon={Wallet}
                title="No automations yet"
                body="Set reminders, bill auto-log, or goal contributions to make the plan run quietly."
                action="Set automation"
                href="/settings"
              />
            )}
          </div>
          <Link href="/settings" className="text-link">View all automations <ArrowRight size={14} /></Link>
        </article>

        <article className="vision-card span-12 roadmap">
          <div className="milestones">
            {[
              ["1 Month", "Build Momentum", data.transactions.length > 0],
              ["3 Months", "Emergency Fund", hasEmergencyFund],
              ["6 Months", "Debt Freedom", debtTotal === 0 && data.debts.length > 0],
              ["12 Months", "Financial Freedom", plan.leftover > 0 && goals.length > 0],
              ["3 Years", "Future You", plan.leftover > 500 && goals.length > 0],
            ].map(([time, label, done]) => (
              <div className={done ? "milestone done" : "milestone"} key={String(label)}>
                <i>{done ? <Check size={14} /> : <Target size={14} />}</i>
                <strong>{time}</strong>
                <span>{label}</span>
              </div>
            ))}
          </div>
          <div className="roadmap-copy">
            <strong>Big plans start with small steps.</strong>
            <span>You are building a future of freedom and peace of mind.</span>
          </div>
        </article>
      </section>
    </main>
  );
}
