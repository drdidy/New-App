"use client";

import gsap from "gsap";
import { useMemo, useState, useEffect, useRef } from "react";
import {
  CalendarClock, CheckCircle2, ChevronDown, CreditCard, HandCoins, Landmark,
  Mountain, Pencil, Plus, Snowflake, Sparkles, Trash2, Users, X,
} from "lucide-react";
import { useStore } from "@/lib/store";
import {
  DEBT_KIND_IS_ORG, inferDebtKind, payoffPlan, payoffProjection,
  simulatePayoff, suggestPersonPayment,
} from "@/lib/insights";
import { clampPct, formatMoney, friendlyDate, monthKey } from "@/lib/format";
import { success } from "@/lib/haptics";
import type { AppData, Debt, DebtDirection, DebtKind } from "@/lib/types";
import AnimatedNumber from "@/components/AnimatedNumber";
import Ring from "@/components/Ring";
import Sparkline from "@/components/Sparkline";
import Burst from "@/components/Burst";

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
  const [burstKey, setBurstKey] = useState(0);

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
    // Milestone confetti only for money you OWE, capped at the debt's balance.
    const target = data.debts.find((x) => x.id === id);
    const counted = target?.direction === "i_owe" ? Math.min(amt, target.balance) : 0;
    const beforePct = original ? ((original - total) / original) * 100 : 0;
    const afterPct = original ? ((original - total + counted) / original) * 100 : 0;
    const crossed = counted > 0 && [25, 50, 75, 100].some((t) => beforePct < t && afterPct >= t);
    payDebt(id, amt);
    success();
    if (crossed) { setBurstKey((k) => k + 1); if (navigator.vibrate) navigator.vibrate([18, 50, 24, 50, 30]); }
    setPayAmt("");
    setPayingId(null);
  }

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">Owe to people & organizations</p>
        <button className="btn-text" onClick={() => setDraft(emptyDraft())}>+ Add debt</button>
      </div>
      <h1 className="pg-title">Debt</h1>
      <div className="pg-rule" />

      {burstKey > 0 && <div style={{ display: "grid", placeItems: "center", height: 0 }}><Burst key={burstKey} /></div>}

      {/* STATEMENT */}
      <div className="st rise">
        <div className="st-row">
          <div>
            <div className="st-label">You owe in total</div>
            <div className="st-num neg"><AnimatedNumber value={total} currency={cur} /></div>
            <p className="st-meta">
              {hasDebt
                ? `Across ${iOwe.length} ${iOwe.length === 1 ? "debt" : "debts"}${owedToMe.length ? ` · ${formatMoney(owedToMe.reduce((s, d) => s + d.balance, 0), cur)} owed to you` : ""}`
                : "Nothing owed — you're debt-free. 🎉"}
            </p>
          </div>
          {hasDebt && (
            <Ring pct={paidPct} size={92} stroke={8} color="#e2b366" track="rgba(241,233,216,0.1)">
              <strong>{Math.round(paidPct)}%</strong>
              <span>paid</span>
            </Ring>
          )}
        </div>
        {hasDebt && (
          <>
            <div className="meter"><span style={{ width: `${paidPct}%` }} /></div>
            <div className="st-links">
              <span>{formatMoney(original - total, cur)} of {formatMoney(original, cur)} paid off</span>
              {targetDate && (sim.months ?? 0) > 0 && <span className="gold" style={{ borderBottomColor: "rgba(226,179,102,0.4)" }}>debt-free {targetDate.toLocaleDateString(undefined, { month: "short", year: "numeric" })} · {sim.months} mo</span>}
            </div>
          </>
        )}
      </div>

      {/* PAYOFF PLANNER — a tool, so it lives on a plate */}
      {hasDebt && (
        <section className="plate rise">
          <div className="plate-title"><Sparkles /> Payoff planner</div>
          <div className="seg" style={{ marginBottom: 14 }}>
            <button className={method === "snowball" ? "on" : ""} onClick={() => setMethod("snowball")}>
              <Snowflake size={13} style={{ display: "inline", marginRight: 5, verticalAlign: "-2px" }} />Snowball · smallest first
            </button>
            <button className={method === "avalanche" ? "on" : ""} onClick={() => setMethod("avalanche")}>
              <Mountain size={13} style={{ display: "inline", marginRight: 5, verticalAlign: "-2px" }} />Avalanche · highest APR
            </button>
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "var(--ink-2)", marginBottom: 6 }}>
            <span>Extra per month</span>
            <b style={{ fontFamily: "var(--serif)", color: "var(--gold)" }}>{formatMoney(extra, cur)}</b>
          </div>
          <input type="range" min={0} max={1000} step={25} value={extra}
            onChange={(e) => setExtra(Number(e.target.value))} aria-label="Extra payment per month" />
          <div className="ticker" style={{ margin: "14px 0 4px" }}>
            <div><span className="tk-l">Payoff time</span><span className="tk-v">{sim.months != null ? `${sim.months} mo` : "—"}</span></div>
            <div><span className="tk-l">Interest saved</span><span className="tk-v pos">{formatMoney(interestSaved, cur)}</span></div>
            <div><span className="tk-l">Monthly total</span><span className="tk-v">{formatMoney(monthlyMin + extra, cur)}</span></div>
          </div>
          {projection.length > 1 && (
            <>
              <Sparkline values={projection} color="#e2b366" height={110} />
              <p className="hint"><Sparkles size={12} style={{ display: "inline", verticalAlign: "-2px" }} /> Projected balance with {formatMoney(extra, cur)}/mo extra, interest included.</p>
            </>
          )}
          {plan.order.length > 1 && (
            <div className="chips" style={{ marginTop: 12 }}>
              {plan.order.map((d, i) => (
                <span key={d.id} className="chip on">{i + 1}. {d.party}</span>
              ))}
            </div>
          )}
        </section>
      )}

      {orgs.length > 0 && (
        <DebtGroup title="Cards & loans" subtitle="Organizations — interest, minimums, due dates" debts={orgs}
          {...{ data, cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }} />
      )}
      {peopleIOwe.length > 0 && (
        <DebtGroup title="People you owe" subtitle="Informal IOUs to friends & family" debts={peopleIOwe}
          {...{ data, cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }} />
      )}
      {owedToMe.length > 0 && (
        <DebtGroup title="Owed to you" subtitle="Money people owe you" debts={owedToMe} incoming
          {...{ data, cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt }} />
      )}

      {!hasDebt && owedToMe.length === 0 && (
        <div className="blank">
          <div className="ic"><CheckCircle2 size={26} /></div>
          <h4>No debts tracked</h4>
          <p>Add a credit card, a loan, or money you owe a friend — then plan the payoff.</p>
          <button className="btn" onClick={() => setDraft(emptyDraft())}><Plus size={16} /> Add a debt</button>
        </div>
      )}

      {draft && <DebtSheet draft={draft} setDraft={setDraft} onSave={saveDraft} onClose={() => setDraft(null)} />}
    </main>
  );
}

