"use client";

import { useStore, summarize } from "@/lib/store";
import { formatMoney, friendlyDate } from "@/lib/format";
import QuickCapture from "@/components/QuickCapture";
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
  "Debt payment": "🤝",
};

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function Home() {
  const { data, ready, deleteTransaction } = useStore();
  if (!ready) return null;

  const s = summarize(data);
  const recent = data.transactions.slice(0, 8);
  const safePos = s.safeToSpend >= 0;

  return (
    <main>
      <p className="h-sub" style={{ marginBottom: 0 }}>
        {greeting()}.
      </p>
      <h1 className="h-title">Here&apos;s where you stand</h1>

      <div className="card hero">
        <div className="label">Safe to spend this month</div>
        <div className={"big " + (safePos ? "pos" : "neg")}>
          {formatMoney(s.safeToSpend, data.currency)}
        </div>
        <div className="h-sub" style={{ margin: "2px 0 0" }}>
          {safePos
            ? "What's left after expenses and minimum payments."
            : "You're over budget — tap Coach for a plan to recover."}
        </div>
      </div>

      <div className="row" style={{ marginBottom: 14 }}>
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
        <div className="row" style={{ marginBottom: 14 }}>
          <div className="card stat">
            <div className="n out">{formatMoney(s.totalIOwe, data.currency)}</div>
            <div className="k">You owe</div>
          </div>
          <div className="card stat">
            <div className="n in">
              {formatMoney(s.totalOwedToMe, data.currency)}
            </div>
            <div className="k">Owed to you</div>
          </div>
        </div>
      )}

      <QuickCapture />

      <div className="section-h">
        <h2>Recent activity</h2>
      </div>
      <div className="card">
        {recent.length === 0 ? (
          <div className="empty">
            Nothing logged yet. Try typing{" "}
            <strong>&quot;spent 12 on coffee&quot;</strong> above.
          </div>
        ) : (
          recent.map((t) => (
            <div className="item" key={t.id}>
              <div className="ic">{CATEGORY_ICON[t.category] || "💸"}</div>
              <div className="meta">
                <div className="t">{t.description || t.category}</div>
                <div className="s">
                  {t.category} · {friendlyDate(t.date)}
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
          ))
        )}
      </div>

      <div className="section-h">
        <h2>Need a hand?</h2>
        <Link href="/advisor">Open Coach →</Link>
      </div>
      <Link href="/advisor" className="card" style={{ display: "block" }}>
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
        </div>
      </Link>
    </main>
  );
}
