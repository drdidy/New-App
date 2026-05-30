"use client";

import { useState } from "react";
import { useStore, summarize } from "@/lib/store";
import { quickInsights, billsThisMonth } from "@/lib/insights";
import { formatMoney, friendlyDate } from "@/lib/format";
import AnimatedNumber from "@/components/AnimatedNumber";
import QuickCapture from "@/components/QuickCapture";
import MemberPicker from "@/components/MemberPicker";
import Avatar from "@/components/Avatar";
import Link from "next/link";

const CATEGORY_ICON: Record<string, string> = {
  Groceries: "🛒",
  Transport: "⛽",
  Dining: "🍔",
  Rent: "🏠",
  Utilities: "💡",
  Salary: "💰",
  Income: "💰",
  Shopping: "🛍️",
  Health: "🩺",
  Entertainment: "🎬",
  "Debt payment": "🤝",
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function Home() {
  const { data, ready, deleteTransaction, markBillPaid, member } = useStore();
  const [view, setView] = useState<string | undefined>(undefined);
  if (!ready) return null;

  const multi = data.members.length > 1;
  const s = summarize(data, view);
  const insights = quickInsights(data, data.currency);
  const recent = data.transactions
    .filter((t) => !view || t.memberId === view)
    .slice(0, 10);
  const upcomingBills = billsThisMonth(data, view).filter((b) => !b.paid);
  const safePos = s.safeToSpend >= 0;
  const firstName = data.members[0]?.name?.split(" ")[0];

  return (
    <main>
      <header className="home-head reveal">
        <div>
          <p className="h-sub" style={{ marginBottom: 0 }}>
            {greeting()}{firstName ? `, ${firstName}` : ""}.
          </p>
          <h1 className="h-title">
            {data.householdName ? data.householdName : "Here's where you stand"}
          </h1>
        </div>
        <div className="head-right">
          <div className="avatars">
            {data.members.map((m) => (
              <Avatar key={m.id} member={m} size={34} />
            ))}
          </div>
          <Link href="/settings" className="gear" aria-label="Settings">
            ⚙️
          </Link>
        </div>
      </header>

      {multi && (
        <div className="reveal d1" style={{ marginBottom: 14 }}>
          <MemberPicker
            members={data.members}
            value={view}
            onChange={setView}
            allLabel="Everyone"
            size="sm"
          />
        </div>
      )}

      <div className="card hero reveal d1">
        <div className="label">Safe to spend this month</div>
        <div className={"big " + (safePos ? "pos" : "neg")}>
          <AnimatedNumber value={s.safeToSpend} currency={data.currency} />
        </div>
        <div className="h-sub" style={{ margin: "2px 0 0" }}>
          {safePos
            ? "What's left after expenses and minimum payments."
            : "You're over budget — tap Coach for a plan to recover."}
        </div>
      </div>

      <div className="row reveal d2" style={{ marginBottom: 14 }}>
        <div className="card stat">
          <div className="n in">{formatMoney(s.income, data.currency)}</div>
          <div className="k">In this month</div>
        </div>
        <div className="card stat">
          <div className="n out">{formatMoney(s.expenses, data.currency)}</div>
          <div className="k">Out this month</div>
        </div>
      </div>

      {(s.totalIOwe > 0 || s.totalOwedToMe > 0) && (
        <div className="row reveal d3" style={{ marginBottom: 14 }}>
          <Link href="/debts" className="card stat">
            <div className="n out">{formatMoney(s.totalIOwe, data.currency)}</div>
            <div className="k">You owe</div>
          </Link>
          <Link href="/debts" className="card stat">
            <div className="n in">
              {formatMoney(s.totalOwedToMe, data.currency)}
            </div>
            <div className="k">Owed to you</div>
          </Link>
        </div>
      )}

      {insights.length > 0 && (
        <div className="insight-chips reveal d3">
          {insights.map((t, i) => (
            <div className="insight-chip" key={i}>
              <span className="dot" />
              {t}
            </div>
          ))}
        </div>
      )}

      <div className="reveal d4">
        <QuickCapture />
      </div>

      {upcomingBills.length > 0 && (
        <>
          <div className="section-h">
            <h2>Bills due this month</h2>
            <Link href="/bills">Manage →</Link>
          </div>
          <div className="card">
            {upcomingBills.slice(0, 4).map((b) => (
              <div className="item" key={b.bill.id}>
                <div className="ic">🧾</div>
                <div className="meta">
                  <div className="t">{b.bill.name}</div>
                  <div className="s">
                    Due {b.dueDay}
                    {b.daysAway >= 0 && b.daysAway <= 6
                      ? b.daysAway === 0
                        ? " · today"
                        : ` · in ${b.daysAway}d`
                      : ""}
                  </div>
                </div>
                <div className="amt out">
                  {formatMoney(b.bill.amount, data.currency)}
                </div>
                <button className="bill-pay" onClick={() => markBillPaid(b.bill.id)}>
                  Mark paid
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      <div className="section-h">
        <h2>Recent activity</h2>
        {data.transactions.length > 0 && (
          <Link href="/insights">See insights →</Link>
        )}
      </div>
      <div className="card">
        {recent.length === 0 ? (
          <div className="empty">
            Nothing logged yet. Try typing{" "}
            <strong>&quot;spent 12 on coffee&quot;</strong> above.
          </div>
        ) : (
          recent.map((t) => {
            const m = member(t.memberId);
            return (
              <div className="item" key={t.id}>
                <div className="ic">{CATEGORY_ICON[t.category] || "💸"}</div>
                <div className="meta">
                  <div className="t">{t.description || t.category}</div>
                  <div className="s">
                    {t.category} · {friendlyDate(t.date)}
                    {multi && m ? ` · ${m.emoji} ${m.name.split(" ")[0]}` : ""}
                  </div>
                </div>
                <div className={"amt " + (t.type === "income" ? "in" : "out")}>
                  {t.type === "income" ? "+" : "−"}
                  {formatMoney(t.amount, data.currency)}
                </div>
                <button
                  className="x"
                  onClick={() => deleteTransaction(t.id)}
                  aria-label="Delete"
                >
                  ×
                </button>
              </div>
            );
          })
        )}
      </div>

      <div className="section-h">
        <h2>Need a hand?</h2>
        <Link href="/advisor">Open Coach →</Link>
      </div>
      <Link href="/advisor" className="card coach-cta" style={{ display: "block" }}>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <div className="ic" style={{ width: 44, height: 44, fontSize: 22 }}>
            💬
          </div>
          <div className="meta">
            <div className="t">Ask your AI money coach</div>
            <div className="s">
              Get a debt payoff plan and advice based on your real numbers.
            </div>
          </div>
          <div className="chev">→</div>
        </div>
      </Link>
    </main>
  );
}
