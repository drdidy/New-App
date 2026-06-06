"use client";

import { useState } from "react";
import { useStore } from "@/lib/store";
import { payoffPlan, simulatePayoff } from "@/lib/insights";
import { formatMoney, clampPct } from "@/lib/format";
import type { DebtDirection } from "@/lib/types";
import Ring from "@/components/Ring";
import Avatar from "@/components/Avatar";
import MemberPicker from "@/components/MemberPicker";

const STRATEGIES = [
  { title: "Snowball", body: "Pay the smallest balance first for fast wins and motivation." },
  { title: "Avalanche", body: "Pay the highest APR first to reduce interest cost." },
  { title: "Hybrid", body: "Clear one small debt, then switch extra money to the highest APR." },
  { title: "Minimum shield", body: "Automate minimums first so fees and credit damage do not pile on." },
  { title: "Negotiate", body: "Ask lenders for hardship plans, APR reductions, or payment dates that match payday." },
];

const CURB_IDEAS = [
  "Freeze new borrowing while the payoff plan is active.",
  "Move one flexible category down by 10% and send the difference to debt.",
  "Use receipts to spot grocery subcategories that are quietly inflating.",
  "Route windfalls and refunds to the current target debt before spending them.",
  "Keep a small emergency buffer so surprise costs do not become new debt.",
];

