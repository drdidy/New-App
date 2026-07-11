"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ArrowRight, CalendarDays, Home, Layers, PiggyBank, Plus, TrendingUp, Trash2, Wallet, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { billsThisMonth, budgetStatus, moneyPlan, monthlyTotals, futureProjection } from "@/lib/insights";
import { clampPct, formatMoney } from "@/lib/format";
import type { Goal } from "@/lib/types";
import AnimatedNumber from "@/components/AnimatedNumber";
import Donut from "@/components/Donut";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import Burst from "@/components/Burst";
import { success } from "@/lib/haptics";

const GOAL_EMOJIS = ["🎯", "🛟", "🏠", "🚗", "✈️", "🎄", "💍", "🎓", "🏖️", "💻"];

const ALLOC = [
  { key: "bills", label: "Bills & needs", color: "#bd8826" },
  { key: "savings", label: "Savings & goals", color: "#23906b" },
  { key: "debt", label: "Debt paydown", color: "#5b8fd6" },
  { key: "budgeted", label: "Everyday budgets", color: "#d0704a" },
];

interface GoalDraft { id?: string; name: string; emoji: string; target: string; monthly: string; }

export default function PlanPage() {
  const { data, ready, addGoal, updateGoal, deleteGoal, contributeGoal } = useStore();
  const root = useRef<HTMLElement>(null);
  const [gDraft, setGDraft] = useState<GoalDraft | null>(null);
  const [addAmt, setAddAmt] = useState("");
  const [celebrate, setCelebrate] = useState(0);

  function openGoal(g?: Goal) {
    setAddAmt("");
    setGDraft(g
      ? { id: g.id, name: g.name, emoji: g.emoji || "🎯", target: String(g.target), monthly: g.monthlyContribution != null ? String(g.monthlyContribution) : "" }
      : { name: "", emoji: "🎯", target: "", monthly: "" });
  }
  function saveGoal() {
    if (!gDraft) return;
    const target = parseFloat(gDraft.target);
    if (!gDraft.name.trim() || !(target > 0)) return;
    const monthly = parseFloat(gDraft.monthly);
    const patch = {
      name: gDraft.name.trim(),
      emoji: gDraft.emoji,
      target,
      monthlyContribution: Number.isFinite(monthly) && monthly > 0 ? monthly : undefined,
    };
    if (gDraft.id) updateGoal(gDraft.id, patch);
    else addGoal({ ...patch, color: "#14b8a6" });
    setGDraft(null);
  }
  function addToGoal() {
    if (!gDraft?.id) return;
    const a = parseFloat(addAmt);
    if (!(a > 0)) return;
    const g = data.goals.find((x) => x.id === gDraft.id);
    contributeGoal(gDraft.id, a);
    // The moment a goal is fully funded deserves more than a longer bar.
    if (g && g.saved < g.target && g.saved + a >= g.target) {
      setCelebrate((c) => c + 1);
      success();
    }
    setGDraft(null);
  }

  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;

  const cur = data.currency;
  const plan = moneyPlan(data);
  const bills = billsThisMonth(data);
  const budgets = budgetStatus(data);
  const goals = data.goals || [];
  const trend = monthlyTotals(data, 6);
  const allocationPct = plan.income ? clampPct((plan.allocated / plan.income) * 100) : 0;

  const sliceVals: Record<string, number> = {
    bills: plan.bills,
    savings: plan.savings,
    debt: plan.debtMin,
    budgeted: plan.budgeted,
  };
  const slices = ALLOC.map((a) => ({ label: a.label, value: sliceVals[a.key], color: a.color })).filter((s) => s.value > 0);

  const events = [
    ...bills.slice(0, 4).map((b) => ({
      id: b.bill.id,
      label: b.bill.name,
      sub: `Due day ${b.dueDay}${b.paid ? " · paid" : ""}`,
      amount: b.bill.amount,
      Icon: b.bill.category.toLowerCase().includes("rent") ? Home : CalendarDays,
    })),
    ...goals.filter((g) => (g.monthlyContribution || 0) > 0).slice(0, 2).map((g) => ({
      id: g.id,
      label: g.name,
      sub: "Monthly contribution",
      amount: g.monthlyContribution || 0,
      Icon: PiggyBank,
    })),
  ];
  const forecast = trend.map((m) => m.income - m.expense);
  const hasForecast = forecast.some(Boolean);
  const hasPlan = plan.income > 0 || plan.allocated > 0 || budgets.length > 0 || goals.length > 0 || bills.length > 0;
  const future = futureProjection(data, 12);
  const debtFree = future && future.debtFreeInMonths != null && future.debtFreeInMonths <= 12;

  return (
    <main className="pg" ref={root}>
      {celebrate > 0 && <Burst key={celebrate} />}
      <div className="pg-head rise">
        <p className="pg-date">Your money plan</p>
        <button className="btn-text" onClick={() => openGoal()}>+ New goal</button>
      </div>
      <h1 className="pg-title rise">Plan</h1>
      <div className="pg-rule rise" />

      {/* STATEMENT + GAUGE */}
      <div className="st rise">
        <div className="st-row">
          <div>
            <div className="st-label">{plan.leftover >= 0 ? "Left to assign" : "Over-allocated"}</div>
            <div className={"st-num" + (plan.leftover >= 0 ? "" : " neg")}>
              <AnimatedNumber value={Math.abs(plan.leftover)} currency={cur} />
            </div>
            <p className="st-meta">
              {hasPlan
                ? plan.leftover >= 0
                  ? "Give every dollar a job — assign this to a goal or buffer."
                  : "You've planned more than you earn. Trim a budget or goal."
                : "Add income, bills, budgets, or goals to build your plan."}
            </p>
          </div>
          <Ring pct={allocationPct} size={92} stroke={8} color="#e2b366" track="rgba(241,233,216,0.1)">
            <strong>{Math.round(allocationPct)}%</strong>
            <span>assigned</span>
          </Ring>
        </div>
        <div className="st-links">
          <Link href="/buckets">Income {plan.income ? formatMoney(plan.income, cur) : "—"}</Link>
          <Link href="/buckets" className="pos" style={{ borderBottomColor: "rgba(76,195,138,0.4)" }}>Saving {formatMoney(plan.savings, cur)}</Link>
          <span>Surplus {formatMoney(plan.leftover, cur)}</span>
        </div>
      </div>

      {/* INCOME & BUCKETS DOOR */}
      <Link href="/buckets" className="flag rise" style={{ marginBottom: 18 }}>
        <span className="flag-txt">
          <Layers size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "-2px" }} />
          <b>Income & buckets</b> — set your salary date; set aside for savings, investing, tithes & giving. <ArrowRight size={12} style={{ display: "inline" }} />
        </span>
      </Link>

      {/* FUTURE YOU */}
      {future && (
        <section className="sec rise">
          <div className="sec-head"><h2>🔮 Future you · 12 months</h2></div>
          <p className="sec-sub">If you keep this up:</p>
          {future.debtNow > 0 && (
            <div className="row" style={{ padding: "9px 0" }}>
              <div className="row-meta"><div className="row-t mut" style={{ fontWeight: 600 }}>Debt</div></div>
              <div className="row-amt">{debtFree ? "Debt-free 🎉" : `${formatMoney(future.debtNow, cur)} → ${formatMoney(future.debtThen, cur)}`}</div>
            </div>
          )}
          {future.savedAdded > 0 && (
            <div className="row" style={{ padding: "9px 0" }}>
              <div className="row-meta"><div className="row-t mut" style={{ fontWeight: 600 }}>Saved</div></div>
              <div className="row-amt pos">+{formatMoney(future.savedAdded, cur)}</div>
            </div>
          )}
          <div className="row" style={{ padding: "9px 0" }}>
            <div className="row-meta"><div className="row-t mut" style={{ fontWeight: 600 }}>Net worth</div></div>
            <div className="row-amt">about {formatMoney(future.netWorthThen, cur)}</div>
          </div>
          <p className="sec-sub">An estimate from your current saving & payment pace — every extra dollar beats it.</p>
        </section>
      )}

      {/* WHERE IT GOES */}
      <section className="sec rise">
        <div className="sec-head"><h2>Where it goes</h2><span className="sec-aux"><Link href="/settings">Edit</Link></span></div>
        {slices.length ? (
          <div className="donut-wrap">
            <Donut slices={slices} centerTop={`${Math.round(allocationPct)}%`} centerSub="assigned" size={158} stroke={22} />
            <div className="legend">
              {slices.map((s) => (
                <div className="legend-row" key={s.label}>
                  <span className="sw" style={{ background: s.color }} />
                  <span className="nm">{s.label}</span>
                  <span className="am">{formatMoney(s.value, cur)}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="blank">
            <div className="ic"><Wallet size={22} /></div>
            <h4>Nothing assigned yet</h4>
            <p>Add bills, budgets, or goals so every dollar gets a role.</p>
          </div>
        )}
      </section>

      {/* CASH FLOW */}
      <section className="sec rise">
        <div className="sec-head"><h2>Cash flow</h2><span className="sec-aux"><span className="tag">6 months</span></span></div>
        <Sparkline values={hasForecast ? forecast : [0, 0, 0, 0, 0, 0]} labels={trend.map((m) => m.label)} color="#e2b366" height={140} />
        <p className="sec-sub"><TrendingUp size={12} style={{ display: "inline", verticalAlign: "-2px" }} /> Money in minus money out, month by month.</p>
      </section>

      {/* BUDGETS */}
      {budgets.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Budgets</h2><span className="sec-aux"><Link href="/settings">Edit</Link></span></div>
          {budgets.slice(0, 6).map((b) => (
            <div className="row" key={b.category} style={{ display: "block" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <span className="row-t">{b.category}</span>
                <span className={"row-amt" + (b.over ? " neg" : "")}>{formatMoney(b.spent, cur)} / {formatMoney(b.limit, cur)}</span>
              </div>
              <div className="meter" style={{ margin: "9px 0 2px" }}><span className={b.over ? "over" : ""} style={{ width: `${Math.min(100, b.pct)}%` }} /></div>
            </div>
          ))}
        </section>
      )}

      {/* SAVINGS GOALS */}
      <section className="sec rise">
        <div className="sec-head"><h2>Savings goals</h2><span className="sec-aux"><button className="link" onClick={() => openGoal()}>+ Add</button></span></div>
        {goals.length ? goals.map((g) => (
          <button className="row" key={g.id} onClick={() => openGoal(g)} style={{ display: "block" }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
              <span className="row-t">{g.emoji} {g.name}</span>
              <span className="row-amt">{formatMoney(g.saved, cur)} / {formatMoney(g.target, cur)}</span>
            </div>
            <div className="meter" style={{ margin: "9px 0 2px" }}><span style={{ width: `${g.target > 0 ? clampPct((g.saved / g.target) * 100) : 0}%` }} /></div>
          </button>
        )) : (
          <div className="blank">
            <div className="ic"><PiggyBank size={22} /></div>
            <h4>No goals yet</h4>
            <p>Create your first goal to protect money before you spend it.</p>
            <button className="btn" onClick={() => openGoal()}><Plus size={16} /> Create a goal</button>
          </div>
        )}
      </section>

      {/* COMING UP */}
      {events.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Coming up</h2><span className="sec-aux"><Link href="/bills">Bills</Link></span></div>
          {events.map((e) => (
            <div className="row" key={e.id}>
              <span className="row-ic"><e.Icon /></span>
              <div className="row-meta"><div className="row-t">{e.label}</div><div className="row-s">{e.sub}</div></div>
              <div className="row-amt neg">{formatMoney(e.amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {gDraft && (
        <div className="sheet-backdrop" onClick={() => setGDraft(null)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-head">
              <h3>{gDraft.id ? "Edit goal" : "New goal"}</h3>
              <button className="btn-icon" onClick={() => setGDraft(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <div className="chips" style={{ marginBottom: 14 }}>
              {GOAL_EMOJIS.map((em) => (
                <button key={em} className={"chip" + (gDraft.emoji === em ? " on" : "")} onClick={() => setGDraft({ ...gDraft, emoji: em })}>{em}</button>
              ))}
            </div>
            <label className="field"><span>Goal name</span>
              <input value={gDraft.name} onChange={(e) => setGDraft({ ...gDraft, name: e.target.value })} placeholder="Emergency fund" autoFocus />
            </label>
            <div className="fieldrow">
              <label className="field"><span>Target</span>
                <input type="number" inputMode="decimal" value={gDraft.target} onChange={(e) => setGDraft({ ...gDraft, target: e.target.value })} placeholder="6000" />
              </label>
              <label className="field"><span>Per month</span>
                <input type="number" inputMode="decimal" value={gDraft.monthly} onChange={(e) => setGDraft({ ...gDraft, monthly: e.target.value })} placeholder="300" />
              </label>
            </div>
            <button className="btn full" onClick={saveGoal} disabled={!gDraft.name.trim() || !(parseFloat(gDraft.target) > 0)}>
              {gDraft.id ? "Save changes" : "Create goal"}
            </button>
            {gDraft.id && (
              <>
                <div className="inline-form" style={{ marginTop: 12 }}>
                  <input className="input" type="number" inputMode="decimal" placeholder="Add money" value={addAmt} onChange={(e) => setAddAmt(e.target.value)} />
                  <button className="btn sm" onClick={addToGoal} disabled={!(parseFloat(addAmt) > 0)}>Add to saved</button>
                </div>
                <button className="btn-ghost danger" style={{ width: "100%", marginTop: 10 }}
                  onClick={() => { if (confirm(`Delete "${gDraft.name}"?`)) { deleteGoal(gDraft.id!); setGDraft(null); } }}>
                  <Trash2 size={15} /> Delete goal
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
