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

  useEffect(() => {
    if (!ready) return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".lx-reveal", { y: 20, opacity: 0, duration: 0.5, ease: "power3.out", stagger: 0.06 });
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
    fundBucket(id, sign * a);
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
    <main className="lx" ref={root}>
      <header className="lx-top lx-reveal">
        <div>
          <p className="lx-eyebrow"><Layers size={13} /> Give every paycheck a job</p>
          <h1 className="lx-h1">Buckets</h1>
        </div>
        <button className="lx-addbtn" onClick={() => openBucket()} aria-label="Add a bucket"><Plus size={20} /></button>
      </header>

      {/* SET-ASIDE HERO */}
      <div className="lx-hero lx-reveal">
        <div className="lx-hero-inner">
          <div className="lx-hero-label">Set aside in buckets</div>
          <div className="lx-hero-num pos"><AnimatedNumber value={totalSetAside} currency={cur} /></div>
          <div className="lx-hero-sub">
            {buckets.length
              ? `Across ${buckets.length} bucket${buckets.length === 1 ? "" : "s"}. Distribute a paycheck to fill them automatically.`
              : "Create buckets for savings, investing, tithes, offerings, and giving — then split each paycheck into them."}
          </div>
          {buckets.length > 0 && (
            <button className="lx-primary full" style={{ marginTop: 16 }} onClick={() => { setDistAmt(monthlyIncome ? String(monthlyIncome) : ""); setDistOpen(true); }}>
              <Sparkles size={16} /> Distribute a paycheck
            </button>
          )}
        </div>
      </div>

      {/* GENEROSITY SNAPSHOT */}
      {giving > 0 && (
        <div className="lx-generosity lx-reveal">
          <div className="lx-generosity-ic">🤲</div>
          <div className="lx-generosity-meta">
            <div className="lx-generosity-num">{formatMoney(giving, cur)}</div>
            <div className="lx-generosity-lbl">set aside to give across {giveBuckets.length} bucket{giveBuckets.length === 1 ? "" : "s"} — generosity in motion. 🙏</div>
          </div>
        </div>
      )}

      {/* INCOME */}
      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Income</h2>
          <button className="lx-headadd" onClick={() => openIncome()}><Plus size={16} /> Add</button>
        </div>
        {income.length ? (
          <div className="lx-list">
            {income.map((x) => {
              const got = x.lastPaidMonth === month;
              return (
                <div className="lx-li" key={x.id}>
                  <span className="ic"><Banknote size={16} /></span>
                  <button className="meta" style={{ background: "none", border: "none", textAlign: "left", cursor: "pointer", padding: 0 }} onClick={() => openIncome(x)}>
                    <div className="t">{x.name}</div>
                    <div className="s">Lands on the {ordinal(x.dayOfMonth)}{x.autoLog ? " · auto" : ""}{got ? " · received ✓" : ""}</div>
                  </button>
                  <div className="amt pos">{formatMoney(x.amount, cur)}</div>
                  {got ? <span className="lx-paid"><Check size={15} /></span>
                    : <button className="lx-ghost sm" onClick={() => { receiveIncome(x.id); success(); }}>Receive</button>}
                  <button className="lx-icon-btn danger" onClick={() => { if (confirm(`Delete "${x.name}"?`)) deleteIncome(x.id); }} aria-label="Delete"><Trash2 size={14} /></button>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="lx-blank">
            <div className="ic"><Banknote size={22} /></div>
            <h4>Add your income</h4>
            <p>Tell the app when your salary lands (e.g. the 30th) and it logs automatically each month.</p>
            <button className="lx-primary" onClick={() => openIncome()}><Plus size={16} /> Add income</button>
          </div>
        )}
      </section>

      {/* BUCKETS */}
      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Your buckets</h2>
          {buckets.length > 0 && <span className="lx-group-total">{formatMoney(totalSetAside, cur)}</span>}
        </div>
        {buckets.length ? (
          <div className="lx-bucketlist">
            {buckets.map((b) => {
              const Meta = KIND[b.kind];
              const pct = b.target ? clampPct((b.balance / b.target) * 100) : 0;
              return (
                <button className="lx-bucket" key={b.id} onClick={() => openBucket(b)}>
                  <span className="lx-bucket-ic"><Meta.Icon size={17} /></span>
                  <div className="lx-bucket-meta">
                    <div className="lx-bucket-top">
                      <span className="nm">{b.emoji || Meta.emoji} {b.name}</span>
                      <b>{formatMoney(b.balance, cur)}</b>
                    </div>
                    <div className="lx-bucket-tags">
                      <span>{Meta.label}</span>
                      {b.allocType && b.allocValue ? <span className="alloc">{b.allocType === "percent" ? `${b.allocValue}% of pay` : `${formatMoney(b.allocValue, cur)}/pay`}</span> : null}
                      {b.target ? <span>of {formatMoney(b.target, cur)}</span> : null}
                    </div>
                    {b.target ? <div className="lx-bucket-bar"><span style={{ width: `${pct}%` }} /></div> : null}
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="lx-blank">
            <div className="ic"><Layers size={22} /></div>
            <h4>No buckets yet</h4>
            <p>Set money aside for what matters: savings, investing, tithes, offerings, and blessing others.</p>
            <button className="lx-primary" onClick={addStarters}><Sparkles size={16} /> Start with a values pack</button>
            <button className="lx-ghost" style={{ marginTop: 8 }} onClick={() => openBucket()}><Plus size={15} /> Or add one bucket</button>
          </div>
        )}
      </section>

      {/* INCOME SHEET */}
      {inc && (
        <Sheet title={inc.id ? "Edit income" : "Add income"} onClose={() => setInc(null)}>
          <label className="lx-field"><span>Name</span>
            <input value={inc.name} onChange={(e) => setInc({ ...inc, name: e.target.value })} placeholder="Salary" autoFocus />
          </label>
          <div className="lx-field-row">
            <label className="lx-field"><span>Amount</span>
              <input type="number" inputMode="decimal" value={inc.amount} onChange={(e) => setInc({ ...inc, amount: e.target.value })} placeholder="4200" />
            </label>
            <label className="lx-field"><span>Day it lands</span>
              <input type="number" inputMode="numeric" value={inc.dayOfMonth} onChange={(e) => setInc({ ...inc, dayOfMonth: e.target.value })} placeholder="30" />
            </label>
          </div>
          <label className="lx-toggle">
            <input type="checkbox" checked={inc.autoLog} onChange={(e) => setInc({ ...inc, autoLog: e.target.checked })} />
            <span>Log it automatically each month</span>
          </label>
          <button className="lx-primary full" style={{ marginTop: 8 }} onClick={saveIncome} disabled={!inc.name.trim() || !(parseFloat(inc.amount) > 0)}>
            {inc.id ? "Save" : "Add income"}
          </button>
        </Sheet>
      )}

      {/* BUCKET SHEET */}
      {bk && (
        <Sheet title={bk.id ? "Edit bucket" : "New bucket"} onClose={() => setBk(null)}>
          <div className="lx-chips" style={{ marginBottom: 14 }}>
            {(Object.keys(KIND) as BucketKind[]).map((k) => (
              <button key={k} className={"lx-chip" + (bk.kind === k ? " on" : "")} onClick={() => setBk({ ...bk, kind: k, emoji: bk.emoji || KIND[k].emoji })}>
                {KIND[k].emoji} {KIND[k].label}
              </button>
            ))}
          </div>
          <label className="lx-field"><span>Name</span>
            <input value={bk.name} onChange={(e) => setBk({ ...bk, name: e.target.value })} placeholder="Tithe, Emergency fund, Bless others…" autoFocus />
          </label>
          <div className="lx-field"><span>Fill from each paycheck</span>
            <div className="lx-seg" style={{ marginTop: 2 }}>
              <button className={bk.allocType === "percent" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "percent" })}>% of pay</button>
              <button className={bk.allocType === "fixed" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "fixed" })}>Fixed</button>
              <button className={bk.allocType === "none" ? "on" : ""} onClick={() => setBk({ ...bk, allocType: "none" })}>Manual</button>
            </div>
          </div>
          {bk.allocType !== "none" && (
            <label className="lx-field"><span>{bk.allocType === "percent" ? "Percent of each paycheck" : "Fixed amount per paycheck"}</span>
              <input type="number" inputMode="decimal" value={bk.allocValue} onChange={(e) => setBk({ ...bk, allocValue: e.target.value })} placeholder={bk.allocType === "percent" ? "10" : "50"} />
            </label>
          )}
          <label className="lx-field"><span>Target (optional)</span>
            <input type="number" inputMode="decimal" value={bk.target} onChange={(e) => setBk({ ...bk, target: e.target.value })} placeholder="e.g. 6000" />
          </label>
          <button className="lx-primary full" onClick={saveBucket} disabled={!bk.name.trim()}>{bk.id ? "Save changes" : "Create bucket"}</button>
          {bk.id && (
            <>
              <div className="lx-pay-row" style={{ marginTop: 12 }}>
                <input type="number" inputMode="decimal" placeholder="Amount" value={fundId === bk.id ? fundAmt : ""} onChange={(e) => { setFundId(bk.id!); setFundAmt(e.target.value); }} />
                <button className="lx-primary sm" onClick={() => doFund(bk.id!, 1)} disabled={fundId !== bk.id || !(parseFloat(fundAmt) > 0)}><Plus size={14} /> Add</button>
                <button className="lx-ghost sm" onClick={() => doFund(bk.id!, -1)} disabled={fundId !== bk.id || !(parseFloat(fundAmt) > 0)}><Minus size={14} /> Spend</button>
              </div>
              <button className="lx-ghost danger" style={{ width: "100%", marginTop: 10 }} onClick={() => { if (confirm(`Delete "${bk.name}"?`)) { deleteBucket(bk.id!); setBk(null); } }}>
                <Trash2 size={15} /> Delete bucket
              </button>
            </>
          )}
        </Sheet>
      )}

      {/* DISTRIBUTE SHEET */}
      {distOpen && (
        <Sheet title="Distribute a paycheck" onClose={() => setDistOpen(false)}>
          <label className="lx-field"><span>Paycheck amount</span>
            <input type="number" inputMode="decimal" value={distAmt} onChange={(e) => setDistAmt(e.target.value)} placeholder="4200" autoFocus />
          </label>
          {split.length > 0 ? (
            <div className="lx-split">
              {split.map(({ b, add }) => (
                <div className="lx-split-row" key={b.id}>
                  <span>{b.emoji || KIND[b.kind].emoji} {b.name}</span>
                  <b className="pos">+{formatMoney(add, cur)}</b>
                </div>
              ))}
              <div className="lx-split-row total">
                <span>Left as free cash</span>
                <b>{formatMoney(Math.max(0, distNum - splitTotal), cur)}</b>
              </div>
            </div>
          ) : (
            <p className="lx-group-sub">Give buckets a “% of pay” or “fixed” rule and they’ll fill here automatically.</p>
          )}
          <button className="lx-primary full" style={{ marginTop: 12 }} onClick={() => { distributePaycheck(distNum); success(); setDistOpen(false); }} disabled={!(distNum > 0) || split.length === 0}>
            <Repeat size={16} /> Fill {split.length} bucket{split.length === 1 ? "" : "s"}
          </button>
        </Sheet>
      )}
    </main>
  );
}

function Sheet({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  return (
    <div className="lx-sheet-backdrop" onClick={onClose}>
      <div className="lx-sheet" onClick={(e) => e.stopPropagation()}>
        <div className="lx-sheet-head">
          <h3>{title}</h3>
          <button className="lx-sheet-x" onClick={onClose} aria-label="Close"><X size={18} /></button>
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
