"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import {
  ArrowRight,
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
  netWorth,
  cashOnHand,
  safeToSpend,
  loggingStreak,
  noSpendStreak,
  worthKnowing,
  paycheckPlan,
} from "@/lib/insights";
import { formatMoney, friendlyDate, monthKey } from "@/lib/format";
import { success } from "@/lib/haptics";
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
  const { data, ready, updateTransaction, deleteTransaction, addAccount, updateAccount, distributePaycheck, markPaycheckDistributed, markCheckIn } = useStore();
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
    success();
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
  const recent = data.transactions.slice(0, 5);
  const knowables = worthKnowing(data, 4);
  const noSpend = noSpendStreak(data);
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
          {(sts.committed > 0 || sts.setAside > 0) && (
            <div className="lx-hero-math">
              <Link href="/spending" className="lx-hero-link">{formatMoney(sts.spendable, cur)} {sts.mode === "cash" ? "on hand" : "income left"}</Link>
              {sts.committed > 0 && <Link href="/bills" className="lx-hero-minus lx-hero-link">− {formatMoney(sts.committed, cur)} due before payday</Link>}
              {sts.setAside > 0 && <Link href="/buckets" className="lx-hero-minus lx-hero-link">− {formatMoney(sts.setAside, cur)} set aside in buckets</Link>}
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

      {/* GIVE & SAVE FIRST — proactive paycheck-allocation nudge */}
      {(() => {
        const plan = paycheckPlan(data);
        if (!plan || data.lastPaycheckDistributed === monthKey()) return null;
        return (
          <section className="lx-payday lx-reveal">
            <div className="lx-payday-head">🙏 You’ve been paid {formatMoney(plan.income, cur)} this month</div>
            <p className="lx-payday-sub">
              Give and save first — set aside {formatMoney(plan.setAside, cur)}
              {plan.tithe > 0 ? `, including ${formatMoney(plan.tithe, cur)} for giving,` : ""} across {plan.bucketCount} bucket{plan.bucketCount === 1 ? "" : "s"} before it slips away.
            </p>
            <div className="lx-payday-actions">
              <button className="lx-primary sm" onClick={() => { distributePaycheck(plan.income); markPaycheckDistributed(); success(); }}>
                <Sparkles size={14} /> Set aside {formatMoney(plan.setAside, cur)}
              </button>
              <button className="lx-ghost sm" onClick={() => markPaycheckDistributed()}>Not now</button>
            </div>
          </section>
        );
      })()}

      {/* STREAK / MOMENTUM */}
      <div className="lx-momentum lx-reveal">
        <div className="lx-momentum-flame"><Flame size={20} /></div>
        <div className="lx-momentum-meta">
          <strong>{streak.count > 0 ? `${streak.count}-day logging streak` : "Start your streak"}</strong>
          <span>
            {noSpend > 0
              ? `🚫 ${noSpend} day${noSpend === 1 ? "" : "s"} without spending — keep it going.`
              : streak.loggedToday
                ? "Logged today — nice. Keep it up tomorrow. 🔥"
                : streak.count > 0
                  ? "Log one thing today to keep your streak alive."
                  : "Log anything below to light it up."}
          </span>
        </div>
        {noSpend > 0 ? (
          <div className="lx-nospend" title="Days in a row with no spending">🚫 {noSpend}d</div>
        ) : (
          <div className="lx-momentum-dots">
            {[0, 1, 2, 3, 4].map((n) => (
              <span key={n} className={n < Math.min(5, streak.count) ? "on" : ""} />
            ))}
          </div>
        )}
      </div>

      {/* Weekly check-in (only when reminders are on and a week has passed) */}
      {data.remindersEnabled && (!data.lastCheckIn || Date.now() - data.lastCheckIn > 7 * 86400000) && (
        <Link
          href="/coach"
          className="lx-checkin lx-reveal"
          onClick={() => { try { sessionStorage.setItem("mc-checkin", "1"); } catch {} markCheckIn(); }}
        >
          🗓️ <b>Weekly check-in time.</b> Tap for your 30-second review with Coach.
        </Link>
      )}

      {knowables.length > 0 && (
        <section className="lx-card lx-reveal lx-know">
          <div className="lx-card-head"><h2>Worth knowing</h2></div>
          {knowables.map((k, i) => (
            <div className={"lx-know-row " + k.tone} key={i}>
              <span className="lx-know-ic">
                {k.tone === "good" ? <Sparkles size={15} /> : k.tone === "warn" ? <ArrowDownRight size={15} /> : <ArrowRight size={15} />}
              </span>
              <span className="lx-know-txt">{k.text}</span>
            </div>
          ))}
        </section>
      )}

      {/* REAL MONEY ROW (balance-first) — every tile drills into its screen */}
      <div className="lx-stats lx-reveal">
        <Link href="/spending" className="lx-stat">
          <Wallet size={16} className="lx-stat-ic" />
          <div className="lx-stat-num">{formatMoney(cash, cur)}</div>
          <div className="lx-stat-lbl">In your accounts</div>
        </Link>
        <Link href="/spending" className="lx-stat">
          <Landmark size={16} className="lx-stat-ic" />
          <div className={"lx-stat-num " + (nw >= 0 ? "pos" : "calm")}>{formatMoney(nw, cur)}</div>
          <div className="lx-stat-lbl">Net worth</div>
        </Link>
        <Link href="/debt" className="lx-stat">
          <ArrowDownRight size={16} className="lx-stat-ic neg" />
          <div className="lx-stat-num neg">{formatMoney(summary.totalIOwe, cur)}</div>
          <div className="lx-stat-lbl">You owe</div>
        </Link>
      </div>

      <div className="lx-reveal"><QuickCapture /></div>

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
