"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Calendar, Check, CreditCard, Landmark, Pencil, Plus, Repeat, Trash2, X, Zap } from "lucide-react";
import { useStore } from "@/lib/store";
import { billsThisMonth } from "@/lib/insights";
import { formatMoney, monthLabel, monthKey } from "@/lib/format";
import { success } from "@/lib/haptics";
import AnimatedNumber from "@/components/AnimatedNumber";
import MemberPicker from "@/components/MemberPicker";

const CATEGORIES = ["Rent", "Utilities", "Subscription", "Insurance", "Phone", "Internet", "Loan", "Childcare", "Other"];
const ICON: Record<string, string> = {
  Rent: "🏠", Utilities: "💡", Subscription: "📺", Insurance: "🛡️", Phone: "📱",
  Internet: "🌐", Loan: "🏦", Childcare: "🧸", Other: "🧾",
};

export default function BillsPage() {
  const { data, ready, addBill, updateBill, deleteBill, markBillPaid, member, payDebt } = useStore();
  const [open, setOpen] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("Rent");
  const [day, setDay] = useState("1");
  const [who, setWho] = useState<string | undefined>(undefined);
  const [autoLog, setAutoLog] = useState(false);

  function openAdd() {
    setEditId(null); setName(""); setAmount(""); setCategory("Rent"); setDay("1"); setWho(undefined); setAutoLog(false);
    setOpen(true);
  }
  function openEdit(b: { id: string; name: string; amount: number; category: string; dayOfMonth: number; memberId?: string; autoLog?: boolean }) {
    setEditId(b.id); setName(b.name); setAmount(String(b.amount)); setCategory(b.category);
    setDay(String(b.dayOfMonth)); setWho(b.memberId); setAutoLog(Boolean(b.autoLog));
    setOpen(true);
  }

  if (!ready) return null;

  const cur = data.currency;
  const multi = data.members.length > 1;
  const bills = billsThisMonth(data);
  const monthlyTotal = bills.reduce((s, b) => s + b.bill.amount, 0);
  const paidTotal = bills.filter((b) => b.paid).reduce((s, b) => s + b.bill.amount, 0);

  // Recurring loan / card payments come from debts that carry a monthly minimum.
  const month = monthKey();
  const loans = data.debts
    .filter((d) => d.direction === "i_owe" && (d.minPayment || 0) > 0 && d.balance > 0)
    .map((d) => ({
      debt: d,
      amount: Math.min(d.minPayment || 0, d.balance),
      day: d.paymentDay || (d.dueDate ? parseInt(d.dueDate.slice(8, 10), 10) || undefined : undefined),
      paidThisMonth: d.lastPaidMonth === month,
    }))
    .sort((a, b) => (a.day || 99) - (b.day || 99));
  const loanTotal = loans.reduce((s, l) => s + l.amount, 0);
  const committedTotal = monthlyTotal + loanTotal;
  // The hero shows bills + loans, so its progress bar must count both too.
  const loanPaidTotal = loans.filter((l) => l.paidThisMonth).reduce((s, l) => s + l.amount, 0);
  const paidPct = committedTotal ? ((paidTotal + loanPaidTotal) / committedTotal) * 100 : 0;

  const draftValid =
    Boolean(name.trim()) &&
    Number.isFinite(parseFloat(amount)) && parseFloat(amount) > 0 &&
    parseInt(day, 10) >= 1 && parseInt(day, 10) <= 31;

  function save() {
    if (!draftValid) return;
    const amt = parseFloat(amount);
    const d = parseInt(day, 10);
    // memberId included on BOTH paths so editing "whose bill" actually sticks.
    const fields = { name: name.trim(), amount: amt, category, dayOfMonth: d, autoLog, memberId: who ?? data.members[0]?.id };
    if (editId) updateBill(editId, fields);
    else addBill(fields);
    setName(""); setAmount(""); setDay("1"); setAutoLog(false); setEditId(null); setOpen(false);
  }

  return (
    <main className="lx">
      <header className="lx-top">
        <div>
          <p className="lx-eyebrow"><Repeat size={13} /> Committed each month</p>
          <h1 className="lx-h1">Recurring</h1>
        </div>
        <button className="lx-addbtn" onClick={openAdd} aria-label="Add a bill"><Plus size={20} /></button>
      </header>

      <div className="lx-hero">
        <div className="lx-hero-inner">
          <div className="lx-hero-label">Recurring this month · {monthLabel(monthKey())}</div>
          <div className="lx-hero-num neg"><AnimatedNumber value={committedTotal} currency={cur} /></div>
          <div className="lx-bar"><span style={{ width: `${paidPct}%` }} /></div>
          <div className="lx-hero-math">
            <span>{formatMoney(monthlyTotal, cur)} bills</span>
            {loanTotal > 0 && <span>+ {formatMoney(loanTotal, cur)} loans & cards</span>}
          </div>
          {committedTotal > 0 && (
            <div className="lx-hero-hint" style={{ cursor: "default", borderBottom: "none" }}>
              ≈ {formatMoney(committedTotal * 12, cur)} a year committed
            </div>
          )}
        </div>
      </div>

      <section className="lx-card">
        {bills.length === 0 ? (
          <div className="lx-blank">
            <div className="ic"><Calendar size={22} /></div>
            <h4>No bills yet</h4>
            <p>Add rent and regular bills so your “safe to spend” knows what’s already committed.</p>
            <button className="lx-primary" onClick={openAdd}><Plus size={16} /> Add a bill</button>
          </div>
        ) : (
          <div className="lx-list">
            {bills.map((b) => {
              const m = member(b.bill.memberId);
              const soon = !b.paid && b.daysAway >= 0 && b.daysAway <= 6;
              return (
                <div className="lx-li" key={b.bill.id}>
                  <span className="ic">{ICON[b.bill.category] || "🧾"}</span>
                  <div className="meta">
                    <div className="t">{b.bill.name}</div>
                    <div className="s">
                      Due day {b.dueDay}{b.bill.autoLog ? " · auto" : ""}{multi && m ? ` · ${m.emoji}` : ""}
                      {b.bill.category === "Subscription" ? ` · ${formatMoney(b.bill.amount * 12, cur)}/yr` : ""}
                      {b.paid ? " · ✓ paid" : soon ? ` · in ${b.daysAway}d` : ""}
                    </div>
                  </div>
                  <div className="amt neg" style={{ opacity: b.paid ? 0.45 : 1 }}>{formatMoney(b.bill.amount, cur)}</div>
                  {b.paid ? (
                    <span className="lx-paid"><Check size={15} /></span>
                  ) : (
                    <button className="lx-ghost sm" onClick={() => { markBillPaid(b.bill.id); success(); }}>Pay</button>
                  )}
                  <button className="lx-icon-btn" onClick={() => openEdit(b.bill)} aria-label="Edit"><Pencil size={14} /></button>
                  <button className="lx-icon-btn danger" onClick={() => { if (confirm(`Delete "${b.bill.name}"?`)) deleteBill(b.bill.id); }} aria-label="Delete"><Trash2 size={14} /></button>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* LOAN & CARD PAYMENTS (from debts) */}
      <section className="lx-card">
        <div className="lx-card-head"><h2>Loan & card payments</h2><Link href="/debt">Manage</Link></div>
        {loans.length === 0 ? (
          <div className="lx-blank">
            <div className="ic"><Landmark size={22} /></div>
            <h4>No loan payments</h4>
            <p>Car payments, student loans, and card minimums live in Debt. Add one with a minimum + due date and it shows here.</p>
            <Link href="/debt" className="lx-primary"><Plus size={16} /> Add a loan or card</Link>
          </div>
        ) : (
          <div className="lx-list">
            {loans.map(({ debt: d, amount, day, paidThisMonth }) => (
              <div className="lx-li" key={d.id}>
                <span className="ic">{(d.kind ?? "loan") === "card" ? <CreditCard size={16} /> : <Landmark size={16} />}</span>
                <div className="meta">
                  <div className="t">{d.party}</div>
                  <div className="s">
                    {day ? `Due the ${day}` : "Monthly"}{d.autoPay ? " · auto-pay ⚡" : ""}{paidThisMonth ? " · ✓ paid" : ""}
                  </div>
                </div>
                <div className="amt neg" style={{ opacity: paidThisMonth ? 0.45 : 1 }}>{formatMoney(amount, cur)}</div>
                {paidThisMonth
                  ? <span className="lx-paid"><Check size={15} /></span>
                  : <button className="lx-ghost sm" onClick={() => { payDebt(d.id, amount); success(); }}>Pay</button>}
                <Link href="/debt" className="lx-icon-btn" aria-label="Manage debt"><ArrowRight size={14} /></Link>
              </div>
            ))}
          </div>
        )}
        {loans.some((l) => !l.debt.autoPay) && (
          <p className="lx-group-sub" style={{ marginTop: 10 }}>
            <Zap size={12} style={{ verticalAlign: "-2px" }} /> Tip: open a loan in Debt and turn on <b>auto-pay</b> so its minimum logs itself each month.
          </p>
        )}
      </section>

      {open && (
        <div className="lx-sheet-backdrop" onClick={() => setOpen(false)}>
          <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
            <div className="lx-sheet-head">
              <h3>{editId ? "Edit bill" : "Add a recurring bill"}</h3>
              <button className="lx-sheet-x" onClick={() => setOpen(false)} aria-label="Close"><X size={18} /></button>
            </div>
            <label className="lx-field"><span>Name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Rent, Netflix, Electric…" autoFocus />
            </label>
            <div className="lx-field-row">
              <label className="lx-field"><span>Amount</span>
                <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" placeholder="1100" />
              </label>
              <label className="lx-field"><span>Due day</span>
                <input value={day} onChange={(e) => setDay(e.target.value)} inputMode="numeric" placeholder="1" />
              </label>
            </div>
            <label className="lx-field"><span>Category</span>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{ICON[c]} {c}</option>)}
              </select>
            </label>
            {multi && (
              <label className="lx-field"><span>Whose bill?</span>
                <MemberPicker members={data.members} value={who ?? data.members[0]?.id} onChange={setWho} size="sm" />
              </label>
            )}
            <label className="lx-toggle">
              <input type="checkbox" checked={autoLog} onChange={(e) => setAutoLog(e.target.checked)} />
              <span>Log it automatically on the due day</span>
            </label>
            <button className="lx-primary full" onClick={save} disabled={!draftValid} style={{ marginTop: 8 }}>{editId ? "Save changes" : "Save bill"}</button>
          </div>
        </div>
      )}
    </main>
  );
}
