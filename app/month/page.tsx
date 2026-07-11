"use client";

import { useEffect, useMemo, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ArrowRight, Feather, TrendingDown, TrendingUp } from "lucide-react";
import { useStore } from "@/lib/store";
import { formatMoney, friendlyDate, monthLabel, prevMonthKey } from "@/lib/format";
import { netWorth } from "@/lib/insights";
import AnimatedNumber from "@/components/AnimatedNumber";

// The Monthly Statement: the month-close ritual. It reads on the month that
// just finished — a statement is written when the books close, not mid-flow.
export default function MonthPage() {
  const { data, ready } = useStore();
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!ready) return;
    // Reading the statement marks it read — the flag on Today goes quiet.
    try { localStorage.setItem("mc-month-read", prevMonthKey()); } catch {}
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = gsap.context(() => {
      gsap.from(".rise", { y: 18, opacity: 0, duration: 0.55, ease: "power3.out", stagger: 0.07 });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  const st = useMemo(() => {
    const month = prevMonthKey();
    const before = (() => {
      const [y, m] = month.split("-").map(Number);
      const d = new Date(y, m - 2, 1);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    })();

    const txs = data.transactions;
    const inMonth = txs.filter((t) => t.date.startsWith(month));
    const spentTxs = inMonth.filter((t) => t.type === "expense");
    const spent = spentTxs.reduce((s, t) => s + t.amount, 0);
    const spentBefore = txs.filter((t) => t.type === "expense" && t.date.startsWith(before)).reduce((s, t) => s + t.amount, 0);
    const income = inMonth.filter((t) => t.type === "income").reduce((s, t) => s + t.amount, 0);
    const net = income - spent;

    const byCat = new Map<string, number>();
    for (const t of spentTxs) byCat.set(t.category, (byCat.get(t.category) || 0) + t.amount);
    const topCats = [...byCat.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4);
    const biggest = spentTxs.slice().sort((a, b) => b.amount - a.amount)[0] || null;

    const debtPaid = data.debts
      .filter((d) => d.direction === "i_owe")
      .flatMap((d) => (d.payments || []).filter((p) => p.date.startsWith(month)).map((p) => ({ party: d.party, amount: p.amount })));
    const debtPaidTotal = debtPaid.reduce((s, p) => s + p.amount, 0);

    // Net worth movement: the snapshot at that month vs the one before it.
    const hist = data.netWorthHistory || [];
    const nwAt = hist.find((h) => h.month === month)?.value ?? null;
    const nwBefore = hist.find((h) => h.month === before)?.value ?? null;
    const nwDelta = nwAt != null && nwBefore != null ? nwAt - nwBefore : null;

    const delta = spentBefore > 0 ? ((spent - spentBefore) / spentBefore) * 100 : null;

    let note: string;
    if (inMonth.length === 0) note = "No entries this month — the statement writes itself once you log as you go.";
    else if (net > 0 && debtPaidTotal > 0) note = `You finished ${formatMoney(net, data.currency)} ahead and put ${formatMoney(debtPaidTotal, data.currency)} against debt. That's a month working exactly as it should.`;
    else if (net > 0) note = `You finished ${formatMoney(net, data.currency)} ahead of your spending. Decide where that surplus lives before the new month decides for you.`;
    else if (delta != null && delta < 0) note = `You spent ${Math.abs(Math.round(delta))}% less than the month before — the direction matters more than the size of the step.`;
    else note = "The month ran hotter than it earned. One category above usually explains most of it — worth a minute before the new month settles in.";

    return { month, spent, spentBefore, delta, income, net, topCats, biggest, debtPaid, debtPaidTotal, nwDelta, count: inMonth.length, note };
  }, [data]);

  if (!ready) return null;
  const cur = data.currency;
  const nw = netWorth(data);

  return (
    <main className="pg" ref={root}>
      <div className="pg-head rise">
        <p className="pg-date">The Monthly Statement</p>
      </div>
      <h1 className="pg-title rise">{monthLabel(st.month)}</h1>
      <div className="pg-rule rise" />

      {/* THE CLOSE */}
      <div className="st rise">
        <div className="st-label">The month closed {st.net >= 0 ? "ahead" : "behind"}</div>
        <div className={"st-num" + (st.net < 0 ? " neg" : "")}>
          <AnimatedNumber value={Math.abs(st.net)} currency={cur} />
        </div>
        <p className="st-meta">
          {formatMoney(st.income, cur)} in · {formatMoney(st.spent, cur)} out
          {st.delta != null && (st.delta <= 0
            ? ` — spending down ${Math.abs(Math.round(st.delta))}% on the month before.`
            : ` — spending up ${Math.round(st.delta)}% on the month before.`)}
        </p>
        <div className="st-links">
          {st.debtPaidTotal > 0 && <span className="gold" style={{ borderBottomColor: "rgba(226,179,102,0.4)" }}>{formatMoney(st.debtPaidTotal, cur)} paid on debt</span>}
          {st.nwDelta != null && st.nwDelta !== 0 && (
            <span className={st.nwDelta > 0 ? "pos" : ""}>
              Net worth {st.nwDelta > 0 ? <TrendingUp size={12} style={{ display: "inline" }} /> : <TrendingDown size={12} style={{ display: "inline" }} />} {formatMoney(Math.abs(st.nwDelta), cur)}
            </span>
          )}
        </div>
      </div>

      {/* WHERE IT WENT */}
      {st.topCats.length > 0 && (
        <section className="sec rise">
          <div className="sec-head"><h2>Where it went</h2><span className="sec-aux"><span className="sec-total">{formatMoney(st.spent, cur)}</span></span></div>
          {st.topCats.map(([cat, amount]) => (
            <div className="row" key={cat}>
              <div className="row-meta"><div className="row-t">{cat}</div></div>
              <div className="row-amt neg">{formatMoney(amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {/* NOTABLE */}
      {(st.biggest || st.debtPaid.length > 0) && (
        <section className="sec rise">
          <div className="sec-head"><h2>Notable</h2></div>
          {st.biggest && (
            <div className="row">
              <span className="row-ic">🧾</span>
              <div className="row-meta">
                <div className="row-t">Biggest purchase — {st.biggest.description || st.biggest.category}</div>
                <div className="row-s">{st.biggest.category} · {friendlyDate(st.biggest.date)}</div>
              </div>
              <div className="row-amt neg">{formatMoney(st.biggest.amount, cur)}</div>
            </div>
          )}
          {st.debtPaid.slice(0, 5).map((p, i) => (
            <div className="row" key={i}>
              <span className="row-ic">🤝</span>
              <div className="row-meta"><div className="row-t">Paid {p.party}</div><div className="row-s">Debt payment</div></div>
              <div className="row-amt pos">−{formatMoney(p.amount, cur)} owed</div>
            </div>
          ))}
        </section>
      )}

      {/* STANDING */}
      <section className="sec rise">
        <div className="sec-head"><h2>Where you stand</h2></div>
        <div className="row">
          <div className="row-meta"><div className="row-t">Net worth today</div></div>
          <div className={"row-amt" + (nw >= 0 ? " pos" : "")}>{formatMoney(nw, cur)}</div>
        </div>
        {nw < 0 && (
          <p className="sec-sub">Below zero is where most wealth stories start — the statement above is what moves it.</p>
        )}
      </section>

      {/* COLOPHON */}
      <div className="flag rise good" style={{ marginTop: 6 }}>
        <span className="flag-txt"><Feather size={13} style={{ display: "inline", marginRight: 6, verticalAlign: "-2px" }} />{st.note}</span>
      </div>

      <p className="sec-sub rise" style={{ textAlign: "center", marginTop: 18 }}>
        <Link href="/ledger" style={{ color: "var(--gold)" }}>Open the full ledger <ArrowRight size={12} style={{ display: "inline" }} /></Link>
      </p>
      <p className="colophon rise">A new statement on the first of every month.</p>
    </main>
  );
}
