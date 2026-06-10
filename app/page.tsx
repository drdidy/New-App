"use client";

import { useEffect, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import {
  ArrowRight,
  ArrowUpRight,
  ArrowDownRight,
  MessageCircleHeart,
  Wallet,
  Landmark,
  Sparkles,
} from "lucide-react";
import { useStore, summarize } from "@/lib/store";
import {
  billsThisMonth,
  netWorth,
  cashOnHand,
  pace,
  quickInsights,
} from "@/lib/insights";
import { formatMoney, friendlyDate } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";
import QuickCapture from "@/components/QuickCapture";

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

const CAT_ICON: Record<string, string> = {
  Groceries: "🛒", Transport: "⛽", Dining: "🍔", Rent: "🏠", Utilities: "💡",
  Salary: "💰", Income: "💰", Shopping: "🛍️", Savings: "🐷", "Debt payment": "🤝",
};

export default function TodayPage() {
  const { data, ready } = useStore();
  const root = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!ready) return;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const ctx = gsap.context(() => {
      gsap.from(".lx-reveal", {
        y: 22,
        opacity: 0,
        duration: 0.6,
        ease: "power3.out",
        stagger: 0.08,
      });
      gsap.from(".lx-hero", {
        scale: 0.96,
        opacity: 0,
        duration: 0.7,
        ease: "back.out(1.6)",
      });
    }, root);
    return () => ctx.revert();
  }, [ready]);

  if (!ready) return null;

  const summary = summarize(data);
  const firstName = data.members[0]?.name?.split(" ")[0] || "there";
  const cash = cashOnHand(data);
  const nw = netWorth(data);
  const daily = pace(data, summary.safeToSpend);
  const bills = billsThisMonth(data).filter((b) => !b.paid);
  const recent = data.transactions.slice(0, 5);
  const goal = data.goals[0];
  const insights = quickInsights(data, data.currency, 2);
  const safePos = summary.safeToSpend >= 0;
  const cur = data.currency;

  return (
    <main className="lx" ref={root}>
      <header className="lx-top lx-reveal">
        <div>
          <p className="lx-eyebrow">{greeting()}, {firstName}</p>
          <h1 className="lx-h1">Today</h1>
        </div>
        <Link href="/coach" className="lx-coachbtn" aria-label="Open coach">
          <MessageCircleHeart size={20} />
        </Link>
      </header>

      {/* HERO */}
      <div className="lx-hero">
        <div className="lx-hero-inner">
          <div className="lx-hero-label">Safe to spend</div>
          <div className={"lx-hero-num " + (safePos ? "pos" : "neg")}>
            <AnimatedNumber value={summary.safeToSpend} currency={cur} />
          </div>
          <div className="lx-hero-sub">
            {safePos
              ? `About ${formatMoney(daily.dailyAllowance, cur)} a day for the ${daily.daysLeft} days ${daily.periodLabel}.`
              : "You're over — tap Coach for a recovery plan."}
          </div>
          <div className="lx-bar"><span style={{ width: `${safePos ? 72 : 16}%` }} /></div>
        </div>
      </div>

      {/* REAL MONEY ROW (balance-first) */}
      <div className="lx-stats lx-reveal">
        <div className="lx-stat">
          <Wallet size={16} className="lx-stat-ic" />
          <div className="lx-stat-num">{formatMoney(cash, cur)}</div>
          <div className="lx-stat-lbl">In your accounts</div>
        </div>
        <div className="lx-stat">
          <Landmark size={16} className="lx-stat-ic" />
          <div className={"lx-stat-num " + (nw >= 0 ? "pos" : "neg")}>{formatMoney(nw, cur)}</div>
          <div className="lx-stat-lbl">Net worth</div>
        </div>
        <Link href="/debt" className="lx-stat">
          <ArrowDownRight size={16} className="lx-stat-ic neg" />
          <div className="lx-stat-num neg">{formatMoney(summary.totalIOwe, cur)}</div>
          <div className="lx-stat-lbl">You owe</div>
        </Link>
      </div>

      {/* IN / OUT */}
      <div className="lx-io lx-reveal">
        <div className="lx-io-item">
          <ArrowUpRight size={15} className="pos" />
          <span className="lx-io-num pos">{formatMoney(summary.income, cur)}</span>
          <span className="lx-io-lbl">In</span>
        </div>
        <div className="lx-io-div" />
        <div className="lx-io-item">
          <ArrowDownRight size={15} className="neg" />
          <span className="lx-io-num neg">{formatMoney(summary.expenses, cur)}</span>
          <span className="lx-io-lbl">Out</span>
        </div>
      </div>

      <div className="lx-reveal"><QuickCapture /></div>

      {insights.length > 0 && (
        <div className="lx-reveal">
          {insights.map((t, i) => (
            <div className="lx-insight" key={i}><Sparkles size={15} /> <span>{t}</span></div>
          ))}
        </div>
      )}

      {bills.length > 0 && (
        <section className="lx-card lx-reveal">
          <div className="lx-card-head"><h2>Bills due</h2><Link href="/bills">Manage</Link></div>
          {bills.slice(0, 3).map((b) => (
            <div className="lx-row" key={b.bill.id}>
              <span className="lx-row-ic">🧾</span>
              <div className="lx-row-meta"><div className="lx-row-t">{b.bill.name}</div><div className="lx-row-s">Due {b.dueDay}</div></div>
              <div className="lx-row-amt neg">{formatMoney(b.bill.amount, cur)}</div>
            </div>
          ))}
        </section>
      )}

      {goal && (
        <section className="lx-card lx-reveal lx-goal">
          <div className="lx-card-head"><h2>{goal.emoji} {goal.name}</h2><Link href="/plan">Plan</Link></div>
          <div className="lx-goal-num">{formatMoney(goal.saved, cur)} <small>of {formatMoney(goal.target, cur)}</small></div>
          <div className="lx-bar"><span style={{ width: `${Math.min(100, (goal.saved / goal.target) * 100)}%` }} /></div>
        </section>
      )}

      <section className="lx-card lx-reveal">
        <div className="lx-card-head"><h2>Recent</h2><Link href="/spending">Insights</Link></div>
        {recent.length === 0 ? (
          <div className="lx-empty">Nothing yet — say <b>“spent 12 on coffee”</b> above.</div>
        ) : recent.map((t) => (
          <div className="lx-row" key={t.id}>
            <span className="lx-row-ic">{CAT_ICON[t.category] || "💸"}</span>
            <div className="lx-row-meta">
              <div className="lx-row-t">{t.description || t.category}</div>
              <div className="lx-row-s">{t.category} · {friendlyDate(t.date)}</div>
            </div>
            <div className={"lx-row-amt " + (t.type === "income" ? "pos" : "neg")}>
              {t.type === "income" ? "+" : "−"}{formatMoney(t.amount, cur)}
            </div>
          </div>
        ))}
      </section>

      <Link href="/coach" className="lx-card lx-cta lx-reveal">
        <div className="lx-cta-ic"><MessageCircleHeart size={22} /></div>
        <div className="lx-cta-meta">
          <div className="lx-cta-t">Ask your money coach</div>
          <div className="lx-cta-s">A plan built on your real numbers.</div>
        </div>
        <ArrowRight size={18} className="lx-cta-arrow" />
      </Link>
    </main>
  );
}
