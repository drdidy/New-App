"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { formatMoney } from "@/lib/format";
import type { DebtDirection } from "@/lib/types";

export default function DebtsPage() {
  const { data, ready, addDebt, payDebt, deleteDebt } = useStore();
  const [open, setOpen] = useState(false);
  const [direction, setDirection] = useState<DebtDirection>("i_owe");
  const [party, setParty] = useState("");
  const [balance, setBalance] = useState("");
  const [apr, setApr] = useState("");
  const [minPayment, setMinPayment] = useState("");
  const [dueDate, setDueDate] = useState("");

  if (!ready) return null;

  const iOwe = data.debts.filter((d) => d.direction === "i_owe");
  const owedToMe = data.debts.filter((d) => d.direction === "owed_to_me");

  function save() {
    const bal = parseFloat(balance);
    if (!party.trim() || !bal || bal <= 0) return;
    addDebt({
      direction,
      party: party.trim(),
      balance: bal,
      apr: apr ? parseFloat(apr) : undefined,
      minPayment: minPayment ? parseFloat(minPayment) : undefined,
      dueDate: dueDate || undefined,
    });
    setParty("");
    setBalance("");
    setApr("");
    setMinPayment("");
    setDueDate("");
    setOpen(false);
  }

  function quickPay(id: string) {
    const v = prompt("How much did you pay?");
    if (!v) return;
    const n = parseFloat(v);
    if (n > 0) payDebt(id, n);
  }

  return (
    <main>
      <h1 className="h-title">Debts &amp; IOUs</h1>
      <p className="h-sub">Everything you owe and everything owed to you.</p>

      <div className="section-h">
        <h2>You owe</h2>
        <span className="pill owe">
          {formatMoney(
            iOwe.reduce((s, d) => s + d.balance, 0),
            data.currency,
          )}
        </span>
      </div>
      <div className="card">
        {iOwe.length === 0 ? (
          <div className="empty">Nothing here. Nice.</div>
        ) : (
          iOwe.map((d) => (
            <div className="item" key={d.id}>
              <div className="ic">💳</div>
              <div className="meta">
                <div className="t">{d.party}</div>
                <div className="s">
                  {d.apr ? `${d.apr}% APR` : "No interest"}
                  {d.minPayment
                    ? ` · min ${formatMoney(d.minPayment, data.currency)}`
                    : ""}
                  {d.dueDate ? ` · due ${d.dueDate}` : ""}
                </div>
              </div>
              <div className="amt out">{formatMoney(d.balance, data.currency)}</div>
              <button className="x" onClick={() => quickPay(d.id)} aria-label="Pay">
                💵
              </button>
              <button className="x" onClick={() => deleteDebt(d.id)} aria-label="Delete">
                ×
              </button>
            </div>
          ))
        )}
      </div>

      <div className="section-h">
        <h2>Owed to you</h2>
        <span className="pill owed">
          {formatMoney(
            owedToMe.reduce((s, d) => s + d.balance, 0),
            data.currency,
          )}
        </span>
      </div>
      <div className="card">
        {owedToMe.length === 0 ? (
          <div className="empty">No one owes you right now.</div>
        ) : (
          owedToMe.map((d) => (
            <div className="item" key={d.id}>
              <div className="ic">🙋</div>
              <div className="meta">
                <div className="t">{d.party}</div>
                <div className="s">Owes you</div>
              </div>
              <div className="amt in">{formatMoney(d.balance, data.currency)}</div>
              <button className="x" onClick={() => quickPay(d.id)} aria-label="Mark repaid">
                💵
              </button>
              <button className="x" onClick={() => deleteDebt(d.id)} aria-label="Delete">
                ×
              </button>
            </div>
          ))
        )}
      </div>

      {open ? (
        <div className="card" style={{ marginTop: 14 }}>
          <div className="field">
            <label>Type</label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as DebtDirection)}
            >
              <option value="i_owe">I owe someone</option>
              <option value="owed_to_me">Someone owes me</option>
            </select>
          </div>
          <div className="field">
            <label>Who / what</label>
            <input
              value={party}
              onChange={(e) => setParty(e.target.value)}
              placeholder="James, Visa card, landlord…"
            />
          </div>
          <div className="field">
            <label>Amount</label>
            <input
              value={balance}
              onChange={(e) => setBalance(e.target.value)}
              inputMode="decimal"
              placeholder="200"
            />
          </div>
          {direction === "i_owe" && (
            <div className="row">
              <div className="field">
                <label>APR % (optional)</label>
                <input
                  value={apr}
                  onChange={(e) => setApr(e.target.value)}
                  inputMode="decimal"
                  placeholder="19.9"
                />
              </div>
              <div className="field">
                <label>Min payment (optional)</label>
                <input
                  value={minPayment}
                  onChange={(e) => setMinPayment(e.target.value)}
                  inputMode="decimal"
                  placeholder="35"
                />
              </div>
            </div>
          )}
          {direction === "i_owe" && (
            <div className="field">
              <label>Next due date (optional)</label>
              <input
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>
          )}
          <div className="capture-actions">
            <button className="btn btn-ghost" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={save}>
              Save
            </button>
          </div>
        </div>
      ) : (
        <button
          className="btn btn-primary btn-block"
          style={{ marginTop: 14 }}
          onClick={() => setOpen(true)}
        >
          + Add a debt or IOU
        </button>
      )}

      <p className="hint" style={{ marginTop: 12, textAlign: "center" }}>
        Tip: you can also just say{" "}
        <strong>&quot;I owe James 200&quot;</strong> on the Home screen.
      </p>
    </main>
  );
}