/* ---------------------------------------------------------------- */

interface GroupProps {
  title: string;
  subtitle: string;
  debts: Debt[];
  incoming?: boolean;
  data: AppData;
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
}

function DebtGroup(props: GroupProps) {
  const { title, subtitle, debts, incoming, cur } = props;
  return (
    <section className="sec rise">
      <div className="sec-head">
        <h2>{title}</h2>
        <span className="sec-aux"><span className="sec-total">{formatMoney(debts.reduce((s, d) => s + d.balance, 0), cur)}</span></span>
      </div>
      <p className="sec-sub">{subtitle}</p>
      {debts.map((d) => (
        <DebtRow key={d.id} debt={d} incoming={incoming} {...props} />
      ))}
    </section>
  );
}

function DebtRow(props: GroupProps & { debt: Debt }) {
  const { debt: d, incoming, data, cur, expanded, setExpanded, payingId, setPayingId, payAmt, setPayAmt, submitPayment, startEdit, deleteDebt } = props;
  const [copied, setCopied] = useState(false);
  const [showScript, setShowScript] = useState(false);
  const kind = d.kind ?? inferDebtKind(d);
  const Meta = KIND_META[kind];
  const money = (n: number) => formatMoney(n, cur);
  const advice = !incoming && kind === "person" ? suggestPersonPayment(data, d) : null;
  const script = !advice
    ? ""
    : advice.mode === "full"
      ? `Hey — I can settle the ${money(d.balance)} I owe you. Sending it over now. 🙏`
      : advice.mode === "partial"
        ? `Hey — I know I owe you ${money(d.balance)}. I can't do it all at once, but can I send ${money(advice.amount)} now and keep chipping away until it's cleared?`
        : `Hey — I haven't forgotten the ${money(d.balance)} I owe you. This month is tight, but I'll send what I can as soon as I'm able. Thanks for being patient. 🙏`;
  const pct = d.original ? clampPct(((d.original - d.balance) / d.original) * 100) : 0;
  const open = expanded === d.id;
  const paying = payingId === d.id;
  const monthNow = monthKey();
  const paidThisMonth = d.lastPaidMonth === monthNow || (d.payments || []).some((p) => p.date.startsWith(monthNow));
  const dueSoon = d.dueDate
    ? Math.ceil((new Date(d.dueDate + "T00:00:00").getTime() - Date.now()) / 86400000)
    : null;

  const sub = [
    d.apr ? `${d.apr}% APR` : null,
    d.minPayment ? `${money(d.minPayment)}/mo min` : null,
    paidThisMonth ? "paid this month ✓" : dueSoon != null ? (dueSoon < 0 ? "overdue" : dueSoon === 0 ? "due today" : `due in ${dueSoon}d`) : null,
  ].filter(Boolean).join(" · ");

  return (
    <>
      <button className="row" onClick={() => setExpanded(open ? null : d.id)} aria-expanded={open}>
        <span className="row-ic"><Meta.icon /></span>
        <div className="row-meta">
          <div className="row-t">{d.party}</div>
          {sub && <div className={"row-s" + (paidThisMonth ? " pos" : dueSoon != null && dueSoon <= 5 && !paidThisMonth ? " neg" : "")}>{sub}</div>}
        </div>
        <div className={"row-amt " + (incoming ? "pos" : "neg")}>{money(d.balance)}</div>
        <ChevronDown size={15} style={{ flex: "none", color: "var(--mut)", transform: open ? "rotate(180deg)" : "none", transition: "transform .2s" }} />
      </button>

      {open && (
        <div className="row-detail">
          {d.original && d.original > d.balance ? (
            <>
              <div className="meter" style={{ margin: "2px 0 8px" }}><span style={{ width: `${pct}%` }} /></div>
              <p className="sec-sub" style={{ margin: "0 0 10px" }}>
                {money((d.original || d.balance) - d.balance)} {incoming ? "received" : "paid"} · {Math.round(pct)}% of {money(d.original || d.balance)}
              </p>
            </>
          ) : null}

          {advice && !paying && (
            <div className={"verdict " + (advice.mode === "full" ? "yes" : advice.mode === "partial" ? "caution" : "wait")} style={{ marginTop: 0, marginBottom: 12 }}>
              {advice.mode === "full" ? (
                <span>You can clear this in full and still keep <b className="gold">{money(advice.spare - d.balance)}</b> safe to spend.</span>
              ) : advice.mode === "partial" ? (
                <span>Suggested: send <b className="gold">{money(advice.amount)}</b> now — affordable from your {money(advice.spare)} safe to spend, and it clears in about {advice.months} month{advice.months === 1 ? "" : "s"}.</span>
              ) : (
                <span>Too tight to send anything safely this month — a short, honest note keeps trust intact.</span>
              )}
              <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
                {advice.mode !== "tight" && (
                  <button className="btn sm" onClick={() => { setPayingId(d.id); setPayAmt(String(advice.amount)); }}>
                    <HandCoins size={14} /> Pay {money(advice.amount)}
                  </button>
                )}
                <button className="btn-ghost sm" onClick={() => { setShowScript(true); setCopied(true); setTimeout(() => setCopied(false), 2500); navigator.clipboard?.writeText(script).catch(() => {}); }}>
                  {copied ? "Copied ✓" : "What to say"}
                </button>
              </div>
              {showScript && <p style={{ margin: "10px 0 0", fontStyle: "italic", color: "var(--ink-2)", fontSize: 13, lineHeight: 1.55 }}>“{script}”</p>}
            </div>
          )}

          {paying ? (
            <div className="inline-form">
              <input className="input" type="number" inputMode="decimal" placeholder="Amount" value={payAmt}
                onChange={(e) => setPayAmt(e.target.value)} autoFocus />
              <button className="btn sm" onClick={() => submitPayment(d.id)}>{incoming ? "Log received" : "Log payment"}</button>
              <button className="btn-ghost sm" onClick={() => setPayingId(null)}>Cancel</button>
            </div>
          ) : (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="btn sm" onClick={() => { setPayingId(d.id); setPayAmt(""); }}>
                <HandCoins size={14} /> {incoming ? "Received" : "Pay"}
              </button>
              <button className="btn-ghost sm" onClick={() => startEdit(d)}><Pencil size={14} /> Edit</button>
              <button className="btn-ghost sm danger" onClick={() => { if (confirm(`Delete "${d.party}"?`)) deleteDebt(d.id); }}>
                <Trash2 size={14} /> Delete
              </button>
            </div>
          )}

          {(d.payments?.length ?? 0) > 0 && (
            <div style={{ marginTop: 12 }}>
              <p className="sec-sub" style={{ margin: "0 0 4px", display: "flex", alignItems: "center", gap: 6 }}><CalendarClock size={12} /> Payment history</p>
              {d.payments!.slice(0, 6).map((p) => (
                <div key={p.id} style={{ display: "flex", justifyContent: "space-between", padding: "5px 0", fontSize: 13, color: "var(--ink-2)", borderBottom: "1px dotted var(--rule-dot)" }}>
                  <span>{friendlyDate(p.date)}</span>
                  <b className={incoming ? "pos" : "neg"} style={{ fontFamily: "var(--serif)" }}>{incoming ? "+" : "−"}{money(p.amount)}</b>
                </div>
              ))}
            </div>
          )}
          {d.note ? <p className="sec-sub" style={{ marginTop: 10, fontStyle: "italic" }}>{d.note}</p> : null}
        </div>
      )}
    </>
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
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-head">
          <h3>{draft.id ? "Edit debt" : "Add a debt"}</h3>
          <button className="btn-icon" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>

        <div className="seg" style={{ marginBottom: 12 }}>
          <button className={draft.direction === "i_owe" ? "on" : ""} onClick={() => set({ direction: "i_owe" })}>I owe</button>
          <button className={draft.direction === "owed_to_me" ? "on" : ""} onClick={() => set({ direction: "owed_to_me", kind: "person" })}>Owed to me</button>
        </div>

        {draft.direction === "i_owe" && (
          <div className="chips" style={{ marginBottom: 14 }}>
            {(Object.keys(KIND_META) as DebtKind[]).map((k) => {
              const M = KIND_META[k];
              return (
                <button key={k} className={"chip" + (draft.kind === k ? " on" : "")} onClick={() => set({ kind: k })}>
                  <M.icon size={13} style={{ display: "inline", verticalAlign: "-2px", marginRight: 4 }} /> {M.label}
                </button>
              );
            })}
          </div>
        )}

        <label className="field">
          <span>{draft.direction === "i_owe" ? "Who do you owe?" : "Who owes you?"}</span>
          <input value={draft.party} onChange={(e) => set({ party: e.target.value })} placeholder={isPerson ? "e.g. James" : "e.g. Visa card"} autoFocus />
        </label>

        <label className="field">
          <span>Balance</span>
          <input type="number" inputMode="decimal" value={draft.balance} onChange={(e) => set({ balance: e.target.value })} placeholder="0" />
        </label>

        {!isPerson && (
          <div className="fieldrow">
            <label className="field">
              <span>APR %</span>
              <input type="number" inputMode="decimal" value={draft.apr} onChange={(e) => set({ apr: e.target.value })} placeholder="0" />
            </label>
            <label className="field">
              <span>Min / month</span>
              <input type="number" inputMode="decimal" value={draft.minPayment} onChange={(e) => set({ minPayment: e.target.value })} placeholder="0" />
            </label>
          </div>
        )}

        <label className="field">
          <span>Next due {isPerson ? "(optional)" : ""}</span>
          <input type="date" value={draft.dueDate} onChange={(e) => set({ dueDate: e.target.value })} />
        </label>

        {!isPerson && draft.dueDate && parseFloat(draft.minPayment) > 0 && (
          <label className="toggle">
            <input type="checkbox" checked={draft.autoPay} onChange={(e) => set({ autoPay: e.target.checked })} />
            <span>Auto-pay the minimum each month on the {ordinal(parseInt(draft.dueDate.slice(8, 10), 10) || 1)}</span>
          </label>
        )}

        <label className="field">
          <span>Note (optional)</span>
          <input value={draft.note} onChange={(e) => set({ note: e.target.value })} placeholder="Anything to remember" />
        </label>

        <button className="btn full" onClick={onSave} disabled={!draft.party.trim() || !(parseFloat(draft.balance) > 0)}>
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
