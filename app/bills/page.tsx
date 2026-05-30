"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { billsThisMonth } from "@/lib/insights";
import { formatMoney, monthLabel, monthKey } from "@/lib/format";
import MemberPicker from "@/components/MemberPicker";

const CATEGORIES = [
  "Rent",
  "Utilities",
  "Subscription",
  "Insurance",
  "Phone",
  "Internet",
  "Loan",
  "Childcare",
  "Other",
];

const ICON: Record<string, string> = {
  Rent: "🏠",
  Utilities: "💡",
  Subscription: "📺",
  Insurance: "🛡️",
  Phone: "📱",
  Internet: "🌐",
  Loan: "🏦",
  Childcare: "🧸",
  Other: "🧾",
};

export default function BillsPage() {
  const { data, ready, addBill, deleteBill, markBillPaid, member } = useStore();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [category, setCategory] = useState("Rent");
  const [day, setDay] = useState("1");
  const [who, setWho] = useState<string | undefined>(undefined);
  const [autoLog, setAutoLog] = useState(false);

  if (!ready) return null;

  const multi = data.members.length > 1;
  const bills = billsThisMonth(data);
  const monthlyTotal = bills.reduce((s, b) => s + b.bill.amount, 0);
  const paidTotal = bills.filter((b) => b.paid).reduce((s, b) => s + b.bill.amount, 0);
  const remaining = monthlyTotal - paidTotal;

  function save() {
    const amt = parseFloat(amount);
    const d = parseInt(day, 10);
    if (!name.trim() || !amt || amt <= 0 || !d || d < 1 || d > 31) return;
    addBill({
      name: name.trim(),
      amount: amt,
      category,
      dayOfMonth: d,
      memberId: who ?? data.members[0]?.id,
      autoLog,
    });
    setName("");
    setAmount("");
    setDay("1");
    setAutoLog(false);
    setOpen(false);
  }

  return (
    <main>
      <h1 className="h-title">Recurring bills</h1>
      <p className="h-sub">
        Your constant monthly costs — rent, utilities, subscriptions. Unpaid ones
        are held back from your &quot;safe to spend&quot;.
      </p>

      {bills.length > 0 && (
        <div className="card hero reveal" style={{ marginBottom: 16 }}>
          <div className="label">Fixed costs for {monthLabel(monthKey())}</div>
          <div className="big" style={{ fontSize: 38 }}>
            {formatMoney(monthlyTotal, data.currency)}
          </div>
          <div className="bills-progress">
            <div className="bar-track" style={{ marginTop: 8 }}>
              <div
                className="bar-fill"
                style={{
                  width: `${monthlyTotal ? (paidTotal / monthlyTotal) * 100 : 0}%`,
                }}
              />
            </div>
            <div className="bills-progress-row">
              <span className="pos">{formatMoney(paidTotal, data.currency)} paid</span>
              <span className="muted">{formatMoney(remaining, data.currency)} left</span>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        {bills.length === 0 ? (
          <div className="empty">
            No bills yet. Add your rent and regular bills so your budget knows
            what&apos;s already committed.
          </div>
        ) : (
          bills.map((b) => {
            const m = member(b.bill.memberId);
            return (
              <div className="item" key={b.bill.id}>
                <div className="ic">{ICON[b.bill.category] || "🧾"}</div>
                <div className="meta">
                  <div className="t">{b.bill.name}</div>
                  <div className="s">
                    Due {ordinal(b.dueDay)}
                    {b.bill.autoLog ? " · auto" : ""}
                    {multi && m ? ` · ${m.emoji}` : ""}
                    {b.paid ? " · ✓ paid" : b.daysAway >= 0 && b.daysAway <= 6 ? ` · in ${b.daysAway}d` : ""}
                  </div>
                </div>
                <div className="amt out" style={{ opacity: b.paid ? 0.5 : 1 }}>
                  {formatMoney(b.bill.amount, data.currency)}
                </div>
                {b.paid ? (
                  <span className="bill-paid">✓</span>
                ) : (
                  <button
                    className="bill-pay"
                    onClick={() => markBillPaid(b.bill.id)}
                  >
                    Mark paid
                  </button>
                )}
                <button
                  className="x"
                  onClick={() => deleteBill(b.bill.id)}
                  aria-label="Delete bill"
                >
                  ×
                </button>
              </div>
            );
          })
        )}
      </div>

      {open ? (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="field">
            <label>Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Rent, Netflix, Electric…"
              autoFocus
            />
          </div>
          <div className="row">
            <div className="field">
              <label>Amount</label>
              <input
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                inputMode="decimal"
                placeholder="1100"
              />
            </div>
            <div className="field">
              <label>Due day</label>
              <input
                value={day}
                onChange={(e) => setDay(e.target.value)}
                inputMode="numeric"
                placeholder="1"
              />
            </div>
          </div>
          <div className="field">
            <label>Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {ICON[c]} {c}
                </option>
              ))}
            </select>
          </div>
          {multi && (
            <div className="field">
              <label>Whose bill?</label>
              <MemberPicker
                members={data.members}
                value={who ?? data.members[0]?.id}
                onChange={setWho}
                size="sm"
              />
            </div>
          )}
          <label className="toggle">
            <input
              type="checkbox"
              checked={autoLog}
              onChange={(e) => setAutoLog(e.target.checked)}
            />
            <span>Log it automatically on the due day</span>
          </label>
          <div className="capture-actions">
            <button className="btn btn-ghost" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={save}>
              Save bill
            </button>
          </div>
        </div>
      ) : (
        <button
          className="btn btn-primary btn-block"
          style={{ marginTop: 14 }}
          onClick={() => setOpen(true)}
        >
          + Add a recurring bill
        </button>
      )}
    </main>
  );
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
