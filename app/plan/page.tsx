"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import {
  ArrowRight,
  CalendarDays,
  Home,
  Layers,
  PiggyBank,
  Plus,
  Target,
  TrendingUp,
  Trash2,
  Wallet,
  X,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { billsThisMonth, budgetStatus, moneyPlan, monthlyTotals } from "@/lib/insights";
import { clampPct, formatMoney } from "@/lib/format";
import type { Goal } from "@/lib/types";

const GOAL_EMOJIS = ["🎯", "🛟", "🏠", "🚗", "✈️", "🎄", "💍", "🎓", "🏖️", "💻"];
import Donut from "@/components/Donut";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";

const ALLOC = [
  { key: "bills", label: "Bills & needs", color: "#0f766e" },
  { key: "savings", label: "Savings & goals", color: "#14b8a6" },
  { key: "debt", label: "Debt paydown", color: "#5e7fa6" },
  { key: "budgeted", label: "Everyday budgets", color: "#d99a4e" },
];

interface GoalDraft { id?: string; name: string; emoji: string; target: string; monthly: string; }

export default function PlanPage() {
  const { data, ready, addGoal, updateGoal, deleteGoal, contributeGoal } = useStore();
  const root = useRef<HTMLElement>(null);
  const [gDraft, setGDraft] = useState<GoalDraft | null>(null);
  const [addAmt, setAddAmt] = useState("");

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
    contributeGoal(gDraft.id, a);
    setGDraft(null);
  }

  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".lx-reveal", { y: 20, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
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

  return (
    <main className="lx" ref={root}>
      <header className="lx-top lx-reveal">
        <div>
          <p className="lx-eyebrow"><Target size={13} /> Your money plan</p>
          <h1 className="lx-h1">Plan</h1>
        </div>
      </header>

      <div className="lx-hero lx-reveal">
        <div className="lx-hero-inner lx-debt-hero">
          <div>
            <div className="lx-hero-label">{plan.leftover >= 0 ? "Left to assign" : "Over-allocated"}</div>
            <div className={"lx-hero-num " + (plan.leftover >= 0 ? "pos" : "neg")}>{formatMoney(Math.abs(plan.leftover), cur)}</div>
            <div className="lx-hero-sub">
              {hasPlan
                ? plan.leftover >= 0
                  ? "Give every dollar a job — assign this to a goal or buffer."
                  : "You've planned more than you earn. Trim a budget or goal."
                : "Add income, bills, budgets, or goals to build your plan."}
            </div>
          </div>
          <Ring pct={allocationPct} size={92} stroke={9} color="#14b8a6" track="rgba(15,30,45,0.08)">
            <strong>{Math.round(allocationPct)}%</strong>
            <span>assigned</span>
          </Ring>
        </div>
      </div>

      <Link href="/buckets" className="lx-card lx-cta lx-reveal">
        <div className="lx-cta-ic"><Layers size={22} /></div>
        <div className="lx-cta-meta">
          <div className="lx-cta-t">Income & buckets</div>
          <div className="lx-cta-s">Set your salary date · set aside for savings, investing, tithes & giving.</div>
        </div>
        <ArrowRight size={18} className="lx-cta-arrow" />
      </Link>

      <div className="lx-mgrid three lx-reveal">
        <Link href="/buckets" className="lx-metric">
          <div className="ic"><Wallet size={17} /></div>
          <div className="lx-metric-lbl">Income</div>
          <div className="lx-metric-num">{plan.income ? formatMoney(plan.income, cur) : "—"}</div>
        </Link>
        <Link href="/buckets" className="lx-metric">
          <div className="ic"><PiggyBank size={17} /></div>
          <div className="lx-metric-lbl">Saving</div>
          <div className="lx-metric-num pos">{formatMoney(plan.savings, cur)}</div>
        </Link>
        <div className="lx-metric">
          <div className="ic gold"><TrendingUp size={17} /></div>
          <div className="lx-metric-lbl">Surplus</div>
          <div className={"lx-metric-num " + (plan.leftover >= 0 ? "" : "neg")}>{formatMoney(plan.leftover, cur)}</div>
        </div>
      </div>

      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Where it goes</h2><Link href="/settings">Edit</Link></div>
        {slices.length ? (
          <div className="lx-donutwrap">
            <Donut slices={slices} centerTop={`${Math.round(allocationPct)}%`} centerSub="assigned" size={168} stroke={24} />
            <div className="lx-legend">
              {slices.map((s) => (
                <div className="lx-legend-row" key={s.label}>
                  <span className="sw" style={{ background: s.color }} />
                  <span className="nm">{s.label}</span>
                  <span className="am">{formatMoney(s.value, cur)}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="lx-blank">
            <div className="ic"><Wallet size={22} /></div>
            <h4>Nothing assigned yet</h4>
            <p>Add bills, budgets, or goals so every dollar gets a role.</p>
          </div>
        )}
      </section>

      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Cash flow</h2><span className="lx-plan-free">6 months</span></div>
        <Sparkline
          values={hasForecast ? forecast : [0, 0, 0, 0, 0, 0]}
          labels={trend.map((m) => m.label)}
          color="#0f766e"
          height={150}
        />
        <p className="lx-proj-note"><TrendingUp size={13} /> Money in minus money out, month by month.</p>
      </section>

      {budgets.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Budgets</h2><Link href="/settings">Edit</Link></div>
          <div className="lx-barlist">
            {budgets.slice(0, 6).map((b) => (
              <div className="lx-barrow" key={b.category}>
                <div className="top">
                  <span className="nm">{b.category}</span>
                  <span className="vals">{formatMoney(b.spent, cur)} / {formatMoney(b.limit, cur)}</span>
                </div>
                <div className="track"><span className={b.over ? "over" : ""} style={{ width: `${Math.min(100, b.pct)}%` }} /></div>
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Savings goals</h2>
          <button className="lx-headadd" onClick={() => openGoal()}><Plus size={16} /> Add</button>
        </div>
        {goals.length ? (
          <div className="lx-barlist">
            {goals.map((g) => (
              <button className="lx-barrow lx-barrow-tap" key={g.id} onClick={() => openGoal(g)}>
                <div className="top">
                  <span className="nm">{g.emoji} {g.name}</span>
                  <span className="vals">{formatMoney(g.saved, cur)} / {formatMoney(g.target, cur)}</span>
                </div>
                <div className="track"><span style={{ width: `${g.target > 0 ? clampPct((g.saved / g.target) * 100) : 0}%` }} /></div>
              </button>
            ))}
          </div>
        ) : (
          <div className="lx-blank">
            <div className="ic"><PiggyBank size={22} /></div>
            <h4>No goals yet</h4>
            <p>Create your first goal to protect money before you spend it.</p>
            <button className="lx-primary" onClick={() => openGoal()}><Plus size={16} /> Create a goal</button>
          </div>
        )}
      </section>

      {events.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Coming up</h2><Link href="/bills">Bills</Link></div>
          <div className="lx-list">
            {events.map((e) => (
              <div className="lx-li" key={e.id}>
                <span className="ic"><e.Icon size={16} /></span>
                <div className="meta"><div className="t">{e.label}</div><div className="s">{e.sub}</div></div>
                <div className="amt neg">{formatMoney(e.amount, cur)}</div>
              </div>
            ))}
          </div>
          <Link href="/bills" className="lx-proj-note" style={{ marginTop: 10 }}>Manage bills <ArrowRight size={13} /></Link>
        </section>
      )}

      {gDraft && (
        <div className="lx-sheet-backdrop" onClick={() => setGDraft(null)}>
          <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="lx-sheet-head">
              <h3>{gDraft.id ? "Edit goal" : "New goal"}</h3>
              <button className="lx-sheet-x" onClick={() => setGDraft(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <div className="lx-emoji-row" style={{ flexWrap: "wrap" }}>
              {GOAL_EMOJIS.map((em) => (
                <button key={em} className={"lx-emoji" + (gDraft.emoji === em ? " on" : "")} onClick={() => setGDraft({ ...gDraft, emoji: em })}>{em}</button>
              ))}
            </div>
            <label className="lx-field"><span>Goal name</span>
              <input value={gDraft.name} onChange={(e) => setGDraft({ ...gDraft, name: e.target.value })} placeholder="Emergency fund" autoFocus />
            </label>
            <div className="lx-field-row">
              <label className="lx-field"><span>Target</span>
                <input type="number" inputMode="decimal" value={gDraft.target} onChange={(e) => setGDraft({ ...gDraft, target: e.target.value })} placeholder="6000" />
              </label>
              <label className="lx-field"><span>Per month</span>
                <input type="number" inputMode="decimal" value={gDraft.monthly} onChange={(e) => setGDraft({ ...gDraft, monthly: e.target.value })} placeholder="300" />
              </label>
            </div>
            <button className="lx-primary full" onClick={saveGoal} disabled={!gDraft.name.trim() || !(parseFloat(gDraft.target) > 0)}>
              {gDraft.id ? "Save changes" : "Create goal"}
            </button>
            {gDraft.id && (
              <>
                <div className="lx-pay-row" style={{ marginTop: 12 }}>
                  <input type="number" inputMode="decimal" placeholder="Add money" value={addAmt} onChange={(e) => setAddAmt(e.target.value)} />
                  <button className="lx-primary sm" onClick={addToGoal} disabled={!(parseFloat(addAmt) > 0)}>Add to saved</button>
                </div>
                <button className="lx-ghost danger" style={{ width: "100%", marginTop: 10 }}
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
