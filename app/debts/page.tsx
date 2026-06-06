"use client";

import {
  ArrowRight,
  BadgeDollarSign,
  CalendarClock,
  CheckCircle2,
  CreditCard,
  Flag,
  Landmark,
  Mountain,
  Snowflake,
  TrendingDown,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { payoffPlan, simulatePayoff } from "@/lib/insights";
import { clampPct, formatMoney } from "@/lib/format";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import { EmptyState, PageHeader } from "@/components/PremiumUI";

export default function DebtsPage() {
  const { data, ready, payDebt } = useStore();
  if (!ready) return null;

  const debts = data.debts.filter((d) => d.direction === "i_owe" && d.balance > 0);
  const total = debts.reduce((sum, d) => sum + d.balance, 0);
  const original = debts.reduce((sum, d) => sum + (d.original || d.balance), 0);
  const paidPct = original ? clampPct(((original - total) / original) * 100) : 0;
  const snowball = payoffPlan(data, "snowball", 75);
  const avalanche = payoffPlan(data, "avalanche", 75);
  const sim = simulatePayoff(data, "snowball", 75);
  const base = simulatePayoff(data, "snowball", 0);
  const interestSaved = Math.max(0, base.totalInterest - sim.totalInterest);
  const monthlyMin = debts.reduce((sum, d) => sum + (d.minPayment || 0), 0);
  const targetDate = snowball.months
    ? new Date(new Date().getFullYear(), new Date().getMonth() + snowball.months, 1)
    : null;
  const nextDebt = [...debts].sort((a, b) => (a.dueDate || "").localeCompare(b.dueDate || ""))[0];
  const hasDebt = debts.length > 0;

  return (
    <main className="vision-page debt-dashboard">
      <PageHeader
        title={hasDebt ? "You have a plan. Let's crush this debt." : "Protect your debt-free progress"}
        subtitle={hasDebt ? "Stay disciplined, follow your plan, and freedom is closer than you think." : "Add debts if you have them, or keep this page as your payoff safety plan."}
        action={<div className="encouragement"><Flag size={20} aria-hidden="true" /> {hasDebt ? "Keep it up. You are doing great." : "Protection mode"}</div>}
      />

      <section className="vision-grid debt-grid">
        <article className="vision-card metric-card span-3">
          <span>Total Debt Balance</span>
          <strong>{formatMoney(total, data.currency)}</strong>
          <small>{hasDebt ? `Across ${debts.length} account${debts.length === 1 ? "" : "s"}` : "No active debt added"}</small>
        </article>

        <article className="vision-card center-card span-3">
          <div className="vision-card-title"><span>Debt Free Progress</span></div>
          <Ring pct={paidPct} size={150} stroke={12} color="#84d6a5">
            <strong>{hasDebt ? `${Math.round(paidPct)}%` : "✓"}</strong>
            <span>{hasDebt ? `${formatMoney(original - total, data.currency)} paid off` : "Protected"}</span>
          </Ring>
          <div className="mini-progress"><span style={{ width: `${paidPct}%` }} /></div>
        </article>

        <article className="vision-card metric-card span-3">
          <span>Target Debt Free Date</span>
          <strong className={!targetDate ? "metric-phrase" : undefined}>{targetDate ? targetDate.toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "Add payments"}</strong>
          <small>{snowball.months ? `In ${snowball.months} months` : "Ready to calculate"}</small>
        </article>

        <article className="vision-card metric-card span-3">
          <span>Interest Saved</span>
          <strong className={!hasDebt ? "metric-phrase" : undefined}>{hasDebt ? formatMoney(interestSaved, data.currency) : "Ready"}</strong>
          <small>{hasDebt ? "By adding $75 monthly" : "Ready to calculate"}</small>
        </article>

        <article className="vision-card span-5">
          <div className="vision-card-title">
            <span>Choose Your Payoff Strategy</span>
            <small>Pick the strategy that motivates you most.</small>
          </div>
          <div className={"strategy-choice" + (!hasDebt ? " muted-preview" : "")}>
            <div className="strategy-option selected">
              <div><Snowflake size={22} /><strong>Snowball</strong><span>Recommended</span></div>
              <p>{hasDebt ? "Pay off smallest balances first to build momentum." : "Add debts to compare payoff strategies."}</p>
              <small>Estimated time: {snowball.months ? `${snowball.months} months` : "Add debts first"}</small>
            </div>
            <div className="strategy-option">
              <div><Mountain size={22} /><strong>Avalanche</strong></div>
              <p>{hasDebt ? "Save the most by paying highest interest debt first." : "Compare APR impact once accounts are added."}</p>
              <small>Estimated time: {avalanche.months ? `${avalanche.months} months` : "Add debts first"}</small>
            </div>
          </div>
        </article>

        <article className="vision-card span-7">
          <div className="vision-card-title">
            <span>Payoff Projection</span>
            <small>Payoff by {targetDate ? targetDate.toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "plan date"}</small>
          </div>
          {hasDebt ? (
            <>
              <Sparkline
                values={[total, total * 0.86, total * 0.7, total * 0.52, total * 0.34, total * 0.18, 0]}
                labels={["Now", "+3m", "+6m", "+9m", "+12m", "+15m", "Free"]}
                color="#6EE7A8"
                height={210}
              />
              <p className="plan-note">Stick to your plan and you will be debt free faster.</p>
            </>
          ) : (
            <EmptyState
              Icon={TrendingDown}
              title="Your payoff projection will appear here"
              body="Add credit cards, loans, or payment plans to generate a payoff path."
              action="Add debt account"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card span-8">
          <div className="vision-card-title"><span>Your Debt Accounts</span></div>
          <div className="debt-table">
            <div className="debt-head">
              <span>Account</span><span>Balance</span><span>APR</span><span>Min.</span><span>Progress</span>
            </div>
            {debts.map((d) => {
              const pct = d.original ? clampPct(((d.original - d.balance) / d.original) * 100) : 0;
              return (
                <div className="debt-row" key={d.id}>
                  <span><CreditCard size={15} /> {d.party}</span>
                  <b>{formatMoney(d.balance, data.currency)}</b>
                  <span>{d.apr ? `${d.apr}%` : "0%"}</span>
                  <span>{formatMoney(d.minPayment || 0, data.currency)}</span>
                  <span className="table-progress"><i style={{ width: `${pct}%` }} />{Math.round(pct)}%</span>
                </div>
              );
            })}
            {debts.length === 0 && (
              <EmptyState
                Icon={CreditCard}
                title="No debt accounts added"
                body="Add credit cards, loans, or payment plans to track progress."
                action="Add debt account"
                href="/settings"
                secondary="Not carrying debt? Great — keep this section as your protection plan."
              />
            )}
          </div>
        </article>

        <article className="vision-card span-4">
          <div className="vision-card-title"><span>Your Monthly Debt Plan</span></div>
          {hasDebt ? (
            <>
              <div className="debt-plan-list">
                <div><span>Minimum Payments</span><b>{formatMoney(monthlyMin, data.currency)}</b></div>
                <div><span>Extra Payment</span><b>{formatMoney(75, data.currency)}</b></div>
                <div className="total"><span>Total Monthly Payment</span><b>{formatMoney(monthlyMin + 75, data.currency)}</b></div>
              </div>
              {nextDebt && (
                <button className="soft-button full" onClick={() => payDebt(nextDebt.id, 75)}>
                  Add $75 to {nextDebt.party}
                </button>
              )}
              <div className="next-payment">
                <CalendarClock size={15} />
                <span>Next payment due</span>
                <b>{nextDebt?.dueDate || "Not set"}</b>
              </div>
            </>
          ) : (
            <EmptyState
              Icon={CalendarClock}
              title="No minimum payments yet"
              body="Add accounts to build your monthly debt plan."
              action="Add debt account"
              href="/settings"
            />
          )}
        </article>

        <article className="vision-card span-12 debt-advice">
          {[
            ["Strategic Payoff Plans", "Snowball or Avalanche. Choose what drives you.", BadgeDollarSign],
            ["Clear Progress Tracking", "See how close you are and stay motivated.", TrendingDown],
            ["Smart Projections", "Know your payoff date and interest savings.", CalendarClock],
            ["Actionable Guidance", "Personalized tips to help you stay on track.", CheckCircle2],
            ["Debt Freedom", "A clear path to a stronger financial life.", Landmark],
          ].map(([title, body, Icon]) => (
            <div key={String(title)}>
              <Icon size={24} />
              <strong>{String(title)}</strong>
              <span>{String(body)}</span>
            </div>
          ))}
        </article>
      </section>
    </main>
  );
}
