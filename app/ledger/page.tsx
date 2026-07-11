"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { BookOpen, Search, Trash2, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, friendlyDate, monthLabel } from "@/lib/format";
import type { Transaction } from "@/lib/types";

const CAT_ICON: Record<string, string> = {
  Groceries: "🛒", Transport: "⛽", Dining: "🍔", Rent: "🏠", Utilities: "💡",
  Salary: "💰", Income: "💰", Shopping: "🛍️", Savings: "🐷", "Debt payment": "🤝",
};

type Filter = "all" | "expense" | "income";

export default function LedgerPage() {
  const { data, ready, updateTransaction, deleteTransaction, member } = useStore();
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [editTx, setEditTx] = useState<Transaction | null>(null);
  const [amt, setAmt] = useState("");
  const [desc, setDesc] = useState("");
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  // Hooks must run unconditionally; the data they read is stable while !ready.
  const months = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const list = data.transactions
      .filter((t) => (filter === "all" ? true : t.type === filter))
      .filter((t) =>
        !needle ||
        (t.description || "").toLowerCase().includes(needle) ||
        t.category.toLowerCase().includes(needle)
      )
      .slice()
      .sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : b.createdAt - a.createdAt));
    const by = new Map<string, { txs: Transaction[]; net: number }>();
    for (const t of list) {
      const key = t.date.slice(0, 7);
      const g = by.get(key) || { txs: [], net: 0 };
      g.txs.push(t);
      g.net += t.type === "income" ? t.amount : -t.amount;
      by.set(key, g);
    }
    return [...by.entries()];
  }, [data.transactions, q, filter]);

  if (!ready) return null;

  const cur = data.currency;
  const multi = data.members.length > 1;
  const total = data.transactions.length;

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

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">Every entry, kept</p>
      </div>
      <h1 className="pg-title rise">Ledger</h1>
      <div className="pg-rule rise" />

      <div className="rise" style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
        <div style={{ position: "relative", flex: 1 }}>
          <Search size={15} style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", color: "var(--mut)" }} />
          <input
            className="input"
            style={{ paddingLeft: 38 }}
            placeholder="Search entries…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
      </div>
      <div className="chips rise" style={{ marginBottom: 4 }}>
        {([["all", "Everything"], ["expense", "Spending"], ["income", "Income"]] as [Filter, string][]).map(([f, label]) => (
          <button key={f} className={"chip" + (filter === f ? " on" : "")} onClick={() => setFilter(f)}>{label}</button>
        ))}
      </div>

      {total === 0 ? (
        <div className="blank rise">
          <div className="ic"><BookOpen size={22} /></div>
          <h4>The ledger is empty</h4>
          <p>Every expense, paycheck, and payment you log lands here — say <b>“spent 12 on coffee”</b> on Today to start it.</p>
        </div>
      ) : months.length === 0 ? (
        <p className="sec-sub rise" style={{ marginTop: 18 }}>Nothing matches “{q}”. Try a category, like <b>Groceries</b>.</p>
      ) : months.map(([month, g]) => (
        <section className="sec rise" key={month}>
          <div className="sec-head">
            <h2>{monthLabel(month)}</h2>
            <span className="sec-aux">
              <span className={"sec-total " + (g.net >= 0 ? "pos" : "")}>{g.net >= 0 ? "+" : "−"}{formatMoney(Math.abs(g.net), cur)}</span>
            </span>
          </div>
          {g.txs.map((t) => {
            const m = multi ? member(t.memberId) : null;
            return (
              <button className="row" key={t.id} onClick={() => openEdit(t)}>
                <span className="row-ic">{CAT_ICON[t.category] || (t.type === "income" ? "💰" : "💸")}</span>
                <div className="row-meta">
                  <div className="row-t">{t.description || t.category}</div>
                  <div className="row-s">{[t.category, friendlyDate(t.date), m?.emoji].filter(Boolean).join(" · ")}</div>
                </div>
                <div className={"row-amt " + (t.type === "income" ? "pos" : "neg")}>
                  {t.type === "income" ? "+" : "−"}{formatMoney(t.amount, cur)}
                </div>
              </button>
            );
          })}
        </section>
      ))}

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
            <button className="btn full" onClick={saveEdit} disabled={!(parseFloat(amt) > 0)}>Save</button>
            <button className="btn-ghost danger" style={{ width: "100%", marginTop: 10 }}
              onClick={() => { deleteTransaction(editTx.id); setEditTx(null); }}>
              <Trash2 size={15} /> Delete entry
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
