"use client";

import { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Lightbulb,
  Mic,
  Plus,
  Send,
  Sparkles,
  Target,
  Trophy,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  budgetStatus,
  cashOnHand,
  categoryBreakdown,
  moneyPlan,
  monthOverMonth,
  netWorth,
  pace,
} from "@/lib/insights";
import { formatMoney } from "@/lib/format";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import { EmptyState, PageHeader } from "@/components/PremiumUI";

interface Msg {
  role: "user" | "assistant";
  content: string;
}

const STARTERS = [
  "Budget review",
  "Savings boost",
  "Debt plan",
  "Investing 101",
];

export default function AdvisorPage() {
  const { data, ready } = useStore();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const hasChattedRef = useRef(false);

  useEffect(() => {
    if (!hasChattedRef.current) return;
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  useEffect(() => {
    if (!ready) return;
    if (typeof sessionStorage !== "undefined" && sessionStorage.getItem("mc-checkin") === "1") {
      sessionStorage.removeItem("mc-checkin");
      send("Do my weekly check-in");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  async function sendMessage(text: string) {
    const value = text.trim();
    if (!value || busy) return;
    hasChattedRef.current = true;
    const next = [...msgs, { role: "user" as const, content: value }];
    setMsgs(next);
    setInput("");
    setBusy(true);

    const nameOf = (id?: string) => data.members.find((m) => m.id === id)?.name ?? null;
    const sum = summarize(data);
    const snapshot = {
      household: data.householdName || null,
      members: data.members.map((m) => ({ name: m.name, monthlyIncome: m.monthlyIncome ?? null })),
      ...sum,
      currency: data.currency,
      moneyPlan: moneyPlan(data),
      pace: pace(data, sum.safeToSpend),
      netWorth: netWorth(data),
      cashOnHand: cashOnHand(data),
      goals: (data.goals || []).map((g) => ({
        name: g.name,
        target: g.target,
        saved: g.saved,
        monthlyContribution: g.monthlyContribution ?? null,
      })),
      budgets: budgetStatus(data).map((b) => ({
        category: b.category,
        spent: Math.round(b.spent),
        limit: b.limit,
        over: b.over,
      })),
      topCategories: categoryBreakdown(data).slice(0, 6).map((c) => ({
        category: c.category,
        amount: Math.round(c.amount),
      })),
      monthOverMonth: monthOverMonth(data),
      recurringBills: billsThisMonth(data).map((b) => ({
        name: b.bill.name,
        amount: b.bill.amount,
        category: b.bill.category,
        dueDay: b.dueDay,
        paid: b.paid,
        whose: nameOf(b.bill.memberId),
      })),
      debts: data.debts.map((d) => ({
        party: d.party,
        direction: d.direction,
        balance: d.balance,
        apr: d.apr ?? null,
        minPayment: d.minPayment ?? null,
        dueDate: d.dueDate ?? null,
        whose: nameOf(d.memberId),
      })),
      recentExpenses: data.transactions.filter((t) => t.type === "expense").slice(0, 24).map((t) => ({
        amount: t.amount,
        category: t.category,
        date: t.date,
        who: nameOf(t.memberId),
        lineItems: t.lineItems?.slice(0, 20).map((item) => ({
          name: item.name,
          amount: item.amount,
          category: item.category,
        })),
      })),
    };

    try {
      const res = await fetch("/api/advisor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: next, snapshot }),
      });
      const dataR = await res.json();
      if (!res.ok) throw new Error(dataR.error || "Coach is unavailable.");
      setMsgs((m) => [...m, { role: "assistant", content: dataR.reply }]);
    } catch (e: any) {
      setMsgs((m) => [
        ...m,
        { role: "assistant", content: "Coach could not connect right now. Your local plan is still available." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  function send(text: string) {
    void sendMessage(text);
  }

  if (!ready) return null;

  const firstName = data.members[0]?.name?.split(" ")[0] || "there";
  const sum = summarize(data);
  const budgets = budgetStatus(data);
  const bestBudget = budgets.find((b) => !b.over);
  const overBudget = budgets.find((b) => b.over);
  const debts = data.debts.filter((d) => d.direction === "i_owe");
  const debtTotal = debts.reduce((s, d) => s + d.balance, 0);
  const topDebt = [...debts].sort((a, b) => (b.apr || 0) - (a.apr || 0))[0];
  const topCategory = categoryBreakdown(data)[0];
  const receiptItems = data.transactions.flatMap((t) =>
    (t.lineItems || []).map((item) => ({
      ...item,
      transactionCategory: t.category,
    })),
  );
  const topReceiptItem = receiptItems
    .filter((item) => item.amount > 0)
    .sort((a, b) => b.amount - a.amount)[0];
  const primaryGoal = data.goals[0];
  const score = sum.safeToSpend >= 0 ? 84 : 62;
  const trend = data.netWorthHistory.length >= 2
    ? data.netWorthHistory.slice(-7).map((p) => p.value)
    : data.transactions.slice(0, 7).reverse().map((t, i) => (i + 1) * t.amount);
  const hasMoneyHistory = trend.length > 1 || data.transactions.length > 0 || data.recurringBills.length > 0 || data.goals.length > 0 || debtTotal > 0;
  const insightProgress = hasMoneyHistory
    ? Math.max(12, Math.min(100, Math.round(score)))
    : 18;
  const weeklyScore = hasMoneyHistory ? score : 18;
  const actionPlan = [
    overBudget
      ? {
          title: `Trim ${overBudget.category}`,
          body: `${formatMoney(overBudget.spent - overBudget.limit, data.currency)} over budget`,
          status: "Needs action",
        }
      : topCategory
        ? {
            title: `Review ${topCategory.category}`,
            body: `${Math.round(topCategory.pct)}% of spending`,
            status: "On track",
          }
        : null,
    topDebt
      ? {
          title: `Attack ${topDebt.party}`,
          body: `${topDebt.apr ? `${topDebt.apr}% APR` : "Balance"} - ${formatMoney(topDebt.balance, data.currency)}`,
          status: "Active",
        }
      : null,
    primaryGoal
      ? {
          title: `Fund ${primaryGoal.name}`,
          body: `${formatMoney(primaryGoal.saved, data.currency)} of ${formatMoney(primaryGoal.target, data.currency)}`,
          status: "Tracking",
        }
      : {
          title: "Create emergency fund",
          body: "Start with a small cash buffer",
          status: "Next",
        },
  ].filter(Boolean) as Array<{ title: string; body: string; status: string }>;

  return (
    <main className="vision-page coach-dashboard">
      <PageHeader
        title={`Hi ${firstName === "there" ? "David" : firstName}. I'm your Money Coach.`}
        subtitle="I'll help you build wealth, reduce stress, and take the next right step."
        action={<span className="pro-badge">Coach Pro</span>}
      />

      <section className="vision-grid coach-grid">
        <article className="vision-card chat-panel span-7">
          <div className="coach-message">
            <span className="coach-avatar"><Bot size={22} /></span>
            <div>
              <strong>{hasMoneyHistory ? "Good morning." : "Welcome in."}</strong>
              <p>
                {hasMoneyHistory
                  ? "You are making solid progress. Let's keep building momentum."
                  : "Add a few real numbers and I will turn them into a calm first plan."}
              </p>
            </div>
          </div>

          <div className="nested-insight">
            <div className="vision-card-title"><span>Today&apos;s Insight</span><Sparkles size={16} /></div>
            <p>
              {!hasMoneyHistory
                ? "Add a few transactions, bills, or goals and I will turn them into specific next steps."
                : bestBudget
                ? `You are within your ${bestBudget.category} budget. Small choices are adding up.`
                : sum.safeToSpend >= 0
                  ? "You have room to spend today while keeping bills protected."
                  : "Your safe-to-spend is under pressure. Let's find the smallest correction."}
            </p>
            <div className="coach-insight-meter" aria-label="Coach confidence indicator">
              <span style={{ width: `${insightProgress}%` }} />
            </div>
            <small>
              {hasMoneyHistory
                ? "Coach is reading your current plan, spending, and debt context."
                : "Waiting for your first money snapshot."}
            </small>
          </div>

          <div className="chat-thread">
            {msgs.length === 0 && (
              <>
                <div className="bubble me">What&apos;s the fastest way I can pay off my debt?</div>
                <div className="bubble coach">
                  {debtTotal > 0
                    ? "Based on your balances, the Snowball method can help you build momentum while the Avalanche method may save the most interest."
                    : "Add your debts and minimum payments, then I can compare Snowball and Avalanche with your real numbers."}
                  <br />
                  <button className="soft-button" onClick={() => send("Compare my debt payoff strategies")}>See my payoff plan <ArrowRight size={14} /></button>
                </div>
              </>
            )}
            {msgs.map((m, i) => (
              <div key={i} className={"bubble " + (m.role === "user" ? "me" : "coach")}>
                {m.content}
              </div>
            ))}
            {busy && <div className="typing"><span /><span /><span /></div>}
            <div ref={endRef} />
          </div>

          <div className="suggest quick-actions">
            {STARTERS.map((s) => (
              <button key={s} onClick={() => send(s)}>{s}</button>
            ))}
          </div>

          <div className="vision-chat-input">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") send(input);
              }}
              placeholder="Ask your coach anything..."
            />
            <button aria-label="Voice input"><Mic size={17} /></button>
            <button aria-label="Send" onClick={() => send(input)} disabled={busy}><Send size={17} /></button>
          </div>
        </article>

        <aside className="coach-side span-5">
          <article className="vision-card">
            <div className="vision-card-title"><span>Your Action Plan</span><small>View all</small></div>
            <div className="action-plan-list">
              {actionPlan.map(({ title, body, status }) => (
                <div className="action-plan-row" key={title}>
                  <span className="icon-tile"><Target size={15} /></span>
                  <div><strong>{title}</strong><small>{body}</small></div>
                  <b>{status}</b>
                </div>
              ))}
            </div>
            <button className="soft-button full"><Plus size={14} /> Add new action</button>
          </article>

          <article className="vision-card weekly-summary">
            <div className="vision-card-title"><span>Weekly Coaching Summary</span></div>
            <div className="summary-layout">
              <Ring pct={weeklyScore} size={132} stroke={11} color="#84d6a5">
                <strong>{hasMoneyHistory ? score : "Ready"}</strong>
                <span>{hasMoneyHistory ? (score >= 80 ? "Great week" : "Reset week") : "First plan"}</span>
              </Ring>
              <ul>
                <li>Safe to spend: {hasMoneyHistory ? formatMoney(sum.safeToSpend, data.currency) : "waiting for data"}</li>
                <li>Debt tracked: {debtTotal > 0 ? formatMoney(debtTotal, data.currency) : "no accounts added"}</li>
                <li>{budgets.length} budget challenge{budgets.length === 1 ? "" : "s"}</li>
              </ul>
            </div>
            <button className="soft-button full">See full summary</button>
          </article>
        </aside>

        <article className="vision-card span-3 feature-card">
          <strong>Scenario Simulator</strong>
          <span>See the impact of your decisions.</span>
          {hasMoneyHistory ? (
            <Sparkline values={trend.length ? trend : [sum.safeToSpend, sum.safeToSpend + 1]} color="#6EE7A8" height={76} />
          ) : (
            <EmptyState
              Icon={Sparkles}
              title="Build your first scenario"
              body="Add income, bills, or goals and Coach can preview your options."
              action="Start tracking"
              href="/"
            />
          )}
          {hasMoneyHistory && <button className="soft-button">Run a scenario</button>}
        </article>

        <article className="vision-card span-3 feature-card">
          <strong>Habit Challenges</strong>
          <span>Build better money habits that last.</span>
          <div className="challenge-box">
            <Trophy size={28} />
            <b>{overBudget ? `${overBudget.category} reset` : topCategory ? `${topCategory.category} check-in` : "First budget week"}</b>
            <small>{overBudget ? "Bring this category back under plan" : "Keep the streak going"}</small>
          </div>
        </article>

        <article className="vision-card span-3 feature-card">
          <strong>Learn & Grow</strong>
          <span>Bite-sized lessons to build your financial IQ.</span>
          <div className="challenge-box">
            <BookOpen size={28} />
            <b>{debtTotal > 0 ? "Debt payoff basics" : primaryGoal ? "Goal funding basics" : "Budgeting basics"}</b>
            <small>5 min lesson</small>
          </div>
        </article>

        <article className="vision-card span-3 feature-card">
          <strong>Your Insights</strong>
          <span>Personalized guidance just for you.</span>
          <div className="challenge-box">
            <Lightbulb size={28} />
            <b>{topReceiptItem ? topReceiptItem.name : hasMoneyHistory ? (sum.safeToSpend >= 0 ? "On track" : "Needs attention") : "First snapshot"}</b>
            <small>
              {topReceiptItem
                ? `${topReceiptItem.category || topReceiptItem.transactionCategory} item from receipts`
                : hasMoneyHistory
                  ? `${formatMoney(sum.safeToSpend, data.currency)} safe today`
                  : "Add income, bills, or a receipt"}
            </small>
          </div>
        </article>
      </section>
    </main>
  );
}
