"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import {
  Banknote,
  Check,
  HandHeart,
  Layers,
  Minus,
  PiggyBank,
  Plus,
  Repeat,
  Sparkles,
  Trash2,
  TrendingUp,
  Wallet,
  X,
} from "lucide-react";
import { useStore } from "@/lib/store";
import { clampPct, formatMoney, monthKey } from "@/lib/format";
import { success } from "@/lib/haptics";
import AnimatedNumber from "@/components/AnimatedNumber";
import type { Bucket, BucketKind, RecurringIncome } from "@/lib/types";
import Burst from "@/components/Burst";

const KIND: Record<BucketKind, { label: string; emoji: string; Icon: typeof PiggyBank }> = {
  save: { label: "Savings", emoji: "🐷", Icon: PiggyBank },
  invest: { label: "Investing", emoji: "📈", Icon: TrendingUp },
  give: { label: "Giving", emoji: "🤲", Icon: HandHeart },
  spend: { label: "Spending", emoji: "🛍️", Icon: Wallet },
  other: { label: "Other", emoji: "💼", Icon: Layers },
};

const STARTER_BUCKETS: Array<Partial<Bucket> & { name: string; emoji: string; kind: BucketKind; allocType: "percent" | "fixed"; allocValue: number }> = [
  { name: "Tithe", emoji: "🙏", kind: "give", allocType: "percent", allocValue: 10 },
  { name: "Offerings", emoji: "💝", kind: "give", allocType: "percent", allocValue: 5 },
  { name: "Savings", emoji: "🐷", kind: "save", allocType: "percent", allocValue: 15 },
  { name: "Investments", emoji: "📈", kind: "invest", allocType: "percent", allocValue: 10 },
  { name: "Bless others", emoji: "🤲", kind: "give", allocType: "fixed", allocValue: 50 },
];

interface IncomeDraft { id?: string; name: string; amount: string; dayOfMonth: string; autoLog: boolean; }
interface BucketDraft { id?: string; name: string; emoji: string; kind: BucketKind; allocType: "percent" | "fixed" | "none"; allocValue: string; target: string; }

