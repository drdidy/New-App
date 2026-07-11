"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Calendar, Check, CreditCard, Landmark, Pencil, Plus, Trash2, X, Zap } from "lucide-react";
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
    const fields = { name: name.trim(), amount: amt, category, dayOfMonth: d, autoLog, memberId: who ?? data.members[0]?.id };
    if (editId) updateBill(editId, fields);
    else addBill(fields);
    setName(""); setAmount(""); setDay("1"); setAutoLog(false); setEditId(null); setOpen(false);
  }

  return (
    <main className="pg">
      <div className="pg-head">
        <p className="pg-date">Committed each month</p>
        <button className="btn-text" onClick={openAdd}>+ Add bill</button>
      </div>
      <h1 className="pg-title">Recurring</h1>
      <div className="pg-rule" />

      {/* STATEMENT */}
      <div className="st">
        <div className="st-label">Recurring this month <span className="tag">{monthLabel(monthKey())}</span></div>
        <div className="st-num neg"><AnimatedNumber value={committedTotal} currency={cur} /></div>
        <div className="meter"><span style={{ width: `${paidPct}%` }} /></div>
        <div className="st-links">
          <span>{formatMoney(monthlyTotal, cur)} bills</span>
          {loanTotal > 0 && <span>+ {formatMoney(loanTotal, cur)} loans & cards</span>}
          {committedTotal > 0 && <span className="gold" style={{ borderBottomColor: "rgba(226,179,102,0.4)" }}>≈ {formatMoney(committedTotal * 12, cur)} a year</span>}
        </div>
      </div>

      {/* BILLS */}
      <section className="sec">
        <div className="sec-head"><h2>Bills</h2><span className="sec-aux"><span className="sec-total">{formatMoney(monthlyTotal, cur)}</span></span></div>
        {bills.length === 0 ? (
          <div className="blank">
            <div className="ic"><Calendar size={22} /></div>
            <h4>No bills yet</h4>
            <p>Add rent and regular bills so your “safe to spend” knows what’s already committed.</p>
            <button className="btn" onClick={openAdd}><Plus size={16} /> Add a bill</button>
          </div>
        ) : bills.map((b) => {
          const m = member(b.bill.memberId);
          const soon = !b.paid && b.daysAway >= 0 && b.daysAway <= 6;
          const sub = [
            `Due day ${b.dueDay}`,
            b.bill.autoLog ? "auto" : null,
            multi && m ? m.emoji : null,
            b.bill.category === "Subscription" ? `${formatMoney(b.bill.amount * 12, cur)}/yr` : null,
            b.paid ? "✓ paid" : soon ? `in ${b.daysAway}d` : null,
          ].filter(Boolean).join(" · ");
          return (
            <div className="row" key={b.bill.id}>
              <span className="row-ic">{ICON[b.bill.category] || "🧾"}</span>
              <div className="row-meta">
                <div className="row-t">{b.bill.name}</div>
                <div className="row-s">{sub}</div>
              </div>
              <div className="row-amt neg" style={{ opacity: b.paid ? 0.5 : 1 }}>{formatMoney(b.bill.amount, cur)}</div>
              {b.paid ? (
                <span className="check"><Check size={15} /></span>
              ) : (
                <button className="btn-ghost sm" onClick={() => { markBillPaid(b.bill.id); success(); }}>Pay</button>
              )}
              <div className="row-acts">
                <button className="btn-icon" onClick={() => openEdit(b.bill)} aria-label="Edit"><Pencil size={14} /></button>
                <button className="btn-icon danger" onClick={() => { if (confirm(`Delete "${b.bill.name}"?`)) deleteBill(b.bill.id); }} aria-label="Delete"><Trash2 size={14} /></button>
              </div>
            </div>
          );
        })}
      </section>

      {/* LOANS & CARDS */}
      <section className="sec">
        <div className="sec-head"><h2>Loan & card payments</h2><span className="sec-aux"><Link href="/debt">Manage</Link></span></div>
        {loans.length === 0 ? (
          <div className="blank">
            <div className="ic"><Landmark size={22} /></div>
            <h4>No loan payments</h4>
            <p>Car payments, student loans, and card minimums live in Debt. Add one with a minimum + due date and it shows here.</p>
            <Link href="/debt" className="btn"><Plus size={16} /> Add a loan or card</Link>
          </div>
        ) : loans.map(({ debt: d, amount: amt, day: dd, paidThisMonth }) => (
          <div className="row" key={d.id}>
            <span className="row-ic">{(d.kind ?? "loan") === "card" ? <CreditCard /> : <Landmark />}</span>
            <div className="row-meta">
              <div className="row-t">{d.party}</div>
              <div className="row-s">{dd ? `Due the ${dd}` : "Monthly"}{d.autoPay ? " · auto-pay ⚡" : ""}{paidThisMonth ? " · ✓ paid" : ""}</div>
            </div>
            <div className="row-amt neg" style={{ opacity: paidThisMonth ? 0.5 : 1 }}>{formatMoney(amt, cur)}</div>
            {paidThisMonth
              ? <span className="check"><Check size={15} /></span>
              : <button className="btn-ghost sm" onClick={() => { payDebt(d.id, amt); success(); }}>Pay</button>}
            <Link href="/debt" className="btn-icon" aria-label="Manage debt"><ArrowRight size={14} /></Link>
          </div>
        ))}
        {loans.some((l) => !l.debt.autoPay) && (
          <p className="sec-sub">
            <Zap size={12} style={{ display: "inline", verticalAlign: "-2px" }} /> Tip: open a loan in Debt and turn on <b>auto-pay</b> so its minimum logs itself each month.
          </p>
        )}
      </section>

      {open && (
        <div className="sheet-backdrop" onClick={() => setOpen(false)}>
          <div className="sheet" onClick={(e) => e.stopPropagation()}>
            <div className="sheet-head">
              <h3>{editId ? "Edit bill" : "Add a recurring bill"}</h3>
              <button className="btn-icon" onClick={() => setOpen(false)} aria-label="Close"><X size={18} /></button>
            </div>
            <label className="field"><span>Name</span>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Rent, Netflix, Electric…" autoFocus />
            </label>
            <div className="fieldrow">
              <label className="field"><span>Amount</span>
                <input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" placeholder="1100" />
              </label>
              <label className="field"><span>Due day</span>
                <input value={day} onChange={(e) => setDay(e.target.value)} inputMode="numeric" placeholder="1" />
              </label>
            </div>
            <label className="field"><span>Category</span>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => <option key={c} value={c}>{ICON[c]} {c}</option>)}
              </select>
            </label>
            {multi && (
              <label className="field"><span>Whose bill?</span>
                <MemberPicker members={data.members} value={who ?? data.members[0]?.id} onChange={setWho} size="sm" />
              </label>
            )}
            <label className="toggle">
              <input type="checkbox" checked={autoLog} onChange={(e) => setAutoLog(e.target.checked)} />
              <span>Log it automatically on the due day</span>
            </label>
            <button className="btn full" onClick={save} disabled={!draftValid} style={{ marginTop: 8 }}>{editId ? "Save changes" : "Save bill"}</button>
          </div>
        </div>
      )}
    </main>
  );
}
