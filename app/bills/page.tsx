"use client";

import { useState } from "react";
import { Calendar, Check, Pencil, Plus, Trash2, X } from "lucide-react";
import { useStore } from "@/lib/store";
import { billsThisMonth } from "@/lib/insights";
import { formatMoney, monthLabel, monthKey } from "@/lib/format";
import MemberPicker from "@/components/MemberPicker";

const CATEGORIES = ["Rent", "Utilities", "Subscription", "Insurance", "Phone", "Internet", "Loan", "Childcare", "Other"];
const ICON: Record<string, string> = {
  Rent: "🏠", Utilities: "💡", Subscription: "📺", Insurance: "🛡️", Phone: "📱",
  Internet: "🌐", Loan: "🏦", Childcare: "🧸", Other: "🧾",
};

export default function BillsPage() {
  const { data, ready, addBill, updateBill, deleteBill, markBillPaid, member } = useStore();
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
  const remaining = monthlyTotal - paidTotal;
  const paidPct = monthlyTotal ? (paidTotal / monthlyTotal) * 100 : 0;

  function save() {
    const amt = parseFloat(amount);
    const d = parseInt(day, 10);
    if (!name.trim() || !Number.isFinite(amt) || amt <= 0 || !d || d < 1 || d > 31) return;
    const fields = { name: name.trim(), amount: amt, category, dayOfMonth: d, autoLog };
    if (editId) updateBill(editId, fields);
    else addBill({ ...fields, memberId: who ?? data.members[0]?.id });
    setName(""); setAmount(""); setDay("1"); setAutoLog(false); setEditId(null); setOpen(false);
  }

  return (
    <main className="lx">
      <header className="lx-top">
        <div>
          <p className="lx-eyebrow"><Calendar size={13} /> Committed each month</p>
          <h1 className="lx-h1">Bills</h1>
        </div>
        <button className="lx-addbtn" onClick={openAdd} aria-label="Add a bill"><Plus size={20} /></button>
      </header>

      <div className="lx-hero">
        <div className="lx-hero-inner">
          <div className="lx-hero-label">Fixed costs · {monthLabel(monthKey())}</div>
          <div className="lx-hero-num neg">{formatMoney(monthlyTotal, cur)}</div>
          <div className="lx-bar"><span style={{ width: `${paidPct}%` }} /></div>
          <div className="lx-hero-math">
            <span className="pos">{formatMoney(paidTotal, cur)} paid</span>
            <span>{formatMoney(remaining, cur)} left this month</span>
          </div>
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
                      {b.paid ? " · ✓ paid" : soon ? ` · in ${b.daysAway}d` : ""}
                    </div>
                  </div>
                  <div className="amt neg" style={{ opacity: b.paid ? 0.45 : 1 }}>{formatMoney(b.bill.amount, cur)}</div>
                  {b.paid ? (
                    <span className="lx-paid"><Check size={15} /></span>
                  ) : (
                    <button className="lx-ghost sm" onClick={() => markBillPaid(b.bill.id)}>Pay</button>
                  )}
                  <button className="lx-icon-btn" onClick={() => openEdit(b.bill)} aria-label="Edit"><Pencil size={14} /></button>
                  <button className="lx-icon-btn danger" onClick={() => { if (confirm(`Delete "${b.bill.name}"?`)) deleteBill(b.bill.id); }} aria-label="Delete"><Trash2 size={14} /></button>
                </div>
              );
            })}
          </div>
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
            <button className="lx-primary full" onClick={save} style={{ marginTop: 8 }}>{editId ? "Save changes" : "Save bill"}</button>
          </div>
        </div>
      )}
    </main>
  );
}
