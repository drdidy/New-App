"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  CalendarClock,
  CheckCircle2,
  ChevronDown,
  CreditCard,
  HandCoins,
  Landmark,
  Mountain,
  Pencil,
  Plus,
  Snowflake,
  Sparkles,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useStore } from "@/lib/store";
import {
  DEBT_KIND_IS_ORG,
  inferDebtKind,
  payoffPlan,
  payoffProjection,
  simulatePayoff,
} from "@/lib/insights";
import { clampPct, formatMoney, friendlyDate } from "@/lib/format";
import type { Debt, DebtDirection, DebtKind } from "@/lib/types";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";

const KIND_META: Record<DebtKind, { label: string; icon: typeof CreditCard }> = {
  person: { label: "Person", icon: Users },
  card: { label: "Credit card", icon: CreditCard },
  loan: { label: "Loan", icon: Landmark },
  bnpl: { label: "Buy now, pay later", icon: HandCoins },
  other: { label: "Other", icon: CreditCard },
};

interface DraftDebt {
  id?: string;
  direction: DebtDirection;
  kind: DebtKind;
  party: string;
  balance: string;
  apr: string;
  minPayment: string;
  dueDate: string;
  autoPay: boolean;
  note: string;
}

function emptyDraft(direction: DebtDirection = "i_owe", kind: DebtKind = "card"): DraftDebt {
  return { direction, kind, party: "", balance: "", apr: "", minPayment: "", dueDate: "", autoPay: false, note: "" };
}

