"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import {
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  MessageCircleHeart,
  Wallet,
  Landmark,
  Sparkles,
  Flame,
  Trash2,
  X,
} from "lucide-react";
import type { Transaction } from "@/lib/types";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  netWorth,
  cashOnHand,
  safeToSpend,
  loggingStreak,
  quickInsights,
} from "@/lib/insights";
import { formatMoney, friendlyDate } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";
import QuickCapture from "@/components/QuickCapture";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

const CAT_ICON: Record<string, string> = {
  Groceries: "🛒", Transport: "⛽", Dining: "🍔", Rent: "🏠", Utilities: "💡",
  Salary: "💰", Income: "💰", Shopping: "🛍️", Savings: "🐷", "Debt payment": "🤝",
};

export default function TodayPage() {
  const { data, ready, updateTransaction, deleteTransaction, addAccount, updateAccount } = useStore();
  const root = useRef<HTMLElement>(null);
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [amt, setAmt] = useState("");
  const [desc, setDesc] = useState("");
  const [balOpen, setBalOpen] = useState(false);
  const [balInput, setBalInput] = useState("");

  function saveBalance() {
    const v = parseFloat(balInput.replace(/[$,\s]/g, ""));
    if (!Number.isFinite(v) || v < 0) return;
    const liquid = (data.accounts || []).find((a) => a.type === "checking" || a.type === "cash");
    if (liquid) updateAccount(liquid.id, { balance: v });
    else addAccount({ name: "Cash on hand", type: "checking", balance: v, emoji: "💵", color: "#5e7fa6" });
    setBalOpen(false);
    setBalInput("");
  }

  function openEdit(t: Transaction) {
    setEditTx(t);
    setAmt(String(t.amount));
    setDesc(t.description || "");
  }
  function saveEdit() {
    if (!editTx) return;
    const a = parseFloat(amt);
    if (!Number.isFinite(a) || a <= 0) return;
    updateTransaction(editTx.id, { amount: Math.abs(a), description: desc.trim() });
    setEditTx(null);
  }

  useEffect(() => {
    if (!ready) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const ctx = gsap.context(() => {
      gsap.from(".lx-reveal", {
        y: 22,
        opacity: 0,
        duration: 0.6,
        ease: "power3.out",
        stagger: 0.08,
      });
      gsap.from(".lx-hero", {
        scale: 0.96,
        opacity: 0,
        duration: 0.7,
        ease: "back.out(1.6)",
      });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;

  const summary = summarize(data);
  const firstName = data.members[0]?.name?.split(" ")[0] || "there";
  const cash = cashOnHand(data);
  const nw = netWorth(data);
  const sts = safeToSpend(data);
  const bills = billsThisMonth(data).filter((b) => !b.paid);
  const recent = data.transactions.slice(0, 5);
  const goal = data.goals[0];
  const insights = quickInsights(data, data.currency, 2);
  const safePos = sts.safe >= 0;
  const cur = data.currency;
  const barPct = sts.spendable > 0 ? Math.max(0, Math.min(100, (sts.safe / sts.spendable) * 100)) : safePos ? 60 : 8;
  const streak = loggingStreak(data);

  return (
    <main className="lx" ref={root}>
      <header className="lx-top lx-reveal">
        <div>
          <p className="lx-eyebrow">{greeting()}, {firstName}</p>
          <h1 className="lx-h1">Today</h1>
        </div>
        <div className="lx-top-actions">
          <div className={"lx-streak" + (streak.loggedToday ? " on" : "")} title={`${streak.count}-day streak`}>
            <Flame size={16} /> {streak.count}
          </div>
          <Link href="/coach" className="lx-coachbtn" aria-label="Open coach">
            <MessageCircleHeart size={20} />
          </Link>
        </div>
      </header>

      {/* HERO */}
      <div className="lx-hero lx-hero-glow">
        <div className="lx-hero-aura" aria-hidden="true" />
        <div className="lx-hero-inner">
          <div className="lx-hero-label">
            Safe to spend
            <span className="lx-hero-tag">{sts.mode === "cash" ? "from real cash" : "from income"}</span>
          </div>
          <div className={"lx-hero-num " + (safePos ? "pos" : "neg")}>
            <AnimatedNumber value={sts.safe} currency={cur} />
          </div>
          <div className="lx-hero-sub">
            {safePos
              ? `About ${formatMoney(sts.dailyAllowance, cur)} a day for the ${sts.daysLeft} days ${sts.periodLabel}.`
              : "You're short for what's due before payday — tap Coach for a plan."}
          </div>
          <div className="lx-bar"><span style={{ width: `${barPct}%` }} /></div>
          {sts.committed > 0 && (
            <div className="lx-hero-math">
              <span>{formatMoney(sts.spendable, cur)} {sts.mode === "cash" ? "on hand" : "income left"}</span>
              <span className="lx-hero-minus">− {formatMoney(sts.committed, cur)} due before payday</span>
            </div>
          )}
          {!sts.hasAccounts && !balOpen && (
            <button className="lx-hero-hint" onClick={() => setBalOpen(true)}>
              Set your real balance to make this exact →
            </button>
          )}
          {!sts.hasAccounts && balOpen && (
            <div className="lx-balset">
              <input
                type="number" inputMode="decimal" autoFocus placeholder="What's in your account now?"
                value={balInput} onChange={(e) => setBalInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && saveBalance()}
              />
              <button className="lx-primary sm" onClick={saveBalance} disabled={!(parseFloat(balInput) >= 0)}>Save</button>
            </div>
          )}
        </div>
      </div>

      {/* STREAK / MOMENTUM */}
      <div className="lx-momentum lx-reveal">
        <div className="lx-momentum-flame"><Flame size={20} /></div>
        <div className="lx-momentum-meta">
          <strong>{streak.count > 0 ? `${streak.count}-day streak` : "Start your streak"}</strong>
          <span>
            {streak.loggedToday
              ? "Logged today — nice. Keep the fire going tomorrow. 🔥"
              : streak.count > 0
                ? "Log one thing today to keep it alive."
                : "Log anything below to light it up."}
          </span>
        </div>
        <div className="lx-momentum-dots">
          {[0, 1, 2, 3, 4].map((n) => (
            <span key={n} className={n < Math.min(5, streak.count) ? "on" : ""} />
          ))}
        </div>
      </div>

      {/* REAL MONEY ROW (balance-first) */}
      <div className="lx-stats lx-reveal">
        <div className="lx-stat">
          <Wallet size={16} className="lx-stat-ic" />
          <div className="lx-stat-num">{formatMoney(cash, cur)}</div>
          <div className="lx-stat-lbl">In your accounts</div>
        </div>
        <div className="lx-stat">
          <Landmark size={16} className="lx-stat-ic" />
          <div className={"lx-stat-num " + (nw >= 0 ? "pos" : "calm")}>{formatMoney(nw, cur)}</div>
          <div className="lx-stat-lbl">Net worth</div>
        </div>
        <Link href="/debt" className="lx-stat">
          <ArrowDownRight size={16} className="lx-stat-ic neg" />
          <div className="lx-stat-num neg">{formatMoney(summary.totalIOwe, cur)}</div>
          <div className="lx-stat-lbl">You owe</div>
        </Link>
      </div>

      {/* IN / OUT */}
      <div className="lx-io lx-reveal">
        <div className="lx-io-item">
          <ArrowUpRight size={15} className="pos" />
          <span className="lx-io-num pos">{formatMoney(summary.income, cur)}</span>
          <span className="lx-io-lbl">In</span>
        </div>
        <div className="lx-io-div" />
        <div className="lx-io-item">
          <ArrowDownRight size={15} className="neg" />
          <span className="lx-io-num neg">{formatMoney(summary.expenses, cur)}</span>
          <span className="lx-io-lbl">Out</span>
        </div>
      </div>

      <div className="lx-reveal"><QuickCapture /></div>

      {insights.length > 0 && (
        <div className="lx-reveal">
          {insights.map((t, i) => (
            <div className="lx-insight" key={i}><Sparkles size={15} /> <span>{t}</span></div>
          ))}
        </div>
      )}

      {bills.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Bills due</h2><Link href="/bills">Manage</Link></div>
          {bills.slice(0, 3).map((b) => (
            <div className="lx-row" key={b.bill.id}>
              <span className="lx-row-ic">🧾</span>
              <div className="lx-row-meta"><div className="lx-row-t">{b.bill.name}</div><div className="lx-row-s">Due {b.dueDay}</div></div>
              <div className="lx-row-amt neg">{formatMoney(b.bill.amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {goal && (
        <section className="lx-card lx-reveal lx-goal">
          <div className="lx-card-head"><h2>{goal.emoji} {goal.name}</h2><Link href="/plan">Plan</Link></div>
          <div className="lx-goal-num">{formatMoney(goal.saved, cur)} <small>of {formatMoney(goal.target, cur)}</small></div>
          <div className="lx-bar"><span style={{ width: `${goal.target > 0 ? Math.min(100, (goal.saved / goal.target) * 100) : 0}%` }} /></div>
        </section>
      )}

      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Recent</h2><Link href="/spending">Insights</Link></div>
        {recent.length === 0 ? (
          <div className="lx-empty">Nothing yet — say <b>“spent 12 on coffee”</b> above.</div>
        ) : recent.map((t) => (
          <button className="lx-row lx-row-tap" key={t.id} onClick={() => openEdit(t)}>
            <span className="lx-row-ic">{CAT_ICON[t.category] || "💸"}</span>
            <div className="lx-row-meta">
              <div className="lx-row-t">{t.description || t.category}</div>
              <div className="lx-row-s">{t.category} · {friendlyDate(t.date)}</div>
            </div>
            <div className={"lx-row-amt " + (t.type === "income" ? "pos" : "neg")}>
              {t.type === "income" ? "+" : "−"}{formatMoney(t.amount, cur)}
            </div>
          </button>
        ))}
        {recent.length > 0 && <div className="lx-row-hint">Tap an entry to edit or delete it.</div>}
      </section>

      <Link href="/coach" className="lx-card lx-cta lx-reveal">
        <div className="lx-cta-ic"><MessageCircleHeart size={22} /></div>
        <div className="lx-cta-meta">
          <div className="lx-cta-t">Ask your money coach</div>
          <div className="lx-cta-s">A plan built on your real numbers.</div>
        </div>
        <ArrowRight size={18} className="lx-cta-arrow" />
      </Link>

      {editTx && (
        <div className="lx-sheet-backdrop" onClick={() => setEditTx(null)}>
          <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="lx-sheet-head">
              <h3>Edit entry</h3>
              <button className="lx-sheet-x" onClick={() => setEditTx(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <p className="lx-group-sub">{editTx.category} · {friendlyDate(editTx.date)} · {editTx.type}</p>
            <label className="lx-field"><span>Amount</span>
              <input type="number" inputMode="decimal" value={amt} onChange={(e) => setAmt(e.target.value)} autoFocus />
            </label>
            <label className="lx-field"><span>Description</span>
              <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={editTx.category} />
            </label>
            <button className="lx-primary full" onClick={saveEdit} disabled={!(parseFloat(amt) > 0)}>Save changes</button>
            <button className="lx-ghost danger" style={{ width: "100%", marginTop: 10 }}
              onClick={() => { deleteTransaction(editTx.id); setEditTx(null); }}>
              <Trash2 size={15} /> Delete this entry
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