export default function BucketsPage() {
  const {
    data, ready,
    addIncome, updateIncome, deleteIncome, receiveIncome,
    addBucket, updateBucket, deleteBucket, fundBucket, distributePaycheck,
  } = useStore();
  const root = useRef<HTMLElement>(null);
  const [inc, setInc] = useState<IncomeDraft | null>(null);
  const [bk, setBk] = useState<BucketDraft | null>(null);
  const [fundId, setFundId] = useState<string | null>(null);
  const [fundAmt, setFundAmt] = useState("");
  const [distOpen, setDistOpen] = useState(false);
  const [distAmt, setDistAmt] = useState("");
  const [celebrate, setCelebrate] = useState(0);

  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;

  const cur = data.currency;
  const income = data.recurringIncome || [];
  const buckets = data.buckets || [];
  const month = monthKey();
  const monthlyIncome = income.reduce((s, x) => s + x.amount, 0);
  const totalSetAside = buckets.reduce((s, b) => s + b.balance, 0);
  const giveBuckets = buckets.filter((b) => b.kind === "give");
  const giving = giveBuckets.reduce((s, b) => s + b.balance, 0);

  // ---- income ----
  function openIncome(x?: RecurringIncome) {
    setInc(x
      ? { id: x.id, name: x.name, amount: String(x.amount), dayOfMonth: String(x.dayOfMonth), autoLog: x.autoLog ?? true }
      : { name: "Salary", amount: "", dayOfMonth: "30", autoLog: true });
  }
  function saveIncome() {
    if (!inc) return;
    const amount = parseFloat(inc.amount);
    const day = parseInt(inc.dayOfMonth, 10);
    if (!inc.name.trim() || !(amount > 0) || !(day >= 1 && day <= 31)) return;
    const fields = { name: inc.name.trim(), amount, dayOfMonth: day, autoLog: inc.autoLog };
    if (inc.id) updateIncome(inc.id, fields);
    else addIncome({ ...fields, memberId: data.members[0]?.id });
    setInc(null);
  }

  // ---- buckets ----
  function openBucket(b?: Bucket) {
    // Fresh fund draft per sheet, so a leftover amount can never silently fund
    // (or drain) a different bucket.
    setFundId(null); setFundAmt("");
    setBk(b
      ? { id: b.id, name: b.name, emoji: b.emoji || KIND[b.kind].emoji, kind: b.kind, allocType: b.allocType ?? "none", allocValue: b.allocValue != null ? String(b.allocValue) : "", target: b.target != null ? String(b.target) : "" }
      : { name: "", emoji: "🐷", kind: "save", allocType: "percent", allocValue: "", target: "" });
  }
  function saveBucket() {
    if (!bk) return;
    if (!bk.name.trim()) return;
    const av = parseFloat(bk.allocValue);
    const tg = parseFloat(bk.target);
    const fields = {
      name: bk.name.trim(), emoji: bk.emoji, kind: bk.kind,
      allocType: bk.allocType === "none" ? undefined : bk.allocType,
      // A single bucket can't claim more than 100% of a paycheck.
      allocValue:
        bk.allocType !== "none" && Number.isFinite(av) && av > 0
          ? bk.allocType === "percent" ? Math.min(av, 100) : av
          : undefined,
      target: Number.isFinite(tg) && tg > 0 ? tg : undefined,
    };
    if (bk.id) updateBucket(bk.id, fields);
    else addBucket({ ...fields, color: "#14b8a6" });
    setBk(null);
  }
  function addStarters() {
    STARTER_BUCKETS.forEach((s) => addBucket({ name: s.name, emoji: s.emoji, kind: s.kind, color: "#14b8a6", allocType: s.allocType, allocValue: s.allocValue }));
  }
  function doFund(id: string, sign: 1 | -1) {
    const a = parseFloat(fundAmt);
    if (!(a > 0)) return;
    const b = buckets.find((x) => x.id === id);
    fundBucket(id, sign * a);
    // Reaching a bucket's target is a finish line, not a rounding event.
    if (sign === 1 && b?.target && b.balance < b.target && b.balance + a >= b.target) {
      setCelebrate((c) => c + 1);
    }
    success();
    setFundId(null); setFundAmt("");
  }
  function previewSplit(amount: number) {
    return buckets
      .filter((b) => b.allocType && b.allocValue)
      .map((b) => ({ b, add: b.allocType === "percent" ? (amount * (b.allocValue || 0)) / 100 : (b.allocValue || 0) }))
      .filter((x) => x.add > 0);
  }

  const distNum = parseFloat(distAmt) || 0;
  const split = previewSplit(distNum);
  const splitTotal = split.reduce((s, x) => s + x.add, 0);

  return (
    <main className="pg" ref={root}>
      {celebrate > 0 && <Burst key={celebrate} />}
      <div className="pg-head rise">
        <p className="pg-date">Give every paycheck a job</p>
        <button className="btn-text" onClick={() => openBucket()}>+ Add bucket</button>
      </div>
      <h1 className="pg-title rise">Buckets</h1>
      <div className="pg-rule rise" />

      {/* STATEMENT */}
      <div className="st rise">
        <div className="st-label">Set aside in buckets</div>
        <div className="st-num"><AnimatedNumber value={totalSetAside} currency={cur} /></div>
        <p className="st-meta">
          {buckets.length
            ? `Across ${buckets.length} bucket${buckets.length === 1 ? "" : "s"}. Distribute a paycheck to fill them automatically.`
            : "Create buckets for savings, investing, tithes, offerings, and giving — then split each paycheck into them."}
        </p>
        {giving > 0 && (
          <div className="st-links">
            <span className="gold" style={{ borderBottomColor: "rgba(226,179,102,0.4)" }}>🤲 {formatMoney(giving, cur)} set aside to give across {giveBuckets.length} bucket{giveBuckets.length === 1 ? "" : "s"} — generosity in motion</span>
          </div>
        )}
        {buckets.length > 0 && (
          <button className="btn full" style={{ marginTop: 16 }} onClick={() => { setDistAmt(monthlyIncome ? String(monthlyIncome) : ""); setDistOpen(true); }}>
            <Sparkles size={16} /> Distribute a paycheck
          </button>
        )}
      </div>

      {/* INCOME */}
      <section className="sec rise">
        <div className="sec-head"><h2>Income</h2><span className="sec-aux"><button className="link" onClick={() => openIncome()}>+ Add</button></span></div>
        {income.length ? income.map((x) => {
          const got = x.lastPaidMonth === month;
          return (
            <div className="row" key={x.id}>
              <span className="row-ic"><Banknote /></span>
              <button className="row-meta" style={{ textAlign: "left" }} onClick={() => openIncome(x)}>
                <div className="row-t">{x.name}</div>
                <div className="row-s">Lands on the {ordinal(x.dayOfMonth)}{x.autoLog ? " · auto" : ""}{got ? " · received ✓" : ""}</div>
              </button>
              <div className="row-amt pos">{formatMoney(x.amount, cur)}</div>
              {got ? <span className="check"><Check size={15} /></span>
                : <button className="btn-ghost sm" onClick={() => { receiveIncome(x.id); success(); }}>Receive</button>}
              <button className="btn-icon danger" onClick={() => { if (confirm(`Delete "${x.name}"?`)) deleteIncome(x.id); }} aria-label="Delete"><Trash2 size={14} /></button>
            </div>
          );
        }) : (
          <div className="blank">
            <div className="ic"><Banknote size={22} /></div>
            <h4>Add your income</h4>
            <p>Tell the app when your salary lands (e.g. the 30th) and it logs automatically each month.</p>
            <button className="btn" onClick={() => openIncome()}><Plus size={16} /> Add income</button>
          </div>
        )}
      </section>

      {/* BUCKETS */}
      <section className="sec rise">
        <div className="sec-head"><h2>Your buckets</h2>
          {buckets.length > 0 && <span className="sec-aux"><span className="sec-total">{formatMoney(totalSetAside, cur)}</span></span>}
        </div>
        {buckets.length ? buckets.map((b) => {
          const Meta = KIND[b.kind];
          const pct = b.target ? clampPct((b.balance / b.target) * 100) : 0;
          const sub = [
            Meta.label,
            b.allocType && b.allocValue ? (b.allocType === "percent" ? `${b.allocValue}% of pay` : `${formatMoney(b.allocValue, cur)}/pay`) : null,
            b.target ? `of ${formatMoney(b.target, cur)}` : null,
          ].filter(Boolean).join(" · ");
          return (
            <button className="row" key={b.id} onClick={() => openBucket(b)} style={{ display: "block" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <span className="row-t">{b.emoji || Meta.emoji} {b.name}</span>
                <span className="row-amt">{formatMoney(b.balance, cur)}</span>
              </div>
              <div className="row-s">{sub}</div>
              {b.target ? <div className="meter" style={{ margin: "9px 0 2px" }}><span style={{ width: `${pct}%` }} /></div> : null}
            </button>
          );
        }) : (
          <div className="blank">
            <div className="ic"><Layers size={22} /></div>
            <h4>No buckets yet</h4>
            <p>Set money aside for what matters: savings, investing, tithes, offerings, and blessing others.</p>
            <button className="btn" onClick={addStarters}><Sparkles size={16} /> Start with a values pack</button>
            <div><button className="btn-ghost" style={{ marginTop: 8 }} onClick={() => openBucket()}><Plus size={15} /> Or add one bucket</button></div>
          </div>
        )}
      </section>

      {/* INCOME SHEET */}
      {inc && (
        <Sheet title={inc.id ? "Edit income" : "Add income"} onClose={() => setInc(null)}>
          <label className="field"><span>Name</span>
            <input value={inc.name} onChange={(e) => setInc({ ...inc, name: e.target.value })} placeholder="Salary" autoFocus />
          </label>
          <div className="fieldrow">
            <label className="field"><span>Amount</span>
              <input type="number" inputMode="decimal" value={inc.amount} onChange={(e) => setInc({ ...inc, amount: e.target.value })} placeholder="4200" />
            </label>
            <label className="field"><span>Day it lands</span>
              <input type="number" inputMode="numeric" value={inc.dayOfMonth} onChange={(e) => setInc({ ...inc, dayOfMonth: e.target.value })} placeholder="30" />
            </label>
          </div>
          <label className="toggle">
            <input type="checkbox" checked={inc.autoLog} onChange={(e) => setInc({ ...inc, autoLog: e.target.checked })} />
            <span>Log it automatically each month</span>
          </label>
          <button className="btn full" style={{ marginTop: 8 }} onClick={saveIncome} disabled={!inc.name.trim() || !(parseFloat(inc.amount) > 0)}>
            {inc.id ? "Save" : "Add income"}
          </button>
        </Sheet>
      )}

      {/* BUCKET SHEET */}
      {bk && (
        <Sheet title={bk.id ? "Edit bucket" : "New bucket"} onClose={() => setBk(null)}>
          <div className="chips" style={{ marginBottom: 14 }}>
            {(Object.keys(KIND) as BucketKind[]).map((k) => (
              <button key={k} className={"chip" + (bk.kind === k ? " on" : "")} onClick={() => setBk({ ...bk, kind: k, emoji: bk.emoji || KIND[k].emoji })}>
                {KIND[k].emoji} {KIND[k].label}
              </button>
            ))}
          </div>
          <label className="field"><span>Name</span>
            <input value={bk.name} onChange={(e) => setBk({ ...bk, name: e.target.value })} placeholder="Tithe, Emergency fund, Bless others…" autoFocus />
          </label>
          <div className="field"><span>Fill from each paycheck</span>
            <div className="seg" style={{ marginTop: 2 }}>
              <button className={bk.allocType === "percent" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "percent" })}>% of pay</button>
              <button className={bk.allocType === "fixed" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "fixed" })}>Fixed</button>
              <button className={bk.allocType === "none" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "none" })}>Manual</button>
            </div>
          </div>
          {bk.allocType !== "none" && (
            <label className="field"><span>{bk.allocType === "percent" ? "Percent of each paycheck" : "Fixed amount per paycheck"}</span>
              <input type="number" inputMode="decimal" value={bk.allocValue} onChange={(e) => setBk({ ...bk, allocValue: e.target.value })} placeholder={bk.allocType === "percent" ? "10" : "50"} />
            </label>
          )}
          <label className="field"><span>Target (optional)</span>
            <input type="number" inputMode="decimal" value={bk.target} onChange={(e) => setBk({ ...bk, target: e.target.value })} placeholder="e.g. 6000" />
          </label>
          <button className="btn full" onClick={saveBucket} disabled={!bk.name.trim()}>{bk.id ? "Save changes" : "Create bucket"}</button>
          {bk.id && (
            <>
              <div className="inline-form" style={{ marginTop: 12 }}>
                <input className="input" type="number" inputMode="decimal" placeholder="Amount" value={fundId === bk.id ? fundAmt : ""} onChange={(e) => { setFundId(bk.id!); setFundAmt(e.target.value); }} />
                <button className="btn sm" onClick={() => doFund(bk.id!, 1)} disabled={fundId !== bk.id || !(parseFloat(fundAmt) > 0)}><Plus size={14} /> Add</button>
                <button className="btn-ghost sm" onClick={() => doFund(bk.id!, -1)} disabled={fundId !== bk.id || !(parseFloat(fundAmt) > 0)}><Minus size={14} /> Spend</button>
              </div>
              <button className="btn-ghost danger" style={{ width: "100%", marginTop: 10 }} onClick={() => { if (confirm(`Delete "${bk.name}"?`)) { deleteBucket(bk.id!); setBk(null); } }}>
                <Trash2 size={15} /> Delete bucket
              </button>
            </>
          )}
        </Sheet>
      )}

      {/* DISTRIBUTE SHEET */}
      {distOpen && (
        <Sheet title="Distribute a paycheck" onClose={() => setDistOpen(false)}>
          <label className="field"><span>Paycheck amount</span>
            <input type="number" inputMode="decimal" value={distAmt} onChange={(e) => setDistAmt(e.target.value)} placeholder="4200" autoFocus />
          </label>
          {split.length > 0 ? (
            <div className="sec" style={{ marginTop: 12, marginBottom: 0 }}>
              {split.map(({ b, add }) => (
                <div className="row" key={b.id}>
                  <span>{b.emoji || KIND[b.kind].emoji} {b.name}</span>
                  <b className="pos">+{formatMoney(add, cur)}</b>
                </div>
              ))}
              <div className="row" style={{ color: "var(--mut)" }}>
                <span>Left as free cash</span>
                <b>{formatMoney(Math.max(0, distNum - splitTotal), cur)}</b>
              </div>
            </div>
          ) : (
            <p className="sec-sub">Give buckets a “% of pay” or “fixed” rule and they’ll fill here automatically.</p>
          )}
          <button className="btn full" style={{ marginTop: 12 }} onClick={() => { distributePaycheck(distNum); success(); setDistOpen(false); }} disabled={!(distNum > 0) || split.length === 0}>
            <Repeat size={16} /> Fill {split.length} bucket{split.length === 1 ? "" : "s"}
          </button>
        </Sheet>
      )}
    </main>
  );
}

function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <div className="sheet-head">
          <h3>{title}</h3>
          <button className="btn-icon" onClick={onClose} aria-label="Close"><X size={18} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ordinal(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}