export default function DebtsPage() {
  const { data, ready, addDebt, updateDebt, payDebt, deleteDebt } = useStore();
  const [extra, setExtra] = useState(75);
  const [method, setMethod] = useState<"snowball" | "avalanche">("snowball");
  const [draft, setDraft] = useState<DraftDebt | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [payingId, setPayingId] = useState<string | null>(null);
  const [payAmt, setPayAmt] = useState("");

  const cur = data?.currency || "USD";

  const all = useMemo(() => (data?.debts || []).filter((d) => d.balance > 0), [data]);
  const iOwe = all.filter((d) => d.direction === "i_owe");
  const orgs = iOwe.filter((d) => DEBT_KIND_IS_ORG[d.kind ?? inferDebtKind(d)]);
  const peopleIOwe = iOwe.filter((d) => !DEBT_KIND_IS_ORG[d.kind ?? inferDebtKind(d)]);
  const owedToMe = all.filter((d) => d.direction === "owed_to_me");

  const planTargets = orgs.concat(peopleIOwe);
  const total = planTargets.reduce((s, d) => s + d.balance, 0);
  const original = planTargets.reduce((s, d) => s + (d.original || d.balance), 0);
  const paidPct = original ? clampPct(((original - total) / original) * 100) : 0;
  const monthlyMin = planTargets.reduce((s, d) => s + (d.minPayment || 0), 0);

  // Real what-if math — interest-accruing simulation, not a guessed curve.
  const sim = simulatePayoff(data!, method, extra);
  const baseline = simulatePayoff(data!, method, 0);
  const interestSaved = Math.max(0, baseline.totalInterest - sim.totalInterest);
  const projection = payoffProjection(data!, method, extra);
  const plan = payoffPlan(data!, method, extra);
  const targetDate = sim.months
    ? new Date(new Date().getFullYear(), new Date().getMonth() + sim.months, 1)
    : null;

  if (!ready) return null;
  const hasDebt = iOwe.length > 0;

  function startEdit(d: Debt) {
    setDraft({
      id: d.id,
      direction: d.direction,
      kind: d.kind ?? inferDebtKind(d),
      party: d.party,
      balance: String(d.balance),
      apr: d.apr != null ? String(d.apr) : "",
      minPayment: d.minPayment != null ? String(d.minPayment) : "",
      dueDate: d.dueDate || "",
      autoPay: Boolean(d.autoPay),
      note: d.note || "",
    });
  }

  function saveDraft() {
    if (!draft) return;
    const balance = Math.max(0, parseFloat(draft.balance) || 0);
    if (!draft.party.trim() || balance <= 0) return;
    const patch = {
      direction: draft.direction,
      kind: draft.kind,
      party: draft.party.trim(),
      balance,
      apr: draft.apr ? Math.max(0, parseFloat(draft.apr)) : undefined,
      minPayment: draft.minPayment ? Math.max(0, parseFloat(draft.minPayment)) : undefined,
      dueDate: draft.dueDate || undefined,
      paymentDay: draft.dueDate ? parseInt(draft.dueDate.slice(8, 10), 10) || undefined : undefined,
      autoPay: draft.autoPay,
      note: draft.note.trim() || undefined,
    };
    if (draft.id) updateDebt(draft.id, patch);
    else addDebt(patch);
    setDraft(null);
  }

  function submitPayment(id: string) {
    const amt = Math.max(0, parseFloat(payAmt) || 0);
    if (amt <= 0) return;
    payDebt(id, amt);
    setPayAmt("");
    setPayingId(null);
  }

  return (
    <main className="lx lx-debt">
      <header className="lx-top">
        <div>
          <p className="lx-eyebrow">Owe to people & organizations</p>
          <h1 className="lx-h1">Debt</h1>
        </div>
        <button className="lx-addbtn" onClick={() => setDraft(emptyDraft())} aria-label="Add a debt">
          <Plus size={20} />
        </button>
      </header>

      {/* SUMMARY HERO */}
      <div className="lx-hero">
        <div className="lx-hero-inner lx-debt-hero">
          <div>
            <div className="lx-hero-label">You owe in total</div>
            <div className="lx-hero-num neg">{formatMoney(total, cur)}</div>
            <div className="lx-hero-sub">
              {hasDebt
                ? `Across ${iOwe.length} ${iOwe.length === 1 ? "debt" : "debts"}${owedToMe.length ? ` · ${formatMoney(owedToMe.reduce((s, d) => s + d.balance, 0), cur)} owed to you` : ""}`
                : "Nothing owed — you're debt-free. 🎉"}
            </div>
          </div>
          {hasDebt && (
            <Ring pct={paidPct} size={92} stroke={9} color="#14b8a6" track="rgba(15,30,45,0.08)">
              <strong>{Math.round(paidPct)}%</strong>
              <span>paid</span>
            </Ring>
          )}
        </div>
      </div>

      {/* WHAT-IF PLANNER */}
      {hasDebt && (
        <section className="lx-card lx-plan">
          <div className="lx-card-head">
            <h2>Payoff planner</h2>
            <span className="lx-plan-free">
              {targetDate ? `Debt-free ${targetDate.toLocaleDateString(undefined, { month: "short", year: "numeric" })}` : "Add a payment"}
            </span>
          </div>

          <div className="lx-method">
            <button
              className={"lx-method-opt" + (method === "snowball" ? " on" : "")}
              onClick={() => setMethod("snowball")}
            >
              <Snowflake size={16} /> Snowball
              <small>Smallest first</small>
            </button>
            <button
              className={"lx-method-opt" + (method === "avalanche" ? " on" : "")}
              onClick={() => setMethod("avalanche")}
            >
              <Mountain size={16} /> Avalanche
              <small>Highest APR first</small>
            </button>
          </div>

          <div className="lx-slider-row">
            <span>Extra per month</span>
            <b>{formatMoney(extra, cur)}</b>
          </div>
          <input
            className="lx-slider"
            type="range"
            min={0}
            max={1000}
            step={25}
            value={extra}
            onChange={(e) => setExtra(Number(e.target.value))}
            aria-label="Extra payment per month"
          />

          <div className="lx-plan-stats">
            <div>
              <span>Payoff time</span>
              <b>{sim.months != null ? `${sim.months} mo` : "—"}</b>
            </div>
            <div>
              <span>Interest saved</span>
              <b className="pos">{formatMoney(interestSaved, cur)}</b>
            </div>
            <div>
              <span>Monthly total</span>
              <b>{formatMoney(monthlyMin + extra, cur)}</b>
            </div>
          </div>

          {projection.length > 1 && (
            <div className="lx-proj">
              <Sparkline values={projection} color="#14b8a6" height={120} />
              <p className="lx-proj-note">
                <Sparkles size={13} /> Projected balance with {formatMoney(extra, cur)}/mo extra, interest included.
              </p>
            </div>
          )}

          {plan.order.length > 1 && (
            <div className="lx-order">
              <span className="lx-order-label">Order to attack</span>
              {plan.order.map((d, i) => (
                <span key={d.id} className="lx-order-chip">
                  {i + 1}. {d.party}
                </span>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ORGANIZATIONS */}
      {orgs.length > 0 && (
        <DebtGroup
          title="Cards & loans"
          subtitle="Organizations — interest, minimums, due dates"
          debts={orgs}
          {...{ cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }}
        />
      )}

      {/* PEOPLE YOU OWE */}
      {peopleIOwe.length > 0 && (
        <DebtGroup
          title="People you owe"
          subtitle="Informal IOUs to friends & family"
          debts={peopleIOwe}
          {...{ cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }}
        />
      )}

      {/* OWED TO YOU */}
      {owedToMe.length > 0 && (
        <DebtGroup
          title="Owed to you"
          subtitle="Money people owe you"
          debts={owedToMe}
          incoming
          {...{ cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }}
        />
      )}

      {!hasDebt && owedToMe.length === 0 && (
        <section className="lx-card">
          <div className="lx-debt-empty">
            <div className="lx-debt-empty-ic"><CheckCircle2 size={26} /></div>
            <h3>No debts tracked</h3>
            <p>Add a credit card, a loan, or money you owe a friend — then plan the payoff.</p>
            <button className="lx-primary" onClick={() => setDraft(emptyDraft())}>
              <Plus size={16} /> Add a debt
            </button>
          </div>
        </section>
      )}

      {/* ADD / EDIT SHEET */}
      {draft && (
        <DebtSheet
          draft={draft}
          setDraft={setDraft}
          onSave={saveDraft}
          onClose={() => setDraft(null)}
        />
      )}
    </main>
  );
}

/* ---------------------------------------------------------------- */

function DebtGroup(props: {
  title: string;
  subtitle: string;
  debts: Debt[];
  incoming?: boolean;
  cur: string;
  expanded: string | null;
  setExpanded: (id: string | null) => void;
  payingId: string | null;
  setPayingId: (id: string | null) => void;
  payAmt: string;
  setPayAmt: (v: string) => void;
  submitPayment: (id: string) => void;
  startEdit: (d: Debt) => void;
  deleteDebt: (id: string) => void;
}) {
  const { title, subtitle, debts, incoming, cur } = props;
  return (
    <section className="lx-card lx-group">
      <div className="lx-card-head">
        <h2>{title}</h2>
        <span className="lx-group-total">{formatMoney(debts.reduce((s, d) => s + d.balance, 0), cur)}</span>
      </div>
      <p className="lx-group-sub">{subtitle}</p>
      {debts.map((d) => (
        <DebtCard key={d.id} debt={d} incoming={incoming} {...props} />
      ))}
    </section>
  );
}

function DebtCard(props: {
  debt: Debt;
  incoming?: boolean;
  cur: string;
  expanded: string | null;
  setExpanded: (id: string | null) => void;
  payingId: string | null;
  setPayingId: (id: string | null) => void;
  payAmt: string;
  setPayAmt: (v: string) => void;
  submitPayment: (id: string) => void;
  startEdit: (d: Debt) => void;
  deleteDebt: (id: string) => void;
}) {
  const { debt: d, incoming, cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt } = props;
  const kind = d.kind ?? inferDebtKind(d);
  const Meta = KIND_META[kind];
  const pct = d.original ? clampPct(((d.original - d.balance) / d.original) * 100) : 0;
  const open = expanded === d.id;
  const paying = payingId === d.id;
  const dueSoon = d.dueDate
    ? Math.ceil((new Date(d.dueDate + "T00:00:00").getTime() - Date.now()) / 86400000)
    : null;

  return (
    <div className={"lx-debt-card" + (open ? " open" : "")}>
      <button className="lx-debt-main" onClick={() => setExpanded(open ? null : d.id)}>
        <span className="lx-debt-ic"><Meta.icon size={18} /></span>
        <div className="lx-debt-meta">
          <div className="lx-debt-name">{d.party}</div>
          <div className="lx-debt-tags">
            {d.apr ? <span>{d.apr}% APR</span> : null}
            {d.minPayment ? <span>{formatMoney(d.minPayment, cur)}/mo min</span> : null}
            {dueSoon != null ? (
              <span className={dueSoon <= 5 ? "warn" : ""}>
                {dueSoon < 0 ? "overdue" : dueSoon === 0 ? "due today" : `due in ${dueSoon}d`}
              </span>
            ) : null}
          </div>
        </div>
        <div className="lx-debt-right">
          <div className={"lx-debt-bal " + (incoming ? "pos" : "neg")}>{formatMoney(d.balance, cur)}</div>
          <ChevronDown size={16} className="lx-debt-chev" />
        </div>
      </button>

      {d.original && d.original > d.balance ? (
        <div className="lx-debt-bar"><span style={{ width: `${pct}%` }} /></div>
      ) : null}

      {open && (
        <div className="lx-debt-detail">
          <div className="lx-debt-progress">
            <span>{formatMoney((d.original || d.balance) - d.balance, cur)} {incoming ? "received" : "paid"}</span>
            <span>{Math.round(pct)}% of {formatMoney(d.original || d.balance, cur)}</span>
          </div>

          {paying ? (
            <div className="lx-pay-row">
              <input
                type="number"
                inputMode="decimal"
                placeholder="Amount"
                value={payAmt}
                onChange={(e) => setPayAmt(e.target.value)}
                autoFocus
              />
              <button className="lx-primary sm" onClick={() => submitPayment(d.id)}>
                {incoming ? "Log received" : "Log payment"}
              </button>
              <button className="lx-ghost sm" onClick={() => setPayingId(null)}>Cancel</button>
            </div>
          ) : (
            <div className="lx-debt-actions">
              <button className="lx-primary sm" onClick={() => { setPayingId(d.id); setPayAmt(""); }}>
                <HandCoins size={14} /> {incoming ? "Received" : "Pay"}
              </button>
              <button className="lx-ghost sm" onClick={() => startEdit(d)}>
                <Pencil size={14} /> Edit
              </button>
              <button className="lx-ghost sm danger" onClick={() => { if (confirm(`Delete "${d.party}"?`)) deleteDebt(d.id); }}>
                <Trash2 size={14} /> Delete
              </button>
            </div>
          )}

          {(d.payments?.length ?? 0) > 0 && (
            <div className="lx-history">
              <span className="lx-history-label"><CalendarClock size={13} /> Payment history</span>
              {d.payments!.slice(0, 6).map((p) => (
                <div className="lx-history-row" key={p.id}>
                  <span>{friendlyDate(p.date)}</span>
                  <b className={incoming ? "pos" : "neg"}>{incoming ? "+" : "−"}{formatMoney(p.amount, cur)}</b>
                </div>
              ))}
            </div>
          )}
          {d.note ? <p className="lx-debt-note">{d.note}</p> : null}
        </div>
      )}
    </div>
  );
}

/* ---------------------------------------------------------------- */

function DebtSheet(props: {
  draft: DraftDebt;
  setDraft: (d: DraftDebt) => void;
  onSave: () => void;
  onClose: () => void;
}) {
  const { draft, setDraft, onSave, onClose } = props;
  const isPerson = draft.kind === "person";
  const set = (patch: Partial<DraftDebt>) => setDraft({ ...draft, ...patch });

  return (
    <div className="lx-sheet-backdrop" onClick={onClose}>
      <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="lx-sheet-head">
          <h3>{draft.id ? "Edit debt" : "Add a debt"}</h3>
          <button className="lx-sheet-x" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="lx-seg">
          <button className={draft.direction === "i_owe" ? "on" : ""} onClick={() => set({ direction: "i_owe" })}>I owe</button>
          <button className={draft.direction === "owed_to_me" ? "on" : ""} onClick={() => set({ direction: "owed_to_me", kind: "person" })}>Owed to me</button>
        </div>

        {draft.direction === "i_owe" && (
          <div className="lx-kinds">
            {(Object.keys(KIND_META) as DebtKind[]).map((k) => {
              const M = KIND_META[k];
              return (
                <button key={k} className={"lx-kind" + (draft.kind === k ? " on" : "")} onClick={() => set({ kind: k })}>
                  <M.icon size={15} /> {M.label}
                </button>
              );
            })}
          </div>
        )}

        <label className="lx-field">
          <span>{draft.direction === "i_owe" ? "Who do you owe?" : "Who owes you?"}</span>
          <input value={draft.party} onChange={(e) => set({ party: e.target.value })} placeholder={isPerson ? "e.g. James" : "e.g. Visa card"} autoFocus />
        </label>

        <label className="lx-field">
          <span>Balance</span>
          <input type="number" inputMode="decimal" value={draft.balance} onChange={(e) => set({ balance: e.target.value })} placeholder="0" />
        </label>

        {!isPerson && (
          <div className="lx-field-row">
            <label className="lx-field">
              <span>APR %</span>
              <input type="number" inputMode="decimal" value={draft.apr} onChange={(e) => set({ apr: e.target.value })} placeholder="0" />
            </label>
            <label className="lx-field">
              <span>Min / month</span>
              <input type="number" inputMode="decimal" value={draft.minPayment} onChange={(e) => set({ minPayment: e.target.value })} placeholder="0" />
            </label>
          </div>
        )}

        <label className="lx-field">
          <span>Next due {isPerson ? "(optional)" : ""}</span>
          <input type="date" value={draft.dueDate} onChange={(e) => set({ dueDate: e.target.value })} />
        </label>

        {!isPerson && draft.dueDate && parseFloat(draft.minPayment) > 0 && (
          <label className="lx-toggle">
            <input type="checkbox" checked={draft.autoPay} onChange={(e) => set({ autoPay: e.target.checked })} />
            <span>Auto-pay the minimum each month on the {ordinal(parseInt(draft.dueDate.slice(8, 10), 10) || 1)}</span>
          </label>
        )}

        <label className="lx-field">
          <span>Note (optional)</span>
          <input value={draft.note} onChange={(e) => set({ note: e.target.value })} placeholder="Anything to remember" />
        </label>

        <button className="lx-primary full" onClick={onSave} disabled={!draft.party.trim() || !(parseFloat(draft.balance) > 0)}>
          {draft.id ? "Save changes" : "Add debt"}
        </button>
      </div>
    </div>
  );
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