export default function DebtsPage() {
  const { data, ready, addDebt, payDebt, deleteDebt, member } = useStore();
  const [open, setOpen] = useState(false);
  const [method, setMethod] = useState<"snowball" | "avalanche">("snowball");
  const [direction, setDirection] = useState<DebtDirection>("i_owe");
  const [party, setParty] = useState("");
  const [balance, setBalance] = useState("");
  const [apr, setApr] = useState("");
  const [minPayment, setMinPayment] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [who, setWho] = useState<string | undefined>(undefined);
  const [extra, setExtra] = useState(0);

  if (!ready) return null;

  const multi = data.members.length > 1;
  const iOwe = data.debts.filter((d) => d.direction === "i_owe");
  const owedToMe = data.debts.filter((d) => d.direction === "owed_to_me");
  const plan = payoffPlan(data, method);
  const totalOwe = iOwe.reduce((s, d) => s + d.balance, 0);

  const base = simulatePayoff(data, method, 0);
  const sim = simulatePayoff(data, method, extra);
  const monthsSaved =
    base.months != null && sim.months != null ? base.months - sim.months : null;
  const interestSaved = base.totalInterest - sim.totalInterest;
  const freeDate =
    sim.months != null
      ? new Date(new Date().getFullYear(), new Date().getMonth() + sim.months, 1)
      : null;

  function save() {
    const bal = parseFloat(balance);
    if (!party.trim() || !bal || bal <= 0) return;
    addDebt({
      direction,
      party: party.trim(),
      balance: bal,
      original: bal,
      apr: apr ? parseFloat(apr) : undefined,
      minPayment: minPayment ? parseFloat(minPayment) : undefined,
      dueDate: dueDate || undefined,
      memberId: who ?? data.members[0]?.id,
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

      {/* Payoff plan */}
      {iOwe.length > 0 && (
        <div className="card hero reveal" style={{ marginBottom: 16 }}>
          <div className="plan-head">
            <div>
              <div className="label">Total you owe</div>
              <div className="big neg" style={{ fontSize: 36 }}>
                {formatMoney(totalOwe, data.currency)}
              </div>
            </div>
          </div>
          <div className="seg" style={{ marginTop: 6 }}>
            <button
              className={"seg-btn" + (method === "snowball" ? " on" : "")}
              onClick={() => setMethod("snowball")}
            >
              ❄️ Snowball
            </button>
            <button
              className={"seg-btn" + (method === "avalanche" ? " on" : "")}
              onClick={() => setMethod("avalanche")}
            >
              🏔️ Avalanche
            </button>
          </div>
          <p className="plan-note">
            {method === "snowball"
              ? "Pay the smallest balance first — quick wins keep you motivated."
              : "Pay the highest interest first — saves you the most money overall."}
            {plan.months
              ? ` At your current minimums, you'd be debt-free in about ${plan.months} month${plan.months === 1 ? "" : "s"}.`
              : ""}
          </p>
          <div className="plan-order">
            {plan.order.map((d, i) => (
              <div className="plan-step" key={d.id}>
                <span className="plan-num">{i + 1}</span>
                <span className="plan-party">{d.party}</span>
                <span className="plan-amt">{formatMoney(d.balance, data.currency)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* What-if simulator */}
      {iOwe.length > 0 && (
        <div className="card reveal" style={{ marginBottom: 16 }}>
          <div className="card-h">What if you paid extra?</div>
          <div className="whatif-val">
            <span className="h-sub" style={{ margin: 0 }}>Extra per month</span>
            <span className="whatif-amount">{formatMoney(extra, data.currency)}</span>
          </div>
          <input
            type="range"
            className="slider"
            min={0}
            max={2000}
            step={25}
            value={extra}
            onChange={(e) => setExtra(parseInt(e.target.value, 10))}
          />
          <div className="whatif-result">
            <div className="whatif-stat">
              <div className="v">
                {freeDate
                  ? freeDate.toLocaleDateString(undefined, { month: "short", year: "numeric" })
                  : "—"}
              </div>
              <div className="l">Debt-free</div>
            </div>
            <div className="whatif-stat">
              <div className="v pos">
                {monthsSaved && monthsSaved > 0 ? `${monthsSaved} mo` : "—"}
              </div>
              <div className="l">Sooner</div>
            </div>
            <div className="whatif-stat">
              <div className="v pos">
                {interestSaved > 1 ? formatMoney(interestSaved, data.currency) : "—"}
              </div>
              <div className="l">Interest saved</div>
            </div>
          </div>
          {extra > 0 && monthsSaved != null && monthsSaved > 0 && (
            <p className="plan-note" style={{ marginBottom: 0 }}>
              Putting an extra {formatMoney(extra, data.currency)}/mo toward your debts
              clears them <strong>{monthsSaved} month{monthsSaved === 1 ? "" : "s"} sooner</strong>
              {interestSaved > 1 ? ` and saves about ${formatMoney(interestSaved, data.currency)} in interest.` : "."}
            </p>
          )}
        </div>
      )}

      {iOwe.length > 0 && (
        <div className="card reveal" style={{ marginBottom: 16 }}>
          <div className="card-h">Ways to attack the debt</div>
          <div className="strategy-grid">
            {STRATEGIES.map((s) => (
              <div className="strategy" key={s.title}>
                <div className="strategy-title">{s.title}</div>
                <div className="strategy-body">{s.body}</div>
              </div>
            ))}
          </div>
          <div className="card-h" style={{ marginTop: 14 }}>Curb new debt</div>
          <ul className="advice-list">
            {CURB_IDEAS.map((idea) => (
              <li key={idea}>{idea}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="section-h">
        <h2>You owe</h2>
        <span className="pill owe">{formatMoney(totalOwe, data.currency)}</span>
      </div>
      <div className="card">
        {iOwe.length === 0 ? (
          <div className="empty">Nothing here. Nice. 🎉</div>
        ) : (
          iOwe.map((d) => {
            const original = d.original || d.balance;
            const paidPct = clampPct(((original - d.balance) / original) * 100);
            const m = member(d.memberId);
            return (
              <div className="item" key={d.id}>
                <Ring pct={paidPct} size={46} stroke={5} color="#bc5446">
                  <span className="ring-pct">{Math.round(paidPct)}%</span>
                </Ring>
                <div className="meta">
                  <div className="t">{d.party}</div>
                  <div className="s">
                    {d.apr ? `${d.apr}% APR` : "No interest"}
                    {d.minPayment
                      ? ` · min ${formatMoney(d.minPayment, data.currency)}`
                      : ""}
                    {d.dueDate ? ` · due ${d.dueDate}` : ""}
                    {multi && m ? ` · ${m.emoji}` : ""}
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
            );
          })
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
          owedToMe.map((d) => {
            const m = member(d.memberId);
            return (
              <div className="item" key={d.id}>
                <div className="ic">🙋</div>
                <div className="meta">
                  <div className="t">{d.party}</div>
                  <div className="s">Owes {multi && m ? m.name.split(" ")[0] : "you"}</div>
                </div>
                <div className="amt in">{formatMoney(d.balance, data.currency)}</div>
                <button className="x" onClick={() => quickPay(d.id)} aria-label="Mark repaid">
                  💵
                </button>
                <button className="x" onClick={() => deleteDebt(d.id)} aria-label="Delete">
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
            <label>Type</label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value as DebtDirection)}
            >
              <option value="i_owe">I owe someone</option>
              <option value="owed_to_me">Someone owes me</option>
            </select>
          </div>
          {multi && (
            <div className="field">
              <label>Whose is it?</label>
              <MemberPicker members={data.members} value={who ?? data.members[0]?.id} onChange={setWho} size="sm" />
            </div>
          )}
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
