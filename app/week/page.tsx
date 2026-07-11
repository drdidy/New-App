"use client";

import { useEffect, useMemo, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ArrowRight, Feather } from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, friendlyDate, isoWeekId } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";

// ISO week helpers — Monday-anchored, matching how people think of "this week".
function weekStart(d: Date): Date {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const day = (x.getDay() + 6) % 7; // Mon=0
  x.setDate(x.getDate() - day);
  return x;
}
const iso = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

export default function WeekPage() {
  const { data, ready } = useStore();
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!ready) return;
    // Opening the edition marks it read — the flag on Today goes quiet.
    try { localStorage.setItem("mc-week-read", isoWeekId(new Date())); } catch {}
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  const edition = useMemo(() => {
    const now = new Date();
    const start = weekStart(now);
    const end = new Date(start); end.setDate(end.getDate() + 6);
    const prevStart = new Date(start); prevStart.setDate(prevStart.getDate() - 7);
    const s0 = iso(start), s1 = iso(end), p0 = iso(prevStart), p1 = iso(new Date(start.getTime() - 86400000));

    const inWeek = (d: string, a: string, b: string) => d >= a && d <= b;
    const txs = data.transactions;
    const spentTxs = txs.filter((t) => t.type === "expense" && inWeek(t.date, s0, s1));
    const spent = spentTxs.reduce((s, t) => s + t.amount, 0);
    const spentPrev = txs.filter((t) => t.type === "expense" && inWeek(t.date, p0, p1)).reduce((s, t) => s + t.amount, 0);
    const income = txs.filter((t) => t.type === "income" && inWeek(t.date, s0, s1)).reduce((s, t) => s + t.amount, 0);

    const byCat = new Map<string, number>();
    for (const t of spentTxs) byCat.set(t.category, (byCat.get(t.category) || 0) + t.amount);
    const topCats = [...byCat.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3);

    const biggest = spentTxs.slice().sort((a, b) => b.amount - a.amount)[0] || null;

    const debtPaid = data.debts
      .filter((d) => d.direction === "i_owe")
      .flatMap((d) => (d.payments || []).filter((p) => inWeek(p.date, s0, s1)).map((p) => ({ party: d.party, amount: p.amount })));
    const debtPaidTotal = debtPaid.reduce((s, p) => s + p.amount, 0);

    // No-spend days: only days that have already happened count.
    const spendDays = new Set(spentTxs.map((t) => t.date));
    const elapsed = Math.min(6, Math.floor((now.getTime() - start.getTime()) / 86400000)) + 1;
    let noSpend = 0;
    for (let i = 0; i < elapsed; i++) {
      const d = new Date(start); d.setDate(d.getDate() + i);
      if (!spendDays.has(iso(d))) noSpend++;
    }

    const delta = spentPrev > 0 ? ((spent - spentPrev) / spentPrev) * 100 : null;
    const sameMonth = start.getMonth() === end.getMonth();
    const range = `${start.toLocaleDateString(undefined, { month: "long", day: "numeric" })} – ${end.toLocaleDateString(undefined, sameMonth ? { day: "numeric" } : { month: "short", day: "numeric" })}`;
    const no = isoWeekId(now).split("-W")[1];

    let note: string;
    if (spentTxs.length === 0 && income === 0) note = "A quiet week in the ledger. Log as you go and next week's edition writes itself.";
    else if (delta != null && delta <= -10) note = `You spent ${Math.abs(Math.round(delta))}% less than last week. That gap is real money — consider moving it into a bucket before it evaporates.`;
    else if (delta != null && delta >= 15) note = `Spending ran ${Math.round(delta)}% hotter than last week. Not a verdict — one line item usually explains it. Worth a look above.`;
    else if (debtPaidTotal > 0) note = `${formatMoney(debtPaidTotal, data.currency)} went against debt this week. Every payment moves the debt-free date closer.`;
    else note = "A steady week. Steady is what compounds.";

    return { spent, spentPrev, delta, income, topCats, biggest, debtPaid, debtPaidTotal, noSpend, range, no, count: spentTxs.length, note };
  }, [data]);

  if (!ready) return null;
  const cur = data.currency;
  const e = edition;

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">The Weekly Edition · No. {e.no}</p>
      </div>
      <h1 className="pg-title rise">{e.range}</h1>
      <div className="pg-rule rise" />

      {/* THE NUMBER */}
      <div className="st rise">
        <div className="st-label">Spent this week</div>
        <div className="st-num neg"><AnimatedNumber value={e.spent} currency={cur} /></div>
        <p className="st-meta">
          {e.delta == null
            ? `${e.count} ${e.count === 1 ? "entry" : "entries"} in the ledger.`
            : e.delta <= 0
              ? `${Math.abs(Math.round(e.delta))}% less than last week (${formatMoney(e.spentPrev, cur)}).`
              : `${Math.round(e.delta)}% more than last week (${formatMoney(e.spentPrev, cur)}).`}
        </p>
        {e.income > 0 || e.debtPaidTotal > 0 ? (
          <div className="st-links">
            {e.income > 0 && <span className="pos">+{formatMoney(e.income, cur)} came in</span>}
            {e.debtPaidTotal > 0 && <span className="gold" style={{ borderBottomColor: "rgba(226,179,102,0.4)" }}>{formatMoney(e.debtPaidTotal, cur)} paid on debt</span>}
          </div>
        ) : null}
      </div>

      {/* WHERE IT WENT */}
      {e.topCats.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Where it went</h2></div>
          {e.topCats.map(([cat, amount]) => (
            <div className="row" key={cat}>
              <div className="row-meta"><div className="row-t">{cat}</div></div>
              <div className="row-amt neg">{formatMoney(amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {/* NOTABLE */}
      {(e.biggest || e.debtPaid.length > 0) && (
        <section className="sec rise">
          <div className="sec-head"><h2>Notable</h2></div>
          {e.biggest && (
            <div className="row">
              <span className="row-ic">🧾</span>
              <div className="row-meta">
                <div className="row-t">Biggest purchase — {e.biggest.description || e.biggest.category}</div>
                <div className="row-s">{e.biggest.category} · {friendlyDate(e.biggest.date)}</div>
              </div>
              <div className="row-amt neg">{formatMoney(e.biggest.amount, cur)}</div>
            </div>
          )}
          {e.debtPaid.map((p, i) => (
            <div className="row" key={i}>
              <span className="row-ic">🤝</span>
              <div className="row-meta"><div className="row-t">Paid {p.party}</div><div className="row-s">Debt payment</div></div>
              <div className="row-amt pos">−{formatMoney(p.amount, cur)} owed</div>
            </div>
          ))}
        </section>
      )}

      {/* QUIET DAYS */}
      <section className="sec rise">
        <div className="sec-head"><h2>Quiet days</h2></div>
        <p className="sec-sub" style={{ marginTop: 10 }}>
          {e.noSpend === 0
            ? "No spend-free days yet this week — even one changes the shape of the month."
            : <><b style={{ color: "var(--ink)" }}>{e.noSpend} day{e.noSpend === 1 ? "" : "s"}</b> this week with nothing spent at all. That&apos;s the quietest kind of win.</>}
        </p>
      </section>

      {/* COLOPHON */}
      <div className="flag rise good" style={{ marginTop: 6 }}>
        <span className="flag-txt"><Feather size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "-2px" }} />{e.note}</span>
      </div>

      <p className="sec-sub rise" style={{ textAlign: "center", marginTop: 18 }}>
        <Link href="/ledger" style={{ color: "var(--gold)" }}>Open the full ledger <ArrowRight size={12} style={{ display: "inline" }} /></Link>
      </p>
      <p className="colophon rise">A new edition every Monday.</p>
    </main>
  );
}
