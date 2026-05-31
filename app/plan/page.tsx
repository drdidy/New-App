"use client";

import { useState } from "react";
import Link from "next/link";
import { useStore } from "@/lib/store";
import { moneyPlan, billsThisMonth } from "@/lib/insights";
import { formatMoney, clampPct, MEMBER_COLORS } from "@/lib/format";
import Ring from "@/components/Ring";

const GOAL_EMOJIS = ["🛟", "✈️", "🏖️", "🚗", "🏠", "🎓", "💍", "🎁"];

const ALLOC = [
  { key: "bills", label: "Bills", color: "#bc5446" },
  { key: "debtMin", label: "Debt", color: "#7c6ba8" },
  { key: "savings", label: "Savings", color: "#2e8b72" },
  { key: "budgeted", label: "Spending", color: "#c2663f" },
] as const;

export default function PlanPage() {
  const {
    data,
    ready,
    setBudget,
    removeBudget,
    addGoal,
    deleteGoal,
    contributeGoal,
  } = useStore();
  const [goalOpen, setGoalOpen] = useState(false);
  const [gName, setGName] = useState("");
  const [gTarget, setGTarget] = useState("");
  const [gMonthly, setGMonthly] = useState("");
  const [gEmoji, setGEmoji] = useState(GOAL_EMOJIS[0]);
  const [gColor, setGColor] = useState(MEMBER_COLORS[0]);
  const [newCat, setNewCat] = useState("");
  const [newLimit, setNewLimit] = useState("");

  if (!ready) return null;

  const plan = moneyPlan(data);
  const bills = billsThisMonth(data);
  const billsTotal = bills.reduce((s, b) => s + b.bill.amount, 0);
  const billsPaid = bills.filter((b) => b.paid).reduce((s, b) => s + b.bill.amount, 0);

  const allocTotal = Math.max(plan.income, plan.allocated, 1);

  function saveGoal() {
    const t = parseFloat(gTarget);
    if (!gName.trim() || !t || t <= 0) return;
    addGoal({
      name: gName.trim(),
      target: t,
      emoji: gEmoji,
      color: gColor,
      monthlyContribution: gMonthly ? parseFloat(gMonthly) : undefined,
    });
    setGName(""); setGTarget(""); setGMonthly(""); setGoalOpen(false);
  }

  function saveBudget() {
    const lim = parseFloat(newLimit);
    if (!newCat.trim() || !lim || lim <= 0) return;
    setBudget(newCat.trim(), lim);
    setNewCat(""); setNewLimit("");
  }

  return (
    <main>
      <h1 className="h-title">Your money plan</h1>
      <p className="h-sub">Give every dollar a job — before you spend it.</p>

      {/* Zero-based allocation */}
      <div className="card reveal">
        <div className="card-h">This month&apos;s plan</div>
        {plan.income === 0 ? (
          <div className="empty">
            Add your income in <Link href="/settings" style={{ color: "var(--amber)" }}>Settings</Link> to
            see your plan.
          </div>
        ) : (
          <>
            <div className="alloc-bar">
              {ALLOC.map((a) => {
                const v = (plan as any)[a.key] as number;
                if (v <= 0) return null;
                return (
                  <span
                    key={a.key}
                    style={{ width: `${(v / allocTotal) * 100}%`, background: a.color }}
                    title={a.label}
                  />
                );
              })}
              {plan.leftover > 0 && (
                <span style={{ width: `${(plan.leftover / allocTotal) * 100}%`, background: "var(--surface-2)" }} />
              )}
            </div>
            <div className="alloc-list">
              <div className="alloc-row total">
                <span>Income</span>
                <span>{formatMoney(plan.income, data.currency)}</span>
              </div>
              {ALLOC.map((a) => {
                const v = (plan as any)[a.key] as number;
                return (
                  <div className="alloc-row" key={a.key}>
                    <span><i style={{ background: a.color }} />{a.label}</span>
                    <span>−{formatMoney(v, data.currency)}</span>
                  </div>
                );
              })}
              <div className={"alloc-row leftover " + (plan.leftover < 0 ? "neg" : "pos")}>
                <span>{plan.leftover < 0 ? "Over-allocated" : "Left to assign"}</span>
                <span>{formatMoney(plan.leftover, data.currency)}</span>
              </div>
            </div>
            <p className="plan-note" style={{ marginBottom: 0 }}>
              {plan.leftover < 0
                ? "Your plan spends more than you earn — trim a category, or ask Coach to help rebalance."
                : plan.leftover > 0
                ? "You've got money still unassigned. Send it to a savings goal or extra debt payment."
                : "Nicely balanced — every dollar has a job."}
            </p>
          </>
        )}
      </div>

      {/* Savings goals */}
      <div className="section-h">
        <h2>Savings goals</h2>
      </div>
      <div className="card">
        {(data.goals || []).length === 0 ? (
          <div className="empty">
            No goals yet. An emergency fund is the best first one — even a small
            buffer changes everything.
          </div>
        ) : (
          data.goals.map((g) => {
            const pct = clampPct((g.saved / g.target) * 100);
            return (
              <div className="item" key={g.id}>
                <Ring pct={pct} size={46} stroke={5} color={g.color}>
                  <span className="ring-pct">{Math.round(pct)}%</span>
                </Ring>
                <div className="meta">
                  <div className="t">{g.emoji} {g.name}</div>
                  <div className="s">
                    {formatMoney(g.saved, data.currency)} of {formatMoney(g.target, data.currency)}
                    {g.monthlyContribution ? ` · ${formatMoney(g.monthlyContribution, data.currency)}/mo` : ""}
                  </div>
                </div>
                <button
                  className="bill-pay"
                  onClick={() => {
                    const v = prompt(`Add to ${g.name}:`);
                    const n = v ? parseFloat(v) : 0;
                    if (n > 0) contributeGoal(g.id, n);
                  }}
                >
                  + Add
                </button>
                <button className="x" onClick={() => deleteGoal(g.id)} aria-label="Delete goal">×</button>
              </div>
            );
          })
        )}
      </div>
      {goalOpen ? (
        <div className="card">
          <div className="field">
            <label>What are you saving for?</label>
            <input value={gName} onChange={(e) => setGName(e.target.value)} placeholder="Emergency fund" autoFocus />
          </div>
          <div className="emoji-pick">
            {GOAL_EMOJIS.map((e) => (
              <button key={e} className={"emoji-opt" + (gEmoji === e ? " on" : "")} onClick={() => setGEmoji(e)} style={gEmoji === e ? { borderColor: gColor } : undefined}>{e}</button>
            ))}
          </div>
          <div className="color-pick">
            {MEMBER_COLORS.map((c) => (
              <button key={c} className={"color-opt" + (gColor === c ? " on" : "")} style={{ background: c }} onClick={() => setGColor(c)} aria-label="colour" />
            ))}
          </div>
          <div className="row">
            <div className="field">
              <label>Target</label>
              <input value={gTarget} onChange={(e) => setGTarget(e.target.value)} inputMode="decimal" placeholder="1000" />
            </div>
            <div className="field">
              <label>Monthly (optional)</label>
              <input value={gMonthly} onChange={(e) => setGMonthly(e.target.value)} inputMode="decimal" placeholder="100" />
            </div>
          </div>
          <div className="capture-actions">
            <button className="btn btn-ghost" onClick={() => setGoalOpen(false)}>Cancel</button>
            <button className="btn btn-primary" onClick={saveGoal}>Save goal</button>
          </div>
        </div>
      ) : (
        <button className="btn btn-ghost btn-block" onClick={() => setGoalOpen(true)}>+ Add a savings goal</button>
      )}

      {/* Category budgets */}
      <div className="section-h">
        <h2>Spending budgets</h2>
      </div>
      <div className="card">
        {data.budgets.length === 0 ? (
          <div className="empty">Cap a category (e.g. Dining) to keep it in check.</div>
        ) : (
          data.budgets.map((b) => (
            <div className="item" key={b.category}>
              <div className="ic">🎯</div>
              <div className="meta">
                <div className="t">{b.category}</div>
                <div className="s">{formatMoney(b.limit, data.currency)} / month</div>
              </div>
              <button className="x" onClick={() => removeBudget(b.category)} aria-label="Remove">×</button>
            </div>
          ))
        )}
        <div className="row" style={{ marginTop: 10 }}>
          <input className="mini-input" value={newCat} onChange={(e) => setNewCat(e.target.value)} placeholder="Category" />
          <input className="mini-input" value={newLimit} onChange={(e) => setNewLimit(e.target.value)} inputMode="decimal" placeholder="Limit" style={{ maxWidth: 110 }} />
        </div>
        <button className="btn btn-ghost btn-block" onClick={saveBudget} style={{ marginTop: 10 }}>Set budget</button>
      </div>

      {/* Bills summary */}
      <div className="section-h">
        <h2>Recurring bills</h2>
        <Link href="/bills">Manage →</Link>
      </div>
      <Link href="/bills" className="card" style={{ display: "block" }}>
        <div className="alloc-row total" style={{ borderBottom: "none" }}>
          <span>{bills.length} bill{bills.length === 1 ? "" : "s"} · {formatMoney(billsTotal, data.currency)}/mo</span>
          <span className="muted">{formatMoney(billsPaid, data.currency)} paid →</span>
        </div>
      </Link>
    </main>
  );
}
