"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ArrowRight, Pencil, Plus, ReceiptText, Trash2, TrendingDown, TrendingUp, Wallet, X } from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import { budgetStatus, cashOnHand, categoryBreakdown, monthOverMonth, monthPace, monthlyTotals, netWorth } from "@/lib/insights";
import { formatMoney } from "@/lib/format";
import type { AccountType } from "@/lib/types";
import AnimatedNumber from "@/components/AnimatedNumber";
import Donut from "@/components/Donut";
import Sparkline from "@/components/Sparkline";

// MONOGRAPH categorical palette — validated (lightness, chroma, CVD, contrast).
const CHART = ["#bd8826", "#5b8fd6", "#d76a94", "#a86bc9", "#1f9a90", "#d0704a", "#23906b"];

const ACCT: Record<AccountType, { emoji: string; label: string }> = {
  checking: { emoji: "🏦", label: "Checking" },
  savings: { emoji: "🐷", label: "Savings" },
  cash: { emoji: "💵", label: "Cash" },
  investment: { emoji: "📈", label: "Investment" },
  other: { emoji: "💼", label: "Other" },
};

interface AcctDraft { id?: string; name: string; type: AccountType; balance: string; }

export default function SpendingPage() {
  const { data, ready, addAccount, updateAccount, deleteAccount } = useStore();
  const [draft, setDraft] = useState<AcctDraft | null>(null);
  const root = useRef<HTMLElement>(null);

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
  const summary = summarize(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);
  const mom = monthOverMonth(data);
  const paceLine = monthPace(data);
  const trend = monthlyTotals(data, 7);
  const nw = netWorth(data);
  const cash = cashOnHand(data);
  const accounts = data.accounts || [];
  const nwHist = data.netWorthHistory || [];
  const lastMonthNw = nwHist.length >= 2 ? nwHist[nwHist.length - 2].value : null;
  const nwDelta = lastMonthNw != null ? nw - lastMonthNw : null;

  const slices = cats.map((c, i) => ({ label: c.category, value: c.amount, color: CHART[i % CHART.length] }));
  const catTotal = cats.reduce((s, c) => s + c.amount, 0);
  const trendVals = trend.map((m) => m.expense);
  const hasExpenses = data.transactions.some((t) => t.type === "expense");

  const merchantMap = new Map<string, { category: string; amount: number }>();
  for (const t of data.transactions.filter((t) => t.type === "expense")) {
    const key = t.description || t.category;
    const prev = merchantMap.get(key) || { category: t.category, amount: 0 };
    merchantMap.set(key, { category: prev.category, amount: prev.amount + t.amount });
  }
  const merchants = [...merchantMap.entries()].map(([name, v]) => ({ name, ...v })).sort((a, b) => b.amount - a.amount).slice(0, 5);

  function saveAcct() {
    if (!draft) return;
    const balance = parseFloat(draft.balance);
    if (!draft.name.trim() || !Number.isFinite(balance)) return;
    if (draft.id) {
      updateAccount(draft.id, { name: draft.name.trim(), type: draft.type, balance });
    } else {
      addAccount({
        name: draft.name.trim(),
        type: draft.type,
        balance,
        emoji: ACCT[draft.type].emoji,
        color: CHART[accounts.length % CHART.length],
      });
    }
    setDraft(null);
  }

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">Money overview</p>
        <button className="btn-text" onClick={() => setDraft({ name: "", type: "checking", balance: "" })}>+ Add account</button>
      </div>
      <h1 className="pg-title rise">Spending</h1>
      <div className="pg-rule rise" />

      {/* STATEMENT — lead with what you have */}
      <div className="st rise">
        <div className="st-label">Money to your name</div>
        <div className="st-num"><AnimatedNumber value={cash} currency={cur} /></div>
        <p className="st-meta">Across {accounts.length} account{accounts.length === 1 ? "" : "s"} — what you actually have right now.</p>
        <div className="st-links">
          <Link href="/debt">
            Net worth&nbsp;<b className={nw >= 0 ? "pos" : ""}>{formatMoney(nw, cur)}</b>
            {nwDelta != null && nwDelta !== 0 && (
              <>&nbsp;{nwDelta > 0 ? <TrendingUp size={12} style={{ display: "inline" }} /> : <TrendingDown size={12} style={{ display: "inline" }} />} {formatMoney(Math.abs(nwDelta), cur)} this month</>
            )}
          </Link>
        </div>
        {nw < 0 && (
          <p className="st-note">Most people building wealth start below zero — what matters is the direction, not today’s number. Every debt payment moves this up. 📈</p>
        )}
      </div>

      {/* ACCOUNTS */}
      <section className="sec rise">
        <div className="sec-head"><h2>Accounts</h2><span className="sec-aux"><span className="sec-total">{formatMoney(cash, cur)}</span></span></div>
        {accounts.length ? accounts.map((a) => (
          <div className="row" key={a.id}>
            <span className="row-ic">{a.emoji || ACCT[a.type].emoji}</span>
            <div className="row-meta"><div className="row-t">{a.name}</div><div className="row-s">{ACCT[a.type].label}</div></div>
            <div className={"row-amt" + (a.balance < 0 ? " neg" : "")}>{formatMoney(a.balance, cur)}</div>
            <div className="row-acts">
              <button className="btn-icon" onClick={() => setDraft({ id: a.id, name: a.name, type: a.type, balance: String(a.balance) })} aria-label="Edit"><Pencil size={14} /></button>
              <button className="btn-icon danger" onClick={() => { if (confirm(`Delete "${a.name}"?`)) deleteAccount(a.id); }} aria-label="Delete"><Trash2 size={14} /></button>
            </div>
          </div>
        )) : (
          <div className="blank">
            <div className="ic"><Wallet size={22} /></div>
            <h4>Add your balances</h4>
            <p>Your real cash on hand powers a true “safe to spend”. Add checking, savings, or cash.</p>
            <button className="btn" onClick={() => setDraft({ name: "", type: "checking", balance: "" })}><Plus size={16} /> Add an account</button>
          </div>
        )}
      </section>

      {/* SPENT THIS MONTH */}
      <section className="sec rise">
        <div className="sec-head">
          <h2>Spent this month</h2>
          {mom.changePct != null && (
            <span className="sec-aux"><span className={"tag " + (mom.changePct > 0 ? "neg" : "pos")}>
              {mom.changePct > 0 ? <TrendingUp size={11} /> : <TrendingDown size={11} />} {Math.abs(Math.round(mom.changePct))}% vs last month
            </span></span>
          )}
        </div>
        <div className="st-num neg" style={{ fontSize: "clamp(28px, 9vw, 38px)", margin: "12px 0 2px" }}>{formatMoney(summary.expenses, cur)}</div>
        {paceLine && (
          <p className="sec-sub" style={{ margin: "2px 0 10px" }}>
            {paceLine.actual <= paceLine.typical
              ? <>You&apos;re usually at <b style={{ color: "var(--ink)" }}>{formatMoney(paceLine.typical, cur)}</b> by day {paceLine.day} — running {formatMoney(paceLine.typical - paceLine.actual, cur)} under your usual pace. 🌿</>
              : <>You&apos;re usually at <b style={{ color: "var(--ink)" }}>{formatMoney(paceLine.typical, cur)}</b> by day {paceLine.day} — running {formatMoney(paceLine.actual - paceLine.typical, cur)} over your usual pace.</>}
          </p>
        )}
        <Sparkline values={hasExpenses ? trendVals : [0, 0, 0, 0, 0, 0, 0]} labels={trend.map((m) => m.label)} color="#ff7864" height={120} />
      </section>

      {/* BY CATEGORY */}
      {cats.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>By category</h2></div>
          <div className="donut-wrap">
            <Donut slices={slices} centerTop={formatMoney(catTotal, cur)} centerSub="total" size={158} stroke={22} />
            <div className="legend">
              {cats.slice(0, 6).map((c, i) => (
                <div className="legend-row" key={c.category}>
                  <span className="sw" style={{ background: CHART[i % CHART.length] }} />
                  <span className="nm">{c.category}</span>
                  <span className="am">{formatMoney(c.amount, cur)}</span>
                  <span className="pc">{Math.round(c.pct)}%</span>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

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

      {/* TOP MERCHANTS */}
      {merchants.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Top merchants</h2></div>
          {merchants.map((m) => (
            <div className="row" key={m.name}>
              <span className="row-ic" style={{ fontFamily: "var(--serif)" }}>{m.name.slice(0, 1).toUpperCase()}</span>
              <div className="row-meta"><div className="row-t">{m.name}</div><div className="row-s">{m.category}</div></div>
              <div className="row-amt neg">{formatMoney(m.amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {!hasExpenses && accounts.length === 0 && (
        <Link href="/" className="flag rise">
          <span className="flag-txt"><ReceiptText size={13} style={{ display: "inline", marginRight: 6 }} /><b>Log your first expense</b> — say “spent 12 on coffee” on Today. <ArrowRight size={12} style={{ display: "inline" }} /></span>
        </Link>
      )}

      {/* ACCOUNT SHEET */}
      {draft && (
        <div className="sheet-backdrop" onClick={() => setDraft(null)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-head">
              <h3>{draft.id ? "Edit account" : "Add account"}</h3>
              <button className="btn-icon" onClick={() => setDraft(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <div className="chips" style={{ marginBottom: 14 }}>
              {(Object.keys(ACCT) as AccountType[]).map((t) => (
                <button key={t} className={"chip" + (draft.type === t ? " on" : "")} onClick={() => setDraft({ ...draft, type: t })}>
                  {ACCT[t].emoji} {ACCT[t].label}
                </button>
              ))}
            </div>
            <label className="field"><span>Name</span>
              <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} placeholder={`${ACCT[draft.type].label} account`} autoFocus />
            </label>
            <label className="field"><span>Current balance</span>
              <input type="number" inputMode="decimal" value={draft.balance} onChange={(e) => setDraft({ ...draft, balance: e.target.value })} placeholder="0" />
            </label>
            <button className="btn full" onClick={saveAcct} disabled={!draft.name.trim() || !Number.isFinite(parseFloat(draft.balance))}>
              {draft.id ? "Save" : "Add account"}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
