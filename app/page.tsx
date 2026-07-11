"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import { Flame, Sparkles, Trash2, X } from "lucide-react";
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
import { formatMoney, friendlyDate, isoWeekId, monthKey } from "@/lib/format";
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
  const [weekUnread, setWeekUnread] = useState(false);
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
    try { setWeekUnread(localStorage.getItem("mc-week-read") !== isoWeekId()); } catch {}
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
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
  const dateLine = new Date().toLocaleDateString(undefined, { weekday: "long", month: "long", day: "numeric" });
  const checkInDue = data.remindersEnabled && (!data.lastCheckIn || Date.now() - data.lastCheckIn > 7 * 86400000);
  const payday = (() => {
    const plan = paycheckPlan(data);
    if (!plan || data.lastPaycheckDistributed === monthKey()) return null;
    return plan;
  })();

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">{dateLine} · {greeting()}, {firstName}</p>
        <span className="tag" title={noSpend > 0 ? "Days in a row without spending" : "Daily logging streak"}>
          {noSpend > 0 ? <>🚫 {noSpend}d no-spend</> : <><Flame size={11} /> {streak.count}d</>}
        </span>
      </div>
      <h1 className="pg-title rise">Today</h1>
      <div className="pg-rule rise" />

      {/* THE STATEMENT */}
      <div className="st rise">
        <div className="st-label">
          Safe to spend
          <span className="tag">{sts.mode === "cash" ? "from real cash" : "from income"}</span>
        </div>
        <div className={"st-num" + (safePos ? "" : " neg")}>
          <AnimatedNumber value={sts.safe} currency={cur} />
        </div>
        <p className="st-meta">
          {safePos
            ? `About ${formatMoney(sts.dailyAllowance, cur)} a day for the ${sts.daysLeft} days ${sts.periodLabel}.`
            : "You're short for what's due before payday — tap Coach for a plan."}
        </p>
        <div className="meter"><span style={{ width: `${barPct}%` }} /></div>
        {(sts.committed > 0 || sts.setAside > 0) && (
          <div className="st-links">
            <Link href="/spending">{formatMoney(sts.spendable, cur)} {sts.mode === "cash" ? "on hand" : "income left"}</Link>
            {sts.committed > 0 && <Link href="/bills" className="neg">− {formatMoney(sts.committed, cur)} due before payday</Link>}
            {sts.setAside > 0 && <Link href="/buckets" className="neg">− {formatMoney(sts.setAside, cur)} set aside in buckets</Link>}
          </div>
        )}
        {!sts.hasAccounts && !balOpen && (
          <p className="st-note"><button className="btn-text" onClick={() => setBalOpen(true)}>Set your real balance to make this exact →</button></p>
        )}
        {!sts.hasAccounts && balOpen && (
          <div className="inline-form" style={{ marginTop: 12 }}>
            <input className="input" type="number" inputMode="decimal" autoFocus placeholder="What's in your account now?"
              value={balInput} onChange={(e) => setBalInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && saveBalance()} />
            <button className="btn sm" onClick={saveBalance} disabled={!(parseFloat(balInput) >= 0)}>Save</button>
          </div>
        )}
      </div>

      {/* GIVE & SAVE FIRST */}
      {payday && (
        <section className="plate rise">
          <div className="plate-title"><Sparkles /> You’ve been paid {formatMoney(payday.income, cur)}</div>
          <p className="flag-txt" style={{ margin: 0 }}>
            Give and save first — set aside <b>{formatMoney(payday.setAside, cur)}</b>
            {payday.tithe > 0 ? <> including <b>{formatMoney(payday.tithe, cur)}</b> for giving,</> : null} across {payday.bucketCount} bucket{payday.bucketCount === 1 ? "" : "s"} before it slips away.
          </p>
          <div style={{ display: "flex", gap: 8, marginTop: 13 }}>
            <button className="btn sm" onClick={() => { distributePaycheck(payday.income); markPaycheckDistributed(); success(); }}>
              Set aside {formatMoney(payday.setAside, cur)}
            </button>
            <button className="btn-ghost sm" onClick={() => markPaycheckDistributed()}>Not now</button>
          </div>
        </section>
      )}

      {/* WEEKLY CHECK-IN */}
      {checkInDue && (
        <Link href="/coach" className="flag rise" style={{ borderBottom: "1px solid var(--rule-soft)", marginBottom: 18 }}
          onClick={() => { try { sessionStorage.setItem("mc-checkin", "1"); } catch {} markCheckIn(); }}>
          <span className="flag-txt">🗓️ <b>Weekly check-in time.</b> Tap for your 30-second review with Coach.</span>
        </Link>
      )}

      {/* THE WEEKLY EDITION */}
      <Link href="/week" className="flag rise" style={{ borderBottom: "1px solid var(--rule-soft)", marginBottom: 18 }}>
        <span className="flag-txt">
          📰 <b>The Weekly Edition</b> — your week in money, typeset.
          {weekUnread && <b style={{ color: "var(--gold)" }}> New issue ✦</b>}
        </span>
      </Link>

      {/* TICKER */}
      <div className="ticker rise">
        <Link href="/spending" className="ticker-cell">
          <span className="tk-l">Accounts</span>
          <span className="tk-v"><AnimatedNumber value={cash} currency={cur} /></span>
        </Link>
        <Link href="/spending" className="ticker-cell">
          <span className="tk-l">Net worth</span>
          <span className={"tk-v" + (nw >= 0 ? " pos" : " mut")}><AnimatedNumber value={nw} currency={cur} /></span>
        </Link>
        <Link href="/debt" className="ticker-cell">
          <span className="tk-l">You owe</span>
          <span className="tk-v neg"><AnimatedNumber value={summary.totalIOwe} currency={cur} /></span>
        </Link>
      </div>

      {/* WORTH KNOWING */}
      {knowables.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Worth knowing</h2></div>
          {knowables.map((k, i) => (
            <div className={"flag " + k.tone} key={i}>
              <span className="flag-txt">{k.text}</span>
            </div>
          ))}
        </section>
      )}

      {/* CAPTURE */}
      <div className="rise"><QuickCapture /></div>

      {/* RECENT */}
      <section className="sec rise">
        <div className="sec-head"><h2>Recent entries</h2><span className="sec-aux"><Link href="/ledger">All entries</Link></span></div>
        {recent.length === 0 ? (
          <p className="sec-sub">Nothing yet — say <b>“spent 12 on coffee”</b> above.</p>
        ) : recent.map((t) => (
          <button className="row" key={t.id} onClick={() => openEdit(t)}>
            <span className="row-ic">{CAT_ICON[t.category] || "💸"}</span>
            <div className="row-meta">
              <div className="row-t">{t.description || t.category}</div>
              <div className="row-s">{t.category} · {friendlyDate(t.date)}</div>
            </div>
            <div className={"row-amt " + (t.type === "income" ? "pos" : "neg")}>
              {t.type === "income" ? "+" : "−"}{formatMoney(t.amount, cur)}
            </div>
          </button>
        ))}
        {recent.length > 0 && <p className="sec-sub">Tap an entry to edit or delete it.</p>}
      </section>

      {editTx && (
        <div className="sheet-backdrop" onClick={() => setEditTx(null)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-head">
              <h3>Edit entry</h3>
              <button className="btn-icon" onClick={() => setEditTx(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <p className="sec-sub" style={{ marginTop: 0 }}>{editTx.category} · {friendlyDate(editTx.date)} · {editTx.type}</p>
            <label className="field"><span>Amount</span>
              <input type="number" inputMode="decimal" value={amt} onChange={(e) => setAmt(e.target.value)} autoFocus />
            </label>
            <label className="field"><span>Description</span>
              <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder={editTx.category} />
            </label>
            <button className="btn full" onClick={saveEdit} disabled={!(parseFloat(amt) > 0)}>Save changes</button>
            <button className="btn-ghost danger full" style={{ width: "100%", marginTop: 10 }}
              onClick={() => { deleteTransaction(editTx.id); setEditTx(null); }}>
              <Trash2 size={15} /> Delete this entry
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
