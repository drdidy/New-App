"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import gsap from "gsap";
import {
  ArrowRight,
  BarChart3,

  Pencil,
  Plus,
  ReceiptText,
  Trash2,
  TrendingDown,
  TrendingUp,
  Wallet,
  X,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  budgetStatus,
  cashOnHand,
  categoryBreakdown,
  monthOverMonth,
  monthlyTotals,
  netWorth,
} from "@/lib/insights";
import { formatMoney } from "@/lib/format";
import type { AccountType } from "@/lib/types";
import AnimatedNumber from "@/components/AnimatedNumber";
import Donut from "@/components/Donut";
import Sparkline from "@/components/Sparkline";

// ONYX categorical palette — validated (lightness band, chroma, CVD, contrast).
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
      gsap.from(".lx-reveal", { y: 20, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;

  const cur = data.currency;
  const summary = summarize(data);
  const cats = categoryBreakdown(data);
  const budgets = budgetStatus(data);
  const mom = monthOverMonth(data);
  const trend = monthlyTotals(data, 7);
  const nw = netWorth(data);
  const cash = cashOnHand(data);
  const accounts = data.accounts || [];
  const nwHist = data.netWorthHistory || [];
  const lastMonthNw = nwHist.length >= 2 ? nwHist[nwHist.length - 2].value : null;
  const nwDelta = lastMonthNw != null ? nw - lastMonthNw : null;

  // Pass every category to the donut so the arcs are proportional to the true
  // total; the legend below still lists the top few. Center total = sum of the
  // slices shown, so the ring and the number always agree.
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
    <main className="lx" ref={root}>
      <header className="lx-top lx-reveal">
        <div>
          <p className="lx-eyebrow"><BarChart3 size={13} /> Money overview</p>
          <h1 className="lx-h1">Spending</h1>
        </div>
        <button className="lx-addbtn" onClick={() => setDraft({ name: "", type: "checking", balance: "" })} aria-label="Add account">
          <Plus size={20} />
        </button>
      </header>

      {/* HERO — lead with what you have; frame net worth as a journey, not a verdict */}
      <div className="lx-hero lx-reveal">
        <div className="lx-hero-inner">
          <div className="lx-hero-label">Money to your name</div>
          <div className="lx-hero-num pos"><AnimatedNumber value={cash} currency={cur} /></div>
          <div className="lx-hero-sub">Across {accounts.length} account{accounts.length === 1 ? "" : "s"} — what you actually have right now.</div>
          <Link href="/debt" className="lx-nw">
            <span className="lx-nw-lbl">Net worth</span>
            <span className={"lx-nw-val " + (nw >= 0 ? "pos" : "")}>{formatMoney(nw, cur)}</span>
            {nwDelta != null && nwDelta !== 0 && (
              <span className={"lx-nw-delta " + (nwDelta > 0 ? "up" : "down")}>
                {nwDelta > 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
                {formatMoney(Math.abs(nwDelta), cur)} this month
              </span>
            )}
            <ArrowRight size={14} className="lx-nw-go" />
          </Link>
          {nw < 0 && (
            <p className="lx-nw-note">
              Most people building wealth start below zero — what matters is the direction, not today’s number. Every debt payment moves this up. 📈
            </p>
          )}
        </div>
      </div>

      {/* ACCOUNTS */}
      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Accounts</h2><span className="lx-group-total">{formatMoney(cash, cur)}</span></div>
        {accounts.length ? (
          <div className="lx-list">
            {accounts.map((a) => (
              <div className="lx-li" key={a.id}>
                <span className="ic" style={{ background: "rgba(15,118,110,0.08)" }}>{a.emoji || ACCT[a.type].emoji}</span>
                <div className="meta"><div className="t">{a.name}</div><div className="s">{ACCT[a.type].label}</div></div>
                <div className="amt" style={{ color: a.balance < 0 ? "var(--au-neg)" : "var(--au-ink)" }}>{formatMoney(a.balance, cur)}</div>
                <button className="lx-icon-btn" onClick={() => setDraft({ id: a.id, name: a.name, type: a.type, balance: String(a.balance) })} aria-label="Edit"><Pencil size={14} /></button>
                <button className="lx-icon-btn danger" onClick={() => { if (confirm(`Delete "${a.name}"?`)) deleteAccount(a.id); }} aria-label="Delete"><Trash2 size={14} /></button>
              </div>
            ))}
          </div>
        ) : (
          <div className="lx-blank">
            <div className="ic"><Wallet size={22} /></div>
            <h4>Add your balances</h4>
            <p>Your real cash on hand powers a true “safe to spend”. Add checking, savings, or cash.</p>
            <button className="lx-primary" onClick={() => setDraft({ name: "", type: "checking", balance: "" })}><Plus size={16} /> Add an account</button>
          </div>
        )}
      </section>

      {/* SPENDING TOTAL + TREND */}
      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Spent this month</h2>
          {mom.changePct != null && (
            <span className={"lx-delta " + (mom.changePct > 0 ? "up" : "down")}>
              {mom.changePct > 0 ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
              {Math.abs(Math.round(mom.changePct))}%
            </span>
          )}
        </div>
        <div className="lx-hero-num neg" style={{ fontSize: 34 }}>{formatMoney(summary.expenses, cur)}</div>
        <Sparkline values={hasExpenses ? trendVals : [0, 0, 0, 0, 0, 0, 0]} labels={trend.map((m) => m.label)} color="#ff7864" height={130} />
      </section>

      {/* CATEGORY DONUT */}
      {cats.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>By category</h2></div>
          <div className="lx-donutwrap">
            <Donut slices={slices} centerTop={formatMoney(catTotal, cur)} centerSub="total" size={168} stroke={24} />
            <div className="lx-legend">
              {cats.slice(0, 6).map((c, i) => (
                <div className="lx-legend-row" key={c.category}>
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
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Budgets</h2><Link href="/settings">Edit</Link></div>
          <div className="lx-barlist">
            {budgets.slice(0, 6).map((b) => (
              <div className="lx-barrow" key={b.category}>
                <div className="top"><span className="nm">{b.category}</span><span className="vals">{formatMoney(b.spent, cur)} / {formatMoney(b.limit, cur)}</span></div>
                <div className="track"><span className={b.over ? "over" : ""} style={{ width: `${Math.min(100, b.pct)}%` }} /></div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* MERCHANTS */}
      {merchants.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Top merchants</h2></div>
          <div className="lx-list">
            {merchants.map((m) => (
              <div className="lx-li" key={m.name}>
                <span className="ic">{m.name.slice(0, 1).toUpperCase()}</span>
                <div className="meta"><div className="t">{m.name}</div><div className="s">{m.category}</div></div>
                <div className="amt neg">{formatMoney(m.amount, cur)}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {!hasExpenses && accounts.length === 0 && (
        <Link href="/" className="lx-card lx-cta lx-reveal">
          <div className="lx-cta-ic"><ReceiptText size={22} /></div>
          <div className="lx-cta-meta"><div className="lx-cta-t">Log your first expense</div><div className="lx-cta-s">Say “spent 12 on coffee” on Today.</div></div>
          <ArrowRight size={18} className="lx-cta-arrow" />
        </Link>
      )}

      {/* ACCOUNT SHEET */}
      {draft && (
        <div className="lx-sheet-backdrop" onClick={() => setDraft(null)}>
          <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="lx-sheet-head">
              <h3>{draft.id ? "Edit account" : "Add account"}</h3>
              <button className="lx-sheet-x" onClick={() => setDraft(null)} aria-label="Close"><X size={18} /></button>
            </div>
            <div className="lx-chips" style={{ marginBottom: 14 }}>
              {(Object.keys(ACCT) as AccountType[]).map((t) => (
                <button key={t} className={"lx-chip" + (draft.type === t ? " on" : "")} onClick={() => setDraft({ ...draft, type: t })}>
                  {ACCT[t].emoji} {ACCT[t].label}
                </button>
              ))}
            </div>
            <label className="lx-field"><span>Name</span>
              <input value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })} placeholder={`${ACCT[draft.type].label} account`} autoFocus />
            </label>
            <label className="lx-field"><span>Current balance</span>
              <input type="number" inputMode="decimal" value={draft.balance} onChange={(e) => setDraft({ ...draft, balance: e.target.value })} placeholder="0" />
            </label>
            <button className="lx-primary full" onClick={saveAcct} disabled={!draft.name.trim() || !Number.isFinite(parseFloat(draft.balance))}>
              {draft.id ? "Save" : "Add account"}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
